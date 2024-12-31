# QuicConnection.py

import asyncio
import random
import socket
import time
from collections import deque
from Packet import Packet, PACKET_H_MAX_SIZE
from Frame import Frame, HANDSHAKE, ACK, DATA, CLOSE, FRAME_H_SIZE
from Stream import Stream

KB = 1024
MB = 1024 * KB
MAX_PACKET_SIZE = 8 * KB  # 8 KB


class QuicConnection:

    def __init__(self, addr=None, r_addr=None):
        self.addr = addr
        self.r_addr = r_addr
        self.con_id = random.randint(0, 2**16 - 1)
        self.r_con_id = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if addr:
            self.sock.bind(self.addr)
        self.streams = {}
        self.packet_number = 0
        self.main_frame_queue = deque()
        self.other_frame_queue = deque()
        self.received_frame_queue = deque()
        self.acknowledged_packets = set()
        self.main_stream = Stream(0, connection=self)
        self.bytes_sent = 0
        self.closed = False

        # Start the frame sender task if an event loop is running
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(self.send_frames())

    async def connect(self, _test_mode=False):
        print("Client initiating handshake with server...")
        self.sock.connect(self.r_addr)
        await self.initiate_handshake(_test_mode)

        while self.r_con_id is None:
            await asyncio.sleep(0.01)
        print("Client connected to server with remote connection ID:", self.r_con_id)

    async def listen(self, _test_mode=False):
        loop = asyncio.get_running_loop()
        print("Listening for initial connection setup...")
        while not self.closed:
            data, addr = await loop.run_in_executor(None, self.sock.recvfrom, 2048)
            await self.handle_packet(data, addr)
            if self.r_con_id is not None:
                print("Handshake completed. Ready to receive packets.")
                if not _test_mode:
                    asyncio.create_task(self.recv_packet_continuously())
                break

    async def recv_packet(self):
        loop = asyncio.get_running_loop()
        try:
            data, addr = await loop.run_in_executor(None, self.sock.recvfrom, MAX_PACKET_SIZE)
            await self.handle_packet(data, addr)
        except asyncio.CancelledError:
            print("recv_packet task cancelled")
        except ConnectionRefusedError:
            print("Connection refused by the server.")
            await self.close()
        except Exception as e:
            print(f"Error receiving packet: {e}")

    async def handle_packet(self, data, addr):
        try:
            packet = Packet.from_bytes(data)

            if packet.src_con_id is not None:
                if self.r_con_id is None:
                    for frame in packet.frames:
                        if frame.frame_type == HANDSHAKE:
                            print(f"Connection request received from {addr}")
                            self.r_con_id = packet.src_con_id
                            self.r_addr = addr
                            self.sock.connect(self.r_addr)
                            ack_packet = Packet(
                                header_form=1, flags=0,
                                src_con_id=self.con_id, dest_con_id=self.r_con_id, packet_number=self.packet_number,
                                frames=[
                                    Frame(stream_id=0, data=None, offset=0, frame_type=(HANDSHAKE | ACK))]
                            )
                            await self.send_packet_data(ack_packet)
                            return
                        elif frame.frame_type == (HANDSHAKE | ACK):
                            print(f"Connection established with {addr}")
                            self.r_con_id = packet.src_con_id
                            self.r_addr = addr
                            return
            else:
                if packet.dest_con_id == self.con_id:
                    if packet.packet_number not in self.acknowledged_packets:
                        self.acknowledged_packets.add(packet.packet_number)

                        for frame in packet.frames:
                            if frame.stream_id == 0:
                                if frame.frame_type == CLOSE:
                                    print("Close packet received. Closing connection.")
                                    await self.close()
                                    return

                                if frame.frame_type != ACK:
                                    self.received_frame_queue.append(frame)
                            elif frame.stream_id in self.streams:
                                await self.streams[frame.stream_id].receive_frame(frame)
                                if all(stream.closed for stream in self.streams.values()):
                                    self.etime = time.time()
                                    print("All streams closed. Closing connection.")
                                    await self.close()
                                    return
                            else:
                                print(f"Unknown stream ID: {frame.stream_id}")
        except asyncio.CancelledError:
            print("handle_packet task cancelled")
        except ValueError as e:
            print(f"Error handling packet: {e}")

    async def close(self):
        if self.closed:
            return

        self.closed = True

        try:
            close_frame = Frame(stream_id=0, data=None,
                                offset=0, frame_type=CLOSE)
            close_packet = Packet(
                header_form=0, flags=0,
                dest_con_id=self.r_con_id, packet_number=self.packet_number, frames=[
                    close_frame]
            )
            await self.send_packet_data(close_packet)
            print("Closing connection.")

            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            print("Socket closed.")

            current_task = asyncio.current_task()
            current_task.done()

        except Exception as e:
            print(f"Error during close: {e}")

        return

    async def send_frames(self):
        while not self.closed:
            await self.queue_frames_from_streams()
            await self.send_packet()
            await asyncio.sleep(0.01)

    async def send_packet(self):
        current_size = PACKET_H_MAX_SIZE
        frames_to_send = []

        # Keep track of frames taken from each stream to avoid starvation
        stream_frame_count = {stream_id: 0 for stream_id in self.streams.keys()}

        while current_size < MAX_PACKET_SIZE:
            # Try to add frames from each stream in round-robin manner
            streams_to_consider = list(self.streams.values())
            frames_added = False

            for stream in streams_to_consider:
                frame = stream.get_next_frame()
                if frame:
                    frame_size = frame.length + FRAME_H_SIZE
                    if current_size + frame_size <= MAX_PACKET_SIZE:
                        frames_to_send.append(frame)
                        current_size += frame_size
                        stream_frame_count[stream.stream_id] += 1
                        frames_added = True

            if not frames_added:
                break  # Exit if no frames were added in this round

        if frames_to_send:
            packet = Packet(
                header_form=0, flags=0,
                dest_con_id=self.r_con_id, packet_number=self.packet_number, frames=frames_to_send
            )
            await self.send_packet_data(packet)
            self.packet_number += 1

    async def send_packet_data(self, packet):
        try:
            data = packet.to_bytes()
            self.bytes_sent += len(data)
            await asyncio.get_running_loop().sock_sendall(self.sock, data)
            await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            print("send_packet_data task cancelled")
        except Exception as e:
            print(f"Error sending packet data: {e}")

    async def queue_frame(self, frame):
        if frame.stream_id == 0:
            self.main_frame_queue.append(frame)
        else:
            self.other_frame_queue.append(frame)

    async def initiate_handshake(self, _test_mode=False):
        initial_packet = Packet(
            header_form=1, flags=0,
            src_con_id=self.con_id, dest_con_id=0, packet_number=self.packet_number,
            frames=[Frame(stream_id=0, data=None,
                          offset=0, frame_type=HANDSHAKE)]
        )
        await self.send_packet_data(initial_packet)
        self.packet_number += 1
        if not _test_mode:
            asyncio.create_task(self.recv_packet_continuously())

    def add_stream(self, stream_id, file_path):
        stream = Stream(stream_id, self, file_path)
        self.streams[stream_id] = stream
        asyncio.create_task(stream.generate_frames())

    async def start_streams_request(self, stream_count):
        self.stime = time.time()
        for i in range(1, stream_count + 1):
            self.streams[i] = Stream(i, self, None)

        request_packet = Packet(
            header_form=0, flags=0,
            dest_con_id=self.r_con_id, packet_number=self.packet_number,
            frames=[
                Frame(stream_id=0, data=f"REQUEST_STREAMS:{stream_count}".encode(), offset=0)]
        )
        await self.send_packet_data(request_packet)
        self.packet_number += 1

    async def send(self, data):
        frame = Frame(stream_id=0, data=data, offset=0)
        await self.queue_frame(frame)

    async def recv(self):
        while not self.closed:
            if self.received_frame_queue:
                frame = self.received_frame_queue.popleft()
                if frame.frame_type == CLOSE:
                    print("Received close Packet. Closing connection.")
                    await self.close()
                    return None
                return frame
            else:
                await asyncio.sleep(0.01)
        return None

    async def queue_frames_from_streams(self):
        for stream_id, stream in self.streams.items():
            if stream_id == 0:
                continue
            if not any(frame.stream_id == stream_id for frame in self.other_frame_queue):
                frame = stream.get_next_frame()
                if frame:
                    self.other_frame_queue.append(frame)

    async def recv_packet_continuously(self):
        while not self.closed:
            await self.recv_packet()
            await asyncio.sleep(0.01)
