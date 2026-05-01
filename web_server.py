'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com

Based on this example from AlexiK: https://stackoverflow.com/questions/32595130/javascript-html5-canvas-display-from-python-websocket-server
'''

from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer  # , SimpleSSLWebSocketServer
from main_game import setup_simulation
# from live_visuals import ClientGameVisualisation, WebServerVisualisation
from live_visuals import WebServerVisualisation
from game import GameBeginner, GameRegular, GameAdvanced
from players_human import PlayerHuman
from players_heuristical import PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter
from players_heuristical import PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter, PlayerRegularPirate
from players_heuristical import PlayerAdvancedExplorer, PlayerAdvancedTrader, PlayerAdvancedRouter, PlayerAdvancedPirate
# import zmq
# import zmq.auth
# from zmq.auth.thread import ThreadAuthenticator
import sys
sys.stdout.reconfigure(line_buffering=True)
import os
import time
import random
import string
import json
from threading import Thread

DEFAULT_PORT = 10000

DEFAULT_WIDTH = int(0.8 * 1366)
DEFAULT_HEIGHT = int(0.8 * 768)
DIMENSION_INCREMENT = 2

GAME_MODES = {
    #               'Exploratory':{'game_type':GameBeginner, 'player_set':{"blueviolet":PlayerBeginnerExplorer
    #                                                                    , "red":PlayerBeginnerTrader
    #                                                                    , "yellow":PlayerBeginnerRouter
    # #                                                                    , "green":PlayerBeginnerGenetic
    #                                                                    , "orange":PlayerBeginnerExplorer
    #                                                                       }}
    #               ,
    'Quick': {'game_type': GameRegular, 'player_set': {
        "orange": PlayerRegularPirate
        , "blueviolet": PlayerRegularExplorer
        , "red": PlayerRegularTrader
        , "yellow": PlayerRegularRouter
        #                                                                    , "green":PlayerRegularGenetic
    }}
    ,
    'Deep': {'game_type': GameAdvanced, 'player_set': {
        "orange": PlayerAdvancedPirate
        , "blueviolet": PlayerAdvancedExplorer
        , "red": PlayerAdvancedTrader
        , "yellow": PlayerAdvancedRouter
        #                                                                    , "green":PlayerRegularGenetic
    }}
}
DEFAULT_GAME_MODE = "Deep"
DEFAULT_LOCAL_PLAYERS = 1
DEFAULT_VIRTUAL_PLAYERS = 3
DEFAULT_REMOTE_PLAYERS = 0
DEFAULT_JOINING_PLAYERS = 1
MAX_NAME_CHARS = 5
ORDINALS = ["first", "second", "third", "fourth"]
NAMES = ["Ron", "Ali", "Jim", "Jon", "Bill", "Sam", "Nic", "Mel", "Su", "Mo", "Don", "Hal", "Sal", "Cat"]
MAX_NAME_USES = 100  # Allow names to be extended by up to two digits
# @TODO the below should be moved to the config file for all simulation and game versions
MOVEMENT_RULES = "initial"
EXPLORATION_RULES = "continuous"
MYTHICAL_CITY = True

next_game_id = 0
clients = []
client_visuals = {}
client_players = {}
games = {}  # referenced by game IDs
players = {}  # referenced by names, which must be unique on the server
client_games = {}  # referenced by ClientSocket
# player_clients = {} #refernced by players
# player_games = {} #refereced by players
# Track new games as they're being initiated, based on sequential game IDs
new_game_clients = {}  # referenced by game ID
new_game_types = {}  # referenced by game ID
new_game_colours = {}  # referenced by game ID
new_game_players = {}  # referenced by game ID, return the colour assigned to them
new_game_cpu_players = {}  # referenced by game ID, dicts of CPU players and their colours


def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class ClientSocket(WebSocket):
    '''Shares whole images of clients' play areas and receives input coordinates.
    
    Architecture:
    Client Side |    Server Side
    Web app    <-> Socket <-> Server   <->   Visualisation  <- Game
                                               /\                \/
                                              Player <- Adventurer/Agent
    
    '''
    INPUT_DELAY = 0.1  # delay time between checking for input, in seconds
    TIMEOUT_DELAY = 5  # delay time between heartbeats, after which loop will stop keeping the socket alive

    width = DEFAULT_WIDTH
    height = DEFAULT_HEIGHT
    global DIMENSION_INCREMENT

    coords_buffer = None
    text_buffer = None

    def get_text(self):
        output = self.text_buffer
        self.text_buffer = None
        return output

    def get_coords(self):
        output = self.coords_buffer
        self.coords_buffer = None
        return output

    #    def init_ZMQ(self):
    #        '''Set up a socket with a secure threadsafe message queue based on ZeroMQ: https://en.wikipedia.org/wiki/ZeroMQ
    #        '''
    #        file = sys.argv[0]
    #        base_dir = os.path.dirname(file)
    #        keys_dir = os.path.join(base_dir, 'certificates')
    #        public_keys_dir = os.path.join(base_dir, 'public_keys')
    #        secret_keys_dir = os.path.join(base_dir, 'private_keys')
    #        self.context = zmq.Context()
    #        self.socket = self.context.socket(zmq.DEALER)
    #        client_secret_file = os.path.join(secret_keys_dir, "client.key_secret")
    #        client_public, client_secret = zmq.auth.load_certificate(client_secret_file)
    #        self.socket.curve_publickey = client_public
    #        self.socket.curve_secretkey = client_secret
    #        server_public_file = os.path.join(public_keys_dir, "server.key")
    #        server_public, _ = zmq.auth.load_certificate(server_public_file)
    #        self.socket.curve_serverkey = server_public
    #        self.width = "0"
    #        self.height = "0"

    def setup_client_players(self, game_id, num_client_players):
        """Seeks remote input to determine the names of
        """
        global client_players
        client_players[self] = []
        for player_num in range(num_client_players):
            # Names must be unique within this game (across all its clients)
            game_names = ({p.name for p in new_game_players.get(game_id, {})}
                          | {p.name for p in client_players[self]})
            # Get the player to submit a name
            prompt_text = ("What is the name of the " + ORDINALS[
                player_num] + " player on this computer? (hit enter for random)")
            player_name = None
            self.sendMessage("PROMPT[00100]" + prompt_text)
            print("Prompting client at " + str(self.address) + " with: " + prompt_text)
            while player_name is None:
                player_name = self.get_text()
                if player_name is not None:
                    if len(player_name) > MAX_NAME_CHARS:
                        prompt_text = (player_name.capitalize() + " is too long. Pick a new name for the " + ORDINALS[
                            player_num] + " player on this computer? (fewer than " + str(MAX_NAME_CHARS) + " letters)")
                        player_name = None
                    elif player_name in game_names:
                        prompt_text = (player_name.capitalize() + " is taken in this game. Pick a new name for the " + ORDINALS[
                            player_num] + " player on this computer?")
                        player_name = None
                    elif player_name == "BLANK":
                        player_name = random.choice(NAMES)
                        print("Assigning a random name: " + player_name)
                        while player_name in game_names:
                            player_name += str(random.randint(0, MAX_NAME_USES))
                            print("Random name wasn't unique so appending a number: " + player_name)
                        break
                    else:
                        break
                    self.sendMessage("PROMPT[00100]" + prompt_text)
                    print("Prompting client at " + str(self.address) + " with: " + prompt_text)
                else:
                    time.sleep(self.INPUT_DELAY)
            player = PlayerHuman(player_name)
            players[(game_id, player_name)] = player
            client_players[self].append(player)

    def create_game(self, new_game_type="", num_client_players=None, num_virtual_players=0, num_players=None):
        """Seeks remote input to specify and set up a game that can then be joined by players.
        """
        global next_game_id, client_players
        global new_game_clients, new_game_types, new_game_colours, new_game_players, new_game_cpu_players
        game_id = next_game_id
        next_game_id += 1
        new_game_clients[game_id] = [self]
        print("Seeking game specification from newly joined client")
        prompt_text = "Please specify which mode of Cartolan you would like to host: "
        valid_options = []
        for game_type in GAME_MODES:
            prompt_text += "'" + game_type + "'"
            valid_options.append(game_type)
            if len(valid_options) < len(GAME_MODES):
                prompt_text += ", or "
            else:
                prompt_text += "."
        if new_game_type not in valid_options:
            prompt_text += " (Hit enter for default " + DEFAULT_GAME_MODE + ")"
            print("Prompting client at " + str(self.address) + " with: " + prompt_text)
            self.sendMessage("PROMPT[00100]" + prompt_text)
        while not new_game_type in valid_options:
            new_game_type = self.get_text()
            if new_game_type:
                if new_game_type == "BLANK":
                    print("Game type prompt was left blank, so assuming default mode of " + DEFAULT_GAME_MODE)
                    new_game_type = DEFAULT_GAME_MODE
                elif not new_game_type in valid_options:
                    new_game_type = None
                    self.sendMessage("PROMPT[00100]" + prompt_text)
            time.sleep(self.INPUT_DELAY)
        # new_game_type = DEFAULT_GAME_MODE  # Deprecating multiple game modes
        new_game_types[game_id] = new_game_type
        min_players = GAME_MODES[new_game_type]["game_type"].MIN_PLAYERS
        max_players = GAME_MODES[new_game_type]["game_type"].MAX_PLAYERS
        available_colours = random.sample(list(GAME_MODES[new_game_type]["player_set"].keys()), max_players)
        new_game_colours[game_id] = []
        # Get remote user input about how many players they have at their end
        valid_options = [str(i) for i in range(1, max_players + 1)]
        if str(num_client_players) not in valid_options:
            prompt_text = ("Please specify how many players will play from this computer, between " + valid_options[
                0] + " and " + valid_options[-1] + "?")
            prompt_text += " (Hit enter for default " + str(DEFAULT_LOCAL_PLAYERS) + ")"
            num_client_players = None
            print("Prompting client at " + str(self.address) + " with: " + prompt_text)
            self.sendMessage("PROMPT[00100]" + prompt_text)
        while not str(num_client_players) in valid_options:
            received_input = self.get_text()
            if received_input:
                if received_input.isnumeric():
                    num_client_players = int(received_input)
                    if not str(num_client_players) in valid_options:
                        num_client_players = None
                        self.sendMessage("PROMPT[00100]" + prompt_text)
                else:
                    # For any input besides a number, assume the default
                    num_client_players = DEFAULT_LOCAL_PLAYERS
            else:
                time.sleep(self.INPUT_DELAY)
        # Name and set up these host human players
        if (client_players.get(self) is None
                or not len(client_players[self]) == num_client_players):
            # Name and set up these host human players
            self.setup_client_players(game_id, num_client_players)
        # Assign colours to these local players
        new_game_players[game_id] = {}
        for player in client_players[self]:
            player_colour = available_colours.pop()
            #            new_game_colours[game_id].append(player_colour)
            new_game_players[game_id][player] = player_colour
        # Get remote user input about how many computer players the game will have
        if num_client_players < max_players:
            valid_options = [str(i) for i in range(0, max_players - num_client_players + 1)]
            practical_default = min(DEFAULT_VIRTUAL_PLAYERS, int(valid_options[-1]))
            prompt_text = ("Please specify how many computer-controlled players will play, between " + valid_options[
                0] + " and " + valid_options[-1] + "?")
            prompt_text += " (Hit enter for default " + str(practical_default) + ")"
            print("Prompting client at " + str(self.address) + " with: " + prompt_text)
            self.sendMessage("PROMPT[00100]" + prompt_text)
            num_virtual_players = None
            while not str(num_virtual_players) in valid_options:
                received_input = self.get_text()
                if received_input:
                    if received_input.isnumeric():
                        num_virtual_players = int(received_input)
                        if not str(num_virtual_players) in valid_options:
                            num_virtual_players = None
                            self.sendMessage("PROMPT[00100]" + prompt_text)
                    else:
                        # For any input besides a number, assume the default, or the closest to it possible
                        num_virtual_players = practical_default
                        print("No viable option chosen, so defaulting to " + str(practical_default))
                else:
                    time.sleep(self.INPUT_DELAY)
        # Assign random names and colours to these CPU players
        if new_game_cpu_players.get(game_id) is None:
            new_game_cpu_players[game_id] = {}
        for player_num in range(num_virtual_players):
            player_colour = available_colours.pop()
            #            new_game_colours[game_id].append(player_colour)
            game_names = {p.name for p in new_game_players.get(game_id, {})} | {p.name for p in client_players[self]}
            player_name = "AI:" + random.choice(NAMES)
            while player_name in game_names:
                player_name += str(random.randint(0, MAX_NAME_USES))
            player = GAME_MODES[new_game_type]["player_set"][player_colour](player_name)
            players[(game_id, player_name)] = player
            client_players[self].append(player)
            new_game_players[game_id][player] = player_colour
            new_game_cpu_players[game_id][player] = player_colour
        # Get remote user input about how many other players they want in their game
        if num_players is None:
            num_players = num_client_players + num_virtual_players
        # If there are still spaces available then allow for remote players
        if num_players < max_players:
            valid_options = [str(i) for i in range(max(min_players - num_players, 0), max_players - num_players + 1)]
            practical_default = min(DEFAULT_REMOTE_PLAYERS, int(valid_options[-1]))
            prompt_text = ("Please specify how many players from other computers will play, between " + str(
                valid_options[0]) + " and " + str(valid_options[-1]) + "?")
            prompt_text += " (Hit enter for default " + str(practical_default) + ")"
            print("Prompting client at " + str(self.address) + " with: " + prompt_text)
            self.sendMessage("PROMPT[00100]" + prompt_text)
            num_players = None
            while not num_players in range(min_players, max_players + 1):
                received_input = self.get_text()
                if received_input:
                    if received_input.isnumeric():
                        num_players = num_client_players + num_virtual_players + int(received_input)
                        if not num_players in range(min_players, max_players + 1):
                            num_players = None
                            self.sendMessage("PROMPT[00100]" + prompt_text)
                    else:
                        # For any input besides a number, assume the default or the closest to it possible
                        num_players = num_client_players + num_virtual_players + practical_default
                        print("No viable option chosen, so defaulting to " + str(practical_default))
                else:
                    time.sleep(self.INPUT_DELAY)
            new_game_colours[game_id] = random.sample(available_colours, num_players - len(new_game_players[game_id]))
        return game_id

    def join_game(self, game_id, num_client_players=None):
        """Attempts to join a specific game, and otherwise joins the game queue
        """
        global client_players
        global new_game_clients, new_game_types, new_game_colours, new_game_players
        #print("Checking that the specified game exists")
        if new_game_types[game_id] is None:
            return False
        new_game_type = new_game_types[game_id]
        num_existing_clients = len(new_game_clients[game_id])
        # Seek input about how many players there are using this client
        client_players[game_id] = []
        #        min_players = GAME_MODES[new_game_type]["game_type"].MIN_PLAYERS
        max_players = GAME_MODES[new_game_type]["game_type"].MAX_PLAYERS
        if num_client_players not in range(1, max_players + 1):
            num_existing_players = len(new_game_players[game_id])
            num_spaces = len(new_game_colours[game_id])
            num_players = num_existing_players + num_spaces
            print("The existing game has " + str(num_existing_clients) + " other clients connected")
            #        valid_options = [str(i) for i in range(1, num_spaces + 1)]
            practical_default = min(DEFAULT_JOINING_PLAYERS, num_spaces)
            prompt_text = ("The current game has " + str(num_existing_players) + "/"
                           + str(
                        num_players) + "players. Please specify how many players will play from this computer, "
                                       "between 1 and "
                           + str(num_spaces) + "?")
            prompt_text += " (Hit enter for default " + str(practical_default) + ")"
            print("Prompting client at " + str(self.address) + " with: " + prompt_text)
            self.sendMessage("PROMPT[00100]" + prompt_text)
            while not num_client_players in range(1, max_players + 1):
                received_input = self.get_text()
                if received_input:
                    if received_input.isnumeric():
                        num_client_players = int(received_input)
                        if not num_client_players in range(1, max_players + 1):
                            num_client_players = None
                            self.sendMessage("PROMPT[00100]" + prompt_text)
                    else:
                        # For any input besides a number, assume the default
                        num_client_players = practical_default
                        print("No viable option chosen, so defaulting to " + str(practical_default))
                else:
                    time.sleep(self.INPUT_DELAY)
        # Check whether the players have been set up for this client
        if (client_players.get(self) is None
                or not len(client_players[self]) == num_client_players):
            # Name and set up these host human players
            self.setup_client_players(game_id, num_client_players)
        # No blocking is done, check whether the number of spaces for this game has changed and start again if so
        num_spaces = len(new_game_colours[game_id])
        num_existing_players = len(new_game_players[game_id])
        num_players = num_existing_players + num_spaces
        if len(client_players[self]) > num_spaces:
            prompt_text = (
                "This game filled up while you were responding. Enter any response to continue and wait for another.")
            print("Prompting client at " + str(self.address) + " with: " + prompt_text)
            response = None
            while response is None:
                response = self.get_text()
            game_id = None
            return False
        # Assign colours to each new player
        for player in client_players[self]:
            player_colour = new_game_colours[game_id].pop()
            new_game_players[game_id][player] = player_colour
        return True

    def join_queue(self):
        """Adds players to a queue, the first specifies setup, the last hosts in their thread.
        """
        global new_game_clients, new_game_types, new_game_colours, new_game_players

        def report_queue(client, game_id):
            num_existing_players = len(new_game_players[game_id])
            num_players = len(new_game_colours[game_id]) + num_existing_players
            report = str(num_existing_players) + "/" + str(num_players)
            client.sendMessage("PLAYERS[00100]" + report)

        # If no game is specified then create or join the next game in the queue
        in_queue = False
        tried_games = []
        while not in_queue:
            if len(new_game_types) == 0 or len(tried_games) == len(new_game_types):
                print("With no games queued up, configuring a new game.")
                game_id = self.create_game()
                # Notify the player that they are in the queue and how many more players are awaited
                report_queue(self, game_id)
                in_queue = True
            else:
                print("Trying to join this client to a random existing game from the queue")
                # Try adding this client to an existing game, but then try another if that fills up while user is
                # inputting
                # Select a (semi-)random game to join
                game_id = random.choice(list(new_game_types.keys()))

                # Now blocking is done, try to reserve a place in this game
                if self.join_game(game_id):
                    # Notify the client that they are in the queue and how many more players are awaited
                    new_game_clients[game_id].append(self)
                    for client in new_game_clients[game_id]:
                        report_queue(client, game_id)
                    in_queue = True
                else:
                    tried_games.append(game_id)
        # If this client's game is now full then try to start it off
        if not self.start_game(
                game_id):  # testing the negative because otherwise it will take until game conclusion to return
            # Otherwise keep connection alive until a game is joined
            connection_alive = True
            self.connection_confirmed = False
            self.sendMessage("PING[00100]")
            while connection_alive:
                connection_alive = self.connection_confirmed
                self.connection_confirmed = False
                self.sendMessage("PING[00100]")
                time.sleep(self.TIMEOUT_DELAY)
            print(self.address, " timed out")
        else:
            return True

    def start_game(self, game_id):
        """Checks whether a game is full and launches it, then runs it in this thread until completion

        Arguments:
        game_id takes an integer unique reference for a Cartolan game in the global games list
        """
        global client_visuals, client_players, games
        global new_game_clients, new_game_types, new_game_colours, new_game_players
        num_spaces = len(new_game_colours[game_id])
        if not num_spaces == 0:
            return False
        else:
            print("Enough players have joined, so STARTING GAME #" + str(game_id))
        game_players = list(new_game_players[game_id].keys())
        random.shuffle(game_players)
        self.game = setup_simulation(game_players
                                     , GAME_MODES[new_game_types[game_id]]["game_type"]
                                     , MOVEMENT_RULES
                                     , EXPLORATION_RULES
                                     , MYTHICAL_CITY)

        # Move the game's lookups into the active list and clean up
        games[game_id] = {"game": self.game
            , "player_colours": new_game_players.pop(game_id)
            , "players": game_players
            , "cpu_players": new_game_cpu_players.pop(game_id)
            , "game_type": new_game_types.pop(game_id)
            , "clients": new_game_clients.pop(game_id)
                          }
        new_game_colours.pop(game_id)
        # Set up a visual tailored to each client's screen
        visuals = []
        games[game_id]["visuals"] = visuals  # shared list; stored so rejoin can append to it
        for client in games[game_id]["clients"]:
            # create game visualisation corresponding to each client's window resolution
            game_vis = WebServerVisualisation(self.game, visuals, games[game_id]["player_colours"], client,
                                              client.width, client.height)
            print("Visual created for client at " + str(client.address) + " with dimensions: " + str(
                client.width) + "x" + str(client.height))
            client_visuals[client] = game_vis
            visuals.append(game_vis)
            game_vis.client_players = client_players[client]
            for player in client_players[client]:
                player.connect_gui(game_vis)

        # start game in this thread including all the client visuals (so that the players created here are available
        # to just one thread)
        self.game.game_started = True
        self.game.turn = 0
        self.game.game_over = False
        while not self.game.game_over:
            self.game.turn += 1
            self.game.game_over = self.game.play_round()

        # Inform all clients that the game has ended
        win_message = self.game.winning_player.name + " won the game"
        if self.game.wealth_difference >= self.game.game_winning_difference:
            win_message += " by buying a global monopoly with their extra wealth"
        else:
            win_message += " as the richest when the world map was completed"
        win_message += " (refresh to play again)"
        for client in games[game_id]["clients"]:
            print("Closing game for client: " + str(client.address))
            game_vis = client_visuals[client]
            game_vis.draw_play_area()
            game_vis.draw_scores()
            game_vis.draw_tokens()
            game_vis.current_player_colour = game_vis.player_colours[
                self.game.winning_player]  # Change the prompt colour to reflect the winning player
            game_vis.give_prompt(win_message)
            game_vis.update_web_display()
        game_vis.close()
        # Tidy up and indicate that a game was joined and completed, and allow the thread to terminate
        games.pop(game_id)
        return True

    def swap_player(self, game_id, old_player, new_player):
        """Introduces one player in place of another within a game.

        Arguments:
        old_player takes a Cartolan player
        new_player takes a Cartolan player
        """
        global games
        game = games[game_id]["game"]
        # Identify tokens owned by old player and transfer them to the new player
        # First Adventurers
        adventurers = game.adventurers.pop(old_player, [])
        for adventurer in adventurers:
            adventurer.player = new_player
        game.adventurers[new_player] = adventurers
        # Now Agents
        agents = game.agents.pop(old_player, [])
        for agent in agents:
            agent.player = new_player
        game.agents[new_player] = agents

        # Transfer all other player-keyed dicts on the game object
        for attr in ('player_wealths', 'num_tile_choices', 'num_character_choices',
                     'num_discovery_choices', 'value_agent_trade', 'rest_with_adventurers',
                     'transfer_agent_earnings', 'agents_arrest', 'confiscate_treasure',
                     'resting_refurnishes', 'pool_maps', 'rechoose_at_agents', 'assigned_cadres'):
            d = getattr(game, attr, None)
            if d is not None and old_player in d:
                d[new_player] = d.pop(old_player)

        # Remove old player from game and introduce the new player instead
        old_index = game.players.index(old_player)
        game.players.remove(old_player)
        game.players.insert(old_index, new_player)

        # Update the colour lookup (game.players IS games[game_id]["players"] — same list object)
        old_colour = games[game_id]["player_colours"].pop(old_player)
        games[game_id]["player_colours"][new_player] = old_colour

    def kick_player(self, game_id, player):
        """Remove a human player from a live game and replace them with a bot named 'AI:<name>'.

        The bot name acts as the rejoin token — any new client claiming that name can swap back in.

        Arguments:
        player takes a Cartolan PlayerHuman
        """
        game_data = games[game_id]
        colour = game_data["player_colours"].get(player)
        game_type = game_data["game_type"]
        bot_class = GAME_MODES[game_type]["player_set"].get(colour)
        if not bot_class:
            return
        bot = bot_class("AI:" + player.name)
        print("kick_player: replacing " + player.name + " with bot in game " + str(game_id))
        self.swap_player(game_id, player, bot)

    # @TODO decide whether to collect input from this socket via recv or the below
    def handleMessage(self):
        """Distinguish whether this message is an initiation or continuation of a game.
        """
        message = str(self.data)
        protocode, msg = message.split("[00100]")
        if protocode == ("START"):
            print("START...ing a new connection, and creating/joining the next game")
            print(time.strftime('%Y-%m-%d %H:%M %Z', time.gmtime(time.time())))  # timestamp
            #           self.socket.setsockopt(zmq.IDENTITY, str(msg))
            #           self.socket.connect("tcp://LOCALHOST:80")
            #           #Check whether there are enough players in the queue for a game,
            #           #start one in a Thread if so
            #           #@TODO join specifically the game that has been asked for
            self.width, self.height = [int(coord) for coord in msg.split("[55555]")]
            print("Received width: ", self.width, " and height: ", self.height)
            Thread(target=self.join_queue).start()
        elif protocode == ("REJOIN"):
            parts = msg.split("[55555]")
            self.width, self.height = int(parts[0]), int(parts[1])
            player_name = parts[2]
            print("REJOIN requested for player: " + player_name)
            Thread(target=self.rejoin_game, args=(player_name,)).start()
        elif protocode == ("PONG"):
            print("Client responded to ping")
            self.connection_confirmed = True
        elif protocode == ("TEXT"):
            print("TEXT... " + msg)
            if not msg == "":
                self.text_buffer = msg
        #           msg = str(msg)
        #           ident, mdata = msg.split("[11111]")
        #           msg = ('%sSPLIT%s' % (ident, mdata))
        ##           self.socket.send(str(msg))
        elif protocode == ("COORDS"):
            print("Click coordinates input received from client.")
            print(time.strftime('%Y-%m-%d %H:%M %Z', time.gmtime(time.time())))
            try:
                if '[55555]' in msg:
                    # Semantic format: highlight_type[55555]lon[66666]lat
                    ht, rest = msg.split('[55555]', 1)
                    lon_str, lat_str = rest.split('[66666]')
                    self.coords_buffer = {ht: [int(lon_str), int(lat_str)]}
                    print(str(self.coords_buffer))
                else:
                    # Legacy pixel format: x[66666]y
                    input_coords = msg.split('[66666]')
                    if len(input_coords) == 2:
                        self.coords_buffer = [int(input_coords[0]), int(input_coords[1])]
            except:
                self.coords_buffer = None
                print("The client response could not be parsed as click input.")
        elif protocode == ("CHEST"):
            print("Chest tile selection input received from client.")
            print(time.strftime('%Y-%m-%d %H:%M %Z', time.gmtime(time.time())))
            try:
                self.coords_buffer = {'preferred_tile': int(msg)}
                print(str(self.coords_buffer))
            except:
                self.coords_buffer = None
        elif protocode == ("TOGGLE"):
            self.coords_buffer = {'toggle': msg.strip()}
        elif protocode == ("ROUTES"):
            self.coords_buffer = {'routes_toggle': True}
        elif protocode == ("UNDO"):
            self.coords_buffer = {'undo_request': True}
        elif protocode == ("FOCUS"):
            try:
                parts = msg.split('[55555]')
                self.coords_buffer = {'focus': [parts[0], int(parts[1])]}
            except:
                self.coords_buffer = None
        elif protocode == ("OFFERSEL"):
            print("Offer selection input received from client.")
            print(time.strftime('%Y-%m-%d %H:%M %Z', time.gmtime(time.time())))
            try:
                self.coords_buffer = {'offer_select': int(msg)}
                print(str(self.coords_buffer))
            except:
                self.coords_buffer = None
        #           msg = str(msg)
        #           ident, mdata = msg.split("[11111]")
        #           msg = ('%sSPLIT%s' % (ident, mdata))
        ##           self.socket.send(str(msg))
        elif protocode == ("PLAY"):
            self.coords_buffer = {'play': True}
        elif protocode == ("LOBBY"):
            print("Client prompted for a refresh of the lobby data, listing queued and active games.")
            # Share any games being prepared in the queue with this client
            if len(new_game_types) > 0:
                self.list_queued_games()
            # Share any games already in progress with this player, in case they want to watch or replace a CPU player
            if len(games) > 0:
                self.list_active_games()

    def list_queued_games(self):
        """Shares with the client a list of the games currently being prepared in the queue
        """
        global new_game_clients, client_players, new_game_types, new_game_colours, new_game_players, new_game_cpu_players
        # Prepare the list asa JSON table, listing the first host player's name, the numbers of total players,
        # joined players, CPU players
        queued_games = []
        for game_id in new_game_types:
            queued_game = {}
            queued_game["game_id"] = str(game_id)
            queued_game["game_type"] = str(new_game_types[game_id])
            # Name the game according to the first player of its first client
            queued_game["game_name"] = str(client_players[new_game_clients[game_id]][0]) + "'s game"
            # Report the player numbers
            queued_game["existing_players"] = len(new_game_players[game_id])
            queued_game["empty_slots"] = len(new_game_colours[game_id])
            queued_game["total_players"] = queued_game["existing_players"] + queued_game["empty_slots"]
            queued_game["cpu_players"] = len(new_game_cpu_players[game_id])
            # Add all of this to the growing list
            queued_games.append(queued_game)
        self.sendMessage("QUEUE[00100]" + json.dumps(queued_games))

    def list_active_games(self):
        """Shares with the client a list of the games that are already running
        """
        global games, client_players
        # Prepare the list as a JSON table, listing the first host player's name, the numbers of total players,
        # joined players, CPU players
        active_games = []
        for game_id in games:
            game_data = games[game_id]
            active_game = {}
            active_game["game_id"] = str(game_id)
            active_game["game_type"] = str(game_data["game_type"])
            # Name the game according to the first player of its first client
            active_game["game_name"] = str(client_players[game_data["clients"][0]][0]) + "'s game"
            # Report the player numbers
            active_game["total_players"] = len(game_data["players"])
            active_game["cpu_players"] = len(game_data["cpu_players"])
            # Add all of this to the growing list
            active_games.append(active_game)
        self.sendMessage("LIST[00100]" + json.dumps(active_games))

    def handleConnected(self):
        """On initial connection, establish client details
        """
        print(self.address, 'connected')
        clients.append(self)

    #        self.init_ZMQ()
    #        channel.setup()

    def handleClose(self):
        """Gracefully remove a client, replacing their players with bots if mid-game.
        """
        global client_visuals, client_players
        clients.remove(self)
        print(self.address, 'closed')

        # Unblock any game thread currently waiting for input from this client
        self.coords_buffer = {"Nothing": "Nothing"}

        # Replace human players with bots in any active game this client belongs to
        for game_id, game_data in list(games.items()):
            if self in game_data["clients"]:
                for player in list(client_players.get(self, [])):
                    if isinstance(player, PlayerHuman):
                        try:
                            self.kick_player(game_id, player)
                        except Exception as e:
                            print("Error kicking player " + player.name + ": " + str(e))
                # Remove this client's visual from the shared visuals list
                vis = client_visuals.get(self)
                if vis and vis in game_data.get("visuals", []):
                    game_data["visuals"].remove(vis)
                game_data["clients"].remove(self)
                break

        client_players.pop(self, None)
        client_visuals.pop(self, None)

        for client in clients:
            client.sendMessage(self.address[0] + u' - disconnected')

    def rejoin_game(self, player_name):
        """Reconnects a previously disconnected human player, evicting the bot that replaced them.

        Searches active games for a bot placeholder named 'AI:<player_name>' — no separate
        tracking dict needed.

        Arguments:
        player_name takes the string name the player was using when they disconnected
        """
        global games, client_visuals, client_players, players

        bot_name = "AI:" + player_name
        found_game_id = None
        found_bot = None
        for game_id, game_data in list(games.items()):
            for p in game_data["players"]:
                if getattr(p, 'name', None) == bot_name:
                    print("Checking name of "+getattr(p, 'name', None))
                    found_game_id = game_id
                    found_bot = p
                    break
            if not found_game_id is None:
                print("rejoin_game: looking for bot '" + bot_name + "', found in game=" + str(found_game_id))
                break

        if found_game_id is None:
            self.sendMessage("PROMPT[00100]No active game has a bot placeholder for '" + player_name + "'. Check the name and try again.")
            return

        game_id = found_game_id
        bot_player = found_bot

        # Recreate the human player and swap out the bot
        game = games[game_id]["game"]
        player = PlayerHuman(player_name)
        player.join_game(game)  # populates player.games[game.game_id] so connect_gui can register
        players[(game_id, player_name)] = player
        self.swap_player(game_id, bot_player, player)

        # Register this client with the game
        games[game_id]["clients"].append(self)
        client_players[self] = [player]

        # Create a new visualisation for the rejoining client and add it to the shared peer list
        game_vis = WebServerVisualisation(
            game,
            games[game_id]["visuals"],
            games[game_id]["player_colours"],
            self, self.width, self.height,
        )
        game_vis.client_players = [player]
        player.connect_gui(game_vis)
        client_visuals[self] = game_vis
        games[game_id]["visuals"].append(game_vis)

        # Push the current game state to the rejoining client
        game_vis.update_web_display()


def generate_tile_manifest():
    '''Scans the tile image directory and writes tile_manifest.json for the JS client.

    Groups filenames by tile name (prefix before first underscore), deduplicates
    same-base-name variants by preferring .jpg over .png, and excludes backup (~)
    and copy files.
    '''
    here = os.path.dirname(os.path.abspath(__file__))
    tiles_dir = os.path.join(here, 'cartolan_web', 'public_html', 'img', 'map_tiles', 'tiles')
    manifest_path = os.path.join(tiles_dir, 'tile_manifest.json')

    variants = {}  # tile_name -> {variant_stem: chosen_filename}
    for filename in os.listdir(tiles_dir):
        if filename.endswith('~') or ' - Copy' in filename:
            continue
        stem, ext = os.path.splitext(filename)
        if ext.lower() not in ('.jpg', '.png'):
            continue
        if stem.startswith('Map-Tiles'):
            continue
        tile_name = stem.split('_')[0]
        tile_variants = variants.setdefault(tile_name, {})
        # Prefer .jpg; only replace an existing entry if this one is .jpg
        if stem not in tile_variants or ext.lower() == '.jpg':
            tile_variants[stem] = filename

    manifest = {name: list(files.values()) for name, files in sorted(variants.items())}
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    # print("Generated tile manifest: {} tile types".format(len(manifest)))
    # print(json.dumps(manifest, indent=2))


def generate_card_manifest():
    '''Scans the card image directory and writes card_manifest.json for the JS client.

    Groups filenames by card type (prefix before first underscore), deduplicates
    same-base-name variants by preferring .jpg over .png, and excludes backups.
    '''
    here = os.path.dirname(os.path.abspath(__file__))
    cards_dir = os.path.join(here, 'cartolan_web', 'public_html', 'img', 'cards')
    manifest_path = os.path.join(cards_dir, 'card_manifest.json')

    variants = {}  # card_type -> {variant_stem: chosen_filename}
    for filename in os.listdir(cards_dir):
        if filename.endswith('~') or ' - Copy' in filename:
            continue
        stem, ext = os.path.splitext(filename)
        if ext.lower() not in ('.jpg', '.png'):
            continue
        card_type = stem.split('_')[0]
        card_variants = variants.setdefault(card_type, {})
        if stem not in card_variants or ext.lower() == '.jpg':
            card_variants[stem] = filename

    manifest = {ct: list(files.values()) for ct, files in sorted(variants.items())}
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    # print("Generated card manifest: {} card types".format(len(manifest)))
    # print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    generate_tile_manifest()
    generate_card_manifest()
    if len(sys.argv) > 1:
        print("Server port taken to be " + sys.argv[1])
        port = sys.argv[1]
    else:
        port = DEFAULT_PORT
    server = SimpleWebSocketServer('0.0.0.0', port, ClientSocket)
    print("Starting server on port: ", port)
    server.serveforever()
