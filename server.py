import PodSixNet.Channel
import PodSixNet.Server
from time import sleep
class ClientChannel(PodSixNet.Channel.Channel):
    '''The receiving methods for messages from clients for a pygame-based server
    '''
    def Network(self, data):
        print(data)
    
    def Network_move(self, data):
        '''The receiving method for "move" messages from clients
        '''
    
    #@TODO may want to differentiate client instructions more deeply in future, if multiple moves are to be offered at the same time    
    def generic_move_or_action(self, data):
        #deconsolidate all of the data from the dictionary
        longitude = data["longitude"]
        latitude = data["latitude"]
        
        self.gameid = data["gameid"] #id of game given by server at start of game
     
        #tells server to place line
#        self._server.placeLine(hv, x, y, data, self.gameid, num)
    
    def Close(self):
        '''Closes the channel to the client
        '''
        self._server.close(self.gameid)

class CartolanServer(PodSixNet.Server.Server):
    '''A pygame-based server hosting a game and communicating with client visuals.
    
    Architecture:
    Server Side                               |    Client Side
    Visualisation <-  Game       ->  Server  <->   Visualisation -> Player -> Adventurer
         /\             /\            /\                                |
          |              |             |                               \/
         \/             \/            \/                            
        Player     <- Adventurer -> Player                         Agent
    
    Client side Player, Adventurer, and Agent, used for data storage but not methods
    '''
    channelClass = ClientChannel
    
    def __init__(self, *args, **kwargs):
        PodSixNet.Server.Server.__init__(self, *args, **kwargs)
        self.games = []
        self.queue = None
        self.currentIndex = 0
    
    def Connected(self, channel, addr):
        print('new connection:', channel)
        if self.queue == None:
            self.currentIndex += 1
            channel.gameid=self.currentIndex
            self.queue=Game(channel, self.currentIndex)
        else:
            channel.gameid = self.currentIndex
            self.queue.player1 = channel
            self.queue.player0.Send({"action": "startgame","player":0, "gameid": self.queue.gameid})
            self.queue.player1.Send({"action": "startgame","player":1, "gameid": self.queue.gameid})
            self.games.append(self.queue)
            self.queue = None
    
    def placeLine(self, is_h, x, y, data, gameid, num):
        game = [a for a in self.games if a.gameid == gameid]
        if len(game) == 1:
            game[0].placeLine(is_h, x, y, data, num)
    
    def close(self, gameid):
        '''Passes on close instruction to each of the clients
        
        Parameters:    
        game_id should be an integer referencing a game instance in a List
        '''
        try:
            game = [a for a in self.games if a.gameid == gameid][0]
            game.player0.Send({"action":"close"})
            game.player1.Send({"action":"close"})
        except:
            pass
    
    def tick(self):
        # Check for any wins
        # Loop through all of the squares
        index = 0
        change = 3
        for game in self.games:
            change = 3
            for time in range(2):
                for y in range(6):
                    for x in range(6):
                        if game.boardh[y][x] and game.boardv[y][x] and game.boardh[y+1][x] and game.boardv[y][x+1] and not game.owner[x][y]:
                            if self.games[index].turn == 0:
                                self.games[index].owner[x][y] = 2
                                game.player1.Send({"action":"win",  "x":x, "y":y})
                                game.player0.Send({"action":"lose", "x":x, "y":y})
                                change = 1
                            else:
                                self.games[index].owner[x][y] = 1
                                game.player0.Send({"action":"win", "x":x, "y":y})
                                game.player1.Send({"action":"lose", "x":x, "y":y})
                                change = 0
            self.games[index].turn = change if change != 3 else self.games[index].turn
            game.player1.Send({"action":"yourturn", "torf":True if self.games[index].turn == 1 else False})
            game.player0.Send({"action":"yourturn", "torf":True if self.games[index].turn == 0 else False})
            index += 1
        
        self.Pump()

class Game:
    def __init__(self, player0, currentIndex):
        # whose turn (1 or 0)
        self.turn = 0
        #owner map
        self.owner = [[False for x in range(6)] for y in range(6)]
        # Seven lines in each direction to make a six by six grid.
        self.boardh = [[False for x in range(6)] for y in range(7)]
        self.boardv = [[False for x in range(7)] for y in range(6)]
        #initialize the players including the one who started the game
        self.player0 = player0
        self.player1 = None
        #gameid of game
        self.gameid = currentIndex
    
    def placeLine(self, is_h, x, y, data, num):
        #make sure it's their turn
        if num == self.turn:
            self.turn = 0 if self.turn else 1
            self.player1.Send({"action":"yourturn", "torf":True if self.turn == 1 else False})
            self.player0.Send({"action":"yourturn", "torf":True if self.turn == 0 else False})
            #place line in game
            if is_h:
                self.boardh[y][x] = True
            else:
                self.boardv[y][x] = True
            #send data and turn data to each player
            self.player0.Send(data)
            self.player1.Send(data)

# Seek server port from host
print("STARTING SERVER ON LOCALHOST")
address = raw_input("Host:Port (localhost:8000): ")
if not address:
    host, port = "localhost", 8000
else:
    host, port = address.split(":")

server = BoxesServer(localaddr = (host, int(port)))
while True:
    server.tick()
    sleep(0.01)
    