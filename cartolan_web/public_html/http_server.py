'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys
import os
import time
import ssl

DEFAULT_PORT = 9000

class MyHttpRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == './':
            self.path = 'index.html'
        return super().do_GET()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("Server port taken to be "+sys.argv[1])
        port = int(sys.argv[1])
    else:
        port = DEFAULT_PORT
    # Create an object of the above class
    handler_object = MyHttpRequestHandler
    
    http_server = HTTPServer(('localhost', port), handler_object)
    
    # Add SSL encryption
    file = sys.argv[0]
    base_dir = os.path.dirname(file)
    certs_dir = os.path.join(base_dir, '../certificates')
    client_secret_file = os.path.join(certs_dir, "cartolan.local.key")
    server_public_file = os.path.join(certs_dir, "cartolan.local.pem")
    http_server.socket = ssl.wrap_socket(http_server.socket, 
        keyfile=client_secret_file,
        certfile=server_public_file, server_side=True)
    
    # Start the server
    print("Starting the HTTPs server at port: "+str(port))
    print(time.strftime('%Y-%m-%d %H:%M %Z', time.gmtime(time.time()))) #timestamp
    http_server.serve_forever()