# Stream.py

import asyncio
from Frame import *
import random
import time

class Stream:
    def __init__(self, stream_id, connection, file_path=None):
        self.stream_id = stream_id
        self.file_path = file_path or f"files_received/temp_stream_{stream_id}.txt"
        self.connection = connection
        self.received_data = b''
        self.frame_size = random.randint(1000, 2000)
        self.frames = []
        self.frames_received = 0
        self.bytes_received = 0
        self.bytes_sent = 0
        self.closed = False
        self.stime = None  # Start time for the stream
        self.etime = None  # End time for the stream

    async def generate_frames(self):
        """Simulate frame generation for sending (this is a placeholder for actual logic)."""
        with open(self.file_path, 'rb') as f:
            data = f.read()
            for i in range(0, len(data), self.frame_size):
                frame_data = data[i:i + self.frame_size]
                frame = Frame(self.stream_id, frame_data, i)
                self.frames.append(frame)

            last_frame = Frame(self.stream_id, b'', len(data), frame_type=CLOSE)
            self.frames.append(last_frame)
    
    def get_next_frame(self):
        if self.frames:
            if self.stime is None:
                self.stime = time.time()  # Record start time when sending the first frame
            frame = self.frames.pop(0)
            self.bytes_sent += frame.length
            return frame
        return None  # Only return None when no more frames are available

    async def receive_frame(self, frame):
        if self.stime is None:
            self.stime = time.time()  # Record start time when receiving the first frame
        
        self.received_data += frame.data
        self.bytes_received += frame.length
        self.frames_received += 1

        if frame.frame_type == CLOSE:
            if not self.closed:
                self.etime = time.time()  # Set end time only on receiving the CLOSE frame
                print(f"Stream {self.stream_id} reception completed.")
                self.closed = True  # Mark stream as closed

    async def save_to_file(self):
        print(f"Saving stream {self.stream_id} data to {self.file_path}.")
        try:
            with open(self.file_path, 'wb') as f:
                f.write(self.received_data)
        except Exception as e:
            print(f"Error saving stream data to file: {e}")

    def print_stats(self):
        print(f"Stream {self.stream_id} stats:")
        print(f"Frames received: {self.frames_received}")
        print(f"Bytes received: {self.bytes_received}")
        print(f"Bytes sent: {self.bytes_sent}")
        if self.stime and self.etime:
            print(f"Time taken: {(self.etime - self.stime):.2f} seconds")
            print(f"Avg. Bytes Throughput: {self.bytes_received/(self.etime - self.stime):.2f} bytes/sec")
            print(f"Avg. Frames Throughput: {self.frames_received/(self.etime - self.stime):.2f} frames/sec)")
        else:
            print("Stream not fully completed yet.")

