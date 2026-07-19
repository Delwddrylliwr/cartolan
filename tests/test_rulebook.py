'''Rule tests keyed to clauses of the Lite Winds / Shady Routes / Silk Roads rulebooks.

Clauses that later refactor stages implement are marked xfail with the stage noted.
'''

import random

import pytest

from cartolan.core.setup import create_game
from cartolan.core.tiles import Tile, WindDirection, TileEdges
from cartolan.editions import EDITIONS, GameLiteWinds, GameShadyRoutes, GameSilkRoads
from cartolan.editions.lite_winds import TradePortTile
from cartolan.rules.ruleset import LITE_WINDS, SHADY_ROUTES, SILK_ROADS
from tests.scripted import ScriptedPlayer


def make_game(game_type=GameLiteWinds, seed=5):
    players = [ScriptedPlayer("blue"), ScriptedPlayer("red")]
    game = create_game(game_type, players, rng=random.Random(seed))
    game.game_started = True
    game.turn = 1
    return game, players


def place_water(game, lon, lat, wind_north=True, wind_east=True, trade_port=False):
    tile_type = TradePortTile if trade_port else Tile
    if trade_port:
        tile = tile_type(game, "water", WindDirection(wind_north, wind_east),
                         TileEdges(True, True, True, True))
    else:
        tile = tile_type(game, "water", WindDirection(wind_north, wind_east),
                         TileEdges(True, True, True, True), False)
    tile.place_tile(lon, lat)
    return tile


# --- Editions and rule values ---

def test_editions_registry_matches_rulebooks():
    assert list(EDITIONS) == ["LiteWinds", "ShadyRoutes", "SilkRoads"]
    assert issubclass(GameShadyRoutes, GameLiteWinds)
    assert issubclass(GameSilkRoads, GameShadyRoutes)


def test_lite_winds_deck_filters_piracy_cards():
    '''Lite Winds rulebook p.4: remove all cards referring to piracy.'''
    for card in ("chr+attack", "chr+damage", "chr+defence"):
        assert card not in LITE_WINDS.character_cards
        assert card in SHADY_ROUTES.character_cards


def test_win_threshold_is_100_vault_silks():
    '''Lite Winds C.1: victory bought by the first player with 100 Vault Silks.'''
    for ruleset in (LITE_WINDS, SHADY_ROUTES, SILK_ROADS):
        assert ruleset.winning_vault_silks == 100


def test_costs_match_rulebook_tables():
    '''Lite Winds G: rewards and costs of actions.'''
    assert LITE_WINDS.cost_inn_exploring == 0     # hire Inn on newly placed tile
    assert LITE_WINDS.cost_inn_from_city == 5     # hire Inn on existing tile
    assert LITE_WINDS.cost_inn_rest == 1          # rest with opponent's Inn, per character
    assert LITE_WINDS.cost_companion == 15        # hire Companion
    assert LITE_WINDS.value_trade == 1            # trade, per character
    assert SHADY_ROUTES.value_arrest == 5         # arrest pirate successfully
    assert SHADY_ROUTES.value_ransack_inn == 1    # ransack premises
    assert SHADY_ROUTES.cost_inn_restore == 1     # restore ransacked Inn
    assert SHADY_ROUTES.cost_manuscript == 5      # buy Manuscript card


def test_vault_threshold_detected_by_loop_authority():
    game, players = make_game()
    game.vault_silks[players[0]] = 100
    assert game.winning_condition() == "vault threshold"
    assert not game.game_over  # the pure query must not end the game
    assert game.check_win_conditions()
    assert game.game_over and game.win_type == "vault threshold"


# --- Trading (Lite Winds C.5) ---

def test_trade_pays_one_silk_per_character_once_per_port_per_turn():
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    port = place_water(game, 2, 0, trade_port=True)
    adventurer.current_tile = port

    assert adventurer.trade(port)
    assert adventurer.silks == 1  # 1 Silk x 1 character

    assert not adventurer.trade(port)  # only the first visit each turn pays
    assert adventurer.silks == 1

    adventurer.end_turn()
    assert adventurer.trade(port)  # a new turn allows trading here again
    assert adventurer.silks == 2


def test_trade_scales_with_companions():
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    adventurer.num_companions = 2  # 3 characters total
    port = place_water(game, 2, 0, trade_port=True)
    adventurer.current_tile = port
    assert adventurer.trade(port)
    assert adventurer.silks == 3


def test_pirate_cannot_trade():
    '''Shady Routes: pirates cannot trade until redeemed.'''
    game, players = make_game(GameShadyRoutes)
    adventurer = game.adventurers[players[0]][0]
    adventurer.pirate_token = True
    port = place_water(game, 2, 0, trade_port=True)
    adventurer.current_tile = port
    assert not adventurer.trade(port)
    assert adventurer.silks == 0


# --- Exploring (Lite Winds C.6) ---

def test_explore_reward_is_three_per_adjoining_tile():
    '''+3 Silks per adjoining old tile beyond the moved-from one, up to 9.'''
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    # standing on the home city at (0,0); target (1,1) adjoins tiles at (0,1) and (1,0)
    adventurer.current_tile = game.play_area[0][1]
    adjoining = adventurer.get_adjoining_edges(1, 1)
    value = adventurer.get_exploration_value(adjoining, "e")
    assert value == 3  # one adjoining tile besides the moved-from one


def test_explore_reward_capped_at_nine():
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    # surround (1,1) on all four sides
    place_water(game, 1, 2)
    place_water(game, 2, 1)
    adventurer.current_tile = game.play_area[0][1]
    adjoining = adventurer.get_adjoining_edges(1, 1)
    value = adventurer.get_exploration_value(adjoining, "e")
    assert value == 9  # three adjoining tiles besides the moved-from one


def test_mythical_city_awards_five_silks_when_placed():
    '''Lite Winds C.9: the Mythical City awards 5 Silks when placed.'''
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    mythical = game.tile_piles["land"].tiles[-1]  # appended by create_game... find it
    from cartolan.core.tiles import CityTile
    mythical = next(t for t in game.tile_piles["land"].tiles if isinstance(t, CityTile))
    mythical.place_tile(5, 5)
    adventurer.current_tile = mythical
    silks_before = adventurer.silks + game.vault_silks[players[0]]
    players[0].script("check_bank_amount", 0)
    adventurer.discover(mythical)
    silks_after = adventurer.silks + game.vault_silks[players[0]]
    assert silks_after - silks_before == 5
    assert mythical.is_discovered


# --- Inns and resting (Lite Winds C.7) ---

def test_rest_with_opponents_inn_costs_one_silk_per_character():
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    tile = place_water(game, 3, 0)
    inn = game.INN_TYPE(game, players[1], tile)
    adventurer.current_tile = tile
    adventurer.silks = 5
    adventurer.fresh_moves_used = 2
    adventurer.tired_moves_used = 1

    assert adventurer.rest(inn)
    assert adventurer.silks == 4      # paid 1 Silk x 1 character
    assert inn.silks == 1             # left on the tile for the Inn's player
    assert adventurer.fresh_moves_used == 0  # move budgets reset
    assert adventurer.tired_moves_used == 0


def test_rest_once_per_inn_per_turn():
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    tile = place_water(game, 3, 0)
    inn = game.INN_TYPE(game, players[0], tile)
    adventurer.current_tile = tile
    assert adventurer.rest(inn)
    assert not adventurer.rest(inn)  # same Inn refuses a second rest this turn


def test_own_inn_rest_is_free():
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    tile = place_water(game, 3, 0)
    inn = game.INN_TYPE(game, players[0], tile)
    adventurer.current_tile = tile
    adventurer.silks = 5
    assert adventurer.rest(inn)
    assert adventurer.silks == 5


@pytest.mark.xfail(reason="Stage 7: resting grants exactly one map with pile choice", strict=True)
def test_rest_grants_exactly_one_map():
    game, players = make_game()
    game.setup_tile_pile("water")  # ensure draws available
    adventurer = game.adventurers[players[0]][0]
    tile = place_water(game, 3, 0)
    inn = game.INN_TYPE(game, players[0], tile)
    adventurer.current_tile = tile
    adventurer.chest_maps = []
    adventurer.chest_map_offsets = []
    adventurer.rest(inn)
    assert len(adventurer.chest_maps) == 1


@pytest.mark.xfail(reason="Stage 7: map hand capacity is 3 in Lite Winds", strict=True)
def test_map_hand_capacity_is_three():
    assert LITE_WINDS.num_chest_maps == 3


# --- Movement (Lite Winds C.4) ---

def test_fresh_and_tired_move_budgets():
    '''Lite Winds C.4: two moves in any direction while fresh, then two downwind.'''
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    assert adventurer.fresh_move_budget == 2
    assert adventurer.tired_move_budget == 2


def test_fresh_moves_any_direction_then_downwind_only():
    '''Lite Winds C.4: fresh Adventurers move over water or land in any direction;
    tired ones only over water edges in the wind arrow's direction.'''
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    # wind on the starting water tiles points north-east
    adventurer.current_tile = game.play_area[0][1]

    # fresh: all four directions are legal, regardless of wind
    for direction in ("n", "e", "s", "w"):
        assert adventurer.can_move(direction)

    adventurer.fresh_moves_used = 2  # now tired
    assert adventurer.is_tired and not adventurer.is_exhausted
    # tired: only downwind water edges (wind points north and east)
    assert adventurer.can_move("n")
    assert adventurer.can_move("e")
    assert not adventurer.can_move("s")
    assert not adventurer.can_move("w")

    adventurer.tired_moves_used = 2  # now exhausted
    assert adventurer.is_exhausted
    for direction in ("n", "e", "s", "w"):
        assert not adventurer.can_move(direction)
    assert not adventurer.can_move(None)


def test_wind_is_read_from_the_tile_moved_from():
    '''Lite Winds C.4: the wind arrow on the tile they move FROM governs riding the wind.'''
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    # a tile whose wind points south-west
    tile = place_water(game, 5, 5, wind_north=False, wind_east=False)
    adventurer.current_tile = tile
    adventurer.fresh_moves_used = 2  # tired
    assert adventurer.can_move("s")
    assert adventurer.can_move("w")
    assert not adventurer.can_move("n")
    assert not adventurer.can_move("e")


def test_rest_resets_move_budgets_mid_turn():
    '''Lite Winds C.4: Adventurers keep moving until exhausted, unless they rest at an Inn.'''
    game, players = make_game()
    adventurer = game.adventurers[players[0]][0]
    tile = place_water(game, 3, 0)
    inn = game.INN_TYPE(game, players[0], tile)
    adventurer.current_tile = tile
    adventurer.fresh_moves_used = 2
    adventurer.tired_moves_used = 1
    assert adventurer.rest(inn)
    assert not adventurer.is_tired
    assert adventurer.fresh_moves_used == 0 and adventurer.tired_moves_used == 0


# --- Piracy (Shady Routes C.2) ---

def test_successful_ransack_flips_inn_and_pays_one_silk():
    game, players = make_game(GameShadyRoutes)
    attacker = game.adventurers[players[0]][0]
    tile = place_water(game, 3, 0)
    inn = game.INN_TYPE(game, players[1], tile)
    inn.silks = 2
    attacker.current_tile = tile
    attacker.attack_success_prob = 1.1  # force success under the current probability model
    assert attacker.attack(inn)
    assert inn.is_ransacked
    assert inn.silks == 0
    assert attacker.silks == 3  # the Inn's 2 Silks + 1 for ransacking
    assert attacker.pirate_token


def test_ransacked_inn_gives_no_rest_until_restored():
    game, players = make_game(GameShadyRoutes)
    adventurer = game.adventurers[players[0]][0]
    tile = place_water(game, 3, 0)
    inn = game.INN_TYPE(game, players[0], tile)
    inn.is_ransacked = True
    adventurer.current_tile = tile
    assert not adventurer.rest(inn)

    adventurer.silks = 5
    assert adventurer.restore_inn(inn)
    assert not inn.is_ransacked
    assert adventurer.silks == 4  # paid 1 Silk to restore


def test_successful_arrest_rewards_five_and_ends_pirate_expedition():
    game, players = make_game(GameShadyRoutes)
    attacker = game.adventurers[players[0]][0]
    pirate = game.adventurers[players[1]][0]
    tile = place_water(game, 3, 0)
    attacker.current_tile = tile
    tile.move_onto_tile(pirate)
    pirate.pirate_token = True
    pirate.silks = 7
    attacker.attack_success_prob = 1.1  # force success
    assert attacker.attack(pirate)
    assert attacker.silks == 5           # arrest reward
    assert pirate.silks == 0             # pirate's Silks are lost
    assert not pirate.pirate_token       # redeemed
    assert pirate.current_tile is pirate.latest_city  # retreated


@pytest.mark.xfail(reason="Stage 8: attacker becomes a pirate only on SUCCESS", strict=True)
def test_failed_attack_does_not_make_a_pirate():
    game, players = make_game(GameShadyRoutes)
    attacker = game.adventurers[players[0]][0]
    victim = game.adventurers[players[1]][0]
    tile = place_water(game, 3, 0)
    attacker.current_tile = tile
    tile.move_onto_tile(victim)
    victim.silks = 4
    attacker.attack_success_prob = -0.1  # force failure
    assert not attacker.attack(victim)
    assert not attacker.pirate_token


@pytest.mark.xfail(reason="Stage 8: attacks resolve by die roll 1-2 loss, 3-4 draw, 5-6 win", strict=True)
def test_attack_resolver_uses_die_semantics():
    game, _ = make_game(GameShadyRoutes)
    assert hasattr(game, "attack_resolver")


# --- Roads (Silk Roads) ---

@pytest.mark.xfail(reason="Stage 9: Roads are implemented for Silk Roads", strict=True)
def test_roads_exist_in_silk_roads():
    game, players = make_game(GameSilkRoads)
    assert hasattr(game, "roads")


def test_silk_roads_map_hand_is_two():
    '''Silk Roads B.6: each player draws 2 maps for each Adventurer's Chest.'''
    assert SILK_ROADS.num_chest_maps == 2
