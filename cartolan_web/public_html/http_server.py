'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import http.server
import socketserver
import sys
import time
#import ssl

DEFAULT_PORT = 9000

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == './':
            self.path = 'index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("Server port taken to be "+sys.argv[1])
        port = int(sys.argv[1])
    else:
        port = DEFAULT_PORT
    # Create an object of the above class
    handler_object = MyHttpRequestHandler
    
    my_server = socketserver.TCPServer(("", port), handler_object)
    
    # Start the server
    print("Starting the HTTP server at port: "+str(port))
    print(time.strftime('%Y-%m-%d %H:%M %Z', time.gmtime(time.time()))) #timestamp
    my_server.serve_forever()