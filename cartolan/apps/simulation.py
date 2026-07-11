'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import sys
import os
from matplotlib import pyplot
import pandas
import random
from cartolan.core.setup import create_game
from cartolan.editions.modes import GameBeginner, GameRegular, GameAdvanced
from cartolan.players.heuristical import PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter
from cartolan.players.heuristical import PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter, PlayerRegularPirate
from cartolan.players.ann import PlayerFeedFwd
from cartolan.core.tiles import Tile, WindDirection, TileEdges
from cartolan.ui.static_visuals import PlayAreaVisualisation, PlayStatsVisualisation

#Default parameters
GAME_MODE = "Beginner"
MOVEMENT_RULE = "initial" #"budgetted"
EXPLORATION_RULE = "continuous" #"clockwise" #,
MYTHICAL_CITY = True
NUM_PLAYERS = 2
NUM_GAMES = 1000
# Option sets and corresponding information
GAME_MODES = { 'Beginner':{'game_type':GameBeginner, 'player_set':{"blue":PlayerBeginnerExplorer
                                                                        , "red":PlayerBeginnerTrader
                                                                        , "yellow":PlayerBeginnerRouter
                                                                  , "orange":PlayerBeginnerTrader}}
                  , 'Regular':{'game_type':GameRegular, 'player_set':{"blue":PlayerRegularExplorer
                                                                        , "red":PlayerRegularTrader
                                                                        , "yellow":PlayerRegularRouter
                                                                      , "orange":PlayerRegularPirate}}
                  }
MOVEMENT_RULES = ['initial', 'budgetted']
EXPLORATION_RULES = ['clockwise', 'continuous']
NUM_PLAYERS_OPTIONS = [2, 3, 4]

def append_row(dataframe, row):
    '''Appends a dict as a row, replacing pandas.DataFrame.append (removed in pandas 2.0)'''
    return pandas.concat([dataframe, pandas.DataFrame([row])], ignore_index=True)

#First some global functions to set up the game area
class Simulations():
    """Run simulations of the game Cartolan."""

    def __init__(self, num_games=NUM_GAMES):
        self.game_mode = GAME_MODE
        self.movement_rule = MOVEMENT_RULE
        self.exploration_rule = EXPLORATION_RULE
        self.mythical_city = MYTHICAL_CITY
        self.num_players = NUM_PLAYERS
        self.num_games = num_games
        self.game_modes = GAME_MODES

    def click_run_sims(self, event):
        self.run_sims()

    def select_mode(self, label):
        self.game_mode = label

    def select_movement(self, label):
        self.movement_rule = label

    def select_exploration(self, label):
        self.exploration_rule = label

    def set_num_players(self, label):
        self.num_players = int(label)

    def set_num_sims(self, value):
        self.num_games = int(value)

    def setup_players(self):
        players = []
#             num_players = random.choice(num_players_options)
        player_colours = random.sample(list(self.game_modes[self.game_mode]["player_set"]),self.num_players)
        for player_colour in player_colours:
            #player_colour = random.choice(player_set)
            players.append(self.game_modes[self.game_mode]["player_set"][player_colour](player_colour))
        return players


    def run_sims(self):
        '''Method to run through a series of simulations, triggered by a UI button press'''
        #determine logging
        # stdout_backup = sys.stdout
#         sys.stdout = open(os.devnull, 'w')
        os.makedirs("./logs", exist_ok=True)
        sys.stdout = open("./logs/cartolan_log.txt", 'w')
        # sys.stdout = sys.__stdout__

        #data to collect from each simulation
        self.sim_stats = pandas.DataFrame(columns = ["simulation_id", "num_players", "win_type", "turns"
                                                , "remaining_water_tiles"
                                                , "remaining_land_tiles"
                                                , "total_wealth_final", "max_wealth_final", "wealth_difference_final"
                                                , "winning_player_type", "winning_player_order", "winning_player_route"
                                                , "winning_player_agents"
                                                , "winning_player_adventurers"
                                                , "exploration_attempts", "failed_explorations"
                                                , "wealth_p1", "wealth_p2", "wealth_p3", "wealth_p4"
                                                , "num_adventurers_p1", "num_adventurers_p2"
                                                , "num_adventurers_p3", "num_adventurers_p4"
                                                , "num_agents_p1", "num_agents_p2", "num_agents_p3", "num_agents_p4"
                                                , "avg_route_p1", "avg_route_p2", "avg_route_p3", "avg_route_p4"
                                                , "play_area", "players"])
        play_areas = {}
        player_sets = {}

        #retain the leftover tile distributions
        remaining_tile_edges = []

        #Function to collect average route lengths across a player's adventurers
        def avg_route_length(player, game):
            avg_route_length = 0
            for adventurer in game.adventurers[player]:
                avg_route_length += len(adventurer.route)
            return avg_route_length/len(game.adventurers[player])

        # We have arrived! Time for the actual outcomes
        #@TODO multithread this: https://realpython.com/intro-to-python-threading/#starting-a-thread
        for sim_id in range(0, self.num_games):
            print("")
            #Instantiate players
            players = self.setup_players()

            #Instantiate a game
            if self.mythical_city:
                print("Setting up a "+self.game_mode+"-mode game, with "+self.movement_rule+" movement rules, and "
                  +self.exploration_rule+" exploration rules, and a mythical city")
            else:
                print("Setting up a "+self.game_mode+"-mode game, with "+self.movement_rule+" movement rules, and "
                  +self.exploration_rule+" exploration rules, and no mythical city")
            game = create_game(self.game_modes[self.game_mode]["game_type"], players,
                               self.movement_rule, self.exploration_rule, self.mythical_city)

            #run the game
            print("Starting simulation #"+str(sim_id)+" of "+self.game_mode+"-mode Cartolan, with " +str(self.num_players)+ " players")
            game.start_game()

            #record stats
            def player_strip(player_type):
                '''Reduces the name of a player type down '''
                name = player_type.__name__
                if "Beginner" in name:
                    return name[name.find("Beginner")+len("Beginner"):]
                elif "Regular" in name:
                    return name[name.find("Regular")+len("Regular"):]
                else:
                    return name[name.find("Player")+len("Player"):]

            if game.wealth_difference > 0 and self.num_players ==2:
                self.sim_stats = append_row(self.sim_stats, {"simulation_id":sim_id, "num_players":self.num_players
                                    , "win_type":game.win_type, "turns":game.turn
                                    , "remaining_water_tiles":len(game.tile_piles["water"].tiles)+len(game.discard_piles["water"].tiles)
                                    , "remaining_land_tiles":len(game.tile_piles["land"].tiles)+len(game.discard_piles["land"].tiles)
                                    , "total_wealth_final":game.total_vault_wealth
                                    , "max_wealth_final":game.max_wealth
                                    , "wealth_difference_final":game.wealth_difference
                                    , "winning_player_type":player_strip(type(game.winning_player))
                                    , "winning_player_order":game.players.index(game.winning_player)+1
                                    , "winning_player_route":avg_route_length(game.winning_player, game)
                                    , "winning_player_agents":len(game.agents[game.winning_player])
                                    , "winning_player_adventurers":len(game.adventurers[game.winning_player])
                                    , "exploration_attempts":game.exploration_attempts
                                    , "failed_explorations":game.num_failed_explorations
                                    , "wealth_p1":game.player_wealths[game.players[0]]
                                    , "wealth_p2":game.player_wealths[game.players[1]]
                                    , "num_adventurers_p1":len(game.adventurers[players[0]])
                                    , "num_adventurers_p2":len(game.adventurers[players[1]])
                                    , "num_agents_p1":len(game.agents[players[0]])
                                    , "num_agents_p2":len(game.agents[players[1]])
                                    , "avg_route_p1":avg_route_length(players[0], game)
                                    , "avg_route_p2":avg_route_length(players[1], game)
                                              })
            elif game.wealth_difference > 0 and self.num_players ==3:
                self.sim_stats = append_row(self.sim_stats, {"simulation_id":sim_id, "num_players":self.num_players
                                    , "win_type":game.win_type, "turns":game.turn
                                    , "remaining_water_tiles":len(game.tile_piles["water"].tiles)+len(game.discard_piles["water"].tiles)
                                    , "remaining_land_tiles":len(game.tile_piles["land"].tiles)+len(game.discard_piles["land"].tiles)
                                    , "total_wealth_final":game.total_vault_wealth
                                    , "max_wealth_final":game.max_wealth
                                    , "wealth_difference_final":game.wealth_difference
                                    , "winning_player_type":player_strip(type(game.winning_player))
                                    , "winning_player_order":game.players.index(game.winning_player)+1
                                    , "winning_player_route":avg_route_length(game.winning_player, game)
                                    , "winning_player_agents":len(game.agents[game.winning_player])
                                    , "winning_player_adventurers":len(game.adventurers[game.winning_player])
                                    , "exploration_attempts":game.exploration_attempts
                                    , "failed_explorations":game.num_failed_explorations
                                    , "wealth_p1":game.player_wealths[game.players[0]]
                                    , "wealth_p2":game.player_wealths[game.players[1]]
                                    , "wealth_p3":game.player_wealths[game.players[2]]
                                    , "num_adventurers_p1":len(game.adventurers[game.players[0]])
                                    , "num_adventurers_p2":len(game.adventurers[game.players[1]])
                                    , "num_adventurers_p3":len(game.adventurers[game.players[2]])
                                    , "num_agents_p1":len(game.agents[game.players[0]])
                                    , "num_agents_p2":len(game.agents[game.players[1]])
                                    , "num_agents_p3":len(game.agents[game.players[2]])
                                    , "avg_route_p1":avg_route_length(players[0], game)
                                    , "avg_route_p2":avg_route_length(players[1], game)
                                    , "avg_route_p3":avg_route_length(players[2], game)
                                              })
            elif game.wealth_difference > 0 and self.num_players ==4:
                self.sim_stats = append_row(self.sim_stats, {"simulation_id":sim_id, "num_players":self.num_players
                                    , "win_type":game.win_type, "turns":game.turn
                                    , "remaining_water_tiles":len(game.tile_piles["water"].tiles)+len(game.discard_piles["water"].tiles)
                                    , "remaining_land_tiles":len(game.tile_piles["land"].tiles)+len(game.discard_piles["land"].tiles)
                                    , "total_wealth_final":game.total_vault_wealth
                                    , "max_wealth_final":game.max_wealth
                                    , "wealth_difference_final":game.wealth_difference
                                    , "winning_player_type":player_strip(type(game.winning_player))
                                    , "winning_player_order":game.players.index(game.winning_player)+1
                                    , "winning_player_route":avg_route_length(game.winning_player, game)
                                    , "winning_player_agents":len(game.agents[game.winning_player])
                                    , "winning_player_adventurers":len(game.adventurers[game.winning_player])
                                    , "exploration_attempts":game.exploration_attempts
                                    , "failed_explorations":game.num_failed_explorations
                                    , "wealth_p1":game.player_wealths[game.players[0]], "wealth_p2":game.player_wealths[game.players[1]]
                                    , "wealth_p3":game.player_wealths[game.players[2]], "wealth_p4":game.player_wealths[game.players[3]]
                                    , "num_adventurers_p1":len(game.adventurers[game.players[0]])
                                    , "num_adventurers_p2":len(game.adventurers[game.players[1]])
                                    , "num_adventurers_p3":len(game.adventurers[game.players[2]])
                                    , "num_adventurers_p4":len(game.adventurers[game.players[3]])
                                    , "num_agents_p1":len(game.agents[game.players[0]])
                                    , "num_agents_p2":len(game.agents[game.players[1]])
                                    , "num_agents_p3":len(game.agents[game.players[2]])
                                    , "num_agents_p4":len(game.agents[game.players[3]])
                                    , "avg_route_p1":avg_route_length(players[0], game)
                                    , "avg_route_p2":avg_route_length(players[1], game)
                                    , "avg_route_p3":avg_route_length(players[2], game)
                                    , "avg_route_p4":avg_route_length(players[3], game)
                                              })
            play_areas[sim_id] = game.play_area
            player_sets[sim_id] = game.players

            for tile_pile in game.tile_piles.values():
                for tile in tile_pile.tiles:
                    tile_edges = tile.tile_edges
                    tile_edges_string = ""
                    if tile_edges.upwind_clock_water:
                        tile_edges_string += "Water"
                    else:
                        tile_edges_string += "Land"
                    if tile_edges.upwind_anti_water:
                        tile_edges_string += "Water"
                    else:
                        tile_edges_string += "Land"
                    if tile_edges.downwind_clock_water:
                        tile_edges_string += "Water"
                    else:
                        tile_edges_string += "Land"
                    if tile_edges.downwind_anti_water:
                        tile_edges_string += "Water"
                    else:
                        tile_edges_string += "Land"
                    remaining_tile_edges.append(tile_edges_string)


        # Make sure that graphical outputs go here
#         sys.stdout = stdout_backup
        # Let's compare the performance of winning players to others
        play_stats_visualisation = PlayStatsVisualisation(self.sim_stats)
        play_stats_visualisation.win_type_comparison()
        play_stats_visualisation.turns_to_win()
        play_stats_visualisation.player_type_comparison()
        play_stats_visualisation.player_order_comparison()
        play_stats_visualisation.wealth_comparison()
        # play_stats_visualisation.wealth_variance_comparison()
        play_stats_visualisation.route_comparison()
        play_stats_visualisation.token_comparison()
        play_stats_visualisation.tile_comparison()
#         play_stats_visualisation.discards_comparison()
        play_stats_visualisation.remaining_tiles_distribution(remaining_tile_edges)
        play_stats_visualisation.fig.tight_layout(pad=2.0)


        def prep_visuals(sim_id_to_vis, title):
            play_area_to_vis = play_areas[sim_id_to_vis]
            #work out the ideal dimensions for the visualisation
            h_dimension = max(play_area_to_vis.keys())-min(play_area_to_vis.keys())
            h_origin = abs(min(play_area_to_vis.keys()))
            max_latitude = 0
            min_latitude = 0
            v_dimension = 0
            for longitude in play_area_to_vis:
                if max(play_area_to_vis[longitude].keys()) > max_latitude:
                    max_latitude = max(play_area_to_vis[longitude].keys())
                if min(play_area_to_vis[longitude].keys()) < min_latitude:
                    min_latitude = min(play_area_to_vis[longitude].keys())
            v_dimension = max_latitude - min_latitude
            v_origin = abs(min_latitude)
            dimensions = [h_dimension + 1, v_dimension + 1]
            origin = [h_origin, v_origin]
            #render the play area and routes
            game_vis = PlayAreaVisualisation(dimensions, origin, title)
#             game_vis_med_wealth_difference.draw_play_area(play_area_to_vis, play_area_to_vis)
            game_vis.draw_play_area(play_area_to_vis)
            #@TODO earlier agent positions seem to be ignored
            game_vis.draw_tokens(player_sets[sim_id_to_vis])
            game_vis.draw_routes(player_sets[sim_id_to_vis])
            print("Determined that the dimensions for the "+title+" are "+ str(h_dimension)+", "+str(v_dimension))
            print("Determined that the origin positions for the "+title+" are "+ str(h_origin)+", "+str(v_origin))


        # Let's look at the final layout and paths of the game with the median wealth difference, if one exists:
        if self.sim_stats["wealth_difference_final"].median() in self.sim_stats["wealth_difference_final"].values:
            sim_id_med_wealth_difference = self.sim_stats[self.sim_stats["wealth_difference_final"]
                                                  == self.sim_stats["wealth_difference_final"].median()]["simulation_id"].values[0]
            prep_visuals(sim_id_med_wealth_difference, "How the median wealth difference game progressed")

        # Let's also look at the games with maximum and minimum wealth differences
        sim_id_max_wealth_difference = self.sim_stats[self.sim_stats["wealth_difference_final"]
                                                  == self.sim_stats["wealth_difference_final"].max()]["simulation_id"].values[0]
        prep_visuals(sim_id_max_wealth_difference, "How the maximum wealth difference game progressed")

        sim_id_min_wealth_difference = self.sim_stats[self.sim_stats["wealth_difference_final"]
                                                  == self.sim_stats["wealth_difference_final"].min()]["simulation_id"].values[0]
        prep_visuals(sim_id_min_wealth_difference, "How the minimum wealth difference game progressed")

        pyplot.show()


class AISimulations(Simulations):
    '''Runs training simulations in which a PlayerFeedFwd agent plays against heuristical
    opponents, learning via DQN experience replay across many games.

    Model weights and replay memory persist across games; only game-specific tracking
    state is reset between games. Use the parent Simulations.run_sims() with a trained
    model to collect detailed play statistics and visualisations.
    '''
    AI_PLAYER_COLOURS = ["green", "brown", "pink", "purple"]

    def __init__(self, num_games=NUM_GAMES, num_feed_fwd=1, verbose=False):
        super().__init__(num_games)
        self.num_feed_fwd = num_feed_fwd  # number of AI players in each game; must be < num_players
        self.verbose = verbose  # if False, suppresses per-move output and prints one line per game

        # Instantiate AI players once — model weights and replay memory span all games
        self.feed_fwd_players = []
        for ai_idx in range(self.num_feed_fwd):
            ai_player = PlayerFeedFwd(self.AI_PLAYER_COLOURS[ai_idx])
            ai_player.active_training = True
            ai_player.build_network(self.game_modes[self.game_mode]["game_type"])
            self.feed_fwd_players.append(ai_player)

    def setup_players(self):
        '''Returns a fresh player list for one game, resetting per-game AI state.

        Model weights and replay memory are intentionally preserved so the agent
        continues learning across games.
        '''
        self.num_players = random.choice(NUM_PLAYERS_OPTIONS)
        players = []
        for ai_player in self.feed_fwd_players:
            # Reset game-specific tracking; model weights and memory persist
            ai_player.vault_wealth = 0
            ai_player.attack_history = []
            ai_player.best_vault_wealth = 0
            ai_player.best_vault_turn = 0
            ai_player.best_chest_wealths = {}
            ai_player.best_chest_turns = {}
            ai_player.whimsy_probability = 1  # restart from full exploration each game
            players.append(ai_player)

        # Fill remaining seats with a random selection of heuristical opponents
        opponent_colours = random.sample(
            list(self.game_modes[self.game_mode]["player_set"]),
            self.num_players - len(players),
        )
        opponents = [
            self.game_modes[self.game_mode]["player_set"][colour](colour)
            for colour in opponent_colours
        ]

        # Assign a random opponent as the mimic target for each AI player
        for ai_player in self.feed_fwd_players:
            ai_player.player_to_mimic = random.choice(opponents) if opponents else None

        players.extend(opponents)
        return players

    def run_sims(self):
        '''Runs training games and calls replay_training() after every game.

        In-game training (triggered inside continue_turn on positive reward) is
        supplemented by a full end-of-game replay pass so the model also learns
        from loss experiences and from low-reward stretches that never triggered
        mid-game training.

        When verbose=False (default), all per-move output is suppressed and a
        single summary line is printed to the real stdout for each game.
        '''
        real_stdout = sys.__stdout__
        devnull = open(os.devnull, 'w')

        for sim_id in range(self.num_games):
            players = self.setup_players()
            game = create_game(
                self.game_modes[self.game_mode]["game_type"],
                players,
                self.movement_rule,
                self.exploration_rule,
                self.mythical_city,
            )

            if not self.verbose:
                sys.stdout = devnull
            game.start_game()
            sys.stdout = real_stdout

            # End-of-game training pass: replays the full memory buffer regardless
            # of whether any in-game positive reward triggered training during play.
            summary_parts = [f"game {sim_id + 1}/{self.num_games}  turns={game.turn}  #players={self.num_players}\n"]
            for ai_player in self.feed_fwd_players:
                result = "WIN" if game.winning_player == ai_player else "LOSS"
                vault = game.player_wealths.get(ai_player, 0)
                epsilon = max(ai_player.EPSILON_MIN,
                              ai_player.EPSILON_DECAY_PER_GAME ** ai_player.games_played)
                mimicry = max(ai_player.MIMICRY_FLOOR,
                              ai_player.MIMICRY_DECAY_PER_GAME ** ai_player.games_played)
                mimic_name = getattr(ai_player.player_to_mimic, 'name', 'none')
                summary_parts.append(
                    f"{ai_player.name}: {result} vault={vault}"
                    f" gap={game.wealth_difference} mem={len(ai_player.memory)}"
                    f" epsilon={epsilon:.3f} mu={mimicry:.3f}({mimic_name})\n"
                )
                if len(ai_player.memory) > 0:
                    if not self.verbose:
                        sys.stdout = devnull
                    ai_player.replay_training()
                    sys.stdout = real_stdout
                ai_player.games_played += 1
                ai_player.model.save_weights(ai_player.SAVED_MODEL_PATH)

            print("  ".join(summary_parts))

        devnull.close()
        print(f"Training complete: {self.num_games} games, {self.num_feed_fwd} AI player(s)")


# class InteractiveAISimulation(InteractiveSimulation):
#     @TODO wire up once the pygame-based InteractiveSimulation frontend is in place.
#     Follows the same pattern as AISimulations: build_network once in __init__,
#     reset per-game state in setup_players, call replay_training() at end of each game.
