# server.py (with threading)

import socket
import os
import threading
import json # For API responses

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

# --- Routing System ---
# A dictionary to store API routes: { (method, path): handler_function }
ROUTES = {}

def route(method, path):
    def decorator(func):
        ROUTES[(method.upper(), path)] = func
        return func
    return decorator

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

def parse_request(request_data):
    """Parses raw HTTP request data into a dictionary."""
    lines = request_data.split('\r\n')
    request_line = lines[0].split(' ')
    if len(request_line) != 3:
        return None # Malformed request line

    method, path, http_version = request_line
    headers = {}
    body_start_index = -1
    for i, line in enumerate(lines[1:]):
        if line == '': # Empty line indicates end of headers
            body_start_index = i + 2 # +2 for request line and header section
            break
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()

    body = '\r\n'.join(lines[body_start_index:]) if body_start_index != -1 else ''

    return {
        'method': method,
        'path': path,
        'http_version': http_version,
        'headers': headers,
        'body': body
    }

def send_response(conn, status_code, status_message, body, content_type='text/html'):
    headers = [
        f"HTTP/1.1 {status_code} {status_message}",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body) if isinstance(body, bytes) else len(body.encode('utf-8'))}",
        "Connection: close",
        "\r\n"
    ]
    response_headers = "\r\n".join(headers).encode('utf-8')

    conn.sendall(response_headers)
    if isinstance(body, str):
        conn.sendall(body.encode('utf-8'))
    elif isinstance(body, bytes):
        conn.sendall(body)

def handle_client_connection(conn, addr):
    try:
        request_data = conn.recv(4096).decode('utf-8')
        if not request_data:
            return

        print(f"--- Request from {addr} ---")
        # print(request_data) # Uncomment to see full raw request
        print(f"---------------------------\n")

        parsed_request = parse_request(request_data)

        if not parsed_request:
            send_response(conn, 400, "Bad Request", "<h1>400 Malformed Request</h1>")
            return

        method = parsed_request['method']
        path = parsed_request['path']

        # --- API Routing ---
        handler = ROUTES.get((method, path))
        if handler:
            print(f"Dispatching to API handler: {method} {path}")
            # Pass the parsed request data to the handler
            handler(conn, parsed_request)
            return

        # --- Static File Serving (Fallback if no API route matches) ---
        if method == 'GET':
            file_path = os.path.join(STATIC_FILES_DIR, path.lstrip('/'))
            if os.path.isdir(file_path):
                file_path = os.path.join(file_path, 'index.html')

            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    content_type = get_content_type(file_path)
                    send_response(conn, 200, "OK", content, content_type=content_type)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    send_response(conn, 500, "Internal Server Error", "<h1>500 Internal Server Error</h1>")
            else:
                send_response(conn, 404, "Not Found", "<h1>404 Not Found</h1>")
        else:
            send_response(conn, 400, "Bad Request", f"<h1>400 Bad Request: Method {method} not supported for static files.</h1>")

    except Exception as e:
        print(f"Error handling request from {addr}: {e}")
        send_response(conn, 500, "Internal Server Error", "<h1>500 Internal Server Error</h1>")
    finally:
        conn.close() # Ensure connection is closed

# --- Define API Endpoints ---
@route('GET', '/api/hello')
def hello_api(conn, request):
    name = request['headers'].get('X-Name', 'World') # Example of reading a custom header
    response_data = {"message": f"Hello, {name} from API!", "timestamp": threading.current_thread().name}
    send_response(conn, 200, "OK", json.dumps(response_data), content_type='application/json')

@route('GET', '/api/time')
def get_time_api(conn, request):
    import datetime
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response_data = {"current_time": current_time, "thread_name": threading.current_thread().name}
    send_response(conn, 200, "OK", json.dumps(response_data), content_type='application/json')

@route('POST', '/api/echo')
def echo_api(conn, request):
    try:
        request_body = request['body']
        # Try to parse as JSON, otherwise treat as plain text
        try:
            data = json.loads(request_body)
        except json.JSONDecodeError:
            data = {"received_raw_body": request_body}

        response_data = {"status": "success", "echo": data, "method": request['method']}
        send_response(conn, 200, "OK", json.dumps(response_data), content_type='application/json')
    except Exception as e:
        send_response(conn, 400, "Bad Request", json.dumps({"error": str(e)}), content_type='application/json')

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        print(f"Server listening on {HOST}:{PORT}")
        s.listen(5)

        while True:
            conn, addr = s.accept()
            # Create a new thread for each client connection
            client_thread = threading.Thread(
                target=handle_client_connection,
                args=(conn, addr),
                name=f"ClientHandler-{addr[1]}" # Name the thread for debugging
            )
            client_thread.start() # Start the thread
            # conn.close() # Important: Do NOT close the connection here in the main thread.
                         # The thread needs to manage its own connection.

if __name__ == "__main__":
    if not os.path.exists(STATIC_FILES_DIR):
        os.makedirs(STATIC_FILES_DIR)
        print(f"Created static files directory: {STATIC_FILES_DIR}")
    run_server()