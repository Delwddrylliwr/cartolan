'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import random

class Player:
    '''A template for actual Players responding to play in a Game of Cartolan.
    
    Methods:
    __init__ taking a name string
    
    Interfaces:
    continue_turn; continue_move 
    '''
    def __init__(self, name = "red"):
        self.name = name
        self.games = {}
        self.attack_history = {} #per-game record of attacks, for visualisation
        self.player_id = name+str(random.random())
        
    def __hash__(self):
        return hash(self.player_id)
    
    def __eq__(self, other):
        if isinstance(other, Player):
            return self.player_id == other.player_id
        else: return False
        
    def __ne__(self, other):
        if isinstance(other, Player):
            return not self.player_id == other.player_id
        else: return True
    
    def __deepcopy__(self, memo):
        '''Excludes the player class from deep copies, returning just a reference
        '''
        return self
    
    def join_game(self, game):
        '''Establishes dict to retain strategic info for each game
        '''
        self.games[game.game_id] = {"game":game
                  , "locations_to_avoid":[] #tiles to remember to avoid for artificial players @TODO move this into game-specific dict entry
                  , "attack_history":[] #a record of where attacks have taken place, to support visualisation @TODO move this into the visual
                  }
    
    def connect_gui(self, game_vis):
        '''Associates a particular gui with a game
        '''
        game = game_vis.game
        self.games[game.game_id]["game_vis"] = game_vis
    
    def continue_move(self, adventurer):
        '''placeholder for responding to the state of the game by choosing movement for an adventurer'''
        pass

    def continue_turn(self, adventurer):
        '''placeholder for responding to the state of the game'''
        pass

    def check_hire_companion(self, adventurer):
        '''placeholder — subclasses override to allow hiring Companions at cities'''
        return False

    def check_steal_map(self, adventurer, victim):
        '''Whether to take one of the victim's Chest maps after successful piracy.'''
        return True

    def check_steal_manuscript(self, adventurer, victim):
        '''Whether to take one of the victim's Manuscript cards after successful piracy.'''
        return True

    def choose_map_pile(self, adventurer, options):
        '''Chooses which tile pile to draw a map from (blue water or green land).

        Defaults to the fullest pile; subclasses may prompt the player instead.
        '''
        return max(options, key=lambda tile_back: len(adventurer.game.tile_piles[tile_back].tiles))

    def to_json(self):
        return {"name": self.name}
