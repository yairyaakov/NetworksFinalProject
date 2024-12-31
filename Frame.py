# frame.py

import struct

HANDSHAKE = 1
ACK = 2
DATA = 4
CLOSE = 8

FRAME_H_SIZE = 9
class Frame:
    def __init__(self, stream_id, data, offset, frame_type=DATA):
        self.frame_type = frame_type & 0xFF  # Ensure frame_type is 1 byte (max value 255)
        self.stream_id = stream_id
        self.data = data or b''  # Ensure data is always bytes, even if None
        self.offset = offset
        self.length = len(self.data)  # Length of the data only

    def to_bytes(self):
        try:
            # Pack the metadata using struct
            metadata = struct.pack('!BIIH', self.frame_type, self.stream_id, self.offset, self.length)
            # Append the actual data
            serialized_data = metadata + self.data
            return serialized_data
        except struct.error as e:
            print(f"Error serializing frame to bytes: {e}")
            return b''

    @staticmethod
    def from_bytes(data):
        try:
            # Ensure there's enough data for the metadata
            if len(data) < struct.calcsize('!BIIH'):
                raise ValueError("Data too short to unpack frame metadata")

            # Unpack the metadata
            frame_type, stream_id, offset, length = struct.unpack('!BIIH', data[:struct.calcsize('!BIIH')])

            frame_data = data[struct.calcsize('!BIIH'):struct.calcsize('!BIIH') + length]
            # Ensure the length of the data matches the length in the metadata
            if len(frame_data) != length:
                raise ValueError("Incorrect frame data length")
            
            # Return the frame and the remaining data
            return Frame(stream_id, frame_data, offset, frame_type), data[struct.calcsize('!BIIH') + length:]
        
        except (struct.error, ValueError) as e:
            print(f"Error deserializing frame from bytes: {e}")
            raise ValueError("Incorrect frame format")
