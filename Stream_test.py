# test_stream.py

import unittest
import asyncio
import os
from unittest.mock import MagicMock, patch
from Stream import Stream
from Frame import Frame, DATA, CLOSE

class TestStream(unittest.TestCase):

    def setUp(self):
        """Set up example stream for testing."""
        self.file_path = "test_stream_data.txt"
        self.sample_data = b"Hello, this is a test stream data."
        
        # Create a test file with sample data
        with open(self.file_path, 'wb') as f:
            f.write(self.sample_data)
        
        self.connection_mock = MagicMock()  # using dummy connection mock which function as a connection object
        self.stream = Stream(stream_id=1, connection=self.connection_mock, file_path=self.file_path)

    def tearDown(self):
        """Clean up test file after tests."""
        if os.path.exists(self.file_path): # check if file exists
            os.remove(self.file_path) # remove the test file
        if os.path.exists(self.stream.file_path): # check if file exists
            os.remove(self.stream.file_path) # remove the stream file

    def test_generate_frames(self):
        """Test frame generation from file data."""
        asyncio.run(self.stream.generate_frames()) # Generates frames from file data
        
        # Check if frames were generated correctly
        self.assertGreater(len(self.stream.frames), 0, "Frames were not generated correctly.") # check if frames are generated
        self.assertEqual(len(self.stream.frames[-1].data), 0, "Last frame should be a CLOSE frame with no data.") # check if last frame is a CLOSE frame
        self.assertEqual(self.stream.frames[-1].frame_type, CLOSE, "Last frame type should be CLOSE.") # check if last frame type is CLOSE

    def test_get_next_frame(self):
        """Test retrieving the next frame for sending."""
        asyncio.run(self.stream.generate_frames()) # Generates frames from file data
        frame = self.stream.get_next_frame() # Get the next frame

        self.assertIsNotNone(frame, "get_next_frame should return a frame when available.") # check if frame is not None
        self.assertEqual(frame.stream_id, self.stream.stream_id, "Stream ID mismatch in retrieved frame.") # check if stream ID matches
        self.assertEqual(self.stream.bytes_sent, frame.length, "Bytes sent not updated correctly after retrieving frame.") # check if bytes sent is updated correctly
        self.assertIsNotNone(self.stream.stime, "Start time should be set after retrieving first frame.") # check if start time is set

    def test_receive_frame(self):
        """Test processing a received frame."""
        frame_data = b"Test frame data"
        frame = Frame(stream_id=1, data=frame_data, offset=0, frame_type=DATA)
        asyncio.run(self.stream.receive_frame(frame))

        self.assertEqual(self.stream.bytes_received, len(frame_data), "Bytes received not updated correctly after receiving frame.") # check if bytes received is updated correctly
        self.assertEqual(self.stream.frames_received, 1, "Frames received count not updated correctly.") # check if frames received count is updated correctly
        self.assertEqual(self.stream.received_data, frame_data, "Received data not accumulated correctly.") # check if received data is accumulated correctly

    def test_receive_close_frame(self):
        """Test handling of a CLOSE frame."""
        close_frame = Frame(stream_id=1, data=b'', offset=0, frame_type=CLOSE)
        asyncio.run(self.stream.receive_frame(close_frame))

        self.assertTrue(self.stream.closed, "Stream should be marked as closed after receiving a CLOSE frame.") # check if stream is marked as closed
        self.assertIsNotNone(self.stream.etime, "End time should be set after receiving CLOSE frame.") # check if end time is set

    def test_save_to_file(self):
        """Test saving received data to file."""
        frame_data = b"Test frame data"
        frame = Frame(stream_id=1, data=frame_data, offset=0, frame_type=DATA)
        asyncio.run(self.stream.receive_frame(frame)) # receive frame to save data
        asyncio.run(self.stream.save_to_file()) # save data to file

        self.assertTrue(os.path.exists(self.stream.file_path), "File should be created after saving data.") # check if file is created
        with open(self.stream.file_path, 'rb') as f:
            saved_data = f.read() 
        self.assertEqual(saved_data, frame_data, "Saved data does not match received data.") # check if saved data matches received data

    def test_print_stats(self):
        """Test printing of stream statistics."""
        frame_data = b"Test frame data" 
        close_frame = Frame(stream_id=1, data=b'', offset=0, frame_type=CLOSE)

        # Simulate receiving frames
        asyncio.run(self.stream.receive_frame(Frame(stream_id=1, data=frame_data, offset=0, frame_type=DATA)))
        asyncio.run(self.stream.receive_frame(close_frame))

        with patch('builtins.print') as mock_print: # patch is used to mock the print function, we can now check if the print function is called
            self.stream.print_stats() # print stream statistics
            mock_print.assert_any_call(f"Stream {self.stream.stream_id} stats:") # check if stream ID is printed
            mock_print.assert_any_call(f"Frames received: {self.stream.frames_received}") # check if frames received is printed
            mock_print.assert_any_call(f"Bytes received: {self.stream.bytes_received}") # check if bytes received is printed
            mock_print.assert_any_call(f"Bytes sent: {self.stream.bytes_sent}") # check if bytes sent is printed

if __name__ == "__main__":
    unittest.main()
