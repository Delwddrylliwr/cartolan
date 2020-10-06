from keras.optimizers import Adam
import keras
import random
import numpy
import pandas
from operator import add
import collections

#The artificial neural network state will need to be hard stored, rather than retraining each time the notebook is run

class PlayerFeedFwd(Player):
    def __init__(self, colour):
        super().__init__(colour)
        
        #Now for the AI-specific constant parameters
        self.VAULT_INCREASE_REWARD = 1
        self.CHEST_INCREASE_REWARD = 5
        self.GAME_WIN_REWARD = 100 #Significantly higher than the proxy rewards, because it's unclear they will lead to sensible long term winning strategies, although they might be positive milestone objectives
        self.FUTURE_REWARD_DISCOUNT = 0.9 #Exponential discount factor for future rewards, as used in the decomposition of the game into single time period decisions, giving rise to the recursive Bellman equation that the Neural Net approximates
        self.OPTIMISER_LEARNING_RATE = 0.0005
        self.WHIMSY_REDUCTION_PER_TURN = 0.1 #The rate at which random behaviour declines each turn, hyperbolically
        self.MIMICRY_REDUCTION_PER_TURN = 0.05 #The rate at which mimicing behaviour declines each turn, hyperbolically
        self.FIRST_LAYER_SIZE = 120
        self.SECOND_LAYER_SIZE = 120
        self.SAVED_MODEL_PATH = "/ann_models/"
        self.LOAD_OLD_MODEL = True
        self.MEMORY_SIZE = 2500
        self.REPLAY_BATCH_SIZE = 32
        
        #Various trackers of game history will be needed
        self.attack_history = [] #An attack history is needed to play Regular mode games
        self.best_vault_wealth = 0
        self.best_vault_turn = 0
        self.best_chest_wealths = [0] * game.MAX_ADVENTURERS
        self.best_chest_turns = [0] * game.MAX_ADVENTURERS
        
        #Other variables will be needed for the realisation of Q-learning
        self.short_memory = numpy.array([])
        self.whimsy_probability = 1 #The probability of performing a random action rather than that suggested by the ANN response function
        self.mimicry_probability = 1 #The probability of performaing an action as if a heuristical player rather than based on the ANN model
        self.player_to_mimic = None
        self.actual = []
        self.memory = collections.deque(self.MEMORY_SIZE)
        self.predicted_continuation_values = None
        
        #We'll translate network outputs into various decisions:
        self.move_map = {0:"self.move(n)", 1:"self.move(e)", 2:"self.move(s)", 3:"self.move(w)", 4:"self.wait()"}
        
        #@TODO it would make sense to keep track of game parameters themselves as part of the identity of the AI's long term memory, as otherwise state vectors will make no sense to it

    def build_network(self, game_type):
        '''Specifies the topology of the networks behind various decision models for the player.
        
        Arguments
        game is a Cartolan.Game from which game parameters can be read.
        '''
        #We'll use the same base layers for all decisions, to interpret the game situation, and then a different final layer for each
        state_input = keras.Input(shape=( # dimensions are, with oponents in order of play after self: 
                                          1 #, AI player's wealth, might need 32 bit int if game lasts a long time, although probably much less
                                          , 3 #, moves since resting (3xInt) only need 3 bits for 0-4
                                          , 4 #, current tile edges (4xBool)
                                          , 2 #, current tile wind direction (2xBool)
                                          , 6 #, preceding three tile positions (6xInt)
                                          , 1 #, Adventurer index (1xInt) only need 2 bits for 1-3
                                          , game_type.MAX_ADVENTURERS #, own wealth scores (3xInt) might need 32 bit int if game lasts a long time, although probably much less
                                          , 2*game_type.MAX_ADVENTURERS #, own adventurer positions (6xInt) only need 8 bits for -180-180
                                          , 5*game_type.MAX_AGENTS #, own agent wealth (5xInt)
                                          , 10*game_type.MAX_AGENTS #, own agent positions (10xInt)
                                          , 3 #, opponent Vault wealth
                                          , 3*game_type.MAX_ADVENTURERS #, opponent adventurer wealth scores (12xInt)
                                          , 9*game_type.MAX_ADVENTURERS #, opponent Adventurer pirate tokens (9xBool)
                                          , 3*2*game_type.MAX_ADVENTURERS #, opponent Adventurer positions (18xInt)
                                          , 3*game_type.MAX_AGENTS #, oponent agent wealth (15xInt)
                                          , 3*game_type.MAX_AGENTS #, opponent agents dispossessed status (15xBool)
                                          , 3*2*game_type.MAX_AGENTS #, opponent agent positions (30xInt)
                                         ) 
                                   , dtype = (int32, int8, bool, bool, int8, int8, int32, int8, int32, int8, int32, int32, bool, int8, int32, bool, int8) # data types as listed above
                                  ) 
        base_network = layers.Dense(output_dim=self.FIRST_LAYER_SIZE, activation='relu')(state_input)
        base_network = layers.Dropout(0.1)(base_network)
        base_network = layers.Dense(output_dim=self.SECOND_LAYER_SIZE, activation='relu')(base_network)
        base_network = layers.Dropout(0.1)(base_network)
        opt = Adam(self.OPTIMISER_LEARNING_RATE)
    
        #One output layer for deciding movement between the four cardinal compass directions and waiting in place
        move_network = layers.Dense(output_dim=5, activation='softmax')(base_network)
        #One output layer for deciding whether or not to trade at a given Wonder 
        trade_network = layers.Dense(output_dim=1, activation='sigmoid')(base_network)
        #One output layer for deciding whether or not to rest at a given Agent
        rest_network = layers.Dense(output_dim=1, activation='sigmoid')(base_network)
        #One output layer for deciding whether or not to collect wealth from a given Agent
        collect_network = layers.Dense(output_dim=1, activation='sigmoid')(base_network)
        #One output layer for deciding whether or not to place an Agent on a newly discovered tile 
        place_network = layers.Dense(output_dim=1, activation='sigmoid')(base_network)
        #One output layer for deciding whether or not to attack a given Adventurer or Agent 
        attack_network = layers.Dense(output_dim= 3*(game_type.MAX_ADVENTURERS + game_type.MAX_ADVENTURERS), activation='sigmoid')(base_network) #there will be a different attack decision for each opposing Adventurer and Agent to allow for pirate tokens and dispossessions
        #One output layer for deciding whether or not to restore a dispossessed Agent
        restore_network = layers.Dense(output_dim=1, activation='sigmoid')(base_network)
        #One output layer for deciding how much wealth to keep in the adventurers chest when banking the rest at a city - using exponential activation to allow for a subtle decision at low numbers
        bank_network = layers.Dense(output_dim=1, activation='exponential')(base_network)
        #One output layer for deciding whether or not to recruit an Adventurer from a city 
        buy_adventurer_network = layers.Dense(output_dim=1, activation='linear')(base_network) 
#         #One output layer for deciding whether or not to recruit an Agent from the Capital and the coordinates at which to place them # @TODO look into what activation function might be best for choosing a location in a grid
#         buy_agent_network = layers.Dense(output_dim=3, dtype=(int8) activation='linear')(base_network)
#         #One output layer for deciding whether to move an Agent if placing a new one with the maximum number already recruited, and the choice of Agent to move
#         move_agent_network = layers.Dense(output_dim=game.MAX_AGENTS+1, activation='softmax')(base_network)
        
        #Compile the combined model
        model = keras.Model(
            inputs=[state_input],
            outputs=[move_network, trade_network, rest_network, collect_network, place_network, attack_network, restore_network, bank_network, buy_adventurer_network
#                      , buy_agent_network, move_agent_network #with no awareness of the overall play area, there is no point giving the AI this option except to suplant opponents' dispossessed Agents @TODO
                    ],
        )
        
        #@TODO match models to game parameters
        #Import saved network parametrisation, rather than starting from scratch.
        if self.LOAD_OLD_MODEL:
            model.load(self.saved_models_path)
            print("Previous model loaded")
    
    
    def get_state(self, adventurer):
        '''Compiles information about the current game situation that feeds into the AI's learning
        
        Arguments
        adventurer is a Cartolan.Adventurer representing the game token for which the AI is making decisions
        '''
        
        #Shorten the reference to some key data
        current_tile = adventurer.current_tile
        own_adventurers = adventurer.player.adventurers
        own_agents = adventurer.player.agents
        players = adventurer.game.players
        game = adventurer.game
        
        #Compile a list of own adventurers' wealth
        state_own_adventurers_wealth = [0] * game.MAX_ADVENTURERS # Start out with a vector of zeroes, even if there isn't an Adventurer to represent: for the AI they will appear to hold no wealth until they exist
        #Compile a list of own adventurers' positions
        state_own_adventurers_positions = [0] * (2 * game.MAX_ADVENTURERS) # Start out with a vector of zeroes, even if there isn't an Adventurer to represent: for the AI they will appear to wait at the origin until they exist
        for own_adventurer in own_adventurers:
            # Overwrite zero with Chest wealth once adventurers have been brought into the game
            state_own_adventurers_wealth[own_adventurers.index(own_adventurer)] = own_adventurer.wealth
            # Overwrite zeroes with coordinates once adventurers have been brought into the game
            state_own_adventurers_positions[2 * own_adventurers.index(own_adventurer)] = own_adventurer.current_tile.tile_position.latitude
            state_own_adventurers_positions[2 * own_adventurers.index(own_adventurer) + 1] = own_adventurer.current_tile.tile_position.longitude
        
        #Compile a list of own agents' wealth
        state_own_agents_wealth = [0] * game.MAX_AGENTS # Start out with a vector of zeroes, even if there isn't an Adventurer to represent: for the AI they will appear to hold no wealth until they exist
        #Compile a list of own agents' positions
        state_own_agents_positions = [0] * (2 * game.MAX_AGENTS) # Start out with a vector of zeroes, even if there isn't an Adventurer to represent: for the AI they will appear to wait at the origin until they exist
        for own_agent in own_agents:
            # Overwrite zero with Chest wealth once adventurers have been brought into the game
            state_own_agents_wealth[own_agents.index(own_agent)] = own_agent.wealth
            # Overwrite zeroes with coordinates once adventurers have been brought into the game
            state_own_agents_positions[2 * own_agents.index(own_agents)] = own_agent.current_tile.tile_position.latitude
            state_own_agents_positions[2 * own_agents.index(own_agents) + 1] = own_agent.current_tile.tile_position.longitude
        
        #Compile a list of opponents' Vault wealths, listing opponents in the order they will play after this turn, to ease comparison for the AI (given that turn order doesn't seem to be a strong determinant of game position)
        # we're assuming that the AI can safely treat games with fewer opponents the same as with wealthless opponents (although behaviour can still respond to adventurer wealth) 
        state_opp_vault_wealths = [0] * 3 # Start out with a vector of zeroes, even if there isn't a Player to represent: for the AI they will appear to have no wealth: 
        #Compile a list of opponents' Adventurers' wealths, listing opponents in the order they will play after this turn, to ease comparison for the AI (given that turn order doesn't seem to be a strong determinant of game position)
        # we're assuming that the AI can safely treat Adventurers at the origin with no wealth as if they haven't been purchased yet, this may lead to some blips in behaviour as opponents get their adventurers to a city and bank
        state_opp_adventurers_wealths = [0] * (3 * game.MAX_ADVENTURERS) # Start out with a vector of zeroes, even if there isn't an Adventurer to represent: for the AI they will appear to have no wealth in their Chest until they exist: 
        #Compile a list of opponents' Adventurers' pirate statuses, listing opponents in the order they will play after this turn, to ease comparison for the AI (given that turn order doesn't seem to be a strong determinant of game position)
        state_opp_adventurers_pirates = [0] * (3 * game.MAX_ADVENTURERS) # Start out with a vector of zeroes, even if there isn't an Adventurer to represent: for the AI they will appear to not be pirates until they exist
        #Compile a list of opponents' Adventurers' positions, listing opponents in the order they will play after this turn, to ease comparison for the AI (given that turn order doesn't seem to be a strong determinant of game position)
        state_opp_adventurers_positions = [0] * (2 * 3 * game.MAX_ADVENTURERS) # Start out with a vector of zeroes, even if there isn't an Adventurer to represent: for the AI they will appear to wait at the origin until they exist
        #Compile a list of opponents' Agents' wealths, listing opponents in the order they will play after this turn, to ease comparison for the AI (given that turn order doesn't seem to be a strong determinant of game position)
        state_opp_agents_wealths = [0] * (3 * game.MAX_AGENTS) # Start out with a vector of zeroes, even if there isn't an Agent to represent: for the AI they will appear to have no wealth until they exist
        #Compile a list of opponents' Adventurers' pirate statuses, listing opponents in the order they will play after this turn, to ease comparison for the AI (given that turn order doesn't seem to be a strong determinant of game position)
        state_opp_agents_dispossessed = [0] * (3 * game.MAX_AGENTS) # Start out with a vector of zeroes, even if there isn't an Agent to represent: for the AI they will appear to not be dispossessed until they exist
        #Compile a list of opponents' Adventurers' positions, listing opponents in the order they will play after this turn, to ease comparison for the AI (given that turn order doesn't seem to be a strong determinant of game position)
        state_opp_agents_positions = [0] * (2 * 3 * game.MAX_AGENTS) # Start out with a vector of zeroes, even if there isn't an Agent to represent: for the AI they will appear to wait at the origin until they exist
        #Keep track of own index, so that other players' psoitions in play order can be judged
        own_index = players.index(self)
        opponent_index = 0
        if not len(players) == own_index:
            for later_opponent_index in range(own_index + 1, len(players)):
                # Overwrite zeroes with wealth scores, starting with opponents later in the play order - that is, playing more immediately after the AI
                state_opp_vault_wealths[opponent_index] = players[later_opponent_index].vault_wealth
                # Overwrite zeroes with wealth scores, pirate statuses, and positions, once adventurers have been brought into the game, starting with players later than the AI in play order
                opp_adventurers = players[later_opponent_index].adventurers
                for opp_adventurer in opp_adventurers:
                    opp_adventurer_index = opp_adventurers.index(opp_adventurer)
                    state_opp_adventurers_wealths[3 * opponent_index + opp_adventurer_index] = opp_adventurer.wealth
                    state_opp_adventurers_pirates[3 * opponent_index + opp_adventurer_index] = opp_adventurer.pirate_token
                    state_opp_adventurers_positions[2 * 3 * opponent_index + opp_adventurer_index] = opp_adventurer.current_tile.tile_position.latitude
                    state_opp_adventurers_positions[2 * 3 * opponent_index + opp_adventurer_index + 1] = opp_adventurer.current_tile.tile_position.longitude
                # Overwrite zeroes with wealth scores, dispossessed statuses, and positions once Agents have been brought into the game, starting with players later than the AI in play order
                opp_agents = players[later_opponent_index].agents
                for opp_agent in opp_agents:
                    opp_agent_index = opp_agents.index(opp_agent)
                    state_opp_agents_wealths[3 * opponent_index + opp_agent_index] = opp_agent.wealth
                    state_opp_agents_dispossessed[3 * opponent_index + opp_agent_index] = opp_agent.is_dispossessed
                    state_opp_agents_positions[2 * 3 * opponent_index + opp_agent_index] = opp_agent.current_tile.tile_position.latitude
                    state_opp_agents_positions[2 * 3 * opponent_index + opp_agent_index + 1] = opp_agent.current_tile.tile_position.longitude
                opponent_index += 1
        for earlier_opponent_index in range(0, own_index):
            # Overwrite zeroes with wealth scores, now for opponents earlier in the play order - that is, playing less immediately after the AI
            # Overwrite zeroes with coordinates once adventurers have been brought into the game, starting with players later than the AI in play order
            state_opp_vault_wealths[opponent_index] = players[earlier_opponent_index].vault_wealth
            # Overwrite zeroes with coordinates once adventurers have been brought into the game, now going through players earlier than the AI in play order
            opp_adventurers = players[earlier_opponent_index].adventurers
            for opp_adventurer in opp_adventurers:
                opp_adventurer_index = opp_adventurers.index(opp_adventurer)
                state_opp_adventurers_wealths[3 * opponent_index + opp_adventurer_index] = opp_adventurer.wealth
                state_opp_adventurers_pirates[3 * opponent_index + opp_adventurer_index] = opp_adventurer.pirate_token
                state_opp_adventurers_positions[2 * 3 * opponent_index + opp_adventurer_index] = opp_adventurer.current_tile.tile_position.latitude
                state_opp_adventurers_positions[2 * 3 * opponent_index + opp_adventurer_index + 1] = opp_adventurer.current_tile.tile_position.longitude
            # Overwrite zeroes with wealth scores, dispossessed statuses, and positions once Agents have been brought into the game, now for players earlier than the AI in play order
            opp_agents = players[later_opponent_index].agents
            for opp_agent in opp_agents:
                opp_agent_index = opp_agents.index(opp_agent)
                state_opp_agents_wealths[3 * opponent_index + opp_agent_index] = opp_agent.wealth
                state_opp_agents_dispossessed[3 * opponent_index + opp_agent_index] = opp_agent.is_nt_tile.tile_position.latitude
                state_opp_agents_positions[2 * 3 * opponent_index + opp_agent_index + 1] = opp_agent.current_tile.tile_position.longitude
            opponent_index += 1       
        
        
        state = [
              numpy.asarray([adventurer.player.vault_wealth]) #, AI player's wealth, might need 32 bit int if game lasts a long time, although probably much less
              , numpy.asarray([adventurer.downwind_moves, adventurer.upwind_moves, adventurer.land_moves]) #, moves since resting (3xInt) only need 3 bits for 0-4
              , numpy.asarray([current_tile.tile_edges.upwind_clock_water, current_tile.tile_edges.upwind_anti_water, current_tile.tile_edges.downwind_clock_water, current_tile.tile_edges.downwind_anti_water]) #, current tile edges (4xBool)
              , numpy.asarray([current_tile.wind_direction.north, current_tile.wind_direction.east]) #, current tile wind direction (2xBool)
              , 6 #, preceding three tile positions (6xInt)
              , numpy.asarray([own_adventurers.index(adventurer)]) #, Adventurer index (1xInt) only need 2 bits for 1-3
              , numpy.asarray(state_own_adventurers_wealth) #, own wealth scores (3xInt)
              , numpy.asarray(state_own_adventurers_positions) #, own adventurer positions (6xInt) treated as at the Capital (0,0) if they don't yet exist
              , numpy.asarray(state_own_agents_wealth) #, own agent wealth (5xInt) treated as 0 if they don't yet exist
              , numpy.asarray(state_own_agents_positions) #, own agent positions (10xInt)  treated as at the Capital (0,0) if they don't yet exist
              , numpy.asarray(state_opp_vault_wealths) #, opponent Vault wealth (3xInt)
              , numpy.asarray(state_opp_adventurers_wealths) #, opponent Adventurer wealth scores (9xInt)
              , numpy.asarray(state_opp_adventurers_pirates) #, opponent Adventurer pirate tokens (9xBool)
              , numpy.asarray(state_opp_adventurers_positions) #, opponent Adventurer positions (18xInt)
              , numpy.asarray(state_opp_agents_wealths) #, oponent agent wealth (15xInt)
              , numpy.asarray(state_opp_agents_dispossessed) #, opponent agents dispossessed status (15xBool)
              , numpy.asarray(state_opp_agents_positions) #, opponent agent positions (30xInt)
        ]
        
        return state
    
    def remember(self, state, action, reward, next_state, done):
        '''Retains historic game state information for use in replay learning'''
        action = [self.move, self.trade, self.rest, self.collect, self. ]
        self.memory.append((state, action, reward, next_state, done))

    def replay_training(self):
        '''Re-trains the neural network model on past events.
        
        Based on a Bellman equation for the game, where the Value of optimal subsequent play is estimated (and implicitly a policy for how to play) via a 
        numerical approximation in proportion to the reward earned and the current estimate of future rewards earned based on sub-optimal current policy.
        '''
        import random
        #Subset the memory if it exceeds the batch size
        if len(self.memory) > self.REPLAY_BATCH_SIZE:
            batch = random.sample(self.memory, self.REPLAY_BATCH_SIZE)
        else:
            batch = self.memory
        for state, action, reward, next_state, done in batch:
            updated_Q_value = reward
            if not done:
                updated_Q_value += self.FUTURE_REWARD_DISCOUNT * np.amax(self.model(next_state)) # future value of playing out the game after the immediate decision is estimated by the current model on the future state as recorded
            updated_Q_values = self.model(state) # estimated future values of playing out the game under each possible action choice
            # @TODO extend the below to deal with a list of outputs for each of the different output sets
            updated_Q_values[0][np.argmax(action)] = updated_Q_value # replace the future value for the action that was taken with what the current model would now estimate
            self.model.fit(np.array([state]), updated_Q_values, epochs=1, verbose=0)

#     def train_short_memory(self, state, action, reward, next_state, done):
#         '''Updates neural network weight parameters during play to more optimally represent a policy for maximising rewards.
        
#         Based on a Bellman equation for the game, where the Value of optimal susequent play is estimated via a numerical 
#         approximation in proportion to the reward earned and the current estimate of future rewards earned based on sub-optimal current policy.
#         '''
#         #While the game is still in progress, the Bellman value function is approximated by the latest reward training is actual plus expected
#         if not done:
#             target = reward + self.FUTURE_REWARD_DISCOUNT * np.amax(self.model.predict(next_state.reshape((1, 11)))[0]) 
#         else:
#             target = reward
#         target_f = self.model(state)
#         target_f[0][np.argmax(action)] = target
#         self.model.fit(state.reshape((1, 11)), target_f, epochs=1, verbose=0)
    
    def continue_turn(self, adventurer):        
        '''Houses the AI's movement decisions during a single turn.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        import random
        
        #Reset the reward for this move
        reward = 0
        
        #Set the degree of randomness to the AI's behaviour, which will help it explore the space of response functions
        if not params['train']:
            self.whimsy_probability = 0
        else:
            # The randomness of actions will decline as the game progresses, to hopefully settle on optimal behaviour as in simulated annealing
            self.whimsy_probability = 1.0/(1.0 + adventurer.turns_moved * self.WHIMSY_REDUCTION_PER_TURN)
            self.mimicry_probability = 1.0/(1.0 + adventurer.turns_moved * self.MIMICRY_REDUCTION_PER_TURN)
        
        #Move while moves are still available
        while adventurer.turns_moved < adventurer.game.turn:
            #Update the state after the preceding move
            state_old = self.get_state(adventurer)
            
            # perform random actions based on whimsicality, or choose the action based on the ANN
            if random.random() < self.whimsy_probability:
                move_choice = random.randint(0, len(self.move_map))
                move = self.move_map[self.move_map.keys()[move_choice]]
                print("Randomly chose a move of "+move)
#             elif random.random() < self.mimicry_probability:
#                     #@TODO as well as random actions, have the AI play like one of the heuristical players periodically
#                     #@TODO will need to recover the moves that were made while mimicking the heuristical player
            else:
                #Suggest best action based on the old state
                self.predicted_continuation_values = self.model(state_old)
                move_choice = np.argmax(self.predicted_continuation_values[0]) #The final layer for movement is captured in the first output of the model
                move = self.move_map[self.move_map.keys()[move_choice]]
                print("The ANN chose a move of "+move)

            #Get new state, after all of the subsequent trading/placing/attacking decisions will have been made as part of the call to the Adventurer's .move method
            eval(move)
            self.move = move_choice #Record the move made so that it can be included in the memory
            state_new = self.get_state(adventurer)

            #Check for an increase in the greatest vault wealth attained so far and reward discounted by how long it took to achieve this increase
            vault_wealth_increase = self.vault_wealth - self.best_vault_wealth
            if vault_wealth_increase > 0:
                reward += self.VAULT_INCREASE_REWARD * vault_wealth_increase / (abs(adventurer.turns_moved - self.best_vault_turn)+1)
                #Remember the current Vault wealth for future comparison of gains
                self.best_vault_wealth = self.vault_wealth
                self.best_vault_turn = adventurer.turns_moved
                #As the Vault wealth increasing now will mean this Adventurer has banked it, reset the expectation for the Adventurer
            Similarly for this Adventurer
            chest_wealth_increase = adventurer.wealth - self.best_chest_wealths[self.adventurers.index(adventurer)]
            if chest_wealth_increase > 0:
                reward += self.CHEST_INCREASE_REWARD * chest_wealth_increase / (abs(adventurer.turns_moved - self.best_chest_turns[self.adventurers.index(adventurer)])+1)
                #Remember the current Chest wealth for future comparison of gains
                self.best_chest_wealths[self.adventurers.index(adventurer)] = adventurer.wealth
                self.best_chest_turns[self.adventurers.index(adventurer)] = adventurer.turns_moved
            
            #Record the current circumstances for use in replay learning when a positive state is attained
            self.remember(state_old, reward, state_new)
            
            #Check win conditions and reward considerably more than the proxies if victorious
            if adventurer.game.game_over:
                if adventurer.game.winning_player == self:
                    reward += self.GAME_WIN_REWARD * adventurer.game.wealth_difference
            
            #Use the positive reward to estimate long term value and learn 
            if self.active_training and reward > 0:
                #Use replay memory to reinforce everything learned this particular game, given that it might have ultimately contributed to the victory
                self.replay_training(self.memory, self.replay_batch_size)
                #Retain the revised parameters
                self.model.save_weights(weights_path)

        return True
    
    def check_trade(self, adventurer, tile):
        '''Gives the AI's decision whether to trade at a Wonder tile.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        import random
        
        # perform random actions based on whimsicality, or choose the action based on the ANN
        if random.random() < self.whimsy_probability:
            trade = (random.random() > 0.5)
            trade_choice = 
            print("Randomly chose a trade response of "+str(trade))
#             elif random.random() < self.mimicry_probability:
#                     #@TODO as well as random actions, have the AI play like one of the heuristical players periodically
#                     #@TODO will need to recover the moves that were made while mimicking the heuristical player
        else:
            #Suggest best action based on the old state
            self.predicted_continuation_values = self.model(state_old)
            trade_choice = np.argmax(self.predicted_continuation_values[0]) #The final layer for movement is captured in the first output of the model
            move = self.move_map[self.move_map.keys()[move_choice]]
            print("The ANN chose a move of "+move)# perform random actions based on whimsicality, or choose the action based on the ANN
        if random.random() < self.whimsy_probability:
            trade = (random.random() > 0.5)
            print("Randomly chose a trade response of "+str(trade))
        else:
            #Suggest best action based on the old state
            prediction = self.trade_model(self.get_state(adventurer))
            trade = (np.argmax(prediction[0]) > 0.5)
            print("The ANN chose a trade response of "+str(trade))
        self.trade = trade
        return trade
    
    def check_collect_wealth(self, agent):
        '''Gives the AI's decision whether to collect wealth from an Agent.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        import random
        
        # perform random actions based on whimsicality, or choose the action based on the ANN
        if random.random() < self.whimsy_probability:
            collect = (random.random() > 0.5)
            print("Randomly chose a collect response of "+str(collect))
        else:
            #Suggest best action based on the old state
            prediction = self.collect_model(self.get_state(adventurer))
            collect = (np.argmax(prediction[0]) > 0.5)
            print("The ANN chose a collect response of "+str(collect))
        self.collect = collect
        return collect
    
    def check_rest(self, adventurer, agent):
        '''Gives the AI's decision whether to rest at an Agent.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        import random
        
        # perform random actions based on whimsicality, or choose the action based on the ANN
        if random.random() < self.whimsy_probability:
            rest = (random.random() > 0.5)
            print("Randomly rest a collect response of "+str(rest))
        else:
            #Suggest best action based on the old state
            prediction = self.rest_model(self.get_state(adventurer))
            rest = (np.argmax(prediction[0]) > 0.5)
            print("The ANN chose a rest response of "+str(rest))
        self.rest = rest
        return rest
        
    
    def check_bank_wealth(self, adventurer, report="Player is being asked whether to bank wealth"):
        '''Gives the AI's decision how much wealth to deposit when visiting a city.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        import random
        
        # perform random actions based on whimsicality, or choose the action based on the ANN
        if random.random() < self.whimsy_probability:
            collect = (random.random() > 0.5)
            print("Randomly chose a collect response of "+str(collect))
        else:
            #Suggest best action based on the old state
            prediction = self.collect_model(self.get_state(adventurer))
            collect = (np.argmax(prediction[0]) > 0.5)
            print("The ANN chose a collect response of "+str(collect))
        self.collect = collect
        return collect
    
    def check_buy_adventurer(self, adventurer, report="Player is being asked whether to buy an Adventurer"):
        '''Gives the AI's decision whether to buy another Adventurer when visiting a city.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        return recruit
    
    def check_place_agent(self, adventurer):
        '''Gives the AI's decision whether to place an Agent when discovering a new tile.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        return place
    
    def check_buy_agent(self, adventurer, report="Player has been offered to buy an agent by a city"):
        '''Gives the AI's decision whether to place an Agent on an existing tile while visiting a city.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        return None # While the AI is not aware of the tiles across the play area, there is no point in trying to give any decision here @TODO except perhaps to usurp opponents' Agents
    
    def check_move_agent(self, adventurer):
        '''Gives the AI's decision about what Agent to move if placing an Agent when it has already reached the limit.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        return None # While the AI is not aware of the tiles across the play area, there is no point in trying to give any decision here @TODO except perhaps to usurp opponents' Agents
    
    def check_attack_adventurer(self, adventurer, other_adventurer):
        '''Gives the AI's decision whether to attack another player's Adventurer when on the same tile.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        return attack
    
    def check_attack_agent(self, adventurer, agent):
        '''Gives the AI's decision to attach another player's Agent when on its tile.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        return attack
    
    def check_restore_agent(self, adventurer, agent):
        '''Gives the AI's decision to restore a dispossessed Agent when the Adventurer visits its tile.
        
        Arguments
        adventurer takes a Cartolan.Adventurer as the game token for which a decision is needed.
        '''
        return restore