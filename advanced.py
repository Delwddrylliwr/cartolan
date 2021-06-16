'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import random
from regular import AdventurerRegular, AgentRegular, CityTileRegular
from base import WindDirection, TileEdges

class CardAdvanced():
    '''Modifies the rules for objects from other Cartolan classes.
    '''
    def __init__(self, game, card_type):
        self.game = game
        self.card_type = card_type
        self.buffs = game.card_type_buffs[card_type]
        
    def apply_buffs(self, token):
        '''Incorporates rule changes for the Adventurer/Agent that come from this cards
        '''
        for buff_attr in self.buffs:
            #Check that the token has the attribute associated with the buff
            current_attr_val = getattr(token, buff_attr, None) 
            if current_attr_val is not None:
                print("For "+token.player.colour+" player, adding a buff to their "+buff_attr)
                #Apply the buff
                if self.buffs[buff_attr]["buff_type"] == "boost":
                    setattr(token, buff_attr, current_attr_val + self.buffs[buff_attr]["buff_val"])
                elif self.buffs[buff_attr]["buff_type"] == "new":
                    setattr(token, buff_attr, self.buffs[buff_attr]["buff_val"])
                print(token.player.colour+" player's "+buff_attr+" now has value "+str(getattr(token, buff_attr, None)))
    
    def remove_buffs(self, token):
        '''Reverts rule changes for the Adventurer/Agent that come from this card
        '''
        for buff_attr in self.buffs:
            #Check that the token has the attribute associated with the buff
            current_attr_val = getattr(token, buff_attr, None) 
            if current_attr_val is not None:
                #Apply the buff
                if self.buffs[buff_attr]["buff_type"] == "boost":
                    setattr(token, buff_attr, current_attr_val - self.buffs[buff_attr]["buff_val"])
                elif self.buffs[buff_attr]["buff_type"] == "new":
                    #@TODO if a buff has been doubled then it shouldn't be lost
                    setattr(token, buff_attr, getattr(self.game, buff_attr))

class AdventurerAdvanced(AdventurerRegular):
    '''Extends to allow a set of map tiles to be carried by each Adventurer in their chest and placed instead of a random one
    '''
    def __init__(self, game, player, starting_city):
        super().__init__(game, player, starting_city)
        
        #Bring in game variables that might be altered by company/character stats
        self.num_chest_tiles = game.num_chest_tiles
        self.defence_rounds = game.defence_rounds
        self.agent_on_existing = game.agent_on_existing
        self.transfers_to_agents = game.transfers_to_agents
        self.attacks_abandon = game.attacks_abandon
        #Randomly draw a Character card
        #@TODO let the player choose between multiple character cards
        character_cards = self.game.character_cards
        self.character_card = character_cards.pop(random.randint(0, len(character_cards)-1))
        #Take on the changes to rules based on the Character card
        self.character_card.apply_buffs(self)
        #Take on the changes to rules based on the Company card
#        self.company_card = self.game.company_cards[self.player]
#        self.company_card.apply_buffs(self)
#        #Be ready to receive further buffs from Discovery cards
#        self.discovery_cards = []
        #Draw some tiles randomly to the Adventurer's Chest
        self.chest_tiles = []
        self.choose_random_tiles(self.num_chest_tiles)
        #Keep track of which of these should be tried for movement
        self.preferred_tile_num = None
    
    def discover_card(self, card):
        '''Adds a Discovery card to the Adventurer, modifying rules according to the card's buffs
        '''
        self.discovery_cards.append(card)
        card.apply_buffs(self)
    
    def choose_random_tiles(self, num_tiles):
        '''For a given number of tiles, select randomly from across the bags / tile_piles
        '''
        for tile_num in range(num_tiles):
            #Randomly select a tile pile to draw from
            tile_pile = self.game.tile_piles[random.choice(list(self.game.tile_piles.keys()))]
            #Randomly choose a tile from the bag / pile and add it to their Chest
            chosen_tile = tile_pile.tiles.pop(random.randint(0, len(tile_pile.tiles)-1))
            self.chest_tiles.append(chosen_tile)
    
    def move(self, compass_point):
        '''Extends Beginnner movement to rotate Chest tiles after movement (for more comfortable visualisation)
        '''
        moved = super().move(compass_point)
        if moved:
            for chest_tile in self.chest_tiles:
                while not (chest_tile.wind_direction.north == self.current_tile.wind_direction.north and 
                           chest_tile.wind_direction.east == self.current_tile.wind_direction.east):
                    chest_tile.rotate_tile_clock()
        return moved
    
    def explore(self, tile_pile, discard_pile, longitude, latitude, compass_point_moving):
        '''Extends exploration to allow tiles to be used from the Adventurer's Chest
        '''
        #check if there is a chest tile selected and try to place this
        if isinstance(self.preferred_tile_num, int):
            preferred_tile = self.chest_tiles[self.preferred_tile_num]
            #establish what edges adjoin the given space
            adjoining_edges_water = self.get_adjoining_edges(longitude, latitude)
            #try to place the tile
            if self.rotate_and_place(preferred_tile, longitude, latitude, compass_point_moving, adjoining_edges_water):
                self.chest_tiles.pop(self.preferred_tile_num)
                self.preferred_tile_num = None
                return True          
        #If there was no tile selected or this wouldn't fit, then explore normally, drawing a random tile
        return super().explore(tile_pile, discard_pile, longitude, latitude, compass_point_moving)
        
    def attack(self, token):
        '''Extends Regular mode to allow stealing of Chest Tiles
        '''
        #If the target Adventurer has a defensive buff to force multiple rounds of attack then these need to be won first
        if isinstance(token, AdventurerAdvanced):
            for defence_round in range(0, token.defence_rounds-1):
                if random.random() > self.attack_success_prob:
                    return False
        if super().attack(token):
            #Randomly steal tiles to top up
            if isinstance(token, AdventurerAdvanced):
                if len(self.chest_tiles) < self.num_chest_tiles:
                    victim_chest = token.chest_tiles
                    self.chest_tiles.append(victim_chest.pop(random.randint(0, len(victim_chest)-1)))
            if self.attacks_abandon: #Adventurers will return to cities, Agents are removed
                if isinstance(token, AdventurerRegular):
                    token.end_expedition()
                elif isinstance(token, AgentRegular):
                    token.dismiss()
            return True
        else:
            return False
        
    def replenish_chest_tiles(self):
        '''If this Adventurer has fewer chest tiles than the max, then draw more
        '''
        #Count how many tiles they are short of the max chest tiles
        num_tiles_to_choose = self.num_chest_tiles - len(self.chest_tiles)
        #Add this many extra tiles to their chest
        self.choose_random_tiles(num_tiles_to_choose)
    
    def interact_tile(self):
        '''Extends the Regular, to allow placing Agents on existing tiles for some Adventurer buffs
        '''
        super().interact_tile()
        if self.transfers_to_agents:
            self.transfer_funds()
        if self.agent_on_existing:
            #An agent can still be placed on this existing tile, but at the cost of placing from the city
            cost_exploring = self.game.cost_agent_exploring
            cost_existing = self.game.cost_agent_from_city
            if self.wealth >= cost_existing:
                self.game.cost_agent_exploring = cost_existing
                self.place_agent()
                self.game.cost_agent_exploring = cost_exploring
    
    def rechoose_chest_tiles(self):
        '''Checks whether the player will pay to replace all an Adventurer's chest tiles
        '''
#        if self.player.check_rechoose_tiles():
#            #Return current tiles to the bag / tile pile
#            while self.chest_tiles:
#                tile = self.chest_tiles.pop()
#                relevant_pile = self.game.tile_piles[tile.tile_back]
#                relevant_pile.append(tile)
#            #Replenish the empty Chest Tiles
#            self.replenish_chest_tiles()
        
    def transfer_funds(self):
        '''Offers the player the chance to move this Adventurer's trasure to any Agent.
        '''
        return False

class AgentAdvanced(AgentRegular):
    '''Extends Regular mode to replenish Chest Tiles
    '''
    def give_rest(self, adventurer):
        '''Extends Regular mode to replenish Chest Tiles
        '''
        if self.is_dispossessed:
            return False
        else:
            adventurer.replenish_chest_tiles()
            return super().give_rest(adventurer)

class CityTileAdvanced(CityTileRegular):
    '''Extends to replenish Chest Tiles, and offer purchase of refreshed chest tiles
    '''
    def visit_city(self, adventurer, abandoned=False):
       '''Extends to replenish Chest Tiles, and offer purchase of refreshed chest tiles
       '''
       #Top up any missing chest tiles from the bags
       adventurer.replenish_chest_tiles()
       #Offer the chance to pay and completely swap out chest tiles
       adventurer.rechoose_chest_tiles()
       #Continue as usual
       super().visit_city(adventurer, abandoned)

class CapitalTileAdvanced(CityTileAdvanced):
    def __init__(self, game, tile_back = "water"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(True,True,True,True)):
        return super().__init__(game, wind_direction, tile_edges, True, True)

class MythicalTileAdvanced(CityTileAdvanced):
    def __init__(self, game, tile_back = "land"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(False,False,False,False)):
        return super().__init__(game, wind_direction, tile_edges, False, False)