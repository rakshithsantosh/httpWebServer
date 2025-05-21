# server.py

import socket
import os

HOST = '127.0.0.1'
PORT = 8080
STATIC_FILES_DIR = 'static'

# Define common HTTP status codes and their messages
STATUS_CODES = {
    200: "OK",
    400: "Bad Request",
    404: "Not Found",
    500: "Internal Server Error"
}

# Helper to determine Content-Type based on file extension
def get_content_type(file_path):
    _, ext = os.path.splitext(file_path)
    if ext == '.html':
        return 'text/html'
    elif ext == '.css':
        return 'text/css'
    elif ext == '.js':
        return 'application/javascript'
    elif ext == '.json':
        return 'application/json'
    elif ext == '.png':
        return 'image/png'
    elif ext == '.jpg' or ext == '.jpeg':
        return 'image/jpeg'
    elif ext == '.gif':
        return 'image/gif'
    elif ext == '.txt':
        return 'text/plain'
    else:
        return 'application/octet-stream' # Default for unknown types

def handle_request(conn):
    try:
        request_data = conn.recv(4096).decode('utf-8')
        if not request_data:
            return

        print(f"\n--- Raw Request ---\n{request_data}\n-------------------")

        # Basic HTTP Request Line Parsing
        # Example: GET /index.html HTTP/1.1
        request_lines = request_data.split('\r\n')
        request_line = request_lines[0]
        parts = request_line.split(' ')

        if len(parts) != 3:
            send_response(conn, 400, "Bad Request", "<h1>400 Bad Request</h1>")
            return

        method, path, http_version = parts

        print(f"Method: {method}, Path: {path}, HTTP Version: {http_version}")

        # Handling static files
        if method == 'GET':
            file_path = os.path.join(STATIC_FILES_DIR, path.lstrip('/')) # Remove leading slash
            if os.path.isdir(file_path): # If path is a directory, serve index.html within it
                file_path = os.path.join(file_path, 'index.html')

            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    with open(file_path, 'rb') as f: # Read in binary mode
                        content = f.read()
                    content_type = get_content_type(file_path)
                    send_response(conn, 200, "OK", content, content_type=content_type)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    send_response(conn, 500, "Internal Server Error", "<h1>500 Internal Server Error</h1>")
            else:
                send_response(conn, 404, "Not Found", "<h1>404 Not Found</h1>")
        else:
            # For now, only GET is supported for static files
            send_response(conn, 400, "Bad Request", f"<h1>400 Bad Request: Method {method} not supported for static files.</h1>")

    except Exception as e:
        print(f"Error handling request: {e}")
        send_response(conn, 500, "Internal Server Error", "<h1>500 Internal Server Error</h1>")

def send_response(conn, status_code, status_message, body, content_type='text/html'):
    # Prepare HTTP headers
    headers = [
        f"HTTP/1.1 {status_code} {status_message}",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body) if isinstance(body, bytes) else len(body.encode('utf-8'))}", # Handle bytes or string
        "Connection: close", # Tell the client to close the connection after response
        "\r\n" # CRLF to separate headers from body
    ]
    response_headers = "\r\n".join(headers).encode('utf-8')

    # Send headers
    conn.sendall(response_headers)

    # Send body
    if isinstance(body, str):
        conn.sendall(body.encode('utf-8'))
    elif isinstance(body, bytes):
        conn.sendall(body)


def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows reusing the address quickly
        s.bind((HOST, PORT))
        print(f"Server listening on {HOST}:{PORT}")
        s.listen(5)

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                handle_request(conn) # Process the client request
            print(f"Connection with {addr} closed.")

if __name__ == "__main__":
    if not os.path.exists(STATIC_FILES_DIR):
        os.makedirs(STATIC_FILES_DIR)
        print(f"Created static files directory: {STATIC_FILES_DIR}")
    run_server()