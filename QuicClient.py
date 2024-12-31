# quic_client.py

import asyncio
from QuicConnection import QuicConnection , KB, MB
from sys import argv
import socket
async def run_client(client , num_of_streams):
    """Function to run the QUIC client operations."""
    await client.connect()
    await client.start_streams_request(stream_count=num_of_streams)

    try:
        while not client.closed:
            frame = await client.recv()
            if frame:
                print(f"Received frame from server: {frame.data}")
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        print("Connection is Closed, Printing Statistics and graphs")
    except Exception as e:
        print(f"Quic client error: {e}")


async def main(host, server_port, num_of_streams):
    """Main function to initialize and run the client."""
    client = QuicConnection(r_addr=(host, server_port))

    try:
        await run_client(client , num_of_streams)
    except KeyboardInterrupt:
        print("Quic client stopped.")
    finally:
        # Perform any cleanup or statistics gathering here
        if client.closed:
            print("Client is closed. Finalizing...")
        else:
            await client.close()  # Ensure the client is closed properly

    return client  # Return the client object for further use

if __name__ == "__main__":
    if len(argv) != 4:
        print("Usage: python quic_client.py <host> <port> <num_of_streams>")
        exit(1)
    
    try:
        host = socket.gethostbyname(argv[1])
        server_port = int(argv[2])
        num_of_streams = int(argv[3])
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        exit
    
    
    client = None
    try:
        # Run the main function and get the client
        client = asyncio.run(main(host, server_port, num_of_streams))
    except KeyboardInterrupt:
        print("Quic client stopped.")
    except Exception as e:
        print(f"Quic client error: {e}")

    if client is None:
        exit(1)
    # print the statistics

    with open(f"stats/client_{client.streams.__len__()}_streams_stats.txt", "w") as f:
        for stream in client.streams.values():
            f.write(f"Stream {stream.stream_id}:\n")
            f.write(f"Frames received: {stream.frames_received}\n")
            f.write(f"Bytes received: {stream.bytes_received}\n")
            f.write(
                f"Time taken: {(stream.etime - stream.stime):.2f} seconds\n\n")
            f.write(
                f"Avg. Bytes Throughput: {stream.bytes_received/(stream.etime - stream.stime):.2f} bytes/sec\n\n")
            f.write(
                f"Avg. Frames Throughput: {stream.frames_received/(stream.etime - stream.stime):.2f} frames/sec\n\n")

            stream.print_stats()
            print()

        total_bytes_received = sum(
            stream.bytes_received for stream in client.streams.values())
        total_frames_received = sum(
            stream.frames_received for stream in client.streams.values())

        f.write(f"Total bytes sent: {client.bytes_sent}\n")
        f.write(f"Total bytes received: {total_bytes_received}\n")
        f.write(f"Total frames received: {total_frames_received}\n")
        f.write(
            f"Total time taken: {(client.etime - client.stime):.2f} seconds\n")
        f.write(f"Total Avg. Frames Throughput: {round(total_frames_received/(client.etime - client.stime))} frames/sec\n\n")
        avg_bytes_throughput = total_bytes_received / (client.etime - client.stime)
        
        if avg_bytes_throughput < KB:
            f.write(f"Total Avg. Bytes Throughput: {avg_bytes_throughput:.2f} bytes/sec\n")
            print(f"Total Avg. Bytes Throughput: {avg_bytes_throughput:.2f} bytes/sec")
        elif avg_bytes_throughput < MB:
            f.write(f"Total Avg. Bytes Throughput: {avg_bytes_throughput/KB:.2f} KB/sec\n")
            print(f"Total Avg. Bytes Throughput: {avg_bytes_throughput/KB:.2f} KB/sec")
        else:
            f.write(f"Total Avg. Bytes Throughput: {avg_bytes_throughput/MB:.2f} MB/sec\n")
            print(f"Total Avg. Bytes Throughput: {avg_bytes_throughput/MB:.2f} MB/sec")
            
        
        print(f"Total bytes sent: {client.bytes_sent}")
        print(f"Total bytes received: {total_bytes_received}")
        print(f"Total frames received: {total_frames_received}")
        print(f"Total time taken: {(client.etime - client.stime):.2f} seconds")
        print(
            f"Total Avg. Frames Throughput: {round(total_frames_received/(client.etime - client.stime))} frames/sec")
