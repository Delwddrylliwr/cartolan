'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com

Based on this example from AlexiK: https://stackoverflow.com/questions/32595130/javascript-html5-canvas-display-from-python-websocket-server
'''

from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer, SimpleSSLWebSocketServer
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
import sys
import os
import random
import pygame
from pygame.locals import *
import base64
import string
from threading import Thread

clients = []

def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class WebServer(WebSocket):
    def initZMQ(self):
        file = sys.argv[0]
        base_dir = os.path.dirname(file)
        keys_dir = os.path.join(base_dir, 'certificates')
        public_keys_dir = os.path.join(base_dir, 'public_keys')
        secret_keys_dir = os.path.join(base_dir, 'private_keys')
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")
        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
        self.socket.curve_publickey = client_public
        self.socket.curve_secretkey = client_secret
        server_public_file = os.path.join(public_keys_dir, "server.key")
        server_public, _ = zmq.auth.load_certificate(server_public_file)
        self.socket.curve_serverkey = server_public
        self.width = "0"
        self.height = "0"
    def ondata(self):
        while True:
            try:
                data = self.socket.recv()
                code, self.width = data.split('[55555]')
                data = self.socket.recv()
                code, self.height = data.split('[55555]')
                self.width = int(self.width)
                self.height = int(self.height)
                self.width = float(self.width /1.5)
                self.height = float(self.height /1.5)
                print (self.width, self.height)
                data = self.socket.recv()   
                image = pygame.image.frombuffer(data
                                                , (int(self.width), int(self.height))
                                                ,"RGB")
                randname = id_generator()
                pygame.image.save(image, randname+".png")
                out = open(randname+".png","rb").read()
                self.sendMessage(base64.b64encode(out))
                print("data sent")
                os.remove(randname+".png")
            except Exception as e:
                print (e)
    
    def handleMessage(self):
       try:
           message = str(self.data) 
           protocode, msg = message.split("[00100]")
           if protocode == ("SUB"):
               print("SUB")
               self.socket.setsockopt(zmq.IDENTITY, str(msg))
               self.socket.connect("tcp://127.0.0.1:9001")
               Thread(target=self.ondata).start()
           elif protocode == ("MESSAGE"):
               print("MESSAGE")
               msg = str(msg)
               ident, mdata = msg.split("[11111]")
               msg = ('%sSPLIT%s' % (ident, mdata))
               self.socket.send(str(msg))
           else:
               raise Exception
       except Exception as e:
           print (e)

    def handleConnected(self):
       print (self.address, 'connected')
       clients.append(self)
       self.initZMQ()


    def handleClose(self):
       clients.remove(self)
       print (self.address, 'closed')
       for client in clients:
          client.sendMessage(self.address[0] + u' - disconnected')

server = SimpleWebSocketServer('', 10000, WebServer)
server.serveforever()