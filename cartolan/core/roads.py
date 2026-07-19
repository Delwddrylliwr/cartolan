'''Roads for the Silk Roads expansion.

A Road spans the edge between two adjacent tiles. From the turn after it is
built, it lets even tired Adventurers keep moving across that edge.
'''

OPPOSITE = {"n": "s", "s": "n", "e": "w", "w": "e"}
OFFSETS = {"n": (0, 1), "e": (1, 0), "s": (0, -1), "w": (-1, 0)}


def edge_ref(tile_position, direction):
    '''Canonical reference for the edge from a tile position in a compass direction.

    Returns a sorted pair of (longitude, latitude) coordinates, so the same edge
    is found from either side.
    '''
    lon, lat = tile_position.longitude, tile_position.latitude
    d_lon, d_lat = OFFSETS[direction[0].lower()]
    return tuple(sorted([(lon, lat), (lon + d_lon, lat + d_lat)]))


class Road:
    '''A Road built by a player across one tile edge.

    Arguments:
    player: the owning Cartolan.Player
    edge: an edge_ref pair of coordinates
    turn_built: the game turn it was built; it becomes usable the following turn
    '''

    def __init__(self, player, edge, turn_built):
        self.player = player
        self.edge = edge
        self.turn_built = turn_built

    def is_active(self, turn):
        '''Roads allow movement only after the turn they were placed.'''
        return turn > self.turn_built

    def to_json(self):
        (a_lon, a_lat), (b_lon, b_lat) = self.edge
        return {"player_name": self.player.name,
                "a": [a_lon, a_lat], "b": [b_lon, b_lat],
                "turn_built": self.turn_built}
