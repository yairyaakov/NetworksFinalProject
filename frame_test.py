# test_frame.py

import unittest
import struct
from Frame import Frame, HANDSHAKE, ACK, DATA, CLOSE

class TestFrame(unittest.TestCase):
    
    def setUp(self):
        """Set up example frames for testing."""
        self.frame_data = b'Hello, QUIC!'  # Example data for frame
        self.frame = Frame(stream_id=1, data=self.frame_data, offset=0, frame_type=DATA)
        self.empty_frame = Frame(stream_id=1, data=b'', offset=0, frame_type=DATA)

    def test_to_bytes(self):
        """Test the serialization of a Frame object to bytes."""
        serialized = self.frame.to_bytes()
        self.assertIsInstance(serialized, bytes, "Serialized frame should be of type bytes")
        self.assertTrue(len(serialized) > 0, "Serialized frame should not be empty")
        
        # Manually calculate the expected length
        expected_length = struct.calcsize('!BIIH') + len(self.frame_data)  # metadata size + data length
        self.assertEqual(len(serialized), expected_length, "Serialized frame length mismatch")

    def test_from_bytes(self):
        """Test the deserialization of bytes to a Frame object."""
        serialized = self.frame.to_bytes()
        deserialized_frame, remaining_data = Frame.from_bytes(serialized)
        
        self.assertIsInstance(deserialized_frame, Frame, "Deserialized object should be of type Frame")
        self.assertEqual(deserialized_frame.stream_id, self.frame.stream_id, "Stream ID mismatch after deserialization")
        self.assertEqual(deserialized_frame.offset, self.frame.offset, "Offset mismatch after deserialization")
        self.assertEqual(deserialized_frame.data, self.frame.data, "Data mismatch after deserialization")
        self.assertEqual(deserialized_frame.frame_type, self.frame.frame_type, "Frame type mismatch after deserialization")
        self.assertEqual(remaining_data, b'', "There should be no remaining data after full deserialization")

    def test_empty_frame_serialization(self):
        """Test serialization and deserialization of an empty frame."""
        serialized = self.empty_frame.to_bytes()
        deserialized_frame, remaining_data = Frame.from_bytes(serialized)
        
        self.assertEqual(deserialized_frame.data, b'', "Empty frame data mismatch after deserialization")
        self.assertEqual(deserialized_frame.length, 0, "Empty frame length mismatch after deserialization")

    def test_incorrect_length_deserialization(self):
        """Test deserialization with incorrect length in metadata."""
        serialized = self.frame.to_bytes()
        
        # Corrupt the length part of the serialized data (set it to a higher value than actual)
        corrupted_serialized = serialized[:9] + struct.pack('!H', 1000) + serialized[11:]  # Change length to 1000

        with self.assertRaises(ValueError) as cm:
            Frame.from_bytes(corrupted_serialized)
        self.assertEqual(str(cm.exception), "Incorrect frame format")

    def test_incomplete_data_deserialization(self):
        """Test deserialization with incomplete data."""
        serialized = self.frame.to_bytes()
        
        # Provide only a part of the serialized data (incomplete data)
        incomplete_serialized = serialized[:5]  # Cut off data in the middle
        
        with self.assertRaises(ValueError) as cm:
            Frame.from_bytes(incomplete_serialized)
        self.assertEqual(str(cm.exception), "Incorrect frame format")

    def test_min_max_values(self):
        """Test frame serialization/deserialization with min and max values for stream_id and offset."""
        max_int_frame = Frame(stream_id=2**31-1, data=self.frame_data, offset=2**31-1, frame_type=HANDSHAKE)
        serialized = max_int_frame.to_bytes()
        deserialized_frame, remaining_data = Frame.from_bytes(serialized)

        self.assertEqual(deserialized_frame.stream_id, max_int_frame.stream_id, "Stream ID mismatch for max int value")
        self.assertEqual(deserialized_frame.offset, max_int_frame.offset, "Offset mismatch for max int value")

        min_int_frame = Frame(stream_id=0, data=b'', offset=0, frame_type=CLOSE)
        serialized = min_int_frame.to_bytes()
        deserialized_frame, remaining_data = Frame.from_bytes(serialized)

        self.assertEqual(deserialized_frame.stream_id, min_int_frame.stream_id, "Stream ID mismatch for min int value")
        self.assertEqual(deserialized_frame.offset, min_int_frame.offset, "Offset mismatch for min int value")
        self.assertEqual(deserialized_frame.data, min_int_frame.data, "Data mismatch for min int value")

if __name__ == "__main__":
    unittest.main()
