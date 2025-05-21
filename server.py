#server.py

import socket

HOST = '127.0.0.1' #Localhost | standard loopback interface address
PORT = 8000

def run_server():
     # 1. Create a socket
    # AF_INET specifies the address family (IPv4)
    # SOCK_STREAM specifies the socket type (TCP)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
         # 2. Bind the socket to the host and port
        s.bind((HOST, PORT))
        print(f"Server listening on {HOST}:{PORT}")

        # 3. Listen for incoming connections
        # The '5' is the backlog argument, specifying the maximum number of
        # queued connections.
        s.listen(5)

        while True:
            # 4. Accept a new connection
            # This is a blocking call; it waits until a client connects.
            # conn is a new socket object representing the connection to the client.
            # addr is a tuple (host, port) of the client.
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                # 5. Read data from the client
                # 1024 is the buffer size in bytes.
                data = conn.recv(1024)
                if not data:
                    break # Client disconnected
                print(f"Received from client: {data.decode('utf-8')}")

                # 6. Send a response back to the client
                # For now, just echo back what we received.
                response = f"Hello, client! You sent: {data.decode('utf-8')}"
                conn.sendall(response.encode('utf-8'))

if __name__ == "__main__":
    run_server()