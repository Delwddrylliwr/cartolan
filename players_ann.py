'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import keras
from keras import layers
from keras.optimizers import Adam
import random
import numpy as np
import collections

from base import Player


class PlayerFeedFwd(Player):
    def __init__(self, colour):
        super().__init__(colour)

        self.VAULT_INCREASE_REWARD = 1
        self.CHEST_INCREASE_REWARD = 5
        self.GAME_WIN_REWARD = 100
        self.FUTURE_REWARD_DISCOUNT = 0.9
        self.OPTIMISER_LEARNING_RATE = 0.0005
        self.WHIMSY_REDUCTION_PER_TURN = 0.1
        self.MIMICRY_REDUCTION_PER_TURN = 0.05
        self.FIRST_LAYER_SIZE = 120
        self.SECOND_LAYER_SIZE = 120
        self.SAVED_MODEL_PATH = "/ann_models/"
        self.LOAD_OLD_MODEL = True
        self.MEMORY_SIZE = 2500
        self.REPLAY_BATCH_SIZE = 32

        self.attack_history = []
        self.best_vault_wealth = 0
        self.best_vault_turn = 0
        # Keyed by adventurer to avoid needing MAX_ADVENTURERS at init time
        self.best_chest_wealths = {}
        self.best_chest_turns = {}

        self.short_memory = np.array([])
        self.whimsy_probability = 1
        self.mimicry_probability = 1
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
        #   10 base tile features + 4 agent features + 2 adventurer-count features
        self.WINDOW_TILE_BASE_FEATURES = 10
        self.WINDOW_TILE_AGENT_FEATURES = 4
        self.WINDOW_TILE_ADVENTURER_FEATURES = 2
        self.FEATURES_PER_WINDOW_TILE = (
            self.WINDOW_TILE_BASE_FEATURES
            + self.WINDOW_TILE_AGENT_FEATURES
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
          offset 10: an agent is present
          offset 11: agent owner relative index (0=own, 1=next opponent, …)
          offset 12: agent wealth
          offset 13: agent is dispossessed
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
                    window[offset + 7] = float(tile.is_wonder)
                    window[offset + 8] = float(tile.tile_back == 'land')
                    # City type: 1.0=capital, 0.5=mythical city, 0.0=not a city
                    if hasattr(tile, 'is_capital'):
                        window[offset + 9] = 1.0 if tile.is_capital else 0.5

                    # Agent on this tile (at most one per tile)
                    agent = tile.agent
                    if agent is not None:
                        window[offset + 10] = 1.0
                        window[offset + 11] = float(
                            self._player_relative_index(agent.player, game, own_player))
                        window[offset + 12] = float(agent.wealth)
                        window[offset + 13] = float(getattr(agent, 'is_dispossessed', False))

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
        window_side = 2 * self.WINDOW_RADIUS + 1
        window_features_per_adventurer = window_side ** 2 * self.FEATURES_PER_WINDOW_TILE
        window_features_total = window_features_per_adventurer * game_type.MAX_ADVENTURERS
        global_state_size = (
            1                                   # vault wealth
            + 3                                 # moves since resting
            + 4                                 # current tile edges
            + 2                                 # current tile wind direction
            + 6                                 # preceding three tile positions
            + 1                                 # adventurer index (which adventurer is deciding)
            + game_type.MAX_ADVENTURERS         # own adventurer wealth
            + 2 * game_type.MAX_ADVENTURERS     # own adventurer positions
            + game_type.MAX_AGENTS              # own agent wealth
            + 2 * game_type.MAX_AGENTS          # own agent positions
            + 3                                 # opponent vault wealth (up to 3 opponents)
            + 3 * game_type.MAX_ADVENTURERS     # opponent adventurer wealth
            + 3 * game_type.MAX_ADVENTURERS     # opponent adventurer pirate tokens
            + 2 * 3 * game_type.MAX_ADVENTURERS # opponent adventurer positions
            + 3 * game_type.MAX_AGENTS          # opponent agent wealth
            + 3 * game_type.MAX_AGENTS          # opponent agent dispossessed status
            + 2 * 3 * game_type.MAX_AGENTS      # opponent agent positions
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
        for i in range(game_type.MAX_ADVENTURERS):
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
            units=3 * (game_type.MAX_ADVENTURERS + game_type.MAX_AGENTS),
            activation='sigmoid'
        )(base_network)
        restore_network = layers.Dense(units=1, activation='sigmoid')(base_network)
        bank_network = layers.Dense(units=1, activation='exponential')(base_network)
        buy_adventurer_network = layers.Dense(units=1, activation='sigmoid')(base_network)

        model = keras.Model(
            inputs=[state_input],
            outputs=[move_network, trade_network, rest_network, collect_network,
                     place_network, attack_network, restore_network, bank_network,
                     buy_adventurer_network],
        )
        model.compile(optimizer=opt, loss='mse')

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
        own_adventurers = adventurer.player.adventurers
        own_agents = adventurer.player.agents
        players = adventurer.game.players
        game = adventurer.game

        state_own_adventurers_wealth = [0] * game.MAX_ADVENTURERS
        state_own_adventurers_positions = [0] * (2 * game.MAX_ADVENTURERS)
        for own_adventurer in own_adventurers:
            idx = own_adventurers.index(own_adventurer)
            state_own_adventurers_wealth[idx] = own_adventurer.wealth
            state_own_adventurers_positions[2 * idx] = own_adventurer.current_tile.tile_position.longitude
            state_own_adventurers_positions[2 * idx + 1] = own_adventurer.current_tile.tile_position.latitude

        state_own_agents_wealth = [0] * game.MAX_AGENTS
        state_own_agents_positions = [0] * (2 * game.MAX_AGENTS)
        for own_agent in own_agents:
            idx = own_agents.index(own_agent)
            state_own_agents_wealth[idx] = own_agent.wealth
            state_own_agents_positions[2 * idx] = own_agent.current_tile.tile_position.longitude
            state_own_agents_positions[2 * idx + 1] = own_agent.current_tile.tile_position.latitude

        state_opp_vault_wealths = [0] * 3
        state_opp_adventurers_wealths = [0] * (3 * game.MAX_ADVENTURERS)
        state_opp_adventurers_pirates = [0] * (3 * game.MAX_ADVENTURERS)
        state_opp_adventurers_positions = [0] * (2 * 3 * game.MAX_ADVENTURERS)
        state_opp_agents_wealths = [0] * (3 * game.MAX_AGENTS)
        state_opp_agents_dispossessed = [0] * (3 * game.MAX_AGENTS)
        state_opp_agents_positions = [0] * (2 * 3 * game.MAX_AGENTS)

        own_index = players.index(self)
        opponent_index = 0

        def encode_opponent(player_index):
            nonlocal opponent_index
            p = players[player_index]
            state_opp_vault_wealths[opponent_index] = p.vault_wealth
            opp_adventurers = game.adventurers.get(p, [])
            for opp_adventurer in opp_adventurers:
                oa_idx = opp_adventurers.index(opp_adventurer)
                flat = 3 * opponent_index + oa_idx
                state_opp_adventurers_wealths[flat] = opp_adventurer.wealth
                state_opp_adventurers_pirates[flat] = int(getattr(opp_adventurer, 'pirate_token', False))
                state_opp_adventurers_positions[2 * flat] = opp_adventurer.current_tile.tile_position.longitude
                state_opp_adventurers_positions[2 * flat + 1] = opp_adventurer.current_tile.tile_position.latitude
            opp_agents = game.agents.get(p, [])
            for opp_agent in opp_agents:
                oa_idx = opp_agents.index(opp_agent)
                flat = 3 * opponent_index + oa_idx
                state_opp_agents_wealths[flat] = opp_agent.wealth
                state_opp_agents_dispossessed[flat] = int(getattr(opp_agent, 'is_dispossessed', False))
                state_opp_agents_positions[2 * flat] = opp_agent.current_tile.tile_position.longitude
                state_opp_agents_positions[2 * flat + 1] = opp_agent.current_tile.tile_position.latitude
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
        for slot in range(game.MAX_ADVENTURERS):
            if slot < len(all_own_adventurers):
                windows.append(self.get_local_window(all_own_adventurers[slot]))
            else:
                windows.append(np.zeros(window_size))

        state = np.concatenate([
            *windows,
            [adventurer.player.vault_wealth],
            [adventurer.downwind_moves, adventurer.upwind_moves, adventurer.land_moves],
            [current_tile.tile_edges.upwind_clock_water, current_tile.tile_edges.upwind_anti_water,
             current_tile.tile_edges.downwind_clock_water, current_tile.tile_edges.downwind_anti_water],
            [current_tile.wind_direction.north, current_tile.wind_direction.east],
            preceding_positions,
            [own_adventurers.index(adventurer)],
            state_own_adventurers_wealth,
            state_own_adventurers_positions,
            state_own_agents_wealth,
            state_own_agents_positions,
            state_opp_vault_wealths,
            state_opp_adventurers_wealths,
            state_opp_adventurers_pirates,
            state_opp_adventurers_positions,
            state_opp_agents_wealths,
            state_opp_agents_dispossessed,
            state_opp_agents_positions,
        ]).astype(float)

        return state

    def remember(self, state, action, reward, next_state, done):
        '''Retains historic game state information for use in replay learning.'''
        self.memory.append((state, action, reward, next_state, done))

    def replay_training(self):
        '''Re-trains the model on a random batch of past experiences (experience replay).

        Based on a Bellman equation where the value of optimal subsequent play is estimated
        via a numerical approximation using the current model on future states.
        '''
        if len(self.memory) > self.REPLAY_BATCH_SIZE:
            batch = random.sample(self.memory, self.REPLAY_BATCH_SIZE)
        else:
            batch = list(self.memory)
        for state, action, reward, next_state, done in batch:
            updated_Q_value = reward
            if not done:
                # Use the move head (output 0) to estimate value of optimal continuation
                next_preds = self.model(np.array([next_state]))
                updated_Q_value += self.FUTURE_REWARD_DISCOUNT * np.amax(next_preds[0])
            current_preds = self.model(np.array([state]))
            # Build target output list, updating only the move head for the action taken
            # @TODO extend to update all decision heads independently
            targets = [np.array(p) for p in current_preds]
            targets[0][0][action] = updated_Q_value
            self.model.fit(np.array([state]), targets, epochs=1, verbose=0)

    def continue_turn(self, adventurer):
        '''Houses the AI's movement decisions during a single turn.

        Arguments
        adventurer is a Cartolan.Adventurer representing the token being moved.
        '''
        reward = 0

        if not getattr(self, 'active_training', False):
            self.whimsy_probability = 0
        else:
            self.whimsy_probability = 1.0 / (1.0 + adventurer.turns_moved * self.WHIMSY_REDUCTION_PER_TURN)
            self.mimicry_probability = 1.0 / (1.0 + adventurer.turns_moved * self.MIMICRY_REDUCTION_PER_TURN)

        while adventurer.turns_moved < adventurer.game.turn:
            state_old = self.get_state(adventurer)

            if random.random() < self.whimsy_probability:
                move_choice = random.randint(0, len(self.move_map) - 1)
                print("Randomly chose direction: " + self.move_map[move_choice])
            else:
                self.predicted_continuation_values = self.model(np.array([state_old]))
                move_choice = int(np.argmax(self.predicted_continuation_values[0]))
                print("ANN chose direction: " + self.move_map[move_choice])

            direction = self.move_map[move_choice]
            if direction == 'wait':
                adventurer.wait()
            else:
                adventurer.move(direction)

            state_new = self.get_state(adventurer)

            vault_wealth_increase = self.vault_wealth - self.best_vault_wealth
            if vault_wealth_increase > 0:
                reward += self.VAULT_INCREASE_REWARD * vault_wealth_increase / (
                    abs(adventurer.turns_moved - self.best_vault_turn) + 1)
                self.best_vault_wealth = self.vault_wealth
                self.best_vault_turn = adventurer.turns_moved

            # Similarly for this adventurer's chest wealth
            if adventurer not in self.best_chest_wealths:
                self.best_chest_wealths[adventurer] = 0
                self.best_chest_turns[adventurer] = 0
            chest_wealth_increase = adventurer.wealth - self.best_chest_wealths[adventurer]
            if chest_wealth_increase > 0:
                reward += self.CHEST_INCREASE_REWARD * chest_wealth_increase / (
                    abs(adventurer.turns_moved - self.best_chest_turns[adventurer]) + 1)
                self.best_chest_wealths[adventurer] = adventurer.wealth
                self.best_chest_turns[adventurer] = adventurer.turns_moved

            done = adventurer.game.game_over
            if done:
                # Apply terminal reward before remember() so the final experience
                # stored in the replay buffer includes the win/loss signal.
                if adventurer.game.winning_player == self:
                    reward += self.GAME_WIN_REWARD * adventurer.game.wealth_difference
                else:
                    reward -= self.GAME_WIN_REWARD
            self.remember(state_old, move_choice, reward, state_new, done)

            if getattr(self, 'active_training', False) and reward > 0:
                self.replay_training()
                self.model.save_weights(self.SAVED_MODEL_PATH)

        return True

    def check_trade(self, adventurer, tile):
        '''Gives the AI's decision whether to trade at a Wonder tile.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        tile is the Wonder tile being visited.
        '''
        if random.random() < self.whimsy_probability:
            trade = random.random() > 0.5
            print("Randomly chose trade: " + str(trade))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            trade = prediction[1][0][0] > 0.5  # output index 1 = trade_network
            print("ANN chose trade: " + str(trade))
        return trade

    def check_collect_wealth(self, adventurer, agent):
        '''Gives the AI's decision whether to collect wealth from an Agent.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        agent is the Agent token being visited.
        '''
        if random.random() < self.whimsy_probability:
            collect = random.random() > 0.5
            print("Randomly chose collect: " + str(collect))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            collect = prediction[3][0][0] > 0.5  # output index 3 = collect_network
            print("ANN chose collect: " + str(collect))
        return collect

    def check_rest(self, adventurer, agent):
        '''Gives the AI's decision whether to rest at an Agent.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        agent is the Agent token being visited.
        '''
        if random.random() < self.whimsy_probability:
            rest = random.random() > 0.5
            print("Randomly chose rest: " + str(rest))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            rest = prediction[2][0][0] > 0.5  # output index 2 = rest_network
            print("ANN chose rest: " + str(rest))
        return rest

    def check_bank_wealth(self, adventurer, report="Player is being asked whether to bank wealth"):
        '''Gives the AI's decision how much wealth to keep in the chest when banking at a city.

        Returns an int: the amount of wealth to retain in the chest (the rest is banked).

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        '''
        if random.random() < self.whimsy_probability:
            keep = random.randint(0, adventurer.wealth) if adventurer.wealth > 0 else 0
            print("Randomly chose to keep: " + str(keep))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            keep = max(0, min(int(prediction[7][0][0]), adventurer.wealth))  # output index 7 = bank_network
            print("ANN chose to keep: " + str(keep))
        return keep

    def check_buy_adventurer(self, adventurer, report="Player is being asked whether to buy an Adventurer"):
        '''Gives the AI's decision whether to recruit a new Adventurer when visiting a city.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        '''
        if random.random() < self.whimsy_probability:
            recruit = random.random() > 0.5
            print("Randomly chose recruit: " + str(recruit))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            recruit = prediction[8][0][0] > 0.5  # output index 8 = buy_adventurer_network
            print("ANN chose recruit: " + str(recruit))
        return recruit

    def check_place_agent(self, adventurer):
        '''Gives the AI's decision whether to place an Agent when discovering a new tile.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        '''
        if random.random() < self.whimsy_probability:
            place = random.random() > 0.5
            print("Randomly chose place agent: " + str(place))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            place = prediction[4][0][0] > 0.5  # output index 4 = place_network
            print("ANN chose place agent: " + str(place))
        return place

    def check_buy_agent(self, adventurer, report="Player has been offered to buy an agent by a city"):
        '''Gives the AI's decision whether to place an Agent on an existing tile from a city.

        Returns None while the ANN lacks awareness of the full play area.
        '''
        return None  # @TODO enable once play area map is included in state

    def check_move_agent(self, adventurer):
        '''Gives the AI's decision about which Agent to move when at the placement limit.

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
            attack = random.random() > 0.5
            print("Randomly chose attack adventurer: " + str(attack))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            attack = prediction[5][0][0] > 0.5  # output index 5 = attack_network
            print("ANN chose attack adventurer: " + str(attack))
        return attack

    def check_attack_agent(self, adventurer, agent):
        '''Gives the AI's decision whether to attack another player's Agent.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        agent is the opposing Agent on the tile.
        '''
        if random.random() < self.whimsy_probability:
            attack = random.random() > 0.5
            print("Randomly chose attack agent: " + str(attack))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            attack = prediction[5][0][0] > 0.5  # output index 5 = attack_network
            print("ANN chose attack agent: " + str(attack))
        return attack

    def check_restore_agent(self, adventurer, agent):
        '''Gives the AI's decision whether to restore a dispossessed Agent.

        Arguments
        adventurer is a Cartolan.Adventurer as the token for which a decision is needed.
        agent is the player's dispossessed Agent on the tile.
        '''
        if random.random() < self.whimsy_probability:
            restore = random.random() > 0.5
            print("Randomly chose restore: " + str(restore))
        else:
            prediction = self.model(np.array([self.get_state(adventurer)]))
            restore = prediction[6][0][0] > 0.5  # output index 6 = restore_network
            print("ANN chose restore: " + str(restore))
        return restore
