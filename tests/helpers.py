'''Headless game construction for tests, delegating to the canonical setup.'''

import contextlib
import io

from cartolan.core.setup import create_game


def build_game(game_type, players, mythical_city=True):
    return create_game(game_type, players, mythical_city)


def run_to_completion(game):
    with contextlib.redirect_stdout(io.StringIO()):
        game.start_game()
    return game
