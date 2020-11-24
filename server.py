import PodSixNet.Channel
import PodSixNet.Server
import random
from players_human import PlayerHuman
from visuals import GameVisualisation, NetworkGameVisualisation
from time import sleep

class ClientChannel(PodSixNet.Channel.Channel):
    '''The receiving methods for messages from clients for a pygame-based server
    '''
    def Network(self, data):
        print(data)
        
    def Network_setup(self, data):
        '''The receiving method for "setup" messages from clients, to get the number of players
        '''
        self.player_colours = data["player_colours"]
        for player_colour in self.player_colours:
            self.players.append(PlayerHuman(player_colour))
    
    def Network_input(self, data):
        '''Receiving method for plain 'input' messages from clients
        '''
        self._server. = data["input"]
        
    def Network_move(self, data):
        '''The receiving method for "move" messages from clients
        '''
        self.generic_move_or_action(data)
    
    def Network_buy(self, data):
        '''The receiving method for "buy" messages from clients
        '''
        self.generic_move_or_action(data)
    
    def Network_attack(self, data):
        '''The receiving method for "attack" messages from clients
        '''
        self.generic_move_or_action(data)
        
    #@TODO may want to differentiate client instructions more deeply in future, if multiple moves are to be offered at the same time    
    def generic_move_or_action(self, data):
        #deconsolidate all of the data from the dictionary
        longitude = data["longitude"]
        latitude = data["latitude"]
        
        player_colour = data["player_colour"]
        adventurer_num = data["adventurer_num"]
        
#        if not self.gameid == data["gameid"]: #id of game given by server at start of game
            #@TODO handle a message from the wrong game for this channel
            
        #tells server to pass coordinates on to the waiting game
        self._server.pass_coordinates(longitude, latitude, self.gameid, player_colour, adventurer_num)
    
    def Network_quit(self, data):
        '''The receiving method for "quit" messages from clients
        '''
        self._server.player_quits(self.game_id, data["player_colour"])
    
    def Close(self):
        '''Closes the channel to the client
        '''
        self._server.close(self.gameid)

class CartolanServer(PodSixNet.Server.Server):
    '''A pygame-based server hosting a game and communicating with client visuals.
    
    Architecture:
    Server Side                               |    Client Side
        Game <- Visualisation   ->  Server   <->   Visualisation -> Player -> Adventurer
         /\             /\            /\                                |
          |              |             |                               \/
         \/             \/            \/                            
        Adventurer  -> Player                                        Agent
    
    Client side Player, Adventurer, and Agent, used for data storage but not methods
    '''
    channelClass = ClientChannel
    WAIT_DURATION = 1
    TIMEOUT_DURATION = 60
    
    def __init__(self, game_modes, dimensions, origin, *args, **kwargs):
        PodSixNet.Server.Server.__init__(self, *args, **kwargs)
        self.game_modes = game_modes
        self.dimensions = dimensions
        self.orgin = origin
        self.games = {}
        self.input_buffer = {}
        #Track the latest game as it's being initiated
        self.next_game = None
        self.next_game_id = 0
        self.next_game_type = None
        self.num_players = None
        self.next_game_players = {}
        self.local_game = self.check_local_game()
    
    def check_local_game(self):
        '''Seeks input from the Host machine's owner if they aren't currently in a game
        '''
        #Check whether a local player is looking to host a game
        prompt = "Please specify how many local players will play?"
        num_local_players = None
        while not int(num_local_players) >= 0:
            num_local_players = int(input(prompt))
        # Seek game specification from host player
        if num_local_players > 0:
            prompt = "Please specify which mode of Cartolan you would like to host: '"
            for game_type in self.game_modes:
                prompt += "'"+game_type+"', or "
            while not self.next_game_type in self.game_modes:
                self.next_game_type = input(prompt).lower()
            #Create the players
            for player_colour in random.choices(self.game_modes[self.game_type]["player_set"], k=num_local_players):
                self.next_game_players.append(PlayerHuman(player_colour))
                self.next_player_channels[player_colour] = None #keep track of local players with a None instead of a podsixnet.channel
            self.min_players = self.game_modes[game_type]["game_type"].MIN_PLAYERS
            self.max_players = self.game_modes[game_type]["game_type"].MAX_PLAYERS
            prompt = "Please specify how many other players will play, between 0 and " +str(self.max_players - num_local_players)+ "?"
            num_players = None
            while not num_players in range(self.min_players, self.max_players):
                num_players = num_local_players + int(input(prompt))
            #Set up the game if there are enough players
            if len(self.next_game_players) >= num_players:
                next_game = self.next_game_type(self.players.keys(), self.MOVEMENT_RULES, self.EXPLORATION_RULES)
                next_game_vis = GameVisualisation(self.next_game, self.dimensions, self.orgin)
                self.games[next_game.game_id] = {"game_vis":next_game_vis, "player_channels":self.next_player_channels}
                self.next_players_channels = {}
            return True
        else:
            return False       
    
    #@TODO allow players to join a game, replacing a virtual player 
    def Connected(self, channel, addr):
        '''Allocates players to games
        '''
        print('new connection:', channel)
        if self.next_game == None:
            # Seek game specification from newly joined client
            prompt_text = "Please specify which mode of Cartolan you would like to host: "
            game_type = ""
            for game_type in self.game_modes:
                prompt_text += "'"+game_type+"', or "
            channel.send({"action":"prompt", "colour":"block", "prompt_text":prompt_text})
            while not game_type in self.game_modes:
                game_type = self.remote_input(channel)
            self.min_players = self.game_modes[game_type]["game_type"].MIN_PLAYERS
            self.max_players = self.game_modes[game_type]["game_type"].MAX_PLAYERS
            prompt_text = ("Please specify how many players will play from this computer, between 1 and " +str(self.max_players)+ "?")
            channel.send({"action":"prompt", "colour":"block", "prompt_text":prompt_text})
            num_client_players = None
            while not num_client_players in range(1, self.max_players + 1):
                num_client_players = int(self.remote_input(channel))
            prompt_text("Please specify how many other players will play, between 1 and " +str(self.max_players - num_client_players)+ "?")
            channel.send({"action":"prompt", "colour":"block", "prompt_text":prompt_text})
            num_players = None
            while not num_players in range(self.min_players, self.max_players + 1):
                num_players = num_client_players + int(self.remote_input(channel))
            for player in channel.players:
                self.next_game_players.append(player)
                self.next_player_channels[player.colour] = channel
        else:
            channel.gameid = self.game.game_id
            self.queue.append(channel)
            self.next_game_players.append(channel.players)
            if len(self.next_game_players) == self.num_players:
                next_game = self.next_game_type(self.next_player_channels.keys(), self.MOVEMENT_RULES, self.EXPLORATION_RULES)
                next_game_vis = NetworkGameVisualisation(self.next_game, channel)
                for chan in self.queue:
                    chan.Send({"action": "start_game","player":0, "gameid": self.queue.gameid})
                    chan.game_id = next_game.game_id
                    self.games[next_game.game_id] = {"game_vis":next_game_vis, "player_channels":self.next_game_players}
                    self.next_player_channels = {}
    
    def close(self, game_id):
        '''Passes on close instruction to each of the clients
        
        Parameters:    
        game_id should be an integer referencing a game instance in a List
        '''
        try:
            player_channels = self.games[game_id]["player_channels"]
            for channel in set(player_channels.values()):
                if channel:
                    channel.Send({"action":"close"})
                else:
                    # Free up the local game slot if this was the local game
                    self.local_game = False
        except:
            pass
    
    def pass_coordinates(self, longitude, latitude, game_id, player_colour, adventurer_num):
        '''Checks that the game is awaiting input from a player, and makes it available.
        
        Arguments:
        longitude an Int giving one of the grid coordinates
        latitude an Int giving one of the grid coordinates
        game_id a hexadecimal string uniquely identifying
        player_colour a string identifying the player within the game, by their colour
        adventurer_number an Int identifying the Adventurer token for which the player is submitting a movement/action
        '''
        if not self.games[game_id]["current_player_colour"] == player_colour:
            return False
        else:
            self.games[game_id]["current_player_input"] = [longitude, latitude]
            return True
    
    def remote_give_prompt(self, game, player_colour, prompt):
        '''Passes a prompt for the relevant remote players 
        '''
        channel = self.games[game.game_id]["player_channels"][player_colour]
        channel.send({"action":"prompt", "player_colour":player_colour, "prompt_text":prompt})
    
    def remote_clear_prompt(self, game, player_colour):
        '''Clears prompts for the relevant remote player
        '''
        channel = self.games[game.game_id]["player_channels"][player_colour]
        channel.send({"action":"prompt", "player_colour":player_colour})
    
    def remote_input(self, channel):
        '''Allows players to submit text input
        '''
        #collect and return any input left in the buffer
        input_text = self.input_buffer[channel]
        self.input_buffer[channel] = None
        return input_text
    
    def remote_input_coords(self, adventurer):
        '''Allows Players to submit coordinates directly
        '''
        #identify game and player through adventurer
        game_id = adventurer.game.game_id
        player = adventurer.player
        #collect and return any coordinates left for the game by that player's remote version
        if not self.games[game_id]["current_player_colour"] == player.player_colour:
            input_coords = self.games[game_id]["current_player_input"]
            #Record that the coordinates have been collected
            self.games[game_id]["current_player_input"] = None
            return input_coords
        else:
            return None
    
    def player_quits(self, game_id, player_colour):
        '''When a player quits an active game, replace them with a virtual player.
        '''
        game_vis = self.games[game_id]["game_vis"]
        player_channels = self.games[game_id]["player_channels"]
        player_channels[player_colour] = self.game_modes[game_vis.game.__class__]["player_sets"][player_colour](player_colour)
    
    def tick(self):
        '''Checks the games for players quitting and handles appropriately
        '''
        # Check for any player actions or quit messages
        for game_id in self.games:
            game = games[game_id]["game"]
                                
        
        self.Pump()


    