'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import copy
import random
import uuid

from cartolan.core.utils import replace_references
from cartolan.core.events import GameEvent
from cartolan.core.tokens import Token
from cartolan.core.cards import Card
from cartolan.core.tiles import Tile, TilePile

import logging

logger = logging.getLogger(__name__)


class _GlobalRandom:
    '''Deepcopy-safe view of the global random module, used as the default rng.'''

    def __getattr__(self, name):
        return getattr(random, name)

    def __deepcopy__(self, memo):
        return self


GLOBAL_RNG = _GlobalRandom()


class _SubscriberList(list):
    '''Event subscribers are shared by reference: excluded from deep copies so
    that the save/restore undo machinery never clones UI callbacks.'''

    def __deepcopy__(self, memo):
        return self


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
        self.vault_silks = {}
        self.adventurers = {}
        self.inns = {}
        for player in players:
            self.vault_silks[player] = 0
            self.adventurers[player] = []
            self.inns[player] = []
        
        self.game_started = False #Keep track of whether the game is running
        self.turn = 0
        self.event_subscribers = _SubscriberList() #callables notified of GameEvents via emit()
        
        #some information to keep track of centrally for players to make decisions
        self.winning_player = None
        self.max_vault_silks = 0
        self.total_vault_silks =  0
        self.total_chest_silks = 0
        self.silks_difference = 0
        self.num_failed_explorations = 0
#         self.inn_network = None #placeholder to keep track of which routes are possible in a single turn
#         self.inn_distances = [[]] #placeholder to keep track of where trade routes could be built
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

    def emit(self, kind, actor=None, **data):
        '''Notifies subscribers of a notable game occurrence.

        Arguments:
        kind: short dotted event identifier, e.g. "move", "explore.fail"
        actor: the token or player that acted, if any
        data: free-form supporting detail
        '''
        event = GameEvent(kind, actor, data)
        for subscriber in self.event_subscribers:
            subscriber(event)

    def save(self):
        '''Backs up the game and tokens' states, so that they can be restored later e.g. to undo a mistake
        '''
#        logger.debug("Backing up game state")
        self.backup = None #Avoid recursively backing up deep copies of earlier versions
        self.backup = copy.deepcopy(self)
#        memo = {}
#        try: 
#            self.backup = copy.deepcopy(self, memo)
#        except Exception as error:
#            logger.debug(error)
#            logger.debug(memo)
#            exit()
        
    def restore(self):
        '''Restores a previous game state.
        
        Thanks to Nithin: https://stackoverflow.com/questions/1216356/is-it-safe-to-replace-a-self-object-by-another-object-of-the-same-type-in-a-meth
        '''
        valid_classes = [Game, Token, Card, Tile, TilePile, list, dict]
        memo = []
        replace_references(self.backup, self, self.backup, memo, valid_classes) #Make sure that all elements within the backup copy of the game refer up to the true game
#        logger.debug("Investigated objects:")
#        logger.debug(memo)
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
    #                logger.debug("Restoring attributes of "+str(adventurer)+" from backup "+str(restored_copy)+"but keeping the reference.")
                    adventurer.__dict__.update(restored_copy.__dict__)
    #                #Because the adventurers came from the deep-copied game they will have references to the "copy" that has been abandoned
#                    adventurer.game = self
                    #adventurers are also referenced by tiles, so these will need updating
                    memo = []
                    replace_references(restored_copy, adventurer, self, memo, valid_classes)
#                    logger.debug("Investigated objects:")
#                    logger.debug(memo)
                else:
                    #If this adventurer wasn't in the backup, then discard it
                    adventurers[player].pop(adventurer)
            for inn in self.inns.get(player, []):
                #Because the inns came from the deep-copied game they will have references to the "copy" that has been abandoned
                inn.game = self        
#        logger.debug("Replacing the new replica of the game's Adventurer's list, "+str(self.adventurers)+", with the original full of original Adventurer references, "+str(adventurers))
        self.adventurers = adventurers
        #Tiles may still have references to the 
        #Now make sure there is a backup still in place for subsequent restores (the backup had no backup iteself)
        self.save()
    
#    def establish_turn_order(self):
#        '''Randomises the order in which Player objects will be activated'''
#        random.shuffle(self.players)
