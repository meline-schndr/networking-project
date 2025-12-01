import os
import json
import socket

def run_web_server_thread(stats, host='localhost', port=10000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    sock.bind((host, port))
    sock.listen(1)
    print(f"[WEB] > INFO: Dashboard actif sur http://localhost:{port}")

    WEB_DIR = os.path.dirname(os.path.abspath(f"{__file__}"))
    

    while True:
        try:
            conn, addr = sock.accept()
            request = conn.recv(1024).decode('utf-8')
            
            if not request: continue
            first_line = request.split('\n')[0]
            method, path, _ = first_line.split(' ')

            response_header = ""
            response_body = b""
            content_type = "text/html"

            
            if path == '/api/stats':
                content_type = "application/json"
                data = {
                    "accepted": stats.accepted_orders,
                    "refused": stats.refused_orders
                }
                response_body = json.dumps(data).encode('utf-8')

            else:
                if path == '/': 
                    file_path = os.path.join(WEB_DIR, 'index.html')
                else:
                    filename = path.lstrip('/')
                    file_path = os.path.join(WEB_DIR, filename)

                if file_path.endswith('.css'): content_type = "text/css"
                elif file_path.endswith('.js'): content_type = "application/javascript"
                
                try:
                    with open(file_path, 'rb') as f:
                        response_body = f.read()
                except FileNotFoundError:
                    # Gestion 404
                    response_header = "HTTP/1.1 404 Not Found\n\n"
                    conn.sendall(response_header.encode('utf-8'))
                    conn.close()
                    continue

            response_header = f"HTTP/1.1 200 OK\nContent-Type: {content_type}\nContent-Length: {len(response_body)}\nAccess-Control-Allow-Origin: *\n\n"
            
            conn.sendall(response_header.encode('utf-8') + response_body)
            conn.close()

        except Exception as e:
            print(f"[WEB] > Erreur: {e}")
            try: conn.close()
            except: pass