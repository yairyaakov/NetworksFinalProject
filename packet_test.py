# test_packet.py

import unittest
import struct
from Packet import Packet
from Frame import Frame, HANDSHAKE, ACK, DATA, CLOSE

class TestPacket(unittest.TestCase):

    def setUp(self):
        """Set up example packets for testing."""
        self.frame_data = b'Hello, QUIC!'
        self.frame1 = Frame(stream_id=1, data=self.frame_data, offset=0, frame_type=DATA)
        self.frame2 = Frame(stream_id=1, data=b'', offset=13, frame_type=ACK)

        # Packet with frames and a long header
        self.packet_long_header = Packet(
            header_form=1, flags=0,
            src_con_id=1234, dest_con_id=5678,
            packet_number=1, frames=[self.frame1, self.frame2]
        )

        # Packet with frames and a short header
        self.packet_short_header = Packet(
            header_form=0, flags=0,
            dest_con_id=5678,
            packet_number=1, frames=[self.frame1]
        )

    def test_to_bytes_long_header(self):
        """Test serialization of a Packet object with a long header to bytes."""
        serialized = self.packet_long_header.to_bytes()
        self.assertIsInstance(serialized, bytes, "Serialized packet should be of type bytes")
        self.assertTrue(len(serialized) > 0, "Serialized packet should not be empty")

        # Calculate expected length
        expected_length = struct.calcsize('!BIII') + self.frame1.to_bytes().__len__() + self.frame2.to_bytes().__len__()
        self.assertEqual(len(serialized), expected_length, "Serialized packet length mismatch for long header")

    def test_to_bytes_short_header(self):
        """Test serialization of a Packet object with a short header to bytes."""
        serialized = self.packet_short_header.to_bytes()
        self.assertIsInstance(serialized, bytes, "Serialized packet should be of type bytes")
        self.assertTrue(len(serialized) > 0, "Serialized packet should not be empty")

        # Calculate expected length
        expected_length = struct.calcsize('!BII') + self.frame1.to_bytes().__len__()
        self.assertEqual(len(serialized), expected_length, "Serialized packet length mismatch for short header")

    def test_from_bytes_long_header(self):
        """Test deserialization of bytes to a Packet object with a long header."""
        serialized = self.packet_long_header.to_bytes()
        deserialized_packet = Packet.from_bytes(serialized)

        self.assertIsInstance(deserialized_packet, Packet, "Deserialized object should be of type Packet")
        self.assertEqual(deserialized_packet.header_form, self.packet_long_header.header_form, "Header form mismatch after deserialization")
        self.assertEqual(deserialized_packet.src_con_id, self.packet_long_header.src_con_id, "Source Connection ID mismatch after deserialization")
        self.assertEqual(deserialized_packet.dest_con_id, self.packet_long_header.dest_con_id, "Destination Connection ID mismatch after deserialization")
        self.assertEqual(deserialized_packet.packet_number, self.packet_long_header.packet_number, "Packet number mismatch after deserialization")
        self.assertEqual(len(deserialized_packet.frames), len(self.packet_long_header.frames), "Frame count mismatch after deserialization")

    def test_from_bytes_short_header(self):
        """Test deserialization of bytes to a Packet object with a short header."""
        serialized = self.packet_short_header.to_bytes()
        deserialized_packet = Packet.from_bytes(serialized)

        self.assertIsInstance(deserialized_packet, Packet, "Deserialized object should be of type Packet")
        self.assertEqual(deserialized_packet.header_form, self.packet_short_header.header_form, "Header form mismatch after deserialization")
        self.assertIsNone(deserialized_packet.src_con_id, "Source Connection ID should be None for short header")
        self.assertEqual(deserialized_packet.dest_con_id, self.packet_short_header.dest_con_id, "Destination Connection ID mismatch after deserialization")
        self.assertEqual(deserialized_packet.packet_number, self.packet_short_header.packet_number, "Packet number mismatch after deserialization")
        self.assertEqual(len(deserialized_packet.frames), len(self.packet_short_header.frames), "Frame count mismatch after deserialization")

    def test_incorrect_data_deserialization(self):
        """Test deserialization with incorrect data length."""
        serialized = self.packet_long_header.to_bytes()
        
        # Corrupt the packet by cutting off part of the data
        corrupted_serialized = serialized[:-5]

        with self.assertRaises(ValueError) as cm:
            Packet.from_bytes(corrupted_serialized)
        self.assertEqual(str(cm.exception), "Incorrect packet format")

    def test_add_frame(self):
        """Test adding a frame to a packet."""
        packet = Packet(header_form=0, flags=0, dest_con_id=5678, packet_number=1)
        initial_frame_count = len(packet.frames)
        packet.add_frame(self.frame1)
        self.assertEqual(len(packet.frames), initial_frame_count + 1, "Frame count did not increase after adding a frame")
        self.assertEqual(packet.frames[-1], self.frame1, "Last frame in packet does not match the added frame")

if __name__ == "__main__":
    unittest.main()
