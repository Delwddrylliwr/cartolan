'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import copy
import uuid

from cartolan.core.utils import replace_references
from cartolan.core.tokens import Token
from cartolan.core.cards import Card
from cartolan.core.tiles import Tile, TilePile

class Game:
    '''A template for maintaining a record of the game state in different modes of Cartolan.
    
    Methods:
    __init__ taking a list full of Player objects
    establish_turn_order taking no arguments
    '''
    MAX_PLAYERS = 4
    MIN_PLAYERS = 2
    
    def __init__(self, players):
        if len(players) in range(self.MIN_PLAYERS, self.MAX_PLAYERS +1):
            self.players = players
#            self.establish_turn_order()
        else: raise Exception("Game created with an invalid number of players: should be 2-4, but was " +str(len(players)))
        
        #register this game with each of the players
        self.game_id = uuid.uuid4()
        for player in players:
            player.join_game(self)

        self.tile_count = 0
        self.tile_piles = {}
        self.play_area = {}
        self.player_wealths = {}
        self.adventurers = {}
        self.agents = {}
        for player in players:
            self.player_wealths[player] = 0
            self.adventurers[player] = []
            self.agents[player] = []
        
        self.game_started = False #Keep track of whether the game is running
        self.turn = 0
        
        #some information to keep track of centrally for players to make decisions
        self.winning_player = None
        self.max_wealth = 0
        self.total_vault_wealth =  0
        self.total_chest_wealth = 0
        self.wealth_difference = 0
        self.num_failed_explorations = 0
#         self.agent_network = None #placeholder to keep track of which routes are possible in a single turn
#         self.agent_distances = [[]] #placeholder to keep track of where trade routes could be built
#         self.most_lucrative_route_value = 0
#         self.most_lucrative_route_player = None

    def register(self, asset):
        '''Gives game elements IDs that are consistent with others of their type
        Args:
            asset: a game element that needs an ID consistent with others of its type

        Returns: an id specific to this game
        '''
        if isinstance(asset, Tile):
            tile_id = self.tile_count
            self.tile_count += 1
            return tile_id
        elif isinstance(asset, Card):
            card_id = self.card_count
            self.card_count += 1
            return card_id

    def save(self):
        '''Backs up the game and tokens' states, so that they can be restored later e.g. to undo a mistake
        '''
#        print("Backing up game state")
        self.backup = None #Avoid recursively backing up deep copies of earlier versions
        self.backup = copy.deepcopy(self)
#        memo = {}
#        try: 
#            self.backup = copy.deepcopy(self, memo)
#        except Exception as error:
#            print(error)
#            print(memo)
#            exit()
        
    def restore(self):
        '''Restores a previous game state.
        
        Thanks to Nithin: https://stackoverflow.com/questions/1216356/is-it-safe-to-replace-a-self-object-by-another-object-of-the-same-type-in-a-meth
        '''
        valid_classes = [Game, Token, Card, Tile, TilePile, list, dict]
        memo = []
        replace_references(self.backup, self, self.backup, memo, valid_classes) #Make sure that all elements within the backup copy of the game refer up to the true game
#        print("Investigated objects:")
#        print(memo)
        adventurers = self.adventurers #retain the list currently used for adventurers
        self.__dict__.update(self.backup.__dict__)
        #Now for each adventurer return to the original object reference, but 
        #swap its attributes for the deep copy's - so that restoring in the 
        #middle of an Adventurer's move doesn't break references around it
        for player in adventurers:
            backup_adventurers = self.adventurers.get(player, [])
            for adventurer in adventurers[player]:
                adventurer_num = adventurers[player].index(adventurer)
                if len(backup_adventurers) > adventurer_num:
                    restored_copy = backup_adventurers[adventurer_num]
    #                print("Restoring attributes of "+str(adventurer)+" from backup "+str(restored_copy)+"but keeping the reference.")
                    adventurer.__dict__.update(restored_copy.__dict__)
    #                #Because the adventurers came from the deep-copied game they will have references to the "copy" that has been abandoned
#                    adventurer.game = self
                    #adventurers are also referenced by tiles, so these will need updating
                    memo = []
                    replace_references(restored_copy, adventurer, self, memo, valid_classes)
#                    print("Investigated objects:")
#                    print(memo)
                else:
                    #If this adventurer wasn't in the backup, then discard it
                    adventurers[player].pop(adventurer)
            for agent in self.agents.get(player, []):
                #Because the agents came from the deep-copied game they will have references to the "copy" that has been abandoned
                agent.game = self        
#        print("Replacing the new replica of the game's Adventurer's list, "+str(self.adventurers)+", with the original full of original Adventurer references, "+str(adventurers))
        self.adventurers = adventurers
        #Tiles may still have references to the 
        #Now make sure there is a backup still in place for subsequent restores (the backup had no backup iteself)
        self.save()
    
#    def establish_turn_order(self):
#        '''Randomises the order in which Player objects will be activated'''
#        random.shuffle(self.players)
