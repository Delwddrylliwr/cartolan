'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com

Cartolan - Lite Winds: the base game.

Adventurers race out on expeditions over land and sea, exploring with the maps
they carry, trading at Trade Ports, hiring Inns to rest along their route, and
banking Silks at Cities. Character cards give each Adventurer a perk, and
Companions can be hired at Cities to scale trade. First player to bank 100
Vault Silks wins.
'''

import copy
import csv
import dataclasses
import logging
import os

from cartolan.core.game import Game, GLOBAL_RNG
from cartolan.core.movement import classify_move, legal_directions, spend_move, rest_moves
from cartolan.core.tokens import Adventurer, Inn
from cartolan.core.tiles import Tile, TilePile, CityTile, WindDirection, TileEdges
from cartolan.core.cards import Card
from cartolan.rules.ruleset import LITE_WINDS

logger = logging.getLogger(__name__)


class ModifierCard(Card):
    '''A card that modifies the rules for the token or player holding it.'''

    def __init__(self, game, card_type):
        super().__init__(game, card_type)
        self.buffs = game.card_modifiers[card_type[3:]]

    #some supporting functions to deal with different attribute types
    def add(self, a, b):
        '''Applies elementwise addition when given lists of lists rather than numbers
        '''
        if isinstance(a, list) and isinstance(b, list):
            if isinstance(a[0], list) and isinstance(b[0], list):
                combs = [[a[i], b[i]] for i in range(min(len(a), len(b)))]
                return [[ comb[0][j] + comb[1][j] for j in range(min(len(comb[0]), len(comb[1])))] for comb in combs]
        else:
            return a + b

    def sub(self, a, b):
        '''Applies elementwise subtraction when given lists of lists rather than numbers
        '''
        if isinstance(a, list) and isinstance(b, list):
            if isinstance(a[0], list) and isinstance(b[0], list):
                combs = [[a[i], b[i]] for i in range(min(len(a), len(b)))]
                return [[ comb[0][j] - comb[1][j] for j in range(min(len(comb[0]), len(comb[1])))] for comb in combs]
        else:
            return a - b

    def apply_buffs(self, target):
        '''Incorporates rule changes for the Adventurer/Inn that come from this card
        '''
        from cartolan.players.base import Player
        if isinstance(target, (Adventurer, Inn)):
            player_name = target.player.name
            logger.debug("Adding card buffs for "+player_name+"...")
            for buff_attr in self.buffs:
                #Check that the token has the attribute associated with the buff
                current_attr_val = getattr(target, buff_attr, None)
                if current_attr_val is not None:
                    logger.debug("For "+player_name+" "+target.__class__.__name__+", adding a buff to their "+buff_attr)
                    #Apply the buff
                    if self.buffs[buff_attr]["buff_type"] == "boost":
                        setattr(target, buff_attr, self.add(current_attr_val, self.buffs[buff_attr]["buff_val"]))
                    elif self.buffs[buff_attr]["buff_type"] == "new":
                        setattr(target, buff_attr, self.buffs[buff_attr]["buff_val"])
                    logger.debug(player_name+" " +target.__class__.__name__+"'s "+buff_attr+" now has value "+str(getattr(target, buff_attr, None)))
        elif isinstance(target, Player):
            player_name = target.name
            logger.debug("Adding card buffs for "+player_name+"...")
            for buff_attr in self.buffs:
                #Player-level (Culture) buffs modify per-player dict attributes on the game
                current_attr_val = getattr(self.game, buff_attr, None)
                if isinstance(current_attr_val, dict):
                    if current_attr_val[target] is not None:
                        logger.debug("For "+player_name+", adding a buff to their "+buff_attr)
                        current_attr_val[target] = self.buffs[buff_attr]["buff_val"]
                        logger.debug(player_name+"'s "+buff_attr+" now has value "+str(getattr(self.game, buff_attr, None)[target]))

    def remove_buffs(self, target):
        '''Reverts rule changes for the Adventurer/Inn that come from this card
        '''
        if isinstance(target, (Adventurer, Inn)):
            player_name = target.player.name
            logger.debug("Removing card buffs for "+player_name+"...")
            for buff_attr in self.buffs:
                #Check that the token has the attribute associated with the buff
                current_attr_val = getattr(target, buff_attr, None)
                if current_attr_val is not None:
                    #Remove the buff
                    if self.buffs[buff_attr]["buff_type"] == "boost":
                        setattr(target, buff_attr, self.sub(current_attr_val, self.buffs[buff_attr]["buff_val"]))
                    elif self.buffs[buff_attr]["buff_type"] == "new":
                        #@TODO if a buff has been doubled up then it shouldn't be lost
                        setattr(target, buff_attr, getattr(self.game, buff_attr))
                    logger.debug(player_name+"'s "+buff_attr+" now has value "+str(getattr(target, buff_attr, None)))


class AdventurerLiteWinds(Adventurer):
    '''An Adventurer token in the Lite Winds base game.

    Carries Chest maps for exploring, trades at Trade Ports, rests with Inns,
    and is represented by a Character card (with more added by Companions).
    '''
    def __init__(self, game, player, starting_city):
        super().__init__(game, player, starting_city)

        logger.debug("adding an adventurer for " +str(player.name))

        #Mirror game variables, so that cards can modify them per token
        self.max_exploration_attempts = game.max_exploration_attempts
        self.fresh_move_budget = game.fresh_move_budget
        self.tired_move_budget = game.tired_move_budget
        self.value_trade = game.value_trade
        self.value_discover_port = game.value_discover_port
        self.value_fill_map_gap = game.value_fill_map_gap
        self.cost_inn_exploring = game.cost_inn_exploring
        self.cost_inn_from_city = game.cost_inn_from_city
        self.cost_adventurer = game.cost_adventurer
        self.inn_on_existing = game.inn_on_existing
        self.last_exploration_adjacents = 0
        self.num_companions = 0
        self.max_companions = game.max_companions
        self.cost_companion = game.cost_companion
        self.num_chest_maps = game.num_chest_maps

        #Some variables that determine valid moves
        self.fresh_moves_used = 0
        self.tired_moves_used = 0
        self.turns_moved = 0
        self.latest_city = starting_city
        self.ports_traded = []
        self.inns_rested = []

        #Some records of actions taken each move
        self.moved = None
        self.traded = False
        self.rested = False
        self.collected = False
        self.placed = False
        self.banked = False
        self.bought_adventurer = 0
        self.bought_inn = 0
        self.moved_inn = None

        #Draw some tiles randomly to the Adventurer's Chest
        self.chest_maps = self.choose_tiles(self.num_chest_maps)
        #Keep track of which of these should be tried for movement
        self.chosen_map_index = None
        #Track manual clockwise rotation offsets (int 0-3) per chest map, applied on top of wind-matching
        self.chest_map_offsets = [0] * len(self.chest_maps)

        #Prepare to hold cards
        self.character_card = None
        self.companion_cards = []
        #Let the player choose a Character card if the game is already under way
        if self.game.game_started:
            self.choose_character()

    @property
    def num_characters(self):
        return self.num_companions + 1

    @property
    def is_tired(self):
        '''A tired Adventurer has used their fresh moves and can only ride the wind.'''
        return self.fresh_moves_used >= self.fresh_move_budget

    @property
    def is_exhausted(self):
        '''An exhausted Adventurer has no moves left and their turn ends.'''
        return self.is_tired and self.tired_moves_used >= self.tired_move_budget

    def to_json(self):
        d = super().to_json()
        d.update({
            "fresh_moves_used": self.fresh_moves_used,
            "tired_moves_used": self.tired_moves_used,
            "fresh_move_budget": self.fresh_move_budget,
            "tired_move_budget": self.tired_move_budget,
            "pirate_token": None,
            "chest_maps": [t.to_json() for t in self.chest_maps],
            "chosen_map_index": self.chosen_map_index,
            "num_chest_maps": self.num_chest_maps,
            "chest_map_offsets": list(self.chest_map_offsets),
            "character_card": self.character_card.to_json() if self.character_card else None,
            "manuscript_cards": None,
            "companion_cards": [c.to_json() for c in self.companion_cards],
        })
        return d

    # --- Character cards and Companions ---

    def choose_character(self):
        '''Lets the player choose a character card from a random subset
        '''
        character_cards = self.game.character_cards
        num_choices = min(self.game.num_character_choices[self.player], len(character_cards))
        if num_choices == 0: #the deck has run out, so no card can be assigned
            return
        card_options = self.game.rng.sample(character_cards, k=num_choices)
        self.character_card = self.player.choose_card(self, card_options)
        character_cards.remove(self.character_card)
        #Take on the changes to rules based on the Character card
        self.character_card.apply_buffs(self)
        self.replenish_chest_maps() #in case the buffs increased the chest map capacity

    def add_companion_card(self):
        '''Draws a character card for a newly hired Companion and applies its buffs to this Adventurer.
        '''
        character_cards = self.game.character_cards
        num_choices = min(self.game.num_character_choices[self.player], len(character_cards))
        if num_choices == 0: #the deck has run out, so the new Companion goes without a card
            return
        card_options = self.game.rng.sample(character_cards, k=num_choices)
        companion_card = self.player.choose_card(self, card_options)
        character_cards.remove(companion_card)
        self.companion_cards.append(companion_card)
        companion_card.apply_buffs(self)
        self.replenish_chest_maps()

    # --- Movement ---

    def has_remaining_moves(self):
        '''Checks whether there are moves left for the Adventurer, regardless of whether there are directions they can move
        '''
        return not self.is_exhausted

    def can_move(self, compass_point):
        '''confirm whether the Adventurer can move in a given cardinal compass direction

        key arguments:
        String word or letter cardinal compass direction, or None to check whether any move is possible
        '''
        if compass_point is None:
            return bool(legal_directions(self))
        if not (compass_point.lower() in ["north","n","east","e","south","s","west","w"]):
            raise Exception("invalid direction given for movement")
        return classify_move(self, compass_point) is not None

    def exploration_needed(self, longitude, latitude):
        '''check whether there is a tile already in a given space, or if exploration is needed

        key arguments:
        int longitude
        int latitude
        '''
        return self.game.play_area.get(longitude) is None or self.game.play_area.get(longitude).get(latitude) is None

    def choose_pile(self, compass_point):
        '''establish which pile to draw from, based on the edge being moved over from the preceding tile
        '''
        if self.current_tile.compass_edge_water(compass_point):
            tile_pile = self.game.tile_piles["water"]
        else:
            tile_pile = self.game.tile_piles["land"]
        logger.debug("Identified the " +tile_pile.tile_back+ " tile pile, which still has " +str(len(tile_pile.tiles)) +" tiles")
        return tile_pile

    def choose_discard_pile(self, compass_point):
        ''' establish which discard pile to use, based on the edge being moved over from the preceding tile
        '''
        if self.current_tile.compass_edge_water(compass_point):
            discard_pile = self.game.discard_piles["water"]
        else:
            discard_pile = self.game.discard_piles["land"]
        logger.debug("Identified the " +discard_pile.tile_back+ " discard pile, which still has " +str(len(discard_pile.tiles)) +" tiles")
        return discard_pile

    def choose_tiles(self, num_tiles):
        '''For a given number of tiles, select tiles from across the bags / tile_piles
        '''
        chosen_tiles = []
        for tile_num in range(num_tiles):
            #Alternate between bags
            pile_num = tile_num % len(self.game.tile_piles)
            #Select the tile pile to draw from
            tile_pile = self.game.tile_piles[list(self.game.tile_piles.keys())[pile_num]]
            #Choose the next tile from the bag / pile and add it to their Chest
            if tile_pile.tiles:
                chosen_tiles.append(tile_pile.tiles.pop())
        return chosen_tiles

    def match_chest_directions(self):
        '''Rotates all chest maps to match the current tile's wind direction, then applies any manual offsets.
        '''
        for i, chest_map in enumerate(self.chest_maps):
            while not (chest_map.wind_direction.north == self.current_tile.wind_direction.north and
                       chest_map.wind_direction.east == self.current_tile.wind_direction.east):
                chest_map.rotate_tile_clock()
            offset = self.chest_map_offsets[i] if i < len(self.chest_map_offsets) else 0
            for _ in range(offset):
                chest_map.rotate_tile_clock()

    def run_tile_actions(self):
        '''Offers the rulebook's sequence of actions on the tile the move finished on.

        Lite Winds C.3: trade, then rest with a preexisting Inn, then hire an Inn.
        (Shady Routes inserts attacking between trading and resting.)
        '''
        for action in self.game.ACTION_ORDER:
            getattr(self, "offer_" + action)()

    def offer_trade(self):
        #check whether this is a trade port, and if the player wants to trade
        if self.current_tile.has_trade_port:
            if self.player.check_trade(self, self.current_tile):
                self.trade(self.current_tile)

    def offer_rest(self):
        #check whether there is an inn here, collect any silks left with it, and then check rest
        if self.current_tile.inn:
            inn = self.current_tile.inn
            if inn.player == self.player:
                if inn.silks > 0:
                    if self.player.check_collect_silks(inn):
                        self.collect_silks()
            if self.can_rest(inn):
                if self.player.check_rest(self, inn):
                    if self.rest(inn) and inn not in self.inns_rested:
                        self.inns_rested.append(inn)

    def offer_hire_inn(self):
        #check whether an Inn can be hired on this pre-existing tile
        if self.inn_on_existing and self.check_tile_available(self.current_tile):
            if self.silks >= self.cost_inn_from_city:
                cost_exploring = self.cost_inn_exploring
                self.cost_inn_exploring = self.cost_inn_from_city
                self.hire_inn()
                self.cost_inn_exploring = cost_exploring

    def end_turn(self):
        '''Resets in-turn trackers, and return discarded tiles to the main piles
        '''
        self.turns_moved += 1
        #the adventurer will rest now before the next turn and be ready
        rest_moves(self)
        #the list of inns rested with is reset
        self.inns_rested = []
        #reset Adventurer's list of visited Trade Ports
        self.ports_traded = []
        #return any discarded tiles to the main piles (if they weren't already empty)
        for discard_pile in self.game.discard_piles.values():
            if discard_pile:
                main_pile = self.game.tile_piles[discard_pile.tile_back]
                main_pile.tiles.extend(discard_pile.tiles)
                main_pile.shuffle_tiles(self.game.rng)
                discard_pile.tiles = []

    def move(self, compass_point):
        '''move the Adventurer over the tile edge in a given cardinal compass direction

        key arguments:
        String word or letter cardinal compass direction
        '''
        #Reset records of actions taken from the previous move and record the direction of movement
        self.moved = compass_point # even if exploration fails this still counts as a move
        self.traded = False
        self.rested = False
        self.collected = False
        self.placed = False
        self.banked = False
        self.bought_adventurer = 0
        self.bought_inn = 0
        self.moved_inn = None

        # check whether the next tile exists and explore if needed
        moved = False
        move_kind = classify_move(self, compass_point)
        if move_kind is not None:
            #spend this move from the budgets - even if exploration subsequently fails
            logger.debug("Making a " +move_kind.value+ " move, with existing silks "+str(self.silks))
            spend_move(self, move_kind)

            #locate the space in the play area that the Adventurer is moving into
            longitude_increment = int(compass_point.lower() in ["east","e"]) - int(compass_point.lower() in ["west","w"])
            new_longitude = self.current_tile.tile_position.longitude + longitude_increment
            latitude_increment = int(compass_point.lower() in ["north","n"]) - int(compass_point.lower() in ["south","s"])
            new_latitude = self.current_tile.tile_position.latitude + latitude_increment

            #is this an existing tile or is exploration needed?
            if self.exploration_needed(new_longitude, new_latitude):
                # establish which pile to draw from, given the edge being crossed
                tile_pile = self.choose_pile(compass_point)
                discard_pile = self.choose_discard_pile(compass_point)

                if self.explore(tile_pile, discard_pile, new_longitude, new_latitude, compass_point):
                    #place the Adventurer on the newly placed Tile
                    self.current_tile.move_off_tile(self)
                    self.current_tile = self.game.play_area.get(new_longitude).get(new_latitude)
                    self.current_tile.move_onto_tile(self)
                    #as a new tile there are some special considerations
                    self.discover(self.current_tile)
                    moved = True
                else:
                    logger.debug("Exploration failed, but offering Adventurer available actions on original tile")
                    if not isinstance(self.current_tile, CityTile):
                        self.run_tile_actions()
                    moved = False
            else:
                #place the Adventurer on the next existing Tile
                self.current_tile.move_off_tile(self)
                self.current_tile = self.game.play_area.get(new_longitude).get(new_latitude)
                self.current_tile.move_onto_tile(self)
                #carry out any actions that are possible given this tile or tokens on it
                if isinstance(self.current_tile, CityTile):
                    self.current_tile.visit_city(self, False)
                else:
                    self.run_tile_actions()
                moved = True

        #check whether any more moves will be possible
        if not self.can_move(None):
            logger.debug("Adventurer determined that cannot move any more, so finishing turn, with Chest silks "+str(self.silks)+", and Vault silks "+str(self.game.vault_silks[self.player]))
            self.end_turn()

        return moved #even if exploration fails this still counts as a move

    def wait(self):
        '''Allows the Adventurer to just wait in place rather than moving, to end a turn early'''
        logger.debug("Adventurer is choosing to wait in place, with silks "+str(self.silks))
        #Reset records of actions taken from previous move, and record that this was a choice to wait in place
        self.moved = "wait"
        self.traded = False
        self.rested = False
        self.collected = False
        self.placed = False
        self.banked = False
        self.bought_adventurer = 0
        self.bought_inn = 0
        self.moved_inn = None

        #Treat this as if it was a move, spending fresh budget first
        if not self.is_tired:
            self.fresh_moves_used += 1
        else:
            self.tired_moves_used += 1

        #carry out any actions that are possible given this tile or tokens on it
        tile = self.current_tile
        if isinstance(tile, CityTile):
            tile.visit_city(self, False)
        else:
            if tile.dropped_silks > 0:
                self.silks += tile.dropped_silks
                tile.dropped_silks = 0
            self.run_tile_actions()

        if not self.can_move(None):
            logger.debug("Adventurer determined that cannot move any more, so finishing turn, with Chest silks "+str(self.silks)+", and Vault silks "+str(self.game.vault_silks[self.player]))
            self.end_turn()

        return True

    # --- Exploration ---

    def get_adjoining_edges(self, longitude, latitude):
        '''for a given set of coordinates, gets the adjoining edges from the neighbouring tiles, if any'''
        adjoining_edges_water = {"n":None, "e":None, "s":None, "w":None}
        for longitude_increment in [- 1, 1]:
            if not self.game.play_area.get(longitude + longitude_increment) is None:
                neighbour_tile = self.game.play_area.get(longitude + longitude_increment).get(latitude)
                if not neighbour_tile is None:
                    #for the tile -1 longitude it will be the eastern edge that is relevant
                    if longitude_increment == -1:
                        adjoining_edges_water["w"] = neighbour_tile.compass_edge_water("east")
                    else:
                        adjoining_edges_water["e"] = neighbour_tile.compass_edge_water("west")
        for latitude_increment in [- 1, 1]:
            if not self.game.play_area.get(longitude) is None:
                neighbour_tile = self.game.play_area.get(longitude).get(latitude + latitude_increment)
                if not neighbour_tile is None:
                    #for the tile -1 latitude it will be the northern edge that is relevant
                    if latitude_increment == -1:
                        adjoining_edges_water["s"] = neighbour_tile.compass_edge_water("north")
                    else:
                        adjoining_edges_water["n"] = neighbour_tile.compass_edge_water("south")
        logger.debug("Identified adjoining edges as, North: " +str(adjoining_edges_water["n"])+ ", East: " +str(adjoining_edges_water["e"])
              + ", South: " +str(adjoining_edges_water["s"])+ ", West: " +str(adjoining_edges_water["w"]))
        return adjoining_edges_water

    def get_exploration_value(self, adjoining_edges_water, compass_point_moving):
        '''calculate the score that would come from filling a particular gap in the map'''
        num_adjacent_water = 0
        num_adjacent_land = 0
        for compass_point in ['n', 'e', 's', 'w']:
            if adjoining_edges_water[compass_point]:
                num_adjacent_water += 1
            elif adjoining_edges_water[compass_point] is not None:
                num_adjacent_land += 1
        #Exclude the edge over which the Adventurer is moving
        if self.current_tile.compass_edge_water(compass_point_moving):
            num_adjacent_water -= 1
        else:
            num_adjacent_land -= 1

        #Store total for use by discover() when awarding manuscripts
        self.last_exploration_adjacents = num_adjacent_water + num_adjacent_land
        #Calculate the score this represents
        exploration_value = self.value_fill_map_gap[num_adjacent_water][num_adjacent_land]
        logger.debug(self.player.name+" the gap in the  map is adjacent to " +str(num_adjacent_water)
              + " water tiles and " +str(num_adjacent_land)+ " land tiles, and is worth "
              +str(exploration_value))
        return exploration_value

    def rotate_and_place(self, potential_tile, longitude, latitude, compass_point_moving, adjoining_edges_water):
        '''For a given potential tile try it in the various rotations that are allowed, and then place it if possible
        '''
        # rotate the potential tile to the orientation of the current tile
        while not (potential_tile.wind_direction.north == self.current_tile.wind_direction.north and
                   potential_tile.wind_direction.east == self.current_tile.wind_direction.east):
            potential_tile.rotate_tile_clock()

        # check whether the tile will place, rotating as needed
        if self.rotated_tile_fits(potential_tile, compass_point_moving, adjoining_edges_water):
            # place tile and feed back to calling function that tile has been placed
            potential_tile.place_tile(longitude, latitude)
            # if this filled a gap in the map then award the Adventurer accordingly
            self.silks += self.get_exploration_value(adjoining_edges_water, compass_point_moving)
            return True
        else:
            #Feed back to the calling function that the tile wouldn't place under any suitable rotation
            return False

    def place_tile_exact(self, potential_tile, longitude, latitude, compass_point_moving, adjoining_edges_water):
        '''Place a tile in its exact current orientation without allowing any rotation.
        Returns True and awards silks if the tile fits; returns False otherwise.
        '''
        compass_points = ["n", "e", "s", "w"]
        edge_matches = True
        while edge_matches and len(compass_points) > 0:
            cp = compass_points.pop()
            edge_matches = (adjoining_edges_water[cp] is None or
                            adjoining_edges_water[cp] == potential_tile.compass_edge_water(cp))
        if edge_matches:
            potential_tile.place_tile(longitude, latitude)
            self.silks += self.get_exploration_value(adjoining_edges_water, compass_point_moving)
            return True
        return False

    def rotated_tile_fits(self, potential_tile, compass_point_moving, adjoining_edges_water):
        '''Check whether a given tile will fit into an adjacent space to the Adventurer
        '''
        # first establish the set of rotations under this ruleset
        def null():
            pass
        if self.game.exploration_rules == "clockwise": # this version 1 of exploration rules will just try a clockwise rotation and then an anti
            rotations = [null, potential_tile.rotate_tile_anti, potential_tile.rotate_tile_clock] # remember these will pop in reverse order
        elif  self.game.exploration_rules == "continuous": # this version 2 of the exploration rules will try to line up arrows head to toe as a first preference
            #the rotation will be anti first if the wind direction is north-east or south-west and the movement is north or south
            if ((self.current_tile.wind_direction.north and self.current_tile.wind_direction.east)
                or (not self.current_tile.wind_direction.north and not self.current_tile.wind_direction.east)):
                if compass_point_moving in ["n","s"]:
                    rotations = [null, potential_tile.rotate_tile_anti]
                else:
                    rotations = [null, potential_tile.rotate_tile_clock]
            #the rotation will be anti first if the wind direction is north-west or south-east and the movement is west or east
            elif ((self.current_tile.wind_direction.north and not self.current_tile.wind_direction.east)
                or (not self.current_tile.wind_direction.north and self.current_tile.wind_direction.east)):
                if compass_point_moving in ["n","s"]:
                    rotations = [null, potential_tile.rotate_tile_clock]
                else:
                    rotations = [null, potential_tile.rotate_tile_anti]
            else: raise Exception("Failed to exhaust wind directions")

        while len(rotations) > 0:
            compass_points = ["n", "e", "s", "w"]
            edge_matches = True
            while edge_matches and len(compass_points) > 0:
                compass_point = compass_points.pop()
                edge_matches = adjoining_edges_water[compass_point] is None or adjoining_edges_water[compass_point] == potential_tile.compass_edge_water(compass_point)

            if edge_matches:
                return True
            else:
                #return the tile to the same wind direction as the original
                while not (potential_tile.wind_direction.north == self.current_tile.wind_direction.north and
                       potential_tile.wind_direction.east == self.current_tile.wind_direction.east):
                    potential_tile.rotate_tile_anti()
                # rotate the tile according to the alternative options in the exploration method
                rotations.pop()()
        return False

    def explore(self, tile_pile, discard_pile, longitude, latitude, compass_point_moving):
        '''Tries to place a tile where an Adventurer moves into an empty space,
        preferring a chosen Chest map and falling back to a random draw from the pile.
        '''
        #check if there is a chest map selected and try to place it
        if isinstance(self.chosen_map_index, int):
            chosen_map = self.chest_maps[self.chosen_map_index]
            adjoining_edges_water = self.get_adjoining_edges(longitude, latitude)
            tile_idx = self.chosen_map_index
            offset = self.chest_map_offsets[tile_idx] if tile_idx < len(self.chest_map_offsets) else 0
            if offset != 0:
                # Player manually rotated this tile: only succeed if it fits in its displayed orientation
                if self.place_tile_exact(chosen_map, longitude, latitude, compass_point_moving, adjoining_edges_water):
                    self.chest_maps.pop(tile_idx)
                    self.chest_map_offsets.pop(tile_idx)
                    self.chosen_map_index = None
                    return True
                self.game.num_failed_explorations += 1
                return False
            else:
                # No manual rotation: use the standard auto-rotating placement
                if self.rotate_and_place(chosen_map, longitude, latitude, compass_point_moving, adjoining_edges_water):
                    self.chest_maps.pop(tile_idx)
                    self.chest_map_offsets.pop(tile_idx)
                    self.chosen_map_index = None
                    return True
        #If there was no tile selected, or the unrotated chest map didn't fit, explore from the pile
        return self.explore_from_pile(tile_pile, discard_pile, longitude, latitude, compass_point_moving)

    def explore_from_pile(self, tile_pile, discard_pile, longitude, latitude, compass_point_moving):
        '''Randomly draws and suitably places a Tile from the pile matching the crossed edge

        key arguments:
        TilePile the pile that should be drawn from given the edge that is being moved over
        TilePile the corresponding discard pile for unsuitable tiles
        int the longitude of the space to explore
        int the latitude of the space to explore
        String giving the word or letter for cardinal compass direction from which the Adventurer is moving
        '''
        logger.debug("Exploring to the " +compass_point_moving+ " into the slot at " +str(longitude)+ "," +str(latitude)+ " which has edges...")

        #establish what edges adjoin the given space
        adjoining_edges_water = self.get_adjoining_edges(longitude, latitude)

        # take multiple attempts at drawing a suitable tile from the pile
        for attempt in range(0, self.max_exploration_attempts):
            if tile_pile.tiles:
                logger.debug("Drawing a tile from the " +tile_pile.tile_back+ " tile deck, which has " +str(len(tile_pile.tiles))+ " tiles")
                potential_tile = tile_pile.draw_tile()
            elif discard_pile.tiles:
                logger.debug("Have found main tile pile empty, so shuffling Discard Pile")
                self.game.refresh_pile(tile_pile, discard_pile)
                tile_pile = self.game.tile_piles[tile_pile.tile_back]
                discard_pile = self.game.discard_piles[discard_pile.tile_back]
                potential_tile = tile_pile.draw_tile()
            else: #both piles are exhausted, so this exploration fails and the turn ends; the game loop's win check will end the game
                self.turns_moved += 1
                self.game.vault_silks[self.player] += self.game.value_complete_map
                break
            if self.rotate_and_place(potential_tile, longitude, latitude, compass_point_moving, adjoining_edges_water):
                return True
            # discard the tile
            else:
                discard_pile.add_tile(potential_tile)
                self.game.exploration_attempts += 1

        # feed back to calling function that a tile has NOT been placed
        self.game.num_failed_explorations += 1
        return False

    def replenish_chest_maps(self):
        '''If this Adventurer has fewer chest maps than the max, then draw more
        '''
        #Count how many tiles they are short of the max chest maps
        num_tiles_to_choose = self.num_chest_maps - len(self.chest_maps)
        #Add this many extra tiles to their chest, with zero manual rotation offsets
        new_tiles = self.choose_tiles(num_tiles_to_choose)
        self.chest_maps += new_tiles
        self.chest_map_offsets += [0] * len(new_tiles)

    def swap_chest_maps(self):
        '''Checks whether the player will pay to replace all an Adventurer's chest maps
        '''
        #For each current tile offer replacements, and return the rest to the piles
        new_chest_maps = []
        for tile in self.chest_maps:
            # Alternate between piles for forming the selection
            tile_options = self.choose_tiles(self.game.num_tile_choices[self.player])
            if tile_options:
                #Offer the current tile too
                tile_options.append(tile)
                chosen_tile = self.player.choose_tile(self, tile_options)
                tile_options.remove(chosen_tile)
                new_chest_maps.append(chosen_tile)
                #Return all the other tiles to the relevant piles
                for rejected_tile in tile_options:
                    self.return_to_pile(rejected_tile)
        self.chest_maps = new_chest_maps
        self.chest_map_offsets = [0] * len(new_chest_maps)

    def return_to_pile(self, tile):
        '''Identifies the pile associated with a particular tile and returns it there
        '''
        relevant_pile = self.game.tile_piles[tile.tile_back]
        relevant_pile.tiles.insert(0, tile)

    def discover(self, tile):
        '''Handles the special considerations when a tile is newly placed:
        city discovery, Trade Port bonuses, and the offer to hire an Inn.

        key arguments:
        Cartolan.Tile the tile that has just been placed
        '''
        #check whether this is a discovered city and don't offer the usual
        if isinstance(self.current_tile, CityTile):
            self.current_tile.is_discovered = True
            self.silks += self.game.value_discover_city
            self.current_tile.visit_city(self)
            return True
        # if this is a Trade Port then discovery should be automatic
        if self.current_tile.has_trade_port:
            #award silks
            self.silks += self.value_discover_port[tile.tile_back]
            self.ports_traded.append(tile)
        #check whether an inn can be placed and then whether the player wants to
        self.hire_inn()
        return True

    # --- Actions on tiles ---

    def trade(self, tile):
        '''awards silks when a Trade Port tile is visited for the first time since the last visit to a city

        key arguments:
        Cartolan.Tile giving the tile that has been visited
        '''
        #Record the instruction to Trade
        self.traded = True

        #confirm that this tile is a Trade Port
        if not tile.has_trade_port:
            return False

        # check that Adventurer hasn't visited this Trade Port yet, since visiting a city
        if tile in self.ports_traded:
            return False

       # collect appropriate silks into Chest
        logger.debug("Adventurer is trading on tile "
                  +str(tile.tile_position.longitude)+ "," +str(tile.tile_position.latitude))
        self.silks += self.value_trade * self.num_characters

        # keep track of visiting this Trade Port
        self.ports_traded.append(tile)

        return True

    def check_tile_available(self, tile):
        '''Checks the conditions for being able to place an Inn on a tile.'''
        if tile.inn is None and not isinstance(tile, CityTile):
            return True
        else:
            return False

    def hire_inn(self):
        '''places an Inn as a tile is first placed through exploration'''
        #Record the instruction to place
        self.placed = True

        tile = self.current_tile

        #check that the adventurer has requisite silks in their Chest
        if self.silks >= self.cost_inn_exploring and self.check_tile_available(tile):

            #check whether the player actually wants to place an inn, even if they have to move an existing one
            if self.player.check_hire_inn(self):
                if len(self.game.inns[self.player]) >= self.game.max_inns:
                    inn = self.player.check_move_inn(self)
                    if inn is None:
                        return False
                    else:
                        #pick up the Inn from its existing tile if there are no other inns available
                        inn.current_tile.move_off_tile(inn)
                        tile.move_onto_tile(inn)
                else:
                    inn = self.game.INN_TYPE(self.game, self.player, tile)
                self.silks -= self.cost_inn_exploring
                #prevent the Adventurer using the Inn this turn
                self.inns_rested.append(inn)
                return True
        else: return False

    def can_rest(self, token):
        '''checks whether the Adventurer can rest on this tile'''
        # check whether there is an inn on the tile and whether the adventurer can afford rest here
        if isinstance(token, Inn):
            if ((token.player == self.player
                or self.silks >= token.cost_inn_rest * self.num_characters)
                and token not in self.inns_rested):
                return True
        return False

    def rest(self, token):
        '''rests with an Inn if there is one on the tile'''
        tile = self.current_tile
        logger.debug("Adventurer is resting on tile "
                  +str(tile.tile_position.longitude)+ "," +str(tile.tile_position.latitude))
        return token.give_rest(self)

    def can_collect_silks(self):
        '''checks whether there are silks with an Inn on the current tile that can be collected'''
        tile = self.current_tile
        if tile.inn is None:
            return False
        if tile.inn.player == self.player and tile.inn.silks > 0:
            return True
        else:
            return False

    def collect_silks(self):
        '''Collects any silks that are with any Inn of the same player on the current tile'''
        #Record the instruction to collect
        self.collected = True

        tile = self.current_tile
        if tile.inn is None:
            return False
        else:
            #check that the inn shares a player
            inn = tile.inn
            if tile.inn.player == self.player:
                #transfer silks
                logger.debug("Adventurer is collecting " +str(inn.silks)+ " silks from the inn on tile "
                     +str(inn.current_tile.tile_position.longitude)+","+str(inn.current_tile.tile_position.latitude))
                self.silks += inn.silks
                inn.silks = 0
                return True
            else:
                return False

    def end_expedition(self, city=None):
        '''Prematurely returns an Adventurer to the last city they visited and empties their silks.
        '''
        logger.debug(self.player.name+ "'s expedition has been ended and they've returned to a city")
        self.replenish_chest_maps()
        self.silks = 0
        self.current_tile.move_off_tile(self)
        if isinstance(city, CityTile):
            city.move_onto_tile(self)
        else:
            self.latest_city.move_onto_tile(self)
        self.ports_traded = [] #reset the list of where trade can happen

    def abandon_expedition(self, city_tile):
        '''Deliberately drops silks and returns to a city
        city_tile is a Cartolan CityTile
        '''
        self.current_tile.dropped_silks += self.silks
        self.end_expedition(city=city_tile)
        if isinstance(self.current_tile, CityTile):
            self.current_tile.visit_city(self, abandoned=True)


class InnLiteWinds(Inn):
    '''Represents Inn tokens with their behaviours in the Lite Winds base game

    Methods:
    __init__ takes Cartolan.Game, Cartolan.Player, and Cartolan.Tile objects
    give_rest takes a Cartolan.Adventurer
    manage_trade takes a Cartolan.Adventurer
    '''
    def __init__(self, game, player, tile):
        super().__init__(game, player, tile)

        #Mirror game variables, so that cards can modify them per token
        self.cost_inn_rest = game.cost_inn_rest

    def _give_rest_core(self, adventurer):
        '''Resets the move counts for an Adventurer token, so that they can continue to move

        Arguments:
        Cartolan.Adventurer the Adventurer to rest
        '''
        #check whether Adventurer has rested with this inn already this turn
        if self in adventurer.inns_rested:
            return False

        #check whether Adventurer is from same player and charge if other player
        if not adventurer.player == self.player:
            # pay as necessary — cost scales with the number of characters travelling
            rest_cost = self.cost_inn_rest * adventurer.num_characters
            adventurer.silks -= rest_cost
            self.silks += rest_cost

        # reset move budgets
        rest_moves(adventurer)

        #remember that this Inn has been used already this turn
        if self not in adventurer.inns_rested:
            adventurer.inns_rested.append(self)

        return True

    def give_rest(self, adventurer):
        '''Rests the Adventurer, and replenishes their Chest maps.'''
        adventurer.replenish_chest_maps()
        return self._give_rest_core(adventurer)


class TradePortTile(Tile):
     def __init__(self, game, tile_back = "water"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(True,True,True,True)):
        super().__init__(game, tile_back, wind_direction, tile_edges, True)


class CityTileLiteWinds(CityTile):
    '''Represents a city tile in the Lite Winds base game

    City behaviour (banking, purchases) lives on the Game classes; this tile
    delegates so that existing call sites keep working while tiles stay passive.
    '''

    def move_off_tile(self, token):
        '''Adds a prompt to check how much silks Adventurers want to take with them
        '''
        vault_silks = token.game.vault_silks[token.player]
        if vault_silks > 0:
            travel_silks = token.player.check_travel_silks(token, vault_silks, 0)
            try:
                travel_silks = int(travel_silks)
            except (TypeError, ValueError):
                travel_silks = 0
            travel_silks = max(0, min(vault_silks, travel_silks))
            token.silks += travel_silks
            token.game.vault_silks[token.player] -= travel_silks
        super().move_off_tile(token)

    def visit_city(self, adventurer, abandoned=False):
        return self.game.run_city_visit(adventurer, self, abandoned)

    def bank_silks(self, adventurer):
        return self.game.bank_silks(adventurer)

    def buy_adventurers(self, adventurer):
        return self.game.buy_adventurers(adventurer, self)

    def buy_inns(self, adventurer):
        return self.game.buy_inns(adventurer, self)

    def hire_companion(self, adventurer):
        return self.game.hire_companion(adventurer)

    def offer_purchases(self, adventurer):
        return self.game.offer_purchases(adventurer, self)


class HomeCityTileLiteWinds(CityTileLiteWinds):
    def __init__(self, game, tile_back = "water"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(True,True,True,True)):
        super().__init__(game, wind_direction, tile_edges, True, True)


class MythicalCityTileLiteWinds(CityTileLiteWinds):
    def __init__(self, game, tile_back = "land"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(False,False,False,False)):
        super().__init__(game, wind_direction, tile_edges, False, False)


class GameLiteWinds(Game):
    '''Executes the sequence of play for Cartolan - Lite Winds, the base game.

    Water and land tiles are explored using the maps Adventurers carry, Silks
    are earned by expanding the map and trading at Trade Ports, Inns give rest
    to keep Adventurers moving, and Character cards give each Adventurer and
    Companion a perk.

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
    TILE_TYPES = {"plain":Tile, "home_city":HomeCityTileLiteWinds, "mythical_city":MythicalCityTileLiteWinds, "trade_port":TradePortTile}
    ADVENTURER_TYPE = AdventurerLiteWinds
    INN_TYPE = InnLiteWinds
    CITY_TYPE = CityTileLiteWinds
    CARD_TYPE = ModifierCard

    #The rule values for this edition; instances mirror the fields as attributes
    RULESET = LITE_WINDS
    #Lite Winds C.3: the order of actions offered after each move
    ACTION_ORDER = ("trade", "rest", "hire_inn")


    def __init__(self, players, exploration_rules = 'continuous', rng=None):

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

        if exploration_rules in ["clockwise", "continuous"]:
            self.exploration_rules = exploration_rules
        else: raise Exception("Invalid exploration rules specfied")

        self.cities = []

        self.tile_piles = {"water":TilePile("water",[]), "land":TilePile("land",[])}
        self.discard_piles = {"water":TilePile("water",[]), "land":TilePile("land",[])}

        #Some rule values apply per player, so they can be modified by Culture cards
        self.num_tile_choices = {player: self.ruleset.num_tile_choices for player in players}
        self.num_character_choices = {player: self.ruleset.num_character_choices for player in players}

        #Set up the deck of Character cards
        self.card_count = 0
        self.character_cards = [self.CARD_TYPE(self, card_type) for card_type in self.ruleset.character_cards]

        self.exploration_attempts = 0
        self.win_type = None
        self.game_over = False

    def setup_tile_pile(self, tile_back):
        '''Part of game setup for Cartolan, this builds a shuffled pile of tiles ready for play

        Arguments:
        tile_back a string designating the type of tile and so its distribution of edge combinations
        '''
        total_distribution = []
        special_distributions = {} # per special tile type
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
            discard_pile = self.discard_piles[discard_pile.tile_back]
            logger.debug("Have started a new discard pile, so that now there are "
                 + str(len(self.discard_piles))+ " discard piles.")
            return True
        else:
            return False #both piles are exhausted; the game loop's win check will end the game

    def play_round(self):
        '''Carries out the sequence of play for one round of the game'''
        logger.debug("playing round "+str(self.turn)+" with a silks difference of " +str(self.silks_difference)
             +" and a max vault of " +str(self.max_vault_silks))
        for player in self.players:
            #some logging
            logger.debug(str(player.name)+ " player's turn, with " +str(len(self.adventurers[player]))
                  +" Adventurers, and " +str(self.vault_silks[player])+ " silks in the Vault")

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

    # --- City visits ---

    def run_city_visit(self, adventurer, city, abandoned=False):
        '''Initiates all the possible actions when a city is visited

        Arguments:
        Cartolan.Adventurer the Adventurer arriving on the City tile
        Cartolan.CityTile the city being visited
        Boolean abandoned prevents hiring option if the Adventurer has aborted their expedition, making it harder to replace opponents' Inns.
        '''
        #Top up any missing chest maps from the bags
        adventurer.replenish_chest_maps()

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

        #check if silks are available and move them from the adventurer's Chest to their Vault
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
        Cartolan.CityTile the city selling the Inn
        '''
        #Record the decision to buy an inn this move
        adventurer.bought_inn += 1

        #keep checking whether the player can afford another Inn and wants one until they refuse
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

        Each Companion hired also draws a Character card for the Adventurer's party.

        Args:
            adventurer: the visiting Adventurer
        '''
        while (adventurer.num_companions < adventurer.max_companions
               and self.vault_silks[adventurer.player] >= adventurer.cost_companion):
            if adventurer.player.check_hire_companion(adventurer):
                self.vault_silks[adventurer.player] -= adventurer.cost_companion
                adventurer.num_companions += 1
                adventurer.add_companion_card()
                logger.debug(adventurer.player.name + " hired a Companion (now "
                      + str(adventurer.num_companions) + " companions, "
                      + str(adventurer.num_characters) + " characters total)")
            else:
                return False
        return True

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

    # --- Standings and win conditions ---

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
        '''Serialises the state that the web client renders.'''
        play_area = {}
        for longitude, tiles in self.play_area.items():
            play_area[str(longitude)] = {str(latitude): tile.to_json() for latitude, tile in tiles.items()}
        return {
            "game_mode": "LiteWinds",
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
