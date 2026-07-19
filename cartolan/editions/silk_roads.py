'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com

Cartolan - Silk Roads: the roads expansion on Lite Winds / Shady Routes.

Adventurers can build Roads between tiles: from the turn after they are built,
even tired Adventurers can keep moving along them (paying a toll past other
players' Inns). Exploration changes too: EITHER place a carried Chest map in
any orientation, OR draw blind from the pile matching the crossed edge, where
the tile must be placed wind-matched (or wind tip-to-tail) or the exploration
fails. Setup starts from the Mythical City alone, with 2 maps per Chest drawn
green-then-blue.
'''

import logging

from cartolan.core.movement import MoveKind, classify_move
from cartolan.core.roads import Road, edge_ref, OPPOSITE, OFFSETS
from cartolan.rules.ruleset import SILK_ROADS
from cartolan.editions.shady_routes import (GameShadyRoutes, AdventurerShadyRoutes,
                                            InnShadyRoutes, CityTileShadyRoutes)

logger = logging.getLogger(__name__)


class AdventurerSilkRoads(AdventurerShadyRoutes):
    '''Extends the Shady Routes Adventurer with Road building and blind-draw exploration.'''

    def move(self, compass_point):
        '''Extends movement with the toll for following a Road past another player's Inn.'''
        road_move = (compass_point is not None
                     and classify_move(self, compass_point) is MoveKind.ROAD)
        from_tile = self.current_tile
        moved = super().move(compass_point)
        if road_move and moved:
            self.pay_road_toll(from_tile, self.current_tile)
        return moved

    def pay_road_toll(self, from_tile, to_tile):
        '''Silk Roads C.3: if the Road shares a tile with another player's Inn, the
        Adventurer and each Companion must leave a toll of 1 Silk on the Inn's tile.'''
        for tile in (from_tile, to_tile):
            inn = tile.inn
            if (inn is not None and inn.player != self.player
                    and not getattr(inn, "is_ransacked", False)):
                toll = min(self.silks, self.game.road_toll_per_character * self.num_characters)
                if toll > 0:
                    logger.debug(self.player.name + " leaves a toll of " + str(toll)
                                 + " Silks passing " + inn.player.name + "'s Inn")
                    self.silks -= toll
                    inn.silks += toll

    def explore(self, tile_pile, discard_pile, longitude, latitude, compass_point_moving):
        '''Silk Roads C.4: EITHER place a carried Chest map in any orientation, OR draw
        blind from the pile matching the crossed edge, placing wind-matched or wind
        tip-to-tail; otherwise the exploration fails and the tile is set aside until
        the end of the turn, returning to the bottom of its pile.
        '''
        #a chosen or fitting carried map takes priority
        if super().explore(tile_pile, discard_pile, longitude, latitude, compass_point_moving):
            return True
        #the carried-map failure was counted, but a blind draw is still to be tried
        self.game.num_failed_explorations -= 1
        if not tile_pile.tiles and discard_pile.tiles:
            self.game.refresh_pile(tile_pile, discard_pile)
            tile_pile = self.game.tile_piles[tile_pile.tile_back]
        potential_tile = tile_pile.draw_tile()
        if potential_tile is None:
            return False

        adjoining_edges_water = self.get_adjoining_edges(longitude, latitude)

        #1st try: place with the trade wind arrow matching the current tile's
        while not (potential_tile.wind_direction.north == self.current_tile.wind_direction.north and
                   potential_tile.wind_direction.east == self.current_tile.wind_direction.east):
            potential_tile.rotate_tile_clock()
        if self.place_tile_exact(potential_tile, longitude, latitude, compass_point_moving, adjoining_edges_water):
            return True

        #2nd try: wind tip-to-tail - pointing from just one tile onto the other
        for _ in range(3):
            potential_tile.rotate_tile_clock()
            if self.wind_tip_to_tail(potential_tile, compass_point_moving):
                if self.place_tile_exact(potential_tile, longitude, latitude, compass_point_moving, adjoining_edges_water):
                    return True

        #exploration failed: set the tile aside until the end of the turn
        self.game.pending_discards[potential_tile.tile_back].append(potential_tile)
        self.game.num_failed_explorations += 1
        return False

    def wind_tip_to_tail(self, potential_tile, compass_point_moving):
        '''Whether exactly one of the two tiles' wind arrows points across the shared
        edge into the other (from current to new, or vice versa).'''
        outbound = self.current_tile.compass_edge_downwind(compass_point_moving)
        inbound = potential_tile.compass_edge_downwind(OPPOSITE[compass_point_moving[0].lower()])
        return outbound != inbound

    def offer_build_road(self):
        '''Silk Roads C.1/C.3: at the end of their move the Adventurer may build a Road
        between their tile and any neighbouring tile.'''
        tile = self.current_tile
        if tile.tile_position.longitude is None:
            return
        cost = (self.game.cost_road_new_tile if self.laid_tile_this_move
                else self.game.cost_road_existing)
        if self.silks < cost:
            return
        #the neighbouring tiles without a Road already on that edge
        options = []
        for direction, (d_lon, d_lat) in OFFSETS.items():
            neighbour_lon = tile.tile_position.longitude + d_lon
            neighbour_lat = tile.tile_position.latitude + d_lat
            if self.game.play_area.get(neighbour_lon, {}).get(neighbour_lat) is None:
                continue
            if edge_ref(tile.tile_position, direction) in self.game.roads_by_edge:
                continue
            options.append(direction)
        if not options:
            return
        direction = self.player.check_build_road(self, options, cost)
        if direction not in options:
            return
        #at the Road limit, one must be picked up and moved
        if len(self.game.roads[self.player]) >= self.game.max_roads:
            moved_road = self.player.check_move_road(self)
            if moved_road not in self.game.roads[self.player]:
                return
            self.game.remove_road(moved_road)
        self.silks -= cost
        self.game.build_road(self.player, edge_ref(tile.tile_position, direction))

    def end_turn(self):
        '''Extends to return failed blind-draw tiles to the bottom of their piles.'''
        super().end_turn()
        for tile_back, pending in self.game.pending_discards.items():
            if pending:
                pile = self.game.tile_piles[tile_back]
                for tile in pending:
                    pile.tiles.insert(0, tile)  #the bottom of the pile
                self.game.pending_discards[tile_back] = []


class InnSilkRoads(InnShadyRoutes):
    '''An Inn in the Silk Roads expansion, collecting Road tolls as well as rest fees.'''


class CityTileSilkRoads(CityTileShadyRoutes):
    '''City tile for Silk Roads: behaviour lives on GameSilkRoads.'''


class GameSilkRoads(GameShadyRoutes):
    '''Extends the Shady Routes game with Roads and blind-draw exploration.'''
    ADVENTURER_TYPE = AdventurerSilkRoads
    INN_TYPE = InnSilkRoads
    CITY_TYPE = CityTileSilkRoads

    RULESET = SILK_ROADS
    #Silk Roads D: trade, rest, hire Inn, build Road (attack slots in from Shady Routes)
    ACTION_ORDER = ("trade", "attack", "rest", "hire_inn", "build_road")
    #Silk Roads B: the Mythical City is placed alone, and Chests start green-then-blue
    SOLO_MYTHICAL_SETUP = True
    SETUP_MAP_ORDER = ("land", "water")

    def __init__(self, players, rng=None):
        super().__init__(players, rng)
        #Roads by owner, and by the edge they span
        self.roads = {player: [] for player in players}
        self.roads_by_edge = {}
        #Blind-draw tiles that failed to place, returned to pile bottoms at end of turn
        self.pending_discards = {tile_back: [] for tile_back in self.tile_piles}

    def build_road(self, player, edge):
        '''Places a Road for a player across an edge; usable from the next turn.'''
        road = Road(player, edge, self.turn)
        self.roads[player].append(road)
        self.roads_by_edge[edge] = road
        logger.debug(player.name + " built a road across " + str(edge))
        return road

    def remove_road(self, road):
        '''Picks a Road up off the board.'''
        self.roads[road.player].remove(road)
        self.roads_by_edge.pop(road.edge, None)

    def road_across(self, tile, direction):
        '''Whether an active Road spans the given edge (used by the movement engine).'''
        if tile.tile_position.longitude is None:
            return False
        road = self.roads_by_edge.get(edge_ref(tile.tile_position, direction))
        return road is not None and road.is_active(self.turn)

    def to_json(self):
        d = super().to_json()
        d["game_mode"] = "SilkRoads"
        d["roads"] = {
            player.name: [dict(road.to_json(), active=road.is_active(self.turn))
                          for road in roads]
            for player, roads in self.roads.items()
        }
        return d
