# packet.py

import struct
from Frame import Frame

PACKET_H_MAX_SIZE = 13
class Packet:
    def __init__(self, header_form, flags, dest_con_id, packet_number, src_con_id=None, frames=None):
        self.header_form = header_form
        self.flags = flags
        self.src_con_id = src_con_id
        self.dest_con_id = dest_con_id
        self.packet_number = packet_number
        self.frames = frames if frames is not None else []

    def to_bytes(self):
        try:
            if self.src_con_id is not None:
                header = struct.pack(
                    "!BIII",
                    (self.header_form << 7) | (self.flags & 0x7F),
                    self.src_con_id,
                    self.dest_con_id,
                    self.packet_number
                )
            else:
                header = struct.pack(
                    "!BII",
                    (self.header_form << 7) | (self.flags & 0x7F),
                    self.dest_con_id,
                    self.packet_number
                )

            frames_data = b''.join(frame.to_bytes() for frame in self.frames)
            return header + frames_data
        except struct.error as e:
            print(f"Error serializing packet to bytes: {e}")
            return b''

    @staticmethod
    def from_bytes(data):
        try:
            header_form = data[0] >> 7
            flags = data[0] & 0x7F

            if header_form == 1:
                src_con_id = struct.unpack("!I", data[1:5])[0]
                dest_con_id = struct.unpack("!I", data[5:9])[0]
                packet_number = struct.unpack("!I", data[9:13])[0]
                frames_data = data[13:]
            else:
                dest_con_id = struct.unpack("!I", data[1:5])[0]
                packet_number = struct.unpack("!I", data[5:9])[0]
                frames_data = data[9:]

            frames = []
            while frames_data:
                frame, frames_data = Frame.from_bytes(frames_data)
                frames.append(frame)

            return Packet(header_form, flags, dest_con_id, packet_number, src_con_id if header_form == 1 else None, frames)
        except (struct.error, ValueError) as e:
            print(f"Error deserializing packet from bytes: {e}")
            raise ValueError("Incorrect packet format")

    def add_frame(self, frame):
        self.frames.append(frame)
