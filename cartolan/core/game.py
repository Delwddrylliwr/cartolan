'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import copy
import random
import uuid

from cartolan.core.events import GameEvent
from cartolan.core.cards import Card
from cartolan.core.tiles import Tile

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

    def _shared_identity_memo(self):
        '''A deepcopy memo pre-seeded with the objects whose identity must survive
        a save/restore round trip: the Game itself and its Players, which own live
        UI and network connections.'''
        memo = {id(self): self}
        for player in self.players:
            memo[id(player)] = player
        return memo

    def save(self):
        '''Backs up the game state, so that it can be restored later e.g. to undo a mistake.

        The backup is a deep copy of the game's attributes; the Game, its Players
        and the event subscribers are shared by reference rather than cloned.
        '''
        state = {name: value for name, value in self.__dict__.items() if name != "backup"}
        self.backup = copy.deepcopy(state, self._shared_identity_memo())

    def restore(self):
        '''Restores the last saved game state.

        The identity of the Game, its Players, and the Adventurers present at the
        save is preserved, since UIs and players hold direct references to them
        across an undo. The backup itself is copied rather than consumed, so
        repeated restores return to the same save point.
        '''
        memo = self._shared_identity_memo()
        #each backed-up Adventurer stands in for the live token it was copied from
        live_adventurers = {}
        for player, adventurers in self.adventurers.items():
            backups = self.backup["adventurers"].get(player, [])
            for adventurer, backup_copy in zip(adventurers, backups):
                memo[id(backup_copy)] = adventurer
                live_adventurers[adventurer] = backup_copy
        state = copy.deepcopy(self.backup, memo)
        #the live Adventurers adopt their backed-up attributes, resolved against
        #the same memo so they point into the restored play area
        for adventurer, backup_copy in live_adventurers.items():
            restored = copy.deepcopy(backup_copy.__dict__, memo)
            adventurer.__dict__.clear()
            adventurer.__dict__.update(restored)
        #attributes gained since the save are dropped along with the update
        for name in list(self.__dict__):
            if name != "backup" and name not in state:
                delattr(self, name)
        self.__dict__.update(state)
