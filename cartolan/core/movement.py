'''The movement engine for Cartolan, following the rulebooks' phase model.

Each turn (or after resting at an Inn) an Adventurer is fresh: they can move a
budget of moves in ANY direction, over water or land edges. Then they are
tired: they can still ride the wind for a budget of moves, over a water edge in
the direction the trade wind arrow points on the tile they move FROM (or, in
Silk Roads, along a Road). Then they are exhausted and their turn ends.
'''

from enum import Enum


class MoveKind(Enum):
    FRESH = "fresh"        # any direction, while the fresh budget lasts
    DOWNWIND = "downwind"  # tired: water edge in the wind arrow's direction
    ROAD = "road"          # tired: along a Road (Silk Roads)


COMPASS_POINTS = ("n", "e", "s", "w")


def classify_move(adventurer, direction):
    '''Determines what kind of move an Adventurer would make in a direction, or None if illegal.

    Arguments:
    adventurer: the Adventurer to move
    direction: a cardinal compass direction word or letter
    '''
    if not adventurer.is_tired:
        return MoveKind.FRESH
    if adventurer.is_exhausted:
        return None
    #tired: ride the wind over a water edge, in the direction of the wind
    #arrow on the tile being moved from
    tile = adventurer.current_tile
    if tile.compass_edge_water(direction) and tile.compass_edge_downwind(direction):
        return MoveKind.DOWNWIND
    #tired: follow a Road across this edge (Silk Roads)
    road_at = getattr(adventurer.game, "road_across", None)
    if road_at is not None and road_at(tile, direction):
        return MoveKind.ROAD
    return None


def legal_directions(adventurer):
    '''Maps each cardinal direction the Adventurer could legally move to its MoveKind.'''
    moves = {}
    for direction in COMPASS_POINTS:
        kind = classify_move(adventurer, direction)
        if kind is not None:
            moves[direction] = kind
    return moves


def spend_move(adventurer, kind):
    '''Records that a move of the given kind has been made.'''
    if kind is MoveKind.FRESH:
        adventurer.fresh_moves_used += 1
    else:
        adventurer.tired_moves_used += 1


def rest_moves(adventurer):
    '''Resets the Adventurer's move budgets, as when resting at an Inn or ending a turn.'''
    adventurer.fresh_moves_used = 0
    adventurer.tired_moves_used = 0
