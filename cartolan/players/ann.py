'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import os
try:
    import keras
    from keras import layers
    from keras.optimizers import Adam
except ImportError:  # keras is optional: PlayerFeedFwd raises on use instead of blocking import
    keras = None
    layers = None
    Adam = None
import random
import numpy as np
import collections

from cartolan.players.base import Player


def _require_keras():
    if keras is None:
        raise ImportError("PlayerFeedFwd requires the optional 'keras' dependency: pip install cartolan[ann]")


class PlayerFeedFwd(Player):
    def __init__(self, name):
        super().__init__(name)

        self.VAULT_INCREASE_REWARD = 1
        self.CHEST_INCREASE_REWARD = 2
        self.GAME_WIN_REWARD = 10
        self.FUTURE_REWARD_DISCOUNT = 0.95   # must be high for long-horizon games (~80 turns)
        self.OPTIMISER_LEARNING_RATE = 0.0005
        self.WHIMSY_REDUCTION_PER_TURN = 0.01
        self.MIMICRY_REDUCTION_PER_TURN = 0.01
        self.EPSILON_DECAY_PER_GAME = 0.995   # global exploration decay across training games
        self.EPSILON_MIN = 0.05              # floor: always keep 5% random exploration
        self.MIMICRY_DECAY_PER_GAME = 0.999  # global mimicry decay; slower than epsilon
        self.MIMICRY_FLOOR = 0.05            # minimum mimicry probability
        self.TRAIN_EVERY_N_MOVES = 5         # trigger a replay pass every N moves
        self.FIRST_LAYER_SIZE = 120
        self.SECOND_LAYER_SIZE = 120
        self.SAVED_MODEL_PATH = "ann_models/model.weights.h5"
        self.LOAD_OLD_MODEL = True
        self.MEMORY_SIZE = 2500
        self.REPLAY_BATCH_SIZE = 32

        self.attack_history = []
        self.best_vault_silks = 0
        self.best_vault_turn = 0
        # Keyed by adventurer to avoid needing MAX_ADVENTURERS at init time
        self.best_chest_silks = {}
        self.best_chest_turns = {}

        self.games_played = 0         # global counter; drives epsilon decay
        self.moves_since_last_train = 0
        self.short_memory = np.array([])
        self.whimsy_probability = 1
        self.randomised_latest_move = False
        self.mimicry_probability = 1
        self.mimicked_latest_move = False
        self.player_to_mimic = None
        self.actual = []
        self.memory = collections.deque(maxlen=self.MEMORY_SIZE)
        self.predicted_continuation_values = None
        self.model = None

        # Direction keys passed to adventurer.move(); index aligns with move_network output
        self.move_map = {0: 'n', 1: 'e', 2: 's', 3: 'w', 4: 'wait'}

        # Local observation window hyperparameters
        # Window is (2*WINDOW_RADIUS+1)^2 tiles centered on each adventurer
        self.WINDOW_RADIUS = 3  # 7x7 grid
        # Feature slots per tile in the window (see get_local_window for layout):
        #   10 base tile features + 4 inn features + 2 adventurer-count features
        self.WINDOW_TILE_BASE_FEATURES = 10
        self.WINDOW_TILE_INN_FEATURES = 4
        self.WINDOW_TILE_ADVENTURER_FEATURES = 2
        self.FEATURES_PER_WINDOW_TILE = (
            self.WINDOW_TILE_BASE_FEATURES
            + self.WINDOW_TILE_INN_FEATURES
            + self.WINDOW_TILE_ADVENTURER_FEATURES
        )  # = 16

        # CNN filter counts for the shared spatial encoder applied to each window
        self.CNN_FILTERS_1 = 32
        self.CNN_FILTERS_2 = 64

    def _player_relative_index(self, player, game, own_player):
        '''Returns the turn-order-relative index of a player as seen by own_player.

        0 = own_player, 1 = next player in turn order, 2 = player after that, etc.
        Used to give the ANN a consistent "self vs others" framing regardless of seat position.
        '''
        own_idx = game.players.index(own_player)
        p_idx = game.players.index(player)
        return (p_idx - own_idx) % len(game.players)

    def get_local_window(self, adventurer):
        '''Builds a fixed-size feature vector for the play area around one adventurer.

        The window is (2*WINDOW_RADIUS+1)^2 tiles centered on the adventurer's current
        position. Tiles outside the discovered play area are encoded as all-zeros (unexplored).

        Each tile cell occupies FEATURES_PER_WINDOW_TILE consecutive floats:
          offset  0: explored (1.0) / unexplored (0.0)
          offset  1: upwind-clockwise edge is water
          offset  2: upwind-anticlockwise edge is water
          offset  3: downwind-clockwise edge is water
          offset  4: downwind-anticlockwise edge is water
          offset  5: wind points north
          offset  6: wind points east
          offset  7: tile is a wonder
          offset  8: tile back is land (vs water)
          offset  9: city type  (0.0=none, 0.5=mythical city, 1.0=capital)
          offset 10: an inn is present
          offset 11: inn owner relative index (0=own, 1=next opponent, …)
          offset 12: inn silks
          offset 13: inn is ransacked
          offset 14: count of own adventurers on this tile
          offset 15: count of opponent adventurers on this tile

        Arguments
        adventurer is a Cartolan.Adventurer whose current_tile provides the window centre.
        '''
        game = adventurer.game
        own_player = adventurer.player
        center_lon = adventurer.current_tile.tile_position.longitude
        center_lat = adventurer.current_tile.tile_position.latitude

        window_side = 2 * self.WINDOW_RADIUS + 1
        window = np.zeros(window_side * window_side * self.FEATURES_PER_WINDOW_TILE)

        cell_idx = 0
        for dx in range(-self.WINDOW_RADIUS, self.WINDOW_RADIUS + 1):
            for dy in range(-self.WINDOW_RADIUS, self.WINDOW_RADIUS + 1):
                tile = game.play_area.get(center_lon + dx, {}).get(center_lat + dy)
                offset = cell_idx * self.FEATURES_PER_WINDOW_TILE
                if tile is not None:
                    e = tile.tile_edges
                    window[offset + 0] = 1.0  # explored
                    window[offset + 1] = float(e.upwind_clock_water)
                    window[offset + 2] = float(e.upwind_anti_water)
                    window[offset + 3] = float(e.downwind_clock_water)
                    window[offset + 4] = float(e.downwind_anti_water)
                    window[offset + 5] = float(tile.wind_direction.north)
                    window[offset + 6] = float(tile.wind_direction.east)
                    window[offset + 7] = float(tile.has_trade_port)
                    window[offset + 8] = float(tile.tile_back == 'land')
                    # City type: 1.0=capital, 0.5=mythical city, 0.0=not a city
                    if hasattr(tile, 'is_home_city'):
                        window[offset + 9] = 1.0 if tile.is_home_city else 0.5

                    # Inn on this tile (at most one per tile)
                    inn = tile.inn
                    if inn is not None:
                        window[offset + 10] = 1.0
                        window[offset + 11] = float(
                            self._player_relative_index(inn.player, game, own_player))
                        window[offset + 12] = float(inn.silks)
                        window[offset + 13] = float(getattr(inn, 'is_ransacked', False))

                    # Adventurer counts on this tile, split own vs opponent
                    window[offset + 14] = float(
                        sum(1 for a in tile.adventurers if a.player == own_player))
                    window[offset + 15] = float(
                        sum(1 for a in tile.adventurers if a.player != own_player))

                cell_idx += 1

        return window

    def build_network(self, game_type):
        '''Specifies the topology of the network behind various decision models for the player.

        Arguments
        game_type is a Cartolan.Game subclass from which game parameters can be read.
        '''
        _require_keras()
        window_side = 2 * self.WINDOW_RADIUS + 1
        window_features_per_adventurer = window_side ** 2 * self.FEATURES_PER_WINDOW_TILE
        window_features_total = window_features_per_adventurer * game_type.RULESET.max_adventurers
        global_state_size = (
            1                                   # vault silks
            + 3                                 # moves since resting
            + 4                                 # current tile edges
            + 2                                 # current tile wind direction
            + 6                                 # preceding three tile positions
            + 1                                 # adventurer index (which adventurer is deciding)
            + game_type.RULESET.max_adventurers         # own adventurer silks
            + game_type.RULESET.max_adventurers         # own adventurer companions
            + 2 * game_type.RULESET.max_adventurers     # own adventurer positions
            + game_type.RULESET.max_inns              # own inn silks
            + 2 * game_type.RULESET.max_inns          # own inn positions
            + 3                                 # opponent vault silks (up to 3 opponents)
            + 3 * game_type.RULESET.max_adventurers     # opponent adventurer silks
            + 3 * game_type.RULESET.max_adventurers     # opponent adventurer companions
            + 3 * game_type.RULESET.max_adventurers     # opponent adventurer pirate tokens
            + 2 * 3 * game_type.RULESET.max_adventurers # opponent adventurer positions
            + 3 * game_type.RULESET.max_inns          # opponent inn silks
            + 3 * game_type.RULESET.max_inns          # opponent inn ransacked status
            + 2 * 3 * game_type.RULESET.max_inns      # opponent inn positions
        )
        total_state_size = window_features_total + global_state_size

        # Single flat input; windows occupy the first window_features_total elements,
        # global scalars occupy the remainder.
        state_input = keras.Input(shape=(total_state_size,), name='state')

        # --- Shared CNN spatial encoder ---
        # The same convolutional filters are applied to every adventurer's window so the
        # network learns tile-pattern detectors once and reuses them across all adventurers.
        # Each (7x7x16) window → Conv → Conv → GlobalAveragePooling → 64-d encoding.
        shared_conv1 = layers.Conv2D(
            self.CNN_FILTERS_1, kernel_size=3, padding='same', activation='relu',
            name='shared_conv1')
        shared_conv2 = layers.Conv2D(
            self.CNN_FILTERS_2, kernel_size=3, padding='same', activation='relu',
            name='shared_conv2')
        shared_pool = layers.GlobalAveragePooling2D(name='shared_pool')

        window_encodings = []
        for i in range(game_type.RULESET.max_adventurers):
            start = i * window_features_per_adventurer
            end = (i + 1) * window_features_per_adventurer
            # Slice this adventurer's flat window out of the state vector
            window_flat = state_input[:, start:end]
            # Reshape to (batch, height, width, channels) for Conv2D
            window_2d = layers.Reshape(
                (window_side, window_side, self.FEATURES_PER_WINDOW_TILE),
                name=f'reshape_window_{i}'
            )(window_flat)
            x = shared_conv1(window_2d)
            x = shared_conv2(x)
            x = shared_pool(x)  # → (batch, CNN_FILTERS_2)
            window_encodings.append(x)

        # Slice the global scalar features (everything after the window block)
        global_features = state_input[:, window_features_total:]

        # Concatenate all window encodings with the global state, then feed dense layers.
        # Combined size: MAX_ADVENTURERS * CNN_FILTERS_2 + global_state_size
        combined = layers.Concatenate(name='combined')(window_encodings + [global_features])
        base_network = layers.Dense(units=self.FIRST_LAYER_SIZE, activation='relu')(combined)
        base_network = layers.Dropout(0.1)(base_network)
        base_network = layers.Dense(units=self.SECOND_LAYER_SIZE, activation='relu')(base_network)
        base_network = layers.Dropout(0.1)(base_network)
        opt = Adam(self.OPTIMISER_LEARNING_RATE)

        move_network = layers.Dense(units=5, activation='softmax')(base_network)
        trade_network = layers.Dense(units=1, activation='sigmoid')(base_network)
        rest_network = layers.Dense(units=1, activation='sigmoid')(base_network)
        collect_network = layers.Dense(units=1, activation='sigmoid')(base_network)
        place_network = layers.Dense(units=1, activation='sigmoid')(base_network)
        attack_network = layers.Dense(
            units=3 * (game_type.RULESET.max_adventurers + game_type.RULESET.max_inns),
            activation='sigmoid'
        )(base_network)
        restore_network = layers.Dense(units=1, activation='sigmoid')(base_network)
        bank_network = layers.Dense(units=1, activation='exponential')(base_network)
        buy_adventurer_network = layers.Dense(units=1, activation='sigmoid')(base_network)
        hire_companion_network = layers.Dense(units=1, activation='sigmoid')(base_network)

        model = keras.Model(
            inputs=[state_input],
            outputs=[move_network, trade_network, rest_network, collect_network,
                     place_network, attack_network, restore_network, bank_network,
                     buy_adventurer_network, hire_companion_network],
        )
        model.compile(optimizer=opt, loss='mse')

        os.makedirs(os.path.dirname(self.SAVED_MODEL_PATH), exist_ok=True)

        if self.LOAD_OLD_MODEL:
            try:
                model.load_weights(self.SAVED_MODEL_PATH)
                print("Previous model loaded")
            except Exception:
                print("No saved model found, starting fresh")

        self.model = model

    def get_state(self, adventurer):
        '''Compiles information about the current game situation for the ANN.

        Arguments
        adventurer is a Cartolan.Adventurer representing the token for which a decision is needed.
        '''
        current_tile = adventurer.current_tile
        game = adventurer.game
        own_adventurers = game.adventurers.get(adventurer.player, [])
        own_inns = game.inns.get(adventurer.player, [])
        players = game.players

        state_own_adventurers_wealth = [0] * game.max_adventurers
        state_own_adventurers_companions = [0] * game.max_adventurers
        state_own_adventurers_positions = [0] * (2 * game.max_adventurers)
        for own_adventurer in own_adventurers:
            idx = own_adventurers.index(own_adventurer)
            state_own_adventurers_wealth[idx] = own_adventurer.silks
            state_own_adventurers_companions[idx] = getattr(own_adventurer, 'num_companions', 0)
            state_own_adventurers_positions[2 * idx] = own_adventurer.current_tile.tile_position.longitude
            state_own_adventurers_positions[2 * idx + 1] = own_adventurer.current_tile.tile_position.latitude

        state_own_inns_wealth = [0] * game.max_inns
        state_own_inns_positions = [0] * (2 * game.max_inns)
        for own_inn in own_inns:
            idx = own_inns.index(own_inn)
            state_own_inns_wealth[idx] = own_inn.silks
            state_own_inns_positions[2 * idx] = own_inn.current_tile.tile_position.longitude
            state_own_inns_positions[2 * idx + 1] = own_inn.current_tile.tile_position.latitude

        state_opp_vault_silkss = [0] * 3
        state_opp_adventurers_wealths = [0] * (3 * game.max_adventurers)
        state_opp_adventurers_companions = [0] * (3 * game.max_adventurers)
        state_opp_adventurers_pirates = [0] * (3 * game.max_adventurers)
        state_opp_adventurers_positions = [0] * (2 * 3 * game.max_adventurers)
        state_opp_inns_wealths = [0] * (3 * game.max_inns)
        state_opp_inns_ransacked = [0] * (3 * game.max_inns)
        state_opp_inns_positions = [0] * (2 * 3 * game.max_inns)

        own_index = players.index(self)
        opponent_index = 0

        def encode_opponent(player_index):
            nonlocal opponent_index
            p = players[player_index]
            state_opp_vault_silkss[opponent_index] = game.vault_silks.get(p, 0)
            opp_adventurers = game.adventurers.get(p, [])
            for opp_adventurer in opp_adventurers:
                oa_idx = opp_adventurers.index(opp_adventurer)
                flat = game.max_adventurers * opponent_index + oa_idx
                state_opp_adventurers_wealths[flat] = opp_adventurer.silks
                state_opp_adventurers_companions[flat] = getattr(opp_adventurer, 'num_companions', 0)
                state_opp_adventurers_pirates[flat] = int(getattr(opp_adventurer, 'pirate_token', False))
                state_opp_adventurers_positions[2 * flat] = opp_adventurer.current_tile.tile_position.longitude
                state_opp_adventurers_positions[2 * flat + 1] = opp_adventurer.current_tile.tile_position.latitude
            opp_inns = game.inns.get(p, [])
            for opp_inn in opp_inns:
                oa_idx = opp_inns.index(opp_inn)
                flat = game.max_inns * opponent_index + oa_idx
                state_opp_inns_wealths[flat] = opp_inn.silks
                state_opp_inns_ransacked[flat] = int(getattr(opp_inn, 'is_ransacked', False))
                state_opp_inns_positions[2 * flat] = opp_inn.current_tile.tile_position.longitude
                state_opp_inns_positions[2 * flat + 1] = opp_inn.current_tile.tile_position.latitude
            opponent_index += 1

        for later_idx in range(own_index + 1, len(players)):
            encode_opponent(later_idx)
        for earlier_idx in range(0, own_index):
            encode_opponent(earlier_idx)

        preceding_positions = [0] * 6  # @TODO encode last three tile positions from adventurer.route

        # Build one local observation window per adventurer slot.
        # Slots for adventurers not yet in play are zero-padded so the state vector
        # has a fixed length regardless of how many adventurers have been recruited.
        all_own_adventurers = game.adventurers.get(adventurer.player, [])
        window_size = (2 * self.WINDOW_RADIUS + 1) ** 2 * self.FEATURES_PER_WINDOW_TILE
        windows = []
        for slot in range(game.max_adventurers):
            if slot < len(all_own_adventurers):
                windows.append(self.get_local_window(all_own_adventurers[slot]))
            else:
                windows.append(np.zeros(window_size))

        state = np.concatenate([
            *windows,
            [game.vault_silks.get(adventurer.player, 0)],
            [adventurer.tired_moves_used, adventurer.fresh_moves_used, 0],
            [current_tile.tile_edges.upwind_clock_water, current_tile.tile_edges.upwind_anti_water,
             current_tile.tile_edges.downwind_clock_water, current_tile.tile_edges.downwind_anti_water],
            [current_tile.wind_direction.north, current_tile.wind_direction.east],
            preceding_positions,
            [own_adventurers.index(adventurer)],
            state_own_adventurers_wealth,
            state_own_adventurers_companions,
            state_own_adventurers_positions,
            state_own_inns_wealth,
            state_own_inns_positions,
            state_opp_vault_silkss,
            state_opp_adventurers_wealths,
            state_opp_adventurers_companions,
            state_opp_adventurers_pirates,
            state_opp_adventurers_positions,
            state_opp_inns_wealths,
            state_opp_inns_ransacked,
            state_opp_inns_positions,
        ]).astype(float)

        return state

    def remember(self, state, action, reward, next_state, done):
        '''Retains historic game state information for use in replay learning.'''
        self.memory.append((state, action, reward, next_state, done))

    def replay_training(self):
        '''Re-trains the model on a random batch of past experiences (experience replay).

        Based on a Bellman equation where the value of optimal subsequent play is estimated
        via a numerical approximation using the current model on future states.
        Uses a single vectorised fit() call over the whole batch rather than one per sample.
        '''
        if len(self.memory) > self.REPLAY_BATCH_SIZE:
            batch = random.sample(self.memory, self.REPLAY_BATCH_SIZE)
        else:
            batch = list(self.memory)

        states = np.array([exp[0] for exp in batch])
        next_states = np.array([exp[3] for exp in batch])

        # Two forward passes over the whole batch — much cheaper than N single-sample passes
        current_preds = [p.numpy() for p in self.model(states)]
        next_move_values = self.model(next_states)[0].numpy()  # only move head needed

        # Build target arrays: copy current predictions, then update only the chosen action
        # @TODO extend to update all decision heads independently
        targets = current_preds
        for i, (_, action, reward, _, done) in enumerate(batch):
            updated_Q = reward
            if not done:
                updated_Q += self.FUTURE_REWARD_DISCOUNT * np.amax(next_move_values[i])
            targets[0][i][action] = updated_Q

        self.model.fit(states, targets, epochs=1, verbose=0)

    def continue_turn(self, adventurer):
        '''Houses the AI's movement decisions during a single turn.

        Arguments
        adventurer is a Cartolan.Adventurer representing the token being moved.
        '''
        reward = 0
        #For the first turn of a new game reset all the silks trackers
        if adventurer.turns_moved == 0:
            self.best_vault_silks = 0
            self.best_vault_turn = 0
            self.best_chest_silks[adventurer] = 0
            self.best_chest_turns[adventurer] = 0

        if not getattr(self, 'active_training', False):
            self.whimsy_probability = 0
        else:
            # Global epsilon decays with games_played so exploration reduces as training progresses.
            # Within each game it also decays with turns_moved so the inn exploits more late-game.
            global_epsilon = max(self.EPSILON_MIN, self.EPSILON_DECAY_PER_GAME ** self.games_played)
            self.whimsy_probability = global_epsilon #/ ( 1.0 + adventurer.turns_moved * self.WHIMSY_REDUCTION_PER_TURN)
            global_mimicry = max(self.MIMICRY_FLOOR,
                                 self.MIMICRY_DECAY_PER_GAME ** self.games_played)
            self.mimicry_probability = global_mimicry #/ (1.0 + adventurer.turns_moved * self.MIMICRY_REDUCTION_PER_TURN)

        _DELTA_TO_MOVE = {(0, 1): 0, (1, 0): 1, (0, -1): 2, (-1, 0): 3, (0, 0): 4}

        while adventurer.turns_moved < adventurer.game.turn:
            reward = 0  # reset per move so each experience has only that move's reward

            state_old = self.get_state(adventurer)

            if random.random() < self.whimsy_probability:
                if (self.player_to_mimic is not None
                        and hasattr(self.player_to_mimic, 'continue_move')
                        and random.random() < self.mimicry_probability):
                    # Let the heuristic execute one move; deduce direction from position delta
                    pos_lon = adventurer.current_tile.tile_position.longitude
                    pos_lat = adventurer.current_tile.tile_position.latitude
                    self.player_to_mimic.locations_to_avoid = [[pos_lon, pos_lat]]
                    self.player_to_mimic.continue_move(adventurer)
                    dx = adventurer.current_tile.tile_position.longitude - pos_lon
                    dy = adventurer.current_tile.tile_position.latitude - pos_lat
                    move_choice = _DELTA_TO_MOVE.get((dx, dy), 4)
                    print("Mimicked move: " + self.move_map[move_choice])
                    self.mimicked_latest_move = True
                    self.randomised_latest_move = False
                else:
                    move_choice = random.randint(0, len(self.move_map) - 1)
                    direction = self.move_map[move_choice]
                    if direction == 'wait':
                        adventurer.wait()
                    else:
                        adventurer.move(direction)
                    print("Randomly chose direction: " + self.move_map[move_choice])
                    self.randomised_latest_move = True
                    self.mimicked_latest_move = False
            else:
                self.predicted_continuation_values = self.model(np.array([state_old]))
                move_choice = int(np.argmax(self.predicted_continuation_values[0]))
                direction = self.move_map[move_choice]
                if direction == 'wait':
                    adventurer.wait()
                else:
                    adventurer.move(direction)
                print("ANN chose direction: " + self.move_map[move_choice])
                self.mimicked_latest_move = False
                self.randomised_latest_move = False

            state_new = self.get_state(adventurer)

            current_vault = adventurer.game.vault_silks.get(self, 0)
            vault_silks_increase = current_vault - self.best_vault_silks
            if vault_silks_increase > 0:
                reward += self.VAULT_INCREASE_REWARD * vault_silks_increase / (
                    abs(adventurer.turns_moved - self.best_vault_turn) + 1)
                self.best_vault_silks = current_vault
                self.best_vault_turn = adventurer.turns_moved

            # Similarly for this adventurer's chest silks
            if adventurer not in self.best_chest_silks:
                self.best_chest_silks[adventurer] = 0
                self.best_chest_turns[adventurer] = 0
            chest_silks_increase = adventurer.silks - self.best_chest_silks[adventurer]
            if chest_silks_increase > 0:
                reward += self.CHEST_INCREASE_REWARD * chest_silks_increase / (
                    abs(adventurer.turns_moved - self.best_chest_turns[adventurer]) + 1)
                self.best_chest_silks[adventurer] = adventurer.silks
                self.best_chest_turns[adventurer] = adventurer.turns_moved

            done = adventurer.game.game_over
            if done:
                # Apply terminal reward before remember() so the final experience
                # stored in the replay buffer includes the win/loss signal.
                if adventurer.game.winning_player == self:
                    reward += self.GAME_WIN_REWARD
                else:
                    reward -= self.GAME_WIN_REWARD
            self.remember(state_old, move_choice, reward, state_new, done)

            if getattr(self, 'active_training', False) and len(self.memory) >= self.REPLAY_BATCH_SIZE:
                self.moves_since_last_train += 1
                if self.moves_since_last_train >= self.TRAIN_EVERY_N_MOVES:
                    self.replay_training()
                    self.moves_since_last_train = 0

        return True

    def check_bank_amount(self, adventurer, maximum, minimum=0, report=''):
        '''Bank all available chest silks.'''
        return maximum

    def check_travel_silks(self, adventurer, maximum, default):
        '''Pay no travel toll by default.'''
        return default

    def check_trade(self, adventurer, tile):
        '''Gives the AI's decision whether to trade at a Trade Port tile.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        tile is the Trade Port tile being visited.
        '''
        if random.random() < self.whimsy_probability:
            if (self.player_to_mimic is not None
                    and hasattr(self.player_to_mimic, 'check_trade')
                    and random.random() < self.mimicry_probability):
                trade = self.player_to_mimic.check_trade(adventurer, tile)
                print("Mimicked trade: " + str(trade))
            else:
                trade = random.random() > 0.5
                print("Randomly chose trade: " + str(trade))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            trade = prediction[1][0][0] > 0.5  # output index 1 = trade_network
            print("ANN chose trade: " + str(trade))
        return trade

    def check_collect_silks(self, inn):
        '''Gives the AI's decision whether to collect silks from an Inn.

        Arguments
        inn is the Inn token being visited.
        '''
        adventurer = next(
            (a for a in inn.current_tile.adventurers if a.player == self), None
        )
        if adventurer is None or self.model is None:
            return random.random() > 0.5
        if random.random() < self.whimsy_probability:
            if (self.player_to_mimic is not None
                    and hasattr(self.player_to_mimic, 'check_collect_silks')
                    and random.random() < self.mimicry_probability):
                collect = self.player_to_mimic.check_collect_silks(inn)
                print("Mimicked collect: " + str(collect))
            else:
                collect = random.random() > 0.5
                print("Randomly chose collect: " + str(collect))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            collect = prediction[3][0][0] > 0.5  # output index 3 = collect_network
            print("ANN chose collect: " + str(collect))
        return collect

    def check_rest(self, adventurer, inn):
        '''Gives the AI's decision whether to rest at an Inn.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        inn is the Inn token being visited.
        '''
        if random.random() < self.whimsy_probability:
            if (self.player_to_mimic is not None
                    and hasattr(self.player_to_mimic, 'check_rest')
                    and random.random() < self.mimicry_probability):
                rest = self.player_to_mimic.check_rest(adventurer, inn)
                print("Mimicked rest: " + str(rest))
            else:
                rest = random.random() > 0.5
                print("Randomly chose rest: " + str(rest))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            rest = prediction[2][0][0] > 0.5  # output index 2 = rest_network
            print("ANN chose rest: " + str(rest))
        return rest

    def check_bank_silks(self, adventurer, report="Player is being asked whether to bank silks"):
        '''Gives the AI's decision how much silks to keep in the chest when banking at a city.

        Returns an int: the amount of silks to retain in the chest (the rest is banked).

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        '''
        if random.random() < self.whimsy_probability:
            keep = random.randint(0, adventurer.silks) if adventurer.silks > 0 else 0
            print("Randomly chose to keep: " + str(keep))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            keep = max(0, min(int(prediction[7][0][0]), adventurer.silks))  # output index 7 = bank_network
            print("ANN chose to keep: " + str(keep))
        return keep

    def check_buy_adventurer(self, adventurer, report="Player is being asked whether to buy an Adventurer"):
        '''Gives the AI's decision whether to recruit a new Adventurer when visiting a city.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        '''
        if random.random() < self.whimsy_probability:
            if (self.player_to_mimic is not None
                    and hasattr(self.player_to_mimic, 'check_buy_adventurer')
                    and random.random() < self.mimicry_probability):
                recruit = self.player_to_mimic.check_buy_adventurer(adventurer)
                print("Mimicked recruit: " + str(recruit))
            else:
                recruit = random.random() > 0.5
                print("Randomly chose recruit: " + str(recruit))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            recruit = prediction[8][0][0] > 0.5  # output index 8 = buy_adventurer_network
            print("ANN chose recruit: " + str(recruit))
        return recruit

    def check_hire_inn(self, adventurer):
        '''Gives the AI's decision whether to place an Inn when discovering a new tile.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        '''
        if random.random() < self.whimsy_probability:
            if (self.player_to_mimic is not None
                    and hasattr(self.player_to_mimic, 'check_hire_inn')
                    and random.random() < self.mimicry_probability):
                place = self.player_to_mimic.check_hire_inn(adventurer)
                print("Mimicked place inn: " + str(place))
            else:
                place = random.random() > 0.5
                print("Randomly chose place inn: " + str(place))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            place = prediction[4][0][0] > 0.5  # output index 4 = place_network
            print("ANN chose place inn: " + str(place))
        return place

    def check_buy_inn(self, adventurer, report="Player has been offered to buy an inn by a city"):
        '''Gives the AI's decision whether to place an Inn on an existing tile from a city.

        Returns None while the ANN lacks awareness of the full play area.
        '''
        return None  # @TODO enable once play area map is included in state

    def check_move_inn(self, adventurer):
        '''Gives the AI's decision about which Inn to move when at the placement limit.

        Returns None while the ANN lacks awareness of the full play area.
        '''
        return None  # @TODO enable once play area map is included in state

    def check_attack_adventurer(self, adventurer, other_adventurer):
        '''Gives the AI's decision whether to attack another player's Adventurer.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        other_adventurer is the opposing Adventurer on the same tile.
        '''
        if random.random() < self.whimsy_probability:
            if (self.player_to_mimic is not None
                    and hasattr(self.player_to_mimic, 'check_attack_adventurer')
                    and random.random() < self.mimicry_probability):
                attack = self.player_to_mimic.check_attack_adventurer(adventurer, other_adventurer)
                print("Mimicked attack adventurer: " + str(attack))
            else:
                attack = random.random() > 0.5
                print("Randomly chose attack adventurer: " + str(attack))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            attack = prediction[5][0][0] > 0.5  # output index 5 = attack_network
            print("ANN chose attack adventurer: " + str(attack))
        return attack

    def check_attack_inn(self, adventurer, inn):
        '''Gives the AI's decision whether to attack another player's Inn.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        inn is the opposing Inn on the tile.
        '''
        if random.random() < self.whimsy_probability:
            if (self.player_to_mimic is not None
                    and hasattr(self.player_to_mimic, 'check_attack_inn')
                    and random.random() < self.mimicry_probability):
                attack = self.player_to_mimic.check_attack_inn(adventurer, inn)
                print("Mimicked attack inn: " + str(attack))
            else:
                attack = random.random() > 0.5
                print("Randomly chose attack inn: " + str(attack))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            attack = prediction[5][0][0] > 0.5  # output index 5 = attack_network
            print("ANN chose attack inn: " + str(attack))
        return attack

    def check_restore_inn(self, adventurer, inn):
        '''Gives the AI's decision whether to restore a ransacked Inn.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        inn is the player's ransacked Inn on the tile.
        '''
        if random.random() < self.whimsy_probability:
            if (self.player_to_mimic is not None
                    and hasattr(self.player_to_mimic, 'check_restore_inn')
                    and random.random() < self.mimicry_probability):
                restore = self.player_to_mimic.check_restore_inn(adventurer, inn)
                print("Mimicked restore: " + str(restore))
            else:
                restore = random.random() > 0.5
                print("Randomly chose restore: " + str(restore))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            restore = prediction[6][0][0] > 0.5  # output index 6 = restore_network
            print("ANN chose restore: " + str(restore))
        return restore

    def check_hire_companion(self, adventurer):
        '''Gives the AI's decision whether to hire a companion card when visiting a city.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        '''
        if random.random() < self.whimsy_probability:
            if (self.player_to_mimic is not None
                    and hasattr(self.player_to_mimic, 'check_hire_companion')
                    and random.random() < self.mimicry_probability):
                hire = self.player_to_mimic.check_hire_companion(adventurer)
                print("Mimicked hire companion: " + str(hire))
            else:
                hire = random.random() > 0.5
                print("Randomly chose hire companion: " + str(hire))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            hire = prediction[9][0][0] > 0.5  # output index 9 = hire_companion_network
            print("ANN chose hire companion: " + str(hire))
        return hire
