# quic_server.py

import asyncio
from QuicConnection import QuicConnection
from sys import argv


async def quic_server(port):
    server = QuicConnection(('127.0.0.1', port), None)
    
    await server.listen()

    while True:
        if server.closed:
            break
        frame = await server.recv()
        if frame:
            print(f"Received frame from client: {frame.data}")
            if frame.data.startswith(b'REQUEST_STREAMS:'):
                try:
                    stream_count = int(frame.data.split(b':')[1])
                    print(f"Received request to start {stream_count} streams.")
                    for i in range(stream_count):
                        server.add_stream(i + 1, f"files_to_send/file_{i + 1}.txt")
                except ValueError as e:
                    print(f"Invalid stream request: {e}")
        await asyncio.sleep(0.01)

if __name__ == "__main__":
    if len(argv) != 2:
        print("Usage: python quic_server.py <port>")
        exit(1)
        
    try:
        port = int(argv[1])
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        exit(1)
        
    
    asyncio.run(quic_server(port))
