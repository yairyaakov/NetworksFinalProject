import random

MB = 1024 * 1024
if __name__ == "__main__":
    # Generate a random number between 1 and 100
    # create a file with size of random number * MB (1 MB = 1024 * 1024 bytes)
    
    for i in range(1, 11):
        random_number = random.randint(2,5)
        with open(f"files_to_send/file_{i}.txt", 'wb') as f:
            f.write(b'0' * (random_number * MB))
            print(f"Generated file_{i}.txt with size {random_number} MB.")