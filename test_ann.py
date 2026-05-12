'''
Tests for the ANN player (PlayerFeedFwd) in players_ann.py.

Run with:  pytest test_ann.py -v

Two test classes:
  TestStateVector  — fast unit tests that check the observation vector shape and content.
  TestTrainingSmoke — runs a handful of game rounds to exercise the full train/save path.

Requires keras to be installed; all tests are skipped automatically when it is not.
Install with: pip install keras tensorflow
'''
import os
import numpy as np
import pytest

pytest.importorskip('keras', reason='keras not installed — pip install keras tensorflow')

from game import GameBeginner
from players_ann import PlayerFeedFwd
from players_heuristical import PlayerBeginnerExplorer
from base import Tile, WindDirection, TileEdges


def _setup_game(players):
    '''Minimal game setup equivalent to main_sim.setup_simulation, without the
    matplotlib/scipy visualisation imports that main_sim drags in.'''
    game = GameBeginner(players, 'initial', 'continuous')
    game.CITY_TYPE(game, WindDirection(True, True), TileEdges(True, True, True, True),
                   True, True).place_tile(0, 0)
    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        Tile(game, 'water', WindDirection(True, True),
             TileEdges(True, True, True, True), False).place_tile(dx, dy)
    for player in players:
        game.ADVENTURER_TYPE(game, player, game.cities[0])
    game.setup_tile_pile('water')
    return game


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_game(tmp_path=None):
    '''Returns (ai_player, game) with the AI player seated in a 2-player Beginner game.'''
    ai_player = PlayerFeedFwd('green')
    ai_player.LOAD_OLD_MODEL = False
    if tmp_path is not None:
        ai_player.SAVED_MODEL_PATH = str(tmp_path / 'model.weights.h5')
    heuristic = PlayerBeginnerExplorer('blue')
    game = _setup_game([ai_player, heuristic])
    ai_player.build_network(GameBeginner)
    return ai_player, game


# ---------------------------------------------------------------------------
# State-vector unit tests
# ---------------------------------------------------------------------------

class TestStateVector:
    '''Verify that get_state() produces a vector whose length exactly matches
    the input shape declared in build_network().  Any future change to the
    features included in get_state() that is not reflected in build_network()
    (or vice-versa) will be caught here immediately.'''

    def test_length_matches_network_input(self):
        ai_player, game = _make_game()
        adventurer = game.adventurers[ai_player][0]
        state = ai_player.get_state(adventurer)
        expected = ai_player.model.input_shape[1]
        assert len(state) == expected, (
            f'get_state() returned {len(state)} features but build_network() '
            f'declared {expected}. Update global_state_size in build_network().'
        )

    def test_state_is_finite(self):
        ai_player, game = _make_game()
        adventurer = game.adventurers[ai_player][0]
        state = ai_player.get_state(adventurer)
        assert np.all(np.isfinite(state)), \
            'State vector contains NaN or Inf — check feature encoding in get_state().'

    def test_state_length_is_consistent_across_calls(self):
        ai_player, game = _make_game()
        adventurer = game.adventurers[ai_player][0]
        lengths = {len(ai_player.get_state(adventurer)) for _ in range(3)}
        assert len(lengths) == 1, \
            'get_state() returned different lengths on successive calls.'

    def test_companions_encoded_in_state(self):
        '''Hiring a companion changes num_companions; the state vector must reflect this.'''
        ai_player, game = _make_game()
        adventurer = game.adventurers[ai_player][0]
        state_before = ai_player.get_state(adventurer).copy()
        adventurer.num_companions = 2
        state_after = ai_player.get_state(adventurer)
        assert not np.array_equal(state_before, state_after), (
            'State vector did not change after setting num_companions — '
            'verify that companion counts are included in get_state().'
        )


# ---------------------------------------------------------------------------
# End-to-end training smoke test
# ---------------------------------------------------------------------------

class TestTrainingSmoke:
    '''Plays a small number of game rounds and exercises the replay-training
    and weight-saving path.  This does NOT verify that the model learns
    anything useful — it only checks that the pipeline runs without errors.'''

    NUM_ROUNDS = 5

    def test_training_loop_runs_without_error(self, tmp_path):
        ai_player, game = _make_game(tmp_path)
        ai_player.active_training = True

        # Run a fixed number of rounds rather than a full game so the test
        # stays fast regardless of game length.
        game.game_started = True
        for _ in range(self.NUM_ROUNDS):
            game.turn += 1
            game.play_round()
            if game.game_over:
                break

        assert len(ai_player.memory) > 0, (
            'AI player accumulated no experiences after '
            f'{self.NUM_ROUNDS} rounds — check continue_turn() is being called.'
        )

        # replay_training requires at least one experience; the assert above
        # guarantees we have one before calling it.
        ai_player.replay_training()

    def test_weights_can_be_saved_and_reloaded(self, tmp_path):
        ai_player, game = _make_game(tmp_path)
        ai_player.active_training = True

        game.game_started = True
        for _ in range(self.NUM_ROUNDS):
            game.turn += 1
            game.play_round()
            if game.game_over:
                break

        if len(ai_player.memory) > 0:
            ai_player.replay_training()

        save_path = str(tmp_path / 'model.weights.h5')
        ai_player.model.save_weights(save_path)
        assert os.path.exists(save_path), \
            f'Expected weight file {save_path} was not created.'

        # Confirm a freshly-built network can load those weights without error.
        fresh_player = PlayerFeedFwd('red')
        fresh_player.LOAD_OLD_MODEL = False
        fresh_player.SAVED_MODEL_PATH = save_path
        fresh_player.build_network(GameBeginner)
        fresh_player.model.load_weights(save_path)
