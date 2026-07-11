'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import os

from cartolan.core.game import Game, GLOBAL_RNG
from cartolan.core.tiles import Tile, TilePile, WindDirection, TileEdges
from cartolan.editions.beginner import AdventurerBeginner, InnBeginner, CityTileBeginner, TradePortTile, HomeCityTileBeginner
from cartolan.editions.regular import AdventurerRegular, InnRegular, CityTileRegular, DisasterTile, HomeCityTileRegular, MythicalCityTileRegular
from cartolan.editions.advanced import AdventurerAdvanced, InnAdvanced, CityTileAdvanced, CardAdvanced
import random
import csv
#bring in all the constants from the config file
import copy
import dataclasses

from cartolan.rules.ruleset import BEGINNER, REGULAR, ADVANCED

import logging

logger = logging.getLogger(__name__)

class GameBeginner(Game):
    '''Executes the sequence of play for the Beginner mode of the board game Cartolan - Trade Winds
    
    Beginner mode involves only water tiles being placed as Adventurer tokens are moved around the play area 
    collecting silks from discovering and trading at Trade Port tiles. 
    
    Inn tokens can be placed as tiles are visited to confer silks and movement bonuses to Adventurers.
    
    Methods:
    __init__ takes a List of Cartolan.Players and two Strings
    start_game
    refresh_pile takes two Cartolan.TilePile objects
    play_round
    check_win_conditions
    '''
    #Set non-configurable class level constants
    TILE_PREFIX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tile_distribution_")
    TILE_EXT = ".csv"
    TILE_TYPE_COLS = {"trade_port":1}
    TILE_TYPES = {"plain":Tile, "home_city":HomeCityTileBeginner, "trade_port":TradePortTile}
    ADVENTURER_TYPE = AdventurerBeginner
    INN_TYPE = InnBeginner
    CITY_TYPE = CityTileBeginner
    
    #The rule values for this edition; instances mirror the fields as attributes
    RULESET = BEGINNER


    def __init__(self, players, movement_rules = 'initial', exploration_rules = 'continuous', rng=None):
        
        super().__init__(players)
        
        #Randomness source: defaults to the global random module; tests may pass
        #a seeded random.Random instance for reproducibility
        self.rng = rng if rng is not None else GLOBAL_RNG
        
        #Mirror rule values onto mutable instance attributes: the Ruleset is the
        #single source of truth, but cards may modify per-token copies until the
        #RuleView overlay replaces the setattr buff mechanism
        self.ruleset = self.RULESET
        for rule_field in dataclasses.fields(self.ruleset):
            setattr(self, rule_field.name, copy.deepcopy(getattr(self.ruleset, rule_field.name)))
        
        if movement_rules in ["initial", "budgetted"]:
            self.movement_rules = movement_rules
        else: raise Exception("Invalid movement rules specified")
        
        if exploration_rules in ["clockwise", "continuous"]:
            self.exploration_rules = exploration_rules
        else: raise Exception("Invalid exploration rules specfied")
        
        self.cities = []

        self.tile_piles = {"water":TilePile("water",[])}
        self.discard_piles = {"water":TilePile("water",[])}
        
        self.exploration_attempts = 0
        self.win_type = None
        self.game_over = False
    
    def setup_tile_pile(self, tile_back):
        '''Part of game setup for Cartolan, this creates a tile of shuffled water-backed tiles ready for play
        
        Arguments:
        tile_back a string designating the type of tile and so its distribution of edge combinations
        '''
        total_distribution = []
        special_distributions = {} # for trade_port/disaster
        for tile_type in self.TILE_TYPE_COLS:
            special_distributions[tile_type] = []
        
        tile_filename = self.TILE_PREFIX + tile_back + self.TILE_EXT
        with open(tile_filename) as csvfile:
            readCSV = csv.reader(csvfile)
            for row in readCSV:
                total_distribution.append(int(row[0]))
                for tile_type in self.TILE_TYPE_COLS:
                    special_distributions[tile_type].append(int(row[self.TILE_TYPE_COLS[tile_type]]))
        
        #construct the tile deck
        row_count = 0
        tiles = []
        for uc_water in [True, False]:
            for ua_water in [True, False]:
                for dc_water in [True, False]:
                    for da_water in [True, False]:
                        #for this combination of tile edges create tiles of each special type and plain ones
                        special_tile_num = 0
                        for tile_type in special_distributions:
                            for tile_num in range(0, int(special_distributions[tile_type][row_count])):
                                wind_direction = WindDirection(north = True, east = True)
                                tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
                                tiles.append(self.TILE_TYPES[tile_type](self, tile_back, wind_direction, tile_edges))
                                special_tile_num += 1
                        for tile_num in range(0, int(total_distribution[row_count]) - special_tile_num):
                            wind_direction = WindDirection(north = True, east = True)
                            tile_edges = TileEdges(uc_water, ua_water, dc_water, da_water)
                            tiles.append(Tile(self, tile_back, wind_direction, tile_edges, False))
                        row_count += 1
        
        #draw a suitable number of tiles from the deck for a pile
    #     num_tiles = len(players)*game.WATER_TILES_PER_PLAYER
        num_tiles = self.num_pile_tiles[tile_back]
        tile_pile = self.tile_piles[tile_back]
        for tile in self.rng.sample(tiles, num_tiles):
            tile_pile.add_tile(tile)
        
        tile_pile.shuffle_tiles(self.rng)
        
        logger.debug("Built a " +tile_back+ " tile pile with " +str(len(self.tile_piles[tile_back].tiles))+ " tiles, and shuffled it")
    
    def start_game(self):
        '''Begins the sequence of play, under the assumption that the play area has been set up'''
        self.game_started = True
        self.game_over = False
        while not self.game_over:
            self.turn += 1
            self.game_over = self.play_round()
        
        #report game conclusion to caller
        return True
    
    
    def refresh_pile(self, tile_pile, discard_pile):
        '''Swaps the discard pile of tiles for the active pile, shuffling it
        
        Arguments:
        Cartolan.TilePile the pile to replace
        Cartolan.TilePile the discard pile to put into play
        '''
        #check whether the discard pile is empty too
        if discard_pile.tiles:
            self.tile_piles.pop(tile_pile.tile_back)
            self.tile_piles[tile_pile.tile_back] = discard_pile
            tile_pile = self.tile_piles[tile_pile.tile_back]
            discard_pile.shuffle_tiles(self.rng)
            logger.debug("Have replaced the main tile pile with the discard pile, and shuffled it,"
                  +" so that now there are " +str(len(self.tile_piles))+ " tile piles.")
            #Start a new discard pile
            self.discard_piles.pop(discard_pile.tile_back)
            self.discard_piles[discard_pile.tile_back] = TilePile(discard_pile.tile_back, [])
#             self.discard_piles["water"] = TilePile("water",[])
            discard_pile = self.discard_piles[discard_pile.tile_back]
            logger.debug("Have started a new discard pile, so that now there are "
                 + str(len(self.discard_piles))+ " discard piles.")
            return True
        else:
            return False #both piles are exhausted; the game loop's win check will end the game
    
    def play_round(self):
        '''Carries out the sequence of play for one round of the game'''
        logger.debug("playing round "+str(self.turn)+" with a silks difference of " +str(self.silks_difference) 
             +" and a max silks of " +str(self.max_vault_silks))
        for player in self.players:
            #some logging
            logger.debug(str(player.name)+ " player's turn, with " +str(len(self.adventurers[player])) 
                  +" Adventurers, and " +str(self.vault_silks[player])+ " silks in the Vault")
#             if not player.adventurers[0] is None:
#                 adventurer = player.adventurers[0]
#                 adventurer_tile = adventurer.current_tile
#                 logger.debug("And their first Adventurer has " +str(adventurer.silks)+ " silks, and is on the " +adventurer_tile.tile_back+  " tile at position " +str(adventurer_tile.tile_position.latitude)+ "," +str(adventurer_tile.tile_position.longitude))
            
            # a more sophisticated simulation might need to let players choose their Adventurers' turn order first
            
            # let players move an adventurer so long as it still has valid moves
            for adventurer in self.adventurers[player]:
                if adventurer.turns_moved < self.turn:
                    adventurer.turn_route = [adventurer.current_tile]
                    player.continue_turn(adventurer)
                    logger.debug("") #to help log readability
                    
                    #check whether this adventurer's turn has won them the game
                    if self.check_win_conditions():
                        return True
        
        #log the numbers of tiles remaining in the game
        for tile_back in self.tile_piles.keys():
            tile_pile = self.tile_piles[tile_back]
            discard_pile = self.discard_piles[tile_back]
            logger.debug(str(len(tile_pile.tiles))+" "+tile_back+" tiles left in the main pile and " +str(len(discard_pile.tiles))+" left in the discard pile")
            logger.debug("") #to help log readability
            
    
    def run_city_visit(self, adventurer, city, abandoned=False):
        '''Initiates all the possible actions when a city is visited

        Arguments:
        Cartolan.Adventurer the Adventurer arriving on the City tile
        Cartolan.CityTile the city being visited
        Boolean abandoned prevents hiring option if the Adventurer has aborted their expedition, making it harder to replace opponents' Inns.
        '''
        #record that this is the latest city visited
        adventurer.latest_city = city

        self.bank_silks(adventurer)

        if self.winning_condition() is None and not abandoned:
            self.offer_purchases(adventurer, city)

        #End the Adventurer's turn and reset their moves
        adventurer.end_turn()

        return True

    def bank_silks(self, adventurer):
        '''Offers a player to move silks from their Adventurer's Chest into their Vault

        Arguments:
        Cartolan.Adventurer the Adventurer that has arrived at the City
        '''
        #check whether and how much the player wants to bank
        silks_to_bank = adventurer.player.check_bank_amount(adventurer, adventurer.silks, self.vault_silks[adventurer.player])
        #record the decision about how much silks will be banked
        adventurer.banked = silks_to_bank

        #check if silks is available and move it from the adventurer's Chest to their Vault
        if adventurer.silks >= silks_to_bank:
            adventurer.silks -= silks_to_bank
            self.vault_silks[adventurer.player] += silks_to_bank
            logger.debug(adventurer.player.name+ " has banked " +str(silks_to_bank)+ " in their Vault")
            return True
        else:
            return False

    def buy_adventurers(self, adventurer, city):
        '''Offers the Player of an Adventurer arriving at the City Tile to buy another Adventurer

        Arguments:
        Cartolan.Adventurer the Adventurer arriving at the City
        Cartolan.CityTile the city where the new Adventurer would be placed
        '''
        #record the decision to buy an adventurer this turn
        adventurer.bought_adventurer += 1

        #keep checking whether the player has enough silks and wants to buy another adventurer until they refuse
        while (len(self.adventurers[adventurer.player]) < self.max_adventurers
                and self.vault_silks[adventurer.player] >= adventurer.cost_adventurer):
            if adventurer.player.check_buy_adventurer(adventurer):
                #take payment of silks from their Vault
                self.vault_silks[adventurer.player] -= adventurer.cost_adventurer
                #place another Adventurer for this Player on the City tile
                new_adventurer = self.ADVENTURER_TYPE(self, adventurer.player, city)
                city.move_onto_tile(new_adventurer)
                new_adventurer.turns_moved = self.turn # This new Adventurer will play from the next turn
                logger.debug(adventurer.player.name+ " has bought an adventurer from the city at "
                      +str(city.tile_position.longitude)+","+str(city.tile_position.latitude))
            else:
                return False
        return True

    def buy_inns(self, adventurer, city):
        '''Offers the Player of an Adventurer arriving at the City Tile to buy another Inn and place it on any unclaimed tile

        Arguments:
        Cartolan.Adventurer the Adventurer arriving at the City, if None, then the Player will no longer be prompted
        Cartolan.CityTile the city selling the inn
        '''
        #Record the decision to buy an inn this move
        adventurer.bought_inn += 1

        #keep checking whether the player can afford another Adventurer and wants one until they refuse
        while self.vault_silks[adventurer.player] >= adventurer.cost_inn_from_city:
            tile = adventurer.player.check_buy_inn(adventurer, report="Do you want to place an inn, and where?")
            if not tile:
                return False

            #check whether the tile already has an active Inn
            if not adventurer.check_tile_available(tile):
                continue
            else:
                #pick up an existing Inn from its tile if there are no other inns available
                #otherwise get a new inn
                if len(self.inns[adventurer.player]) >= self.max_inns:
                    inn = adventurer.player.check_move_inn(adventurer)
                    if not inn is None:
                        logger.debug(adventurer.player.name+ " is recalling their inn from the tile at "
                          +str(inn.current_tile.tile_position.longitude)
                              +","+str(inn.current_tile.tile_position.latitude))
                        inn.current_tile.move_off_tile(inn)
                        #place the Inn on that tile
                        tile.move_onto_tile(inn)
                    else:
                        logger.debug(adventurer.player.name+ " did not want to move any existing Inns, so moving on.")
                        return False
                else:
                    inn = self.INN_TYPE(self, adventurer.player, tile)

                #take payment from the Player's Vault
                self.vault_silks[adventurer.player] -= adventurer.cost_inn_from_city
                logger.debug(adventurer.player.name+ " has hired an inn from the city at "
                  +str(city.tile_position.longitude)+","+str(city.tile_position.latitude)
                     +" and sent them to the tile at "
                     +str(tile.tile_position.longitude)+","+str(tile.tile_position.latitude))
        return True

    def hire_companion(self, adventurer):
        '''Offers the visiting Adventurer the chance to hire a Companion, scaling future trade and rest costs.

        Args:
            adventurer: the visiting Adventurer
        '''
        while (adventurer.num_companions < adventurer.max_companions
               and self.vault_silks[adventurer.player] >= adventurer.cost_companion):
            if adventurer.player.check_hire_companion(adventurer):
                self.vault_silks[adventurer.player] -= adventurer.cost_companion
                adventurer.num_companions += 1
                logger.debug(adventurer.player.name + " hired a Companion (now "
                      + str(adventurer.num_companions) + " companions, "
                      + str(adventurer.num_characters) + " characters total)")
            else:
                return False
        return True

    def offer_purchases(self, adventurer, city):
        '''Manages the sequence of purchasing options for players when their Adventurer reaches a city.

        Args:
            adventurer: the visiting Adventurer
            city: the city being visited
        '''
        self.buy_adventurers(adventurer, city)
        if self.inns_from_city:
            self.buy_inns(adventurer, city)
        self.hire_companion(adventurer)

    def update_standings(self):
        '''Recomputes max_vault_silks, silks_difference, and totals from current vault silks.

        silks_difference is the gap between the leading player's vault silks and the
        next-closest player's vault silks.  It is always updated regardless of which
        win condition is active, so it can be used as a performance metric independently.
        '''
        self.max_vault_silks = 0
        self.total_vault_silks = 0
        self.total_chest_silks = 0
        self.silks_difference = 0
        for player in self.players:
            self.total_vault_silks += self.vault_silks[player]
            for adventurer in self.adventurers[player]:
                self.total_chest_silks += adventurer.silks
            if self.vault_silks[player] > self.max_vault_silks:
                self.silks_difference = self.vault_silks[player] - self.max_vault_silks
                self.max_vault_silks = self.vault_silks[player]
                self.winning_player = player
            elif self.max_vault_silks - self.vault_silks[player] < self.silks_difference:
                self.silks_difference = self.max_vault_silks - self.vault_silks[player]

    def winning_condition(self):
        '''Checks whether any win condition is currently satisfied, without changing game state.

        Returns the win type string, or None. Callers that need to end the game must go
        through check_win_conditions, which only the game loop should invoke.
        '''
        self.update_standings()

        if self.winning_vault_silks is not None and self.max_vault_silks >= self.winning_vault_silks:
            return "vault threshold"

        if self.winning_silks_difference is not None and self.silks_difference > self.winning_silks_difference:
            return "silks difference"

        for tile_pile in self.tile_piles.values():
            if not tile_pile.tiles and not self.discard_piles[tile_pile.tile_back].tiles:
                if self.winning_player:
                    return "exhausted " +tile_pile.tile_back+ " tiles"
                return "tiles exhausted but no player banked silks"

        return None

    def check_win_conditions(self):
        '''Applies any satisfied win condition, ending the game.

        The game loop (play_round) is the only authority that ends the game; game logic
        elsewhere may query winning_condition but must not end the game itself.
        '''
        win_type = self.winning_condition()
        if win_type is None:
            return False
        logger.debug("won by " + win_type)
        self.win_type = win_type
        if win_type == "tiles exhausted but no player banked silks":
            max_chest_silks = 0
            for player in self.players:
                for adventurer in self.adventurers[player]:
                    if adventurer.silks > max_chest_silks:
                        self.winning_player = player
                        max_chest_silks = adventurer.silks
        self.game_over = True
        return True

    def to_json(self):
        play_area = {}
        for lon in self.play_area:
            play_area[str(lon)] = {}
            for lat in self.play_area[lon]:
                play_area[str(lon)][str(lat)] = self.play_area[lon][lat].to_json()
        return {
            "game_mode": "Beginner",
            "turn": self.turn,
            "winning_player": self.winning_player.name if self.winning_player else None,
            "silks_difference": self.silks_difference,
            "play_area": play_area,
            "players": [p.name for p in self.players],
            "vault_silks": {p.name: w for p, w in self.vault_silks.items()},
            "adventurers": {p.name: [a.to_json() for a in advs] for p, advs in self.adventurers.items()},
            "inns": {p.name: [a.to_json() for a in agts] for p, agts in self.inns.items()},
            "tile_piles": {back: pile.to_json() for back, pile in self.tile_piles.items()},
            "discard_piles": {back: pile.to_json() for back, pile in self.discard_piles.items()},
            "num_tiles": self.num_pile_tiles,
        }


class GameRegular(GameBeginner):
    '''Extends the GameBeginner class to include extra features of the Regular mode of Cartolan - Trade Winds
    
    In Regular mode inns can be ransacked and restored through Adventurers committing piracy, with rewards and costs.
    
    Methods:
    __init__ takes a List of Cartolan.Player objects and two Strings
    check_win_conditions
    '''
    #Set class constants that can't be configured
    TILE_TYPE_COLS = {"trade_port":1, "disaster":2}
    TILE_TYPES = {"plain":Tile, "home_city":HomeCityTileRegular, "mythical_city":MythicalCityTileRegular, "trade_port":TradePortTile, "disaster":DisasterTile}    
    ADVENTURER_TYPE = AdventurerRegular
    INN_TYPE = InnRegular
    CITY_TYPE = CityTileRegular #no extra functionality needed until Advanced mode

    RULESET = REGULAR

    def __init__(self, players, movement_rules = 'initial', exploration_rules = 'continuous', rng=None):
        super().__init__(players, movement_rules, exploration_rules, rng)
        #Some rule values apply per player, so they can be modified by Culture cards
        self.num_tile_choices = {player: self.ruleset.num_tile_choices for player in players}
        
        # a land tile pile is now needed
        self.tile_piles["land"] = TilePile("land",[])
        self.discard_piles["land"] = TilePile("land",[])
        
        # keep track of some information centrally for players' decisions
        self.dropped_silks = 0
        self.disaster_tiles = []
    
    def run_city_visit(self, adventurer, city, abandoned=False):
        '''Extends to redeem pirates, replenish Chest maps, and offer purchase of refreshed chest maps
        '''
        #Cities provide the Adventurer with civilised clothes so they can be redeemed from piracy
        if adventurer.pirate_token:
            adventurer.pirate_token = False

        #Top up any missing chest maps from the bags
        adventurer.replenish_chest_maps()

        return super().run_city_visit(adventurer, city, abandoned)

    def buy_maps(self, adventurer):
        '''Lets the Adventurer choose to refresh all their Chest maps.

        Args:
            adventurer: the visiting Adventurer
        '''
        # Offer the chance to pay and completely swap out chest maps
        while (self.vault_silks[adventurer.player] >= self.cost_refresh_maps
               and adventurer.player.check_buy_maps(adventurer)):
            self.vault_silks[adventurer.player] -= self.cost_refresh_maps
            adventurer.swap_chest_maps()

    def offer_purchases(self, adventurer, city):
        '''Manages the sequence of purchasing options for players when their Adventurer reaches a city.

        Args:
            adventurer: the visiting Adventurer
            city: the city being visited
        '''
        self.buy_adventurers(adventurer, city)
        self.hire_companion(adventurer)
        if self.inns_from_city:
            self.buy_inns(adventurer, city)
        self.buy_maps(adventurer)

    def winning_condition(self):
        self.dropped_silks = 0
        for tile in self.disaster_tiles:
            self.dropped_silks += tile.dropped_silks

        return super().winning_condition()

    def to_json(self):
        d = super().to_json()
        d["game_mode"] = "Regular"
        return d


class GameAdvanced(GameRegular):
    '''Extends the GameRegular class to include extra features of the Adventurer mode of Cartolan - Trade Winds
    
    Advanced mode allows each Adventurer to carry a small complement of Map Tiles.
    In future, Advanced mode will have tech cards held by Adventurers, to confer advantages, while each adventurer will have a character card giving them starting equipment.
    
    Methods:
    __init__ takes a List of Cartolan.Player objects and two Strings
    '''
    ADVENTURER_TYPE = AdventurerAdvanced
    INN_TYPE = InnAdvanced
    CITY_TYPE = CityTileAdvanced #no extra functionality needed until Advanced mode
    CARD_TYPE = CardAdvanced

    RULESET = ADVANCED

    def __init__(self, players, movement_rules='initial', exploration_rules='continuous', rng=None):
        super().__init__(players, movement_rules, exploration_rules, rng)
        
        #Some rule values apply per player, so they can be modified by Culture cards
        self.num_character_choices = {}
        self.num_manuscript_choices = {}
        self.value_inn_trade = {}
        self.rest_with_adventurers = {}
        self.transfer_inn_earnings = {}
        self.inns_arrest = {}
        self.confiscate_silks = {}
        self.resting_refurnishes = {}
        self.pool_maps = {}
        self.rechoose_at_inns = {}
        #And a placeholder for players to choose a Culture/Company
        self.assigned_cultures = {}
        for player in players:
            self.num_character_choices[player] = self.ruleset.num_character_choices
            self.num_manuscript_choices[player] = self.ruleset.num_manuscript_choices
            self.value_inn_trade[player] = self.ruleset.value_inn_trade
            self.rest_with_adventurers[player] = self.ruleset.rest_with_adventurers
            self.transfer_inn_earnings[player] = self.ruleset.transfer_inn_earnings
            self.inns_arrest[player] = self.ruleset.inns_arrest
            self.confiscate_silks[player] = self.ruleset.confiscate_silks
            self.resting_refurnishes[player] = self.ruleset.resting_refurnishes
            self.pool_maps[player] = self.ruleset.pool_maps
            self.rechoose_at_inns[player] = self.ruleset.rechoose_at_inns
            self.assigned_cultures[player] = None
        
        #Set up the decks of cards
        self.card_count = 0
        self.culture_cards = [self.CARD_TYPE(self, card_type) for card_type in self.ruleset.culture_cards]
        self.character_cards = [self.CARD_TYPE(self, card_type) for card_type in self.ruleset.character_cards]
        self.manuscript_cards = [self.CARD_TYPE(self, card_type) for card_type in self.ruleset.manuscript_cards]
        
    def hire_companion(self, adventurer):
        '''Extends base hire to also draw a character card for the new Companion.
        '''
        companions_before = adventurer.num_companions
        super().hire_companion(adventurer)
        for _ in range(adventurer.num_companions - companions_before):
            adventurer.add_companion_card()
        return adventurer.num_companions > companions_before

    def buy_manuscripts(self, adventurer):
        '''Offers the visiting Adventurer the chance to upgrade themselves.

        Args:
            adventurer: the visiting adventurer
        '''
        logger.debug(
            "Offering " + adventurer.player.name + "'s adventurer the chance to upgrade the Adventurer with a Manuscript card")
        while (self.manuscript_cards
               and self.vault_silks[adventurer.player] >= self.cost_manuscript
               and adventurer.player.check_buy_manuscript(adventurer)):
            logger.debug(adventurer.player.name + "'s has chosen to buy a Manuscript card")
            if adventurer._offer_manuscript_choice():
                self.vault_silks[adventurer.player] -= self.cost_manuscript

    def buy_maps(self, adventurer):
        '''Extends the parent with the potential for a free refresh of maps.

        Args:
            adventurer: the visiting Adventurer
        '''
        # If they have the perk, let them have one swap of maps for free
        if adventurer.rechoose_at_inns:
            cost_refresh_maps = self.cost_refresh_maps
            self.cost_refresh_maps = 0
            if adventurer.player.check_buy_maps(adventurer):
                adventurer.swap_chest_maps()
            self.cost_refresh_maps = cost_refresh_maps
        super().buy_maps(adventurer)

    def offer_purchases(self, adventurer, city):
        '''Extends to allow rule changes from cards
        '''
        self.buy_adventurers(adventurer, city)
        self.hire_companion(adventurer)
        if self.inns_from_city:
            self.buy_inns(adventurer, city)
        self.buy_manuscripts(adventurer)
        self.buy_maps(adventurer)

    def choose_culture(self, player):
        '''Lets the player choose a character card from a random subset
        '''
        culture_cards = self.culture_cards
        card_options = self.rng.sample(culture_cards, k=self.num_culture_choices)
        logger.debug("Offering a selection of Culture cards:")
        for card in card_options:
            logger.debug(card.card_type)
        self.assigned_cultures[player] = player.choose_card(self.adventurers[player][0], card_options)
        culture_cards.remove(self.assigned_cultures[player])
        #Take on the changes to rules based on the Character card
        self.assigned_cultures[player].apply_buffs(player) #for all Adventurers and Inns created after this point
        for adventurer in self.adventurers[player]: #For all existing Adventurers
            self.assigned_cultures[player].apply_buffs(adventurer)

    def to_json(self):
        d = super().to_json()
        d["game_mode"] = "Advanced"
        d["assigned_cultures"] = {
            p.name: card.to_json()
            for p, card in self.assigned_cultures.items()
            if card is not None
        }
        return d

#    def __init__(self, players, movement_rules = 'initial', exploration_rules = 'continuous'):
#        super().__init__(players, movement_rules, exploration_rules)
