'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

class Token:
    '''A template for actual tokens used in play.
    
    Methods:
    __init__ taking a Game and a Player and a Tile from the Cartolan module
    
    Interfaces:
    None
    '''
    def __init__(self, game, player, current_tile):
        self.game = game
        self.player = player
        self.current_tile = current_tile
        
        self.wealth = 0
        self.route = []
        self.turn_route = []
        
        current_tile.move_onto_tile(self)

class Adventurer(Token):
    '''A template for actual Adventurer tokens used in different game modes.
    
    Methods:
    __init__ taking a Game and a Player and a Tile from the Cartolan module
    
    Interfaces:
    move; explore; discover; trade; rest; 
    '''
    def __init__(self, game, player, current_tile):
        super().__init__(game, player, current_tile)
        game.adventurers[player].append(self)
        
        self.turns_moved = 0    
        
#    def __deepcopy__(self, memo):
#        '''Returns a reference instead of a serialisation, so that the same 
#        object reference can continue to be used when a previous game state is 
#        restored.
#        '''
#        return self
    
    def move(self, compass_point):
        '''placeholder for movement'''
        pass
        
    def explore(self, longitude, latitude):
        '''placeholder for exploration'''
        pass
        
    def discover(self, tile):
        '''placeholder for discovering new wealth'''
        pass
        
    def trade(self, tile):
        '''placeholder for trading on a suitable tile'''
        pass
        
    def rest(self, agent):
        '''placeholder for resting with an agent'''
        pass
    
    def attack(self, token):
        '''placeholder for attacking other tokens in Regular and Advanced modes'''
        pass

    def to_json(self):
        return {
            "player_name": self.player.name,
            "longitude": self.current_tile.tile_position.longitude if self.current_tile else None,
            "latitude": self.current_tile.tile_position.latitude if self.current_tile else None,
            "wealth": self.wealth,
            "route": [[t.tile_position.longitude, t.tile_position.latitude] for t in self.route],
            "turn_route": [[t.tile_position.longitude, t.tile_position.latitude] for t in self.turn_route],
        }

class Agent(Token):
    '''A template for actual Agent tokens used in different game modes.
    
    Methods:
    __init__ taking a Game and a Player and a Tile from the Cartolan module
    
    Interfaces:
    give_rest; manage_trade 
    '''
    def __init__(self, game, player, current_tile):
        super().__init__(game, player, current_tile)
        game.agents[player].append(self)
        
    def give_rest(self, adventurer):
        '''placeholder for resting adventurers'''
        pass
    
    def manage_trade(self, adventurer):
        '''placeholder for agents involved in trade on a tile'''
        pass

    def to_json(self):
        return {
            "player_name": self.player.name,
            "longitude": self.current_tile.tile_position.longitude if self.current_tile else None,
            "latitude": self.current_tile.tile_position.latitude if self.current_tile else None,
            "wealth": self.wealth,
            "is_dispossessed": None,
        }
