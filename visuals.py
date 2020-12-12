import matplotlib.image as mpimg # for importing tile images
import math
import tkinter
import pandas
from matplotlib import pyplot # for plotting the tiles in a grid
from scipy import ndimage # for rotating tiles
import numpy
import pygame
import sys
import json
from types import SimpleNamespace
from PodSixNet.Connection import ConnectionListener, connection
from time import sleep
from base import Game, Player, CityTile, Tile, WindDirection, TileEdges
from beginner import AdventurerBeginner, AgentBeginner
from regular import DisasterTile, AdventurerRegular, AgentRegular
from game import GameBeginner, GameRegular, GameAdvanced
from players_human import PlayerHuman
from players_heuristical import PlayerRegularExplorer

     
class PlayAreaVisualisation:
    '''A collection of methods for visualising the play area from a particular game of Cartolan
    
    Methods:
    __init__ takes an array of two Ints and an array of two Ints
    get_screen_width
    get_screen_height
    renew_tile_grid
    increase_max_longitude
    decrease_min_longitude
    increase_max_latitude
    decrease_min_latitude
    play_area_difference takes two nested Dicts of Cartolan.Tiles indexed by latitude and longitude Ints {0:{0:Tile}}
    draw_play_area takes two nested Dicts of Cartolan.Tiles indexed by latitude and longitude Ints {0:{0:Tile}}
    draw_routes takes a List of Cartolan.Player
    draw_tokens takes a List of Cartolan.Player
    draw_move_options takes two lists of two Ints
    draw_wealth_scores takes a list of Cartolan.Player
    clear_move_options
    give_prompt takes a String
    clear_prompt
    get_input_coords
    '''
    #a vector of visual offsets for the players' tokens
    PLAYER_OFFSETS = [[0.5, 0.5],  [0.25, 0.25],  [0.25, 0.75],  [0.75, 0.75]]
    AGENT_OFFSET = [0.75, 0.25] #the placement of agents on the tile
    ADVENTURER_OFFSET = [0.1, 0.1] #the offset to differentiate multiple adventurers on the same tile
    DIMENSION_INCREMENT = 5 #the number of tiles by which the play area is extended when methods are called
    GRID_SPEC = {"left":0.01, "right":0.99, "bottom":0.01, "top":0.99, "wspace":0.1, "hspace":0.1}
    SCREEN_DPI = 120.0
    TEXT_SCALE = 1
    
    # a dict in which to keep the images for tiles
    tile_image_library = {}
    
    def __init__(self, game, dimensions = [33, 21], origin = [15, 15], title = None):
        
        self.game = game
        self.dimensions = dimensions
        self.origin = origin
        self.play_area = {}
        
        #establish dimensions in the same proportions as the screen resolution
        self.establish_proportionate_dimensions()           
        #create the grid of subplots that will hold the tiles
        if title:
            self.fig, self.axarr = pyplot.subplots(self.dimensions[1],self.dimensions[0]
                                           , num=title
#                                         , figsize=(self.visual_area_width, self.visual_area_width*float(dimensions[1])/float(dimensions[0]))
                                        , figsize=(self.visual_width / self.SCREEN_DPI, self.visual_height / self.SCREEN_DPI)
                                        , clear=True, gridspec_kw=self.GRID_SPEC)
#             self.fig.set_size_inches(self.visual_area_width, self.visual_area_width*float(dimensions[1])/float(dimensions[0]), forward=False)
            self.fig.set_size_inches(self.visual_width / self.SCREEN_DPI, self.visual_height / self.SCREEN_DPI, forward=False)
        else:
            self.fig, self.axarr = pyplot.subplots(self.dimensions[1],self.dimensions[0]
                                           , num="Live game visualised"
#                                         , figsize=(self.visual_area_width, self.visual_area_width*float(dimensions[1])/float(dimensions[0]))
#                                         , figsize=(self.visual_width, self.visual_height)
                                        , figsize=(self.visual_width / self.SCREEN_DPI, self.visual_height / self.SCREEN_DPI)
                                        , clear=True, gridspec_kw=self.GRID_SPEC)
            #             self.fig.set_size_inches(self.visual_area_width, self.visual_area_width*float(dimensions[1])/float(dimensions[0]), forward=False)
#             self.fig.set_size_inches(self.visual_width, self.visual_height, forward=False)
            self.fig.set_size_inches(self.visual_width / self.SCREEN_DPI, self.visual_height / self.SCREEN_DPI, forward=False)
        #remove axes for initial rendering
        for horizontal in range(0, self.dimensions[0]):
            for vertical in range(0, self.dimensions[1]):
                self.axarr[vertical, horizontal].axis('off')
        #Axes for keeping track of tokens' current positions
        self.tokenax = self.fig.add_subplot(111, zorder=11)
        self.tokenax.axis("off")
        self.token_width = 2.0 * self.get_screen_width()/float(self.dimensions[0])
        #Axes for keeping track of availble interactions with tiles
        self.moveax = self.fig.add_subplot(111)
        self.moveax.axis("off")
        # set up a standard text prompt
        self.text = self.fig.text(0.5,0, "", va="bottom", ha="center", family='Comic Sans MS', fontsize=18)
        #Axes for keeping track of tokens' routes
        self.routeax = self.fig.add_subplot(111, zorder=10)
        self.routeax.axis("off")
        pyplot.subplots_adjust(left=self.GRID_SPEC["left"], right=self.GRID_SPEC["right"]
                              , bottom=self.GRID_SPEC["bottom"], top=self.GRID_SPEC["top"])
        
        # import tile images and establish a mapping
        if len(self.tile_image_library) == 0:
            self.tile_image_library = {}
            self.tile_image_library["water"] = mpimg.imread('./images/water.png')
            self.tile_image_library["land"] = mpimg.imread('./images/land.png')
            self.tile_image_library["water_disaster"] = mpimg.imread('./images/water_disaster.png') 
            self.tile_image_library["land_disaster"] = mpimg.imread('./images/land_disaster.png') 
            self.tile_image_library["capital"] = mpimg.imread('./images/capital.png') 
            self.tile_image_library["mythical"] = mpimg.imread('./images/mythical.png') 
            for uc_water in [True, False]: 
                for ua_water in [True, False]:
                    for dc_water in [True, False]:
                        for da_water in [True, False]:
                            for wonder in [True, False]:
                                filename = ""
                                if uc_water:
                                    filename += "t"
                                else:
                                    filename += "f"
                                if ua_water:
                                    filename += "t"
                                else:
                                    filename += "f"
                                if dc_water:
                                    filename += "t"
                                else:
                                    filename += "f"
                                if da_water:
                                    filename += "t"
                                else:
                                    filename += "f"
                                if wonder:
                                    filename += "t"
                                else:
                                    filename += "f"

                                self.tile_image_library[str(uc_water)+str(ua_water)+str(dc_water)+str(da_water)
                                                        +str(wonder)] = mpimg.imread('./images/' +filename+ '.png')
    
    def get_screen_width(self):
        '''Checks what the horizontal screen resolution is, to scale visuals accordingly'''
        root = tkinter.Tk()
        return root.winfo_screenwidth()
#         return 1366

    def get_screen_height(self):
        '''Checks what the vertical screen resolution is, to scale visuals accordingly'''
        root = tkinter.Tk()
        return root.winfo_screenheight()
#         return 1366
    
    def establish_proportionate_dimensions(self):
        '''Extends whatever grid dimensions were provided so that they are proportionate to the screen dimensions'''
        self.visual_width = self.get_screen_width()
        self.visual_height = self.get_screen_height()
        print("Established screen dimensions as "+str(self.visual_width)+","+str(self.visual_height))
        #If the horizontal dimension of the grid is greater proportionately to the vertical than the screen width is to the height, then increase the vertical dimension to match 
        if self.dimensions[0]/self.dimensions[1] > self.visual_width/self.visual_height:
            new_grid_vertical = int(self.visual_height*self.dimensions[0]/self.visual_width)
            #Adjust the origin before updating the grid size
            self.origin[1] -= (self.dimensions[1] - new_grid_vertical)//2
            self.dimensions[1] = new_grid_vertical
            #set the figure size so that tiles will be adjacent
            #given that the vertical dimension was rounded down to an integer, the visual height will need to be adjusted down too
            self.visual_height = self.visual_width * self.dimensions[1] / self.dimensions[0]
            print("Vertical dimension updated to "+str(self.dimensions[1])+" and vertical visual size updated to "+str(self.visual_height))
            print("Vertical origin updated to "+str(self.origin[1]))
        else:
            new_grid_horizontal = int(self.visual_width*self.dimensions[1]/self.visual_height)
            #Adjust the origin before updating the grid size
            self.origin[0] -= (self.dimensions[0] - new_grid_horizontal)//2
            self.dimensions[0] = new_grid_horizontal
            #set the figure size so that tiles will be adjacent
            #given that the horizontal dimension was rounded down to an integer, the visual width will need to be adjusted down too
            self.visual_width = self.visual_height * self.dimensions[0] / self.dimensions[1]
            print("Horizontal dimension updated to "+str(self.dimensions[0])+" and horizontal visual size updated to "+str(self.visual_width))
            print("Horizontal origin updated to "+str(self.origin[0]))
         
    
    def renew_tile_grid(self):
        '''Clears and replaces the array of axes that make up the tile grid, for example if dimensions have changed'''
        print("Updating tile grid to dimensions: "+str(self.dimensions[0])+","+str(self.dimensions[1]))
        #Make the proportions of the dimensions suitable for visualisation
        self.establish_proportionate_dimensions()
        
        #clean away existing visuals
#         pyplot.close()
        self.fig.clear()

        #Draw new visuals with the new grid dimensions
        self.fig, self.axarr = pyplot.subplots(self.dimensions[1],self.dimensions[0]
                                       , num="Live game visualised"
                                    , figsize=(self.visual_width / self.SCREEN_DPI, self.visual_height / self.SCREEN_DPI)
                                    , clear=True, gridspec_kw=self.GRID_SPEC)
        self.fig.set_size_inches(self.visual_width / self.SCREEN_DPI, self.visual_height / self.SCREEN_DPI, forward=False)
        #Recognise that no tiles have been drawn on this new grid
        self.play_area = {}
        #remove axis lines and send to the back of the figure, behind the other axes
        for axvec in self.axarr:
            for ax in axvec:
                ax.axis("off")
                ax.set_zorder(0.5)
        #recreate the other axes, forcing them to draw above the tile grid
        self.tokenax = self.fig.add_subplot(111)
        self.tokenax.axis("off")
        self.token_width = 2.0 * self.get_screen_width()/float(self.dimensions[0])
        self.moveax = self.fig.add_subplot(111)
        self.moveax.axis("off")
        self.text = self.fig.text(0.5,0, "", va="bottom", ha="center", family='Comic Sans MS', fontsize=18)
        self.routeax = self.fig.add_subplot(111, zorder=10)
        self.routeax.axis("off")
        pyplot.subplots_adjust(left=self.GRID_SPEC["left"], right=self.GRID_SPEC["right"]
                              , bottom=self.GRID_SPEC["bottom"], top=self.GRID_SPEC["top"])
    
    def increase_max_longitude(self):
        '''Increases the maximum horiztonal extent of the play area by a standard increment'''
        print("Increasing the right-hand limit of tiles")
        self.dimensions[0] += self.DIMENSION_INCREMENT
        self.renew_tile_grid()
    
    def decrease_min_longitude(self):
        '''Increases the maximum horiztonal extent of the play area by a standard increment, moving the origin right'''
        print("Increasing the left-hand limit of tiles")
        self.dimensions[0] += self.DIMENSION_INCREMENT
        self.origin[0] += self.DIMENSION_INCREMENT
        self.renew_tile_grid()
    
    def increase_max_latitude(self):
        '''Increases the maximum vertical extent of the play area by a standard increment'''
        print("Increasing the upper limit of tiles")
        self.dimensions[1] += self.DIMENSION_INCREMENT
        self.renew_tile_grid()
    
    def decrease_min_latitude(self):
        '''Increases the maximum vertical extent of the play area by a standard increment, moving the origin up'''
        print("Increasing the lower limit of tiles")
        self.dimensions[1] += self.DIMENSION_INCREMENT
        self.origin[1] += self.DIMENSION_INCREMENT
        self.renew_tile_grid()
        
    def play_area_difference(self, play_area_new, play_area_old):
        '''Compares two given nested Dicts of Cartolan.Tiles to see which Tiles are present in only one
        
        Arguments:
        Dict of Dict of Cartolan.Tiles, both indexed with Ints, giving the Tiles at different coordinates for the play area of interest
        Dict of Dict of Cartolan.Tiles, both indexed with Ints, giving the Tiles at different coordinates for the play area with tiles to disregard
        '''
        difference = { longitude : play_area_new[longitude].copy() for longitude in set(play_area_new) - set(play_area_old) }
        for longitude in play_area_old:
            if longitude in play_area_new:
                longitude_difference = { latitude : play_area_new[longitude][latitude] 
                                                for latitude in set(play_area_new[longitude])
                                                - set(play_area_old[longitude]) }
                if longitude_difference:
                    if difference.get(longitude):
                        difference[longitude].update(longitude_difference)
                    else:
                        difference[longitude] = longitude_difference
        return difference
    
    def play_area_union(self, play_area_new, play_area_old):
        '''Compares two given nested Dicts of Cartolan.Tiles and combines them into a single nested list without duplicates
        
        Arguments:
        Dict of Dict of Cartolan.Tiles, both indexed with Ints, giving the Tiles at different coordinates for the play area of interest
        Dict of Dict of Cartolan.Tiles, both indexed with Ints, giving the Tiles at different coordinates for the play area
        '''
        #Get the difference between the play_areas, so that we can add only the non-duplicative entries to the union
        difference = self.play_area_difference(play_area_new, play_area_old)
        #Now add all of these different entries onto the old play area
        union = {}
        for longitude in play_area_old:
            union[longitude] = play_area_old[longitude].copy()
            if longitude in difference:
                union[longitude].update(difference[longitude])
        for longitude in set(difference) - set(play_area_old):
            union[longitude] = difference[longitude].copy()
                
        return union
    
    # convert the play_area to a grid of tiles
    def draw_play_area(self):
        '''Renders the tiles that have been laid in a particular game of Cartolan - Trade Winds
        
        Arguments:
        Dict of Dict of Cartolan.Tiles, both indexed with Ints, giving the Tiles at different coordinates for the current state of play
        Dict of Dict of Cartolan.Tiles, both indexed with Ints, giving the Tiles at different coordinates that have been added since last drawing and need to be rendered
        '''
        
        #Make sure duplicate tiles aren't added, by getting the difference between the play area being drawn and that already drawn
        play_area_update = self.play_area_difference(self.game.play_area, self.play_area)
                                       
        for longitude in play_area_update:
            if self.origin[0] + longitude in range(0, self.dimensions[0]):
                for latitude in play_area_update[longitude]:
                    if self.origin[1] + latitude in range(0, self.dimensions[1]):
                        #bring in the relevant image from the library
                        tile = play_area_update[longitude][latitude]
                        e = tile.tile_edges
                        if isinstance(tile, CityTile):
                            if tile.is_capital:
                                tile_image = self.tile_image_library["capital"]
                            else:
                                tile_image = self.tile_image_library["mythical"]
                        elif isinstance(tile, DisasterTile):
                            if tile.tile_back == "water":
                                tile_image = self.tile_image_library["water_disaster"]
                            else:
                                tile_image = self.tile_image_library["land_disaster"]
                        else:
                            wonder = tile.is_wonder
                            tile_image = self.tile_image_library[str(e.upwind_clock_water)+str(e.upwind_anti_water)
                                                                 +str(e.downwind_clock_water)+str(e.downwind_anti_water)
                                                                 +str(wonder)]            

                        #rotate the image appropriately
                        if not tile.wind_direction.north and tile.wind_direction.east:
                            rotated_image = ndimage.rotate(tile_image, 270)
                        elif not tile.wind_direction.north and not tile.wind_direction.east:
                            rotated_image = ndimage.rotate(tile_image, 180)
                        elif tile.wind_direction.north and not tile.wind_direction.east:
                            rotated_image = ndimage.rotate(tile_image, 90)
                        else:
                            rotated_image = ndimage.rotate(tile_image, 0)

                        #place the tile image in the grid
                        horizontal = self.origin[0] + longitude
                        vertical = self.dimensions[1] - self.origin[1] - latitude
#                         print(str(vertical)+","+str(horizontal))
#                         title_loc = str(longitude)+","+str(latitude)
#                         self.axarr[vertical, horizontal].imshow(rotated_image, interpolation='nearest')
                        self.axarr[vertical-1, horizontal].imshow((rotated_image * 255).astype(numpy.uint8), interpolation='nearest')

        #remove axes
        for horizontal in range(0, self.dimensions[0]):
            for vertical in range(0, self.dimensions[1]):
                self.axarr[vertical, horizontal].axis('off')
                self.axarr[vertical, horizontal].set_zorder(0)
        
        # Keep track of what the latest play_area to have been visualised was
        self.play_area = self.play_area_union(self.play_area, play_area_update)
        pyplot.show(block=False)
        return True
        
    
    # it will be useful to see how players moved around the play area during the game, and relative to agents
    def draw_routes(self):
        '''Illustrates the paths that different Adventurers have taken during the course of a game, and the location of Agents
        
        Arguments:
        List of Carolan.Players the Adventurers and Agents that will be rendered
        '''
        from matplotlib import pyplot
        import math
        #try to set up a new master axes spanning all the subplots
#         tokenax = self.fig.add_subplot(111)
#         tokenax = self.tokenax
        # create a set of overarching axes, for drawing players
#         self.tokenax = self.fig.add_subplot(111)
        self.routeax.set_ylim([0,self.dimensions[1]])
        self.routeax.set_xlim([0,self.dimensions[0]])
        self.routeax.axis("off")
        #clear the existing visualisation of tokens / paths
        routeax = self.routeax
        routeax.clear()
    
        players = self.game.players
        for player in players:
            player_offset = self.PLAYER_OFFSETS[players.index(player)]
            for adventurer in self.game.adventurers[player]:
                if adventurer.route:
                    adventurer_offset = player_offset + self.game.adventurers[player].index(adventurer)*self.ADVENTURER_OFFSET
                    previous_step = [self.origin[0] + adventurer.route[0].tile_position.longitude
                                     , self.origin[1] + adventurer.route[0].tile_position.latitude]
                    # we'll introduce a gradual offset during the course of the game, to help keep track of when a route was travelled
#                     previous_offset = 0.25
                    previous_offset = [0.5, 0.5]
                    move = 0
                    for tile in adventurer.route:
                        # plot() to draw a line between two points. Call matplotlib. pyplot. plot(x, y) with x as a list of x-values and y as a list of their corresponding y-values of two points to plot a line segment between them.
                        # you'll need to get the centre-point for each tile_image
#                         offset = 0.25 + float(move)/float(len(adventurer.route))*0.5
                        offset = [0.5 + float(move)/float(len(adventurer.route))*(x - 0.5) for x in adventurer_offset]
                        step = [self.origin[0] + tile.tile_position.longitude, self.origin[1] + tile.tile_position.latitude]
    #                     self.fig.add_axes(rect=[1.0,1.0]).plot([previous_step[0]+0.5,step[0]+0.5],[previous_step[1]+0.5,step[1]+0.5]
    #                                   , color=player.colour)
#                         routeax.plot([previous_step[0]+previous_offset,step[0]+offset],[previous_step[1]+previous_offset,step[1]+offset]
#                                       , color=player.colour, linewidth=round(4.0*offset))
                        routeax.plot([previous_step[0]+previous_offset[0],step[0]+offset[0]],[previous_step[1]+previous_offset[1],step[1]+offset[1]]
                                      , color=player.colour, linewidth=math.ceil(4.0*float(move)/float(len(adventurer.route))))
                        previous_step = step
                        previous_offset = offset
                        move += 1
            
#             for agent in game.agents[player]: 
#                 for tile in agent.route:
#                     # we want to draw a square anywhere that an agent is
#                     # do we also want a marker where agents have previously been?
#                     if tile == agent.route[-1]:
#                         face_colour = player.colour
#                     else:
#                         face_colour = "none"
#                     location = [self.origin[0] + tile.tile_position.longitude
#                                 , self.origin[1] + tile.tile_position.latitude]
#                     routeax.scatter([location[0]+self.AGENT_OFFSET[0]],[location[1]+self.AGENT_OFFSET[1]]
#                                   , linewidth=1, edgecolors=player.colour, facecolor=face_colour, marker="s", s=self.token_width)
                
            if isinstance(player, PlayerRegularExplorer):
                for attack in player.attack_history: 
                    # we want to draw a cross anywhere that an attack happened, the attack_history is full of pairs with a tile and a bool for the attack's success
                    if attack[1]:
                        face_colour = player.colour
                    else:
                        face_colour = "none"
                    tile = attack[0]
                    location = [self.origin[0] + tile.tile_position.longitude + player_offset[0]
                                , self.origin[1] + tile.tile_position.latitude + player_offset[1]]
                    routeax.scatter([location[0]],[location[1]]
                                  , linewidth=1, edgecolors=player.colour, facecolor=face_colour, marker="X", s=self.token_width)

        routeax.set_ylim([0,self.dimensions[1]])
        routeax.set_xlim([0,self.dimensions[0]])
        routeax.axis("off")
        pyplot.show(block=False)
        
        
    def draw_tokens(self):
        '''Illustrates the current location of Adventurers and Agents in a game
        
        Arguments:
        List of Carolan.Players the Adventurers and Agents will be rendered for
        '''
        
        # cycle through the players, drawing the adventurers and agents as markers
        #try to set up a new master axes spanning all the subplots
#         tokenax = self.fig.add_subplot(111)
#         tokenax = self.tokenax
        # create a set of overarching axes, for drawing players
#         self.tokenax = self.fig.add_subplot(111)
        self.tokenax.set_ylim([0,self.dimensions[1]])
        self.tokenax.set_xlim([0,self.dimensions[0]])
        self.tokenax.axis("off")
        #clear the existing visualisation of tokens / paths
        tokenax = self.tokenax
        tokenax.clear()
        
        players = self.game.players
        for player in players:
            player_offset = self.PLAYER_OFFSETS[players.index(player)]
            for adventurer in self.game.adventurers[player]:
                # we want to draw a circle anywhere an Adventurer is
                tile = adventurer.current_tile
                location = [self.origin[0] + tile.tile_position.longitude
                            , self.origin[1] + tile.tile_position.latitude]
                edge_colour = player.colour
                if type(adventurer.game) in [GameRegular, GameAdvanced]:
                    if adventurer.pirate_token:
                        edge_colour = "black" # we'll outline pirates in black
                adventurer_offset = player_offset + self.game.adventurers[player].index(adventurer)*self.ADVENTURER_OFFSET
                tokenax.scatter([location[0]+adventurer_offset[0]],[location[1]+adventurer_offset[1]]
                              , edgecolors=edge_colour, facecolor=player.colour, marker="o"
                               , linewidth=3, s=self.token_width)
                tokenax.annotate(str(self.game.adventurers[player].index(adventurer)+1)
                                 ,(location[0]+adventurer_offset[0], location[1]+adventurer_offset[1])
                                 , color='white', family='Comic Sans MS'
                                , horizontalalignment="center", verticalalignment="center")
            
            for agent in self.game.agents[player]: 
                # we want to draw a square anywhere that an agent is
                tile = agent.current_tile
                location = [self.origin[0] + tile.tile_position.longitude
                            , self.origin[1] + tile.tile_position.latitude]
                face_colour = player.colour
                if type(adventurer.game) in [GameRegular, GameAdvanced]:
                    if agent.is_dispossessed:
                        face_colour = "None" # we'll outline only the agents that are dispossessed
                tokenax.scatter([location[0]+self.AGENT_OFFSET[0]],[location[1]+self.AGENT_OFFSET[1]]
                              , edgecolors=player.colour, facecolor=face_colour, marker="s"
                               , linewidth=3, s=self.token_width)
                tokenax.annotate(str(agent.wealth)
                                 ,(location[0]+self.AGENT_OFFSET[0], location[1]+self.AGENT_OFFSET[1])
                                 , color='white', family='Comic Sans MS'
                                , horizontalalignment="center", verticalalignment="center")
        
#        print("Creating a table of the wealth held by Players and their Adventurers")
        max_num_adventurers = 1
        for player in players:
            if len(self.game.adventurers[player]) > max_num_adventurers:
                max_num_adventurers = len(self.game.adventurers[player])
        scores = []
        for player in players:
            new_row = [str(player.vault_wealth)]
            for adventurer_num in range(0, max_num_adventurers):
                if adventurer_num < len(self.game.adventurers[player]):
                    new_row.append(str(self.game.adventurers[player][adventurer_num].wealth))
                else:
                    new_row.append("")
            scores.append(new_row)
        col_titles = ["Vault"]
        for chest_num in range(1, max_num_adventurers+1):
            col_titles.append("Chest #"+str(chest_num))
        wealth_table = tokenax.table(cellText=scores, edges="open"
                      , loc="upper left"
                    , colLabels=col_titles
                    , cellLoc="center"
                     )
        for header_num in range(0, max_num_adventurers+1):
            cell = wealth_table[(0, header_num)]
            cell.get_text().set_family("Comic Sans MS")
        wealth_table.auto_set_column_width(col=range(0,self.game.MAX_AGENTS+1))
        for player in players:
            cell = wealth_table[(players.index(player)+1,0)]
            cell.get_text().set_family("Comic Sans MS")
            cell.get_text().set_fontsize(round(12 * self.TEXT_SCALE))
            cell.get_text().set_weight('bold')
            cell.get_text().set_color(player.colour)
            for adventurer in self.game.adventurers[player]:
                # we want to record the Chest wealth for each Adventurer
                cell = wealth_table[(players.index(player)+1,self.game.adventurers[player].index(adventurer)+1)]
                cell.get_text().set_family("Comic Sans MS")
                cell.get_text().set_fontsize(round(12 * self.TEXT_SCALE))
                cell.get_text().set_color(player.colour)
            cell.set_height(cell.get_height() * self.TEXT_SCALE) #
        
        tokenax.set_ylim([0,self.dimensions[1]])
        tokenax.set_xlim([0,self.dimensions[0]])
        tokenax.axis("off")
        pyplot.show(block=False)
    
    
    def draw_move_options(self, valid_coords=None, invalid_coords=None, chance_coords=None
                          , buy_coords=None, attack_coords=None):
        '''Outlines tiles that can and can't be moved onto
        
        Arguments:
        List of Lists of two Ints giving coordinates for tiles that can be moved onto
        List of Lists of two Ints giving coordinates for tiles that cannot be moved onto
        '''
        from matplotlib import pyplot
        # cycle through the valid and invalid grid coordinates, outlining the tiles that can and can't be moved to
#         moveax = self.moveax
        #clear any existing visuals
#         create a set of overarching axes, for highlighting movement options
#         self.moveax = self.fig.add_subplot(111)
        self.moveax.set_ylim([0,self.dimensions[1]])
        self.moveax.set_xlim([0,self.dimensions[0]])
        self.moveax.axis("off")
        
        moveax = self.moveax
#         moveax.clear()
        
        if valid_coords:
            for tile_coords in valid_coords:
                rec = pyplot.Rectangle(((tile_coords[0]+self.origin[0]), (tile_coords[1]+self.origin[1])),1.0,1.0
                                       ,fill=False,lw=2, edgecolor='g')
                rec = moveax.add_patch(rec)
                rec.set_clip_on(False)
            
        if invalid_coords:
            for tile_coords in invalid_coords:
                rec = pyplot.Rectangle(((tile_coords[0]+self.origin[0]), (tile_coords[1]+self.origin[1])),1.0,1.0
                                       ,fill=False,lw=2, edgecolor='r', hatch='xx')
                rec = moveax.add_patch(rec)
                rec.set_clip_on(False)
        
        if chance_coords:
            for tile_coords in chance_coords:
                rec = pyplot.Rectangle(((tile_coords[0]+self.origin[0]), (tile_coords[1]+self.origin[1])),1.0,1.0
                                       ,fill=False,lw=2, edgecolor='orange', hatch='//')
                rec = moveax.add_patch(rec)
                rec.set_clip_on(False)
        
        if buy_coords:
            for tile_coords in buy_coords:
                rec = pyplot.Rectangle(((tile_coords[0]+self.origin[0]), (tile_coords[1]+self.origin[1])),1.0,1.0
                                       ,fill=False,lw=2, edgecolor='y', hatch='*')
                rec = moveax.add_patch(rec)
                rec.set_clip_on(False)
        
        if attack_coords:
            for tile_coords in attack_coords:
                rec = pyplot.Rectangle(((tile_coords[0]+self.origin[0]), (tile_coords[1]+self.origin[1])),1.0,1.0
                                       ,fill=False,lw=2, edgecolor='black', hatch='.O')
                rec = moveax.add_patch(rec)
                rec.set_clip_on(False)
        
        moveax.set_ylim([0,self.dimensions[1]])
        moveax.set_xlim([0,self.dimensions[0]])
        moveax.axis("off")
        pyplot.show(block=False)
        
    def draw_scores(self):
        '''Prints a table of current wealth scores in players' Vaults and Adventurers' Chests
        
        Arguments:
        List of Cartolan.Players
        '''  
        pass
#         create a set of overarching axes, for highlighting movement options
#         self.moveax = self.fig.add_subplot(111)
#        self.scoreax.set_ylim([0,self.dimensions[1]])
#        self.scoreax.set_xlim([0,self.dimensions[0]])
#        self.scoreax.axis("off")
#        
#        scoreax = self.scoreax
#        scoreax.clear()
#        
#        players = self.game.players
#        print("Creating a table of the wealth held by Players and their Adventurers")
#        scores = [["Vault wealth", "Adventurer\n #1 wealth", "Adventurer\n #2 wealth", "Adventurer\n #3 wealth"]]
#        pyplot.sca(self.scoreax)
#        wealth_table = pyplot.table(cellText=scores, edges="open", loc='top left')
#        wealth_table.auto_set_column_width(col=range(0,players[0].adventurers[0].game.MAX_AGENTS+1))
#        for player in players:
#            cell = wealth_table.add_cell(players.index(player)+1, 0, width=5, height=5
##                                          , fontproperties={"color":player.colour, "fontsize":20} #Set row colours to match player colours, and enlarge the first column's text size
#                                         , text=str(player.vault_wealth)) #width and height are arbitrary and should be overruled by the auto column width
#            cell.get_text().set_fontsize(20)
#            cell.get_text().set_color(player.colour)
#            for adventurer in self.game.adventurers[player]:
#                # we want to record the Chest wealth for each Adventurer
#                cell = wealth_table.add_cell(players.index(player)+1, self.game.adventurers[player].index(adventurer)+1, 0, height=5
##                                             , fontproperties={"color":player.colour, "fontsize":16} #Set row colours to match player colours, and enlarge the first column's text size
#                                            , text=str(adventurer.wealth)) #width and height are arbitrary and should be overruled by the auto column width
#                cell.get_text().set_fontsize(16)
#                cell.get_text().set_color(player.colour)
#
##         scoreax.add_table(wealth_table)
#        
#        scoreax.set_ylim([0,self.dimensions[1]])
#        scoreax.set_xlim([0,self.dimensions[0]])
#        scoreax.axis("off")
#        scoreax.set_zorder(2.5)
#        pyplot.show(block=False)

        
    def clear_move_options(self):
        '''Remove any outlines that were illustrating possible and impossible moves'''
        from matplotlib import pyplot
        moveax = self.moveax
        #clear any existing visuals
        moveax.clear()
        moveax.set_ylim([0,self.dimensions[1]])
        moveax.set_xlim([0,self.dimensions[0]])
        moveax.axis("off")
        pyplot.show(block=False)
        
    def start_turn(self, player_colour):
        '''An unused template for changing visuals to reflect the current player's colour
        '''
        pass
    
    def give_prompt(self, prompt_text):
        '''Provide text instructing the player on what to do'''
        from matplotlib import pyplot
        self.text.set_text(prompt_text)
        pyplot.show(block=False)
        
    def clear_prompt(self):
        '''Clear any text instructions'''
        from matplotlib import pyplot
        self.text.set_text(None)
        pyplot.show(block=False)
    
    def get_input_coords(self, adventurer):
        '''Collects mouseclick input from the user and converts it into the position of a game tile.
        
        Arguments
        adventurer takes a Cartolan.Adventurer
        '''
        pyplot.ginput(timeout=0) # this call to ginput should reveal the highlights, but it will not be the one that determines movement
        self.clear_prompt()
        self.give_prompt("Click again to confirm")
        move_click = pyplot.ginput(timeout=0)
#         pyplot.show(block=False)
        if not move_click:
            print(self.colour+" player failed to choose a move, so it is assumed the Adventurer will wait in place")
            move_coords = [adventurer.current_tile.tile_position.longitude, adventurer.current_tile.tile_position.latitude]
        else:
            move_coords = [int(move_click[0][0]) - self.origin[0], int(move_click[0][1]) - self.origin[1]]
#                 move_coords = [int(move_click[0][0] * game_vis.dimensions[0]) - game_vis.origin[0]
#                                , int(move_click[0][1] * game_vis.dimensions[1]) - game_vis.origin[0]]
        return move_coords
    
    def close(self):
        '''Elegantly closes the application.
        '''
        pyplot.close()

class GameVisualisation():
    '''A pygame-based interactive visualisation for games of Cartolan
    
    Methods:
    draw_move_options
    draw_tokens
    draw_play_area
    draw_wealth_scores
    draw_routes
    draw_prompt
    '''
    #define some constants that will not vary game by game
    MOVE_TIME_LIMIT = 10 #To force a timeout if players aren't responding
    PLAYER_OFFSETS = [[0.25, 0.25],  [0.25, 0.75],  [0.75, 0.25], [0.75, 0.75]]
    AGENT_OFFSET = [0.5, 0.5] #the placement of agents on the tile, the same for all players and agents, because there will only be one per tile
    ADVENTURER_OFFSETS = [[0.0, 0.0], [0.1, -0.1], [-0.1, 0.1], [-0.1, -0.1], [0.1, 0.1]] #the offset to differentiate multiple adventurers on the same tile
    DIMENSION_INCREMENT = 2 #the number of tiles by which the play area is extended when methods are called
    TILE_BORDER = 0.02 #the share of grid width/height that is used for border
    TOKEN_SCALE = 0.2 #relative to tile sizes
    TOKEN_OUTLINE_SCALE = 0.25 #relative to token scale
    TOKEN_FONT_SCALE = 0.5 #relative to tile sizes
    SCORES_POSITION = [0.0, 0.0]
    SCORES_FONT_SCALE = 0.05 #relative to window size
    SCORES_SPACING = 1.5 #the multiple of the score pixel scale to leave for each number
    PROMPT_POSITION = [0.0, 0.85]
    PROMPT_FONT_SCALE = 0.05 #relative to window size
    
    def __init__(self, game, dimensions, origin):
        #Retain game data
        self.players = game.players
        self.game = game
        self.dimensions = dimensions
        self.origin = origin
        
        self.init_GUI()
        
    def init_GUI(self):
        print("Initialising the pygame window and GUI")
        pygame.init()
        self.window = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
        self.width, self.height = pygame.display.get_surface().get_size()
        self.window.fill((255,255,255)) #fill the screen with white
#        self.window.fill(0) #fill the screen with black
#        self.backing_image = pygame.transform.scale(pygame.image.load('./images/cartolan_backing.png'), [self.width, self.height])
#        self.window.blit(self.backing_image, [0,0])
        pygame.display.set_caption("Cartolan - Trade Winds")
        print("Initialising visual scale variables, to fit window of size "+str(self.width)+"x"+str(self.height))
        self.tile_size = self.height // self.dimensions[1]
        #Tiles will be scaled to fit the smaller dimension
        if self.width < self.tile_size * self.dimensions[0]:
            self.tile_size = self.width // self.dimensions[0]
        self.token_size = int(round(self.TOKEN_SCALE * self.tile_size)) #token size will be proportional to the tiles
        self.outline_width = math.ceil(self.TOKEN_OUTLINE_SCALE * self.token_size)
        self.token_font = pygame.font.SysFont(None, round(self.tile_size * self.TOKEN_FONT_SCALE)) #the font size for tokens will be proportionate to the window size
        self.scores_font = pygame.font.SysFont(None, round(self.height * self.SCORES_FONT_SCALE)) #the font size for scores will be proportionate to the window size
        self.prompt_font = pygame.font.SysFont(None, round(self.height * self.PROMPT_FONT_SCALE)) #the font size for prompt will be proportionate to the window size
        self.prompt_position = [self.PROMPT_POSITION[0]*self.width, self.PROMPT_POSITION[1]*self.height]
        pygame.font.init()
        self.prompt_text = ""
        self.init_graphics()
        pygame.display.flip()
#        self.init_sound()
        print("Initialising state variables")
        self.clock = pygame.time.Clock()
        self.move_timer = self.MOVE_TIME_LIMIT
        self.current_player_colour = pygame.Color("black")
        self.current_adventurer_number = 1
        self.highlights = {"move":[], "invalid":[], "buy":[], "attack":[]}
        
    #    def init_sound(self):
#        '''Imports sounds to accompany play
#        '''
#        self.winSound = pygame.mixer.Sound('win.wav')
#        self.loseSound = pygame.mixer.Sound('lose.wav')
#        self.placeSound = pygame.mixer.Sound('place.wav')
#        # pygame.mixer.music.load("music.wav")
#        # pygame.mixer.music.play()
    
        #Set the visual running
#        while not self.game.game_over:
#            self.update()
    
    def init_graphics(self):
        '''Reads in the images for visualising play
        '''
        print("Importing tile and highlight images and establishing a mapping")
        self.tile_image_library = {}
        self.tile_image_library["water"] = pygame.image.load('./images/water.png')
        self.tile_image_library["land"] = pygame.image.load('./images/land.png')
        self.tile_image_library["water_disaster"] = pygame.image.load('./images/water_disaster.png') 
        self.tile_image_library["land_disaster"] = pygame.image.load('./images/land_disaster.png') 
        self.tile_image_library["capital"] = pygame.image.load('./images/capital.png') 
        self.tile_image_library["mythical"] = pygame.image.load('./images/mythical.png') 
        for uc_water in [True, False]: 
            for ua_water in [True, False]:
                for dc_water in [True, False]:
                    for da_water in [True, False]:
                        for wonder in [True, False]:
                            filename = ""
                            if uc_water:
                                filename += "t"
                            else:
                                filename += "f"
                            if ua_water:
                                filename += "t"
                            else:
                                filename += "f"
                            if dc_water:
                                filename += "t"
                            else:
                                filename += "f"
                            if da_water:
                                filename += "t"
                            else:
                                filename += "f"
                            if wonder:
                                filename += "t"
                            else:
                                filename += "f"
                            tile_image = pygame.image.load('./images/' +filename+ '.png')
                            #Rotate the image for different wind directions
                            #North East wind
                            self.tile_image_library[str(uc_water)+str(ua_water)
                                +str(dc_water)+str(da_water)+str(wonder)+"TrueTrue"] = tile_image
                            #South East wind
                            self.tile_image_library[str(uc_water)+str(ua_water)
                                +str(dc_water)+str(da_water)+str(wonder)+"FalseTrue"] = pygame.transform.rotate(tile_image.copy(), -90)
                            #South West wind
                            self.tile_image_library[str(uc_water)+str(ua_water)
                                +str(dc_water)+str(da_water)+str(wonder)+"FalseFalse"] = pygame.transform.rotate(tile_image.copy(), 180)
                            #North West wind
                            self.tile_image_library[str(uc_water)+str(ua_water)
                                +str(dc_water)+str(da_water)+str(wonder)+"TrueFalse"] = pygame.transform.rotate(tile_image.copy(), 90)
        #rescale the tiles to match the current play area dimensions now, it will only be scaled down and lose more fidelity with subsequent resizing
        bordered_tile_size = round(self.tile_size * (1 - self.TILE_BORDER))
        print("Set tile sizes to be " +str(self.tile_size)+ " pixels, and with border: " +str(bordered_tile_size))
        for tile_type in self.tile_image_library:
            tile_image = self.tile_image_library[tile_type]
            self.tile_image_library[tile_type] = pygame.transform.scale(tile_image, [bordered_tile_size, bordered_tile_size])
        
        # import the masks used to highlight movement options
        self.highlight_library = {}
        self.highlight_library["move"] = pygame.image.load('./images/option_valid_move.png')
        self.highlight_library["invalid"] = pygame.image.load('./images/option_invalid_move.png')
        self.highlight_library["buy"] = pygame.image.load('./images/option_buy.png')
        self.highlight_library["attack"] = pygame.image.load('./images/option_attack.png')
        self.highlight_library["rest"] = pygame.image.load('./images/option_rest.png')
        #rescale the tiles to match the current play area dimensions now, it will only be scaled down and lose more fidelity with subsequent resizing
        for highlight_type in self.highlight_library:
            highlight_image = self.highlight_library[highlight_type]
            self.highlight_library[highlight_type] = pygame.transform.scale(highlight_image, [self.tile_size, self.tile_size])

    def rescale_graphics(self):
        '''Rescales images in response to updated dimensions for the play grid
        '''
        print("Updating the dimensions that will be used for drawing the play area")
#        self.dimensions = dimensions        
        #Tiles, tokens and text will need adjusting to the new dimensions
        if self.height < self.width:
            #Tiles will be scaled to fit the smaller dimension
            self.tile_size = self.height // self.dimensions[1]
        else:
            self.tile_size = self.width // self.dimensions[0]
        self.token_size = int(round(self.TOKEN_SCALE * self.tile_size)) #token size will be proportional to the tiles
        self.outline_width = math.ceil(self.TOKEN_OUTLINE_SCALE * self.token_size)
        self.token_font = pygame.font.SysFont(None, int(self.tile_size * self.TOKEN_FONT_SCALE)) #the font size for tokens will be proportionate to the window size
        #scale down the images as the dimensions of the grid are changed, rather than when placing
        #the tiles' scale will be slightly smaller than the space in the grid, to givea discernible margin
        bordered_tile_size = round(self.tile_size * (1 - self.TILE_BORDER))
        print("Updated tile size to be " +str(self.tile_size)+ " pixels, and with border: " +str(bordered_tile_size))
        for tile_type in self.tile_image_library:
            tile_image = self.tile_image_library[tile_type]
            self.tile_image_library[tile_type] = pygame.transform.scale(tile_image, [bordered_tile_size, bordered_tile_size])
        for highlight_type in self.highlight_library:
            highlight_image = self.highlight_library[highlight_type]
            self.highlight_library[highlight_type] = pygame.transform.scale(highlight_image, [self.tile_size, self.tile_size])
    
    def increase_max_longitude(self):
        '''Deprecated to allow legacy PlayerHuman interaction'''
        pass
    
    def decrease_min_longitude(self):
        '''Deprecated to allow legacy PlayerHuman interaction'''
        pass
    
    def increase_max_latitude(self):
        '''Deprecated to allow legacy PlayerHuman interaction'''
        pass
    
    def decrease_min_latitude(self):
        '''Deprecated to allow legacy PlayerHuman interaction'''
        pass
    
    def is_rescale_needed(self):
        '''Checks the extremes of the play_area and rescales visual elements as needed
        '''
#        print("Checking whether the current play area needs a bigger visuals grid")
        min_longitude, max_longitude = 0, 0
        min_latitude, max_latitude = 0, 0
        for longitude in self.game.play_area:
            if longitude < min_longitude:
                min_longitude = longitude
            elif longitude > max_longitude:
                max_longitude = longitude
            for latitude in self.game.play_area[longitude]:
                if latitude < min_latitude:
                    min_latitude = latitude
                elif latitude > max_latitude:
                    max_latitude = latitude
        rescale_needed = False
        if min_longitude < -self.origin[0] + 1:
            self.origin[0] = -min_longitude + self.DIMENSION_INCREMENT
            rescale_needed = True
        if max_longitude > self.dimensions[0] - self.origin[0] - 2:
            self.dimensions[0] = max_longitude + self.origin[0] + self.DIMENSION_INCREMENT
            rescale_needed = True
        if min_latitude < -self.origin[1] + 1:
            self.origin[1] = -min_latitude + self.DIMENSION_INCREMENT
            rescale_needed = True
        if max_latitude > self.dimensions[1] - self.origin[1] - 2:
            self.dimensions[1] = max_latitude + self.origin[1] + self.DIMENSION_INCREMENT
            rescale_needed = True
        if rescale_needed:
            self.rescale_graphics()   

    def get_horizontal(self, longitude):
        '''Translates a play area horiztonal position into visual grid position
        '''
        return self.origin[0] + longitude
    
    def get_vertical(self, latitude):
        '''Translates a play area vertical position into visual grid position
        '''
        return self.dimensions[1] - self.origin[1] - latitude - 1
    
    def draw_play_area(self):
        '''Renders the tiles that have been laid in a particular game of Cartolan - Trade Winds
        '''
        play_area_update = self.game.play_area
#        print("Drawing the play area, with " +str(len(play_area_update))+" columns of tiles")
        #Check whether the visuals need to be rescaled
        self.is_rescale_needed()
        #Clear what's already been drawn
        self.window.fill((255,255,255))
#        self.window.fill(0)
#        self.window.blit(self.backing_image, [0,0])
        #For each location in the play area draw the tile
        for longitude in play_area_update:
            for latitude in play_area_update[longitude]:
                #bring in the relevant image from the library
                tile = play_area_update[longitude][latitude]
                e = tile.tile_edges
                if isinstance(tile, CityTile):
                    if tile.is_capital:
                        tile_image = self.tile_image_library["capital"]
                    else:
                        tile_image = self.tile_image_library["mythical"]
                elif isinstance(tile, DisasterTile):
                    if tile.tile_back == "water":
                        tile_image = self.tile_image_library["water_disaster"]
                    else:
                        tile_image = self.tile_image_library["land_disaster"]
                else:
                    wonder = tile.is_wonder
                    north = tile.wind_direction.north
                    east = tile.wind_direction.east
                    tile_image = self.tile_image_library[str(e.upwind_clock_water)+str(e.upwind_anti_water)
                                                         +str(e.downwind_clock_water)+str(e.downwind_anti_water)
                                                         +str(wonder)+str(north)+str(east)]
                #place the tile image in the grid
                horizontal = self.get_horizontal(longitude)
                vertical = self.get_vertical(latitude)
#                print("Placing a tile at pixel coordinates " +str(horizontal*self.tile_size)+ ", " +str(vertical*self.tile_size))
                self.window.blit(tile_image, [horizontal*self.tile_size, vertical*self.tile_size])
        # # Keep track of what the latest play_area to have been visualised was
        # self.play_area = self.play_area_union(self.play_area, play_area_update)
        return True
    
    #@TODO highlight the particular token(s) that an action relates to
    def draw_move_options(self, valid_coords=None, invalid_coords=None, chance_coords=None
                          , buy_coords=None, attack_coords=None, rest_coords=None):
        '''Outlines tiles where moves or actions are possible, designated by colour
        '''
#        print("Updating the dict of highlight positions, based on optional arguments")
        highlight_count = 0
        if valid_coords:
            self.highlights["move"] = valid_coords
            highlight_count += len(self.highlights["move"])
        else:
            self.highlights["move"] = []
        if invalid_coords:
            self.highlights["invalid"] = invalid_coords
            highlight_count += len(self.highlights["invalid"])
        else:
            self.highlights["invalid"] = []
        if buy_coords:
            self.highlights["buy"] = buy_coords
            highlight_count += len(self.highlights["buy"])
        else:
            self.highlights["buy"] = []
        if attack_coords:
            self.highlights["attack"] = attack_coords
            highlight_count += len(self.highlights["attack"])
        else:
            self.highlights["attack"] = []
        if rest_coords:
            self.highlights["rest"] = rest_coords
            highlight_count += len(self.highlights["rest"])
        else:
            self.highlights["rest"] = []
#        print("Cycling through the various highlights' grid coordinates, outlining the " +str(highlight_count)+ " tiles that can and can't be subject to moves")
        for highlight_type in self.highlight_library:
            if self.highlights[highlight_type]:
                highlight_image = self.highlight_library[highlight_type]
                for tile_coords in self.highlights[highlight_type]:
                    #place the highlight image on the grid
                    horizontal = self.get_horizontal(tile_coords[0])
                    vertical = self.get_vertical(tile_coords[1])
#                    print("Drawing a highlight at pixel coordinates " +str(horizontal*self.tile_size)+ ", " +str(vertical*self.tile_size))
                    self.window.blit(highlight_image, [horizontal*self.tile_size, vertical*self.tile_size])
    
    def check_highlighted(self, input_longitude, input_latitude):
        '''Given play area grid coordinates, checks whether this is highlighted as a valid move/action
        '''
#        print("Checking whether there is a valid move option at: " +str(input_longitude)+ ", " +str(input_latitude))
        is_option_available = False
        for highlight_type in self.highlight_library:
#            print("There are " +str(len(self.highlights[highlight_type]))+ " options of type " +highlight_type)
            if self.highlights[highlight_type]:
                is_option_available = True
                for tile_coords in self.highlights[highlight_type]:
                    #compare the input coordinates to the highlighted tile's coordinates
                    longitude = tile_coords[0]
                    latitude = tile_coords[1]
                    if longitude == input_longitude and latitude == input_latitude:
                        return highlight_type
        if is_option_available:
            return None
        else:
            return "confirmed"
    
    def clear_move_options(self):
        '''
        '''
#        print("Clearing out the list of valid moves")
        for highlight_type in self.highlight_library:
            self.highlights[highlight_type] = []
    
    def draw_tokens(self):
        '''Illustrates the current location of Adventurers and Agents in a game, along with their paths over the last turn
        '''
#        print("Cycling through the players, drawing the adventurers and agents as markers")
        game = self.game
        players = self.players
        for player in players:
            #We'll want to differentiate players by colour and the offset from the tile location
            colour = pygame.Color(player.colour)
            player_offset = self.PLAYER_OFFSETS[players.index(player)]
            #Each player may have multiple Adventurers to draw
            adventurers = self.game.adventurers[player]
            for adventurer in adventurers:
                # we want to draw a circle anywhere an Adventurer is, differentiating with offsets
                tile = adventurer.current_tile
                adventurer_offset = self.ADVENTURER_OFFSETS[adventurers.index(adventurer)]
                location = [int(self.tile_size * (self.get_horizontal(tile.tile_position.longitude) + player_offset[0] + adventurer_offset[0]))
                            , int(self.tile_size * (self.get_vertical(tile.tile_position.latitude) + player_offset[1] + adventurer_offset[1]))]
                # we want it to be coloured differently for each player
#                print("Drawing the filled circle at " +str(location[0])+ ", " +str(location[1])+ " with radius " +str(self.token_size))
                pygame.draw.circle(self.window, colour, location, self.token_size)
                if isinstance(adventurer, AdventurerRegular):
                    if adventurer.pirate_token:
                        # we'll outline pirates in black
#                        print("Drawing an outline")
                        pygame.draw.circle(self.window, (0, 0, 0), location, self.token_size, self.outline_width)
                #For the text label we'll change the indent 
                token_label = self.token_font.render(str(adventurers.index(adventurer)+1), 1, (0,0,0))
                location[0] -= self.token_size // 2
                location[1] -= self.token_size
                self.window.blit(token_label, location)
            # we want to draw a square anywhere that an agent is
            for agent in game.agents[player]: 
                tile = agent.current_tile
                if not tile:
                    continue
                agent_offset = self.AGENT_OFFSET
                location = [int(self.tile_size * (self.get_horizontal(tile.tile_position.longitude) + agent_offset[0]))
                            , int(self.tile_size * (self.get_vertical(tile.tile_position.latitude) + agent_offset[1]))]
                #Agents will be differentiated by colour, but they will always have the same position because there will only be one per tile
                agent_shape = pygame.Rect(location[0], location[1]
                  , 2*self.token_size, 2*self.token_size)
                # we'll only outline the Agents that are dispossessed
                if isinstance(agent, AgentRegular) and agent.is_dispossessed:
                        pygame.draw.rect(self.window, colour, agent_shape, self.outline_width)
                else:
                    #for a filled rectangle the fill method could be quicker: https://www.pygame.org/docs/ref/draw.html#pygame.draw.rect
                    self.window.fill(colour, rect=agent_shape)
                token_label = self.token_font.render(str(agent.wealth), 1, (0,0,0))
                location[0] += self.token_size // 2
                self.window.blit(token_label, location)
        return True
    
    # it will be useful to see how players moved around the play area during the game, and relative to agents
    def draw_routes(self):
        '''Illustrates the paths that different Adventurers have taken during the course of a game, and the location of Agents
        
        Arguments:
        List of Carolan.Players the Adventurers and Agents that will be rendered
        '''
#        print("Drawing a series of lines to mark out the route travelled by players since the last move")
        players = self.game.players
        for player in players:
            player_offset = self.PLAYER_OFFSETS[players.index(player)]
            adventurers = self.game.adventurers[player]
            colour = pygame.Color(player.colour)
            for adventurer in adventurers:
                if adventurer.route:
                    adventurer_offset = self.ADVENTURER_OFFSETS[adventurers.index(adventurer)]
                    adventurer_offset = [adventurer_offset[i] + player_offset[i] for i in [0, 1]]
                    previous_step = [int(self.tile_size * (self.get_horizontal(adventurer.route[0].tile_position.longitude) + adventurer_offset[0]))
                            , int(self.tile_size * (self.get_vertical(adventurer.route[0].tile_position.latitude) + adventurer_offset[1]))]
                    # we'll introduce a gradual offset during the course of the game, to help keep track of when a route was travelled
                    move = 0
                    for tile in adventurer.route:
                        # you'll need to get the centre-point for each tile_image
                        offset = [0.5 + float(move)/float(len(adventurer.route))*(x - 0.5) for x in adventurer_offset]
                        step = [int(self.tile_size * (self.get_horizontal(tile.tile_position.longitude) + offset[0]))
                                , int(self.tile_size * (self.get_vertical(tile.tile_position.latitude) + offset[1]))]
                        pygame.draw.line(self.window, colour
                                         , [previous_step[0], previous_step[1]]
                                         , [step[0], step[1]]
                                         , math.ceil(4.0*float(move)/float(len(adventurer.route))))
                        previous_step = step
                        move += 1
            
#            if isinstance(player, PlayerRegularExplorer):
#                for attack in player.attack_history: 
#                    # we want to draw a cross anywhere that an attack happened, the attack_history is full of pairs with a tile and a bool for the attack's success
#                    if attack[1]:
#                        face_colour = player.colour
#                    else:
#                        face_colour = "none"
#                    tile = attack[0]
#                    location = [self.origin[0] + tile.tile_position.longitude + player_offset[0]
#                                , self.origin[1] + tile.tile_position.latitude + player_offset[1]]
#                    routeax.scatter([location[0]],[location[1]]
#                                  , linewidth=1, edgecolors=player.colour, facecolor=face_colour, marker="X", s=self.token_width)
    
    def draw_scores(self):
        '''Prints a table of current wealth scores in players' Vaults and Adventurers' Chests
        '''        
#        print("Creating a table of the wealth held by Players and their Adventurers")
        #Draw the column headings
        game = self.game
        score_title = self.scores_font.render("Vault", 1, (0,0,0))
        scores_position = [self.SCORES_POSITION[0] * self.width, self.SCORES_POSITION[1] * self.height]
        self.window.blit(score_title, scores_position)
        #Work out the maximum number of Adventurers in play, to only draw this many columns
        max_num_adventurers = 1
        for player in self.players:
            if len(game.adventurers[player]) > max_num_adventurers:
                max_num_adventurers = len(game.adventurers[player])
        for adventurer_num in range(1, max_num_adventurers + 1):
                score_title = self.scores_font.render("Chest #"+str(adventurer_num), 1, (0,0,0))
                scores_position[0] += self.SCORES_FONT_SCALE * self.SCORES_SPACING * self.width
                self.window.blit(score_title, scores_position)
        for player in self.players:
            colour = pygame.Color(player.colour)
            scores_position[0] = self.SCORES_POSITION[0] * self.width #reset the scores position before going through other rows below
            scores_position[1] += self.SCORES_FONT_SCALE * self.height #increment the vertical position to a new row
            score_value = self.scores_font.render(str(player.vault_wealth), 1, colour)
            self.window.blit(score_value, scores_position)
            for adventurer in game.adventurers[player]:
                    scores_position[0] += self.SCORES_FONT_SCALE * self.SCORES_SPACING * self.width #Shift to a new column
                    score_value = self.scores_font.render(str(adventurer.wealth), 1, colour)
                    self.window.blit(score_value, scores_position)
    
    def draw_prompt(self):
        '''Prints a prompt on what moves/actions are available to the current player
        '''        
#        print("Creating a prompt for the current player")
        #Establish the colour (as the current player's)
        prompt = self.prompt_font.render(self.prompt_text, 1, self.current_player_colour)
        self.window.blit(prompt, self.prompt_position)
    
    def start_turn(self, player_colour):
        '''Identifies the current player by their colour, affecting prompts
        '''
        self.current_player_colour = pygame.Color(player_colour)
    
    def give_prompt(self, prompt_text):
        '''Pushes text to the prompt buffer for the visual
        
        Arguments:
        prompt_text should be a string
        '''
        self.prompt_text = prompt_text
        #Replace all the visuals, rather than overlaying text on old text
#        self.draw_play_area()
#        self.draw_tokens()
#        self.draw_routes()
#        self.draw_move_options()
        self.draw_prompt()
        
    
    def clear_prompt(self):
        '''Empties the prompt buffer for the visual
        '''
        self.promp_text = ""

    def get_input_coords(self, adventurer):
        '''Passes mouseclick input from the user and converts it into the position of a game tile.
        
        Arguments
        adventurer takes a Cartolan.Adventurer
        '''
#        print("Waiting for input from the user")
        pygame.display.flip()
        while True:
            event = pygame.event.wait()
            #quit if the quit button was pressed
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.move_timer = self.MOVE_TIME_LIMIT #reset the timelimit on moving
                longitude = int(math.ceil((event.pos[0])/self.tile_size)) - self.origin[0] - 1
                latitude = self.dimensions[1] - int(math.ceil((event.pos[1])/self.tile_size)) - self.origin[1]
                #check whether the click was within the highlighted space and whether it's a local turn
#                highlighted_option = self.check_highlighted(longitude, latitude)
#                print("Click was a valid option of type: " + highlighted_option)
                if True:
#                if highlighted_option is not None:
                    self.highlights = {"move":[], "invalid":[], "buy":[], "attack":[]} #clear the highlights until the server offers more
#                    print("Have identified a move available at " +str(longitude)+ ", " +str(latitude)+ " of type " +str(highlighted_option))
                    return [longitude, latitude]
            if self.move_timer < 0:
                return False
#                if self.local_player_turn and highlighted_option is not None:
#                    self.Send({"action": highlighted_option, "longitude":longitude, "latitude":latitude, "player": self.current_player_colour, "adventurer": self.current_adventurer_number, "gameid": self.gameid})
#                    self.highlights = [] #clear the highlights until the server offers more
#       #Otherwise wait for suitable input
        
        #update the window
        #@TODO at the point of seeking player input for an Adventurer for the first time this turn, clear its route history
        
        #Get mouse input and translate this into tile coordinates
         #@TODO On hover highlight potential placements and place tiles, in response to mouse position and clicks
#        try: 
#            if not board[ypos][xpos]: self.window.blit(self.hoverlineh if is_horizontal else self.hoverlinev, [xpos*64+5 if is_horizontal else xpos*64, ypos*64 if is_horizontal else ypos*64+5])
#        except:
#            isoutofbounds=True
#            pass
#        if not isoutofbounds:
#            alreadyplaced=board[ypos][xpos]
#        else:
#            alreadyplaced=False
        
#            else:
                #@TODO play a sound prompt that this has been an invalid click
        
        #@TODO alternatively, take keyboard input from the cursor keys and Enter key
        
        #Refresh the display
        pygame.display.flip()
        
        return False
    
    def close(self):
        '''Elegantly closes the application down.
        '''
        pygame.quit()
        sys.exit()
        
    def finished(self):
        self.window.blit(self.gameover if not self.local_win else self.winningscreen, (0,0))
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            pygame.display.flip()


class ClientGameVisualisation(GameVisualisation, ConnectionListener):
    '''A pygame-based interactive visualisation that is client to a remote game.
    
    Because the client games act as master during a local player's turn, this 
    visualisation needs to act as both a receiver and broadcaster of game state.
    
    
    Methods:
    Network_update
    draw_move_options
    draw_tokens
    draw_play_area
    draw_wealth_scores
    '''
    GAME_TYPES = {"beginner":GameBeginner, "regular":GameRegular, "advanced":GameAdvanced}
    
    def __init__(self):
        #Network state data:
        self.local_player_turn = False # Keep track of whether to wait on local player input for updates to visuals, 
        self.local_win = False
        self.running = False
        #@TODO provide a simple window for exchanges with the server
        
        #Establish connection to the server
        address = input("Address of Server: ")
        try:
            if not address:
                host, port="localhost", 8000
            else:
                host, port = address.split(":")
            self.Connect((host, int(port)))
        except:
            print("Error Connecting to Server")
            print("Usage:", "host:port")
            print ("e.g.", "localhost:31425")
            exit()
        print("Cartolan client started")
        #Keep the connection live until the game is activated
        while not self.running:
            self.Pump()
            connection.Pump()
            sleep(0.01)
        
    def update(self):
        '''Redraws visuals and seeks player input, passing it to the server to pass to the server-side Player
        '''
        #distinguish between local and remote play and hand control of the game to the remote player's computer as needed, through the server
        if self.local_player_turn:
            current_player = self.players[self.current_player_colour]
            self.game.adventurers[current_player][self.current_adventurer_number].continue_turn()
            #@TODO check whether this player's turn has now ended and give away control if needed
        else:
            connection.Pump()
            self.Pump()
        #If the game has ended then stop player input and refreshing
        if self.game.game_over:
            self.Send({"action":"quit"})
            return True
        #clear the window and redraw everything
        self.window.fill(0)
        self.draw_play_area()
        self.draw_tokens()
        self.draw_scores()
    
    #Now for a set of methods that will use PodSixNet to respond to messages from the server to progress the game
    def Network_start_game(self, data):
        '''Initiates network game based on data following an {"action":"start_game"} message from the server
        '''
        self.running = True #keep track of whether the game is active or waiting for the server to collect enough players
        self.game_id = data["game_id"] #allow game state to be synched between server and client
        self.local_player_colours = data["local_player_colours"]
        #Set up the local version of the game
        game_type = self.GAME_TYPES(data["game_type"]) #needed to identify the class of other elements like Adventurers and Agents
        players = []
        for player_colour in data["player_colours"]:
            players.append(PlayerHuman(player_colour))
        
        game = game_type(self.players)
        #@TODO build the tile piles
        self.build_pile_water
        if not game_type == GameBeginner:
            self.build_pile_land
        #place the initial tiles and adventurers
        initial_tiles = data["initial_tiles"]
        for tile_json in initial_tiles:
            self.Network_place_tile(tile_json)
        player_adventurers = data["player_adventurers"] #expects a dict of colours and 2-tuples giving the placement(s) of initial Adventurers for each player
        adventurers = {}
        if not len(players) == len(player_adventurers):
            raise Exception("Player attributes from Host have different lengths")
        for player in players:
            for adventurer_location in player_adventurers[player.colour]:
                longitude = game.play_area.get(adventurer_location[0])
                if longitude:
                    adventurer_tile = longitude.get(adventurer_location[0])
                    if adventurer_tile:
                        adventurer = self.game_type.ADVENTURER_TYPE(self, player, game.play_area[adventurer_location[0]][adventurer_location[1]])
                        adventurers[player].append(adventurer)
                    else:
                        raise Exception("Server tried to place on Adventurer where there was no tile")
        
        #With proxy game and players set up, continue the startup of a normal visual
        dimensions = data["dimensions"]
        origin = data["origin"]
        super().__init__(players, game, dimensions, origin)
        
    
    def Network_close(self, data):
        '''Allows remote closing of game through an {"action":"close"} message from the server
        '''
        super().close()
        
    def close(self):
        '''Elegantly closes the application down.
        '''
        self.Send({"action":"close", "data":""})
        super().close()
    
    def Network_new_turn(self, data):
        '''Informs local player(s) which remote player is currently expected to be moving
        '''
        self.local_player_turn = data["is_local_player_turn"]
        self.current_player_colour = data["current_player_colour"]
        self.current_adventurer_number = data["current_adventurer_number"]
        if not self.local_player_turn:
            self.prompt_text = self.current_player_colour +" player is moving their Adventurer #" +str(self.current_adventurer_number)
    
    def Network_place_tile(self, data):
        '''Places a tile based on data following an {"action":"place_tile"} message from the server
        '''
        self.placeSound.play()
        #read location to place at
        longitude = data["longitude"]
        latitude = data["latitude"]
        #read tile characteristics to visualise
        tile_data = data["tile"]
        is_wonder = tile_data["is_wonder"]
        tile_back = tile_data["tile_back"]
        tile_edges_data = tile_data["tile_edges"]
        tile_edges = TileEdges(tile_edges_data["north"], tile_edges_data["east"], tile_edges_data["south"], tile_edges_data["west"])
        wind_direction_data = tile_data["wind_direction"]
        wind_direction = WindDirection(wind_direction_data["north"], wind_direction_data["east"])
        placed_tile = Tile(None, tile_back, wind_direction, tile_edges, is_wonder)
        #Place the tile in the play area
        self.game.play_area[longitude][latitude] = placed_tile
        #remove a matching tile from the tile pile
        tile_removed = False
        tile_pile = self.game.tile_piles[tile_back]
        for tile in tile_pile:
            if tile.compare(placed_tile):
                tile_pile.remove(tile)
                tile_removed = True
        if not tile_removed:
            raise Exception("Server placed a tile that was not in the Tile Pile")
        
    def Network_move_token(self, data):
        '''Moves an Adventurer or Agent based on data following an {"action":"move_token"} message from the server
        '''
        self.placeSound.play()
        #read location to move to
        longitude = data["longitude"]
        latitude = data["latitude"]
        #identify token to move
        player_colour = data["player_colour"]
        token_is_adventurer = data["token_is_adventurer"]
        token_num = data["token_num"]
        #Check that it is this player's turn
        player = self.players[player_colour]
#        if not self.current_player_colour == player_colour:
            #@TODO return a message to the server complaining that the wrong player has tried to move
        #Place the token on the tile at the coordinates
        if token_is_adventurer:
            
            token = game.adventurers[player][token_num]
        else:
            token = game.agents[player][token_num]
        #Check that the tile exists before moving the token there
        if self.game.play_area.get(longitude):
            tile = self.game.play_area.get(longitude).get(latitude)
            if tile:
                tile.move_onto_tile(token)
#        else:
            #@TODO returna  message to the server complaining that it wasn't a valid tile provided
        
    def Network_prompt(self, data):
        '''Updates the prompt based on remote input
        '''
        prompt_text = data["prompt_text"]
        self.give_prompt(prompt)
    
    def Network_clear_prompt(self, data):
        '''Cleares the prompt based on remote input
        '''
        self.clear_prompt()
    
    def Network_end_game(self, data):
        '''Notifies player who won the game based on data following an {"action":"end_game"} message from the server
        '''
        #add one point to my score
        self.winSound.play()
        self.me+=1
        #@TODO prompt a mouse click to quit
        exit()    

class HostGameInterface:
    def __init__(self, server, game):
        #Retain game data
        self.server = server
        self.players = game.players
        self.game = game
        self.shared_play_area = {}
    
    def play_area_difference(self, play_area_new, play_area_old):
        '''Compares two given nested Dicts of Cartolan.Tiles to see which Tiles are present in only one
        
        Arguments:
        Dict of Dict of Cartolan.Tiles, both indexed with Ints, giving the Tiles at different coordinates for the play area of interest
        Dict of Dict of Cartolan.Tiles, both indexed with Ints, giving the Tiles at different coordinates for the play area with tiles to disregard
        '''
        difference = { longitude : play_area_new[longitude].copy() for longitude in set(play_area_new) - set(play_area_old) }
        for longitude in play_area_old:
            if longitude in play_area_new:
                longitude_difference = { latitude : play_area_new[longitude][latitude] 
                                                for latitude in set(play_area_new[longitude])
                                                - set(play_area_old[longitude]) }
                if longitude_difference:
                    if difference.get(longitude):
                        difference[longitude].update(longitude_difference)
                    else:
                        difference[longitude] = longitude_difference
        return difference
    
    def draw_play_area(self):
        '''Shares with the server the new tiles that have been added since last updating
        '''
        #Determine change in play area and share this with the server
        play_area_update = self.play_area_difference(self.game.play_area, self.shared_play_area)
        print("Drawing the play area, with " +str(len(play_area_update))+" columns of tiles")
        self.server.remote_draw_play_area(self.game, play_area_update)
        return True
    
    #@TODO highlight the particular token(s) that an action relates to
    def draw_move_options(self, valid_coords=None, invalid_coords=None, chance_coords=None
                          , buy_coords=None, attack_coords=None, rest_coords=None):
        '''Outlines tiles where moves or actions are possible, designated by colour
        '''
#        print("Updating the dict of highlight positions, based on optional arguments")
        self.server.remote_draw_move_options(self.game, valid_coords=None, invalid_coords=None, chance_coords=None
                          , buy_coords=None, attack_coords=None, rest_coords=None)
        
    def clear_move_options(self):
        '''
        '''
#        print("Clearing out the list of valid moves")
        self.server.remote_clear_move_options(self.game)
    
    def draw_tokens(self):
        '''Identifies which tokens have changed position/status and passing them to the server
        '''
#        print("Cycling through the players, drawing the adventurers and agents as markers")
    
    # it will be useful to see how players moved around the play area during the game, and relative to agents
    def draw_routes(self):
        '''Illustrates the paths that different Adventurers have taken during the course of a game, and the location of Agents
        
        Arguments:
        List of Carolan.Players the Adventurers and Agents that will be rendered
        '''
        print("Drawing a series of lines to mark out the route travelled by players since the last move")
        
    def draw_scores(self):
        '''Prints a table of current wealth scores in players' Vaults and Adventurers' Chests
        '''        
        print("Creating a table of the wealth held by Players and their Adventurers")
    
    def draw_prompt(self):
        '''Prints a prompt on what moves/actions are available to the current player
        '''        
#        print("Creating a prompt for the current player")
    
    def start_turn(self, player_colour):
        '''Identifies the current player by their colour, affecting prompts
        '''
        #notify the current player that they are moving
        
        #set the text for other players to inform them who is moving
    
    def give_prompt(self, prompt_text):
        '''Pushes text to the prompt buffer for the visual
        
        Arguments:
        prompt_text should be a string
        '''
    
    def clear_prompt(self):
        '''Empties the prompt buffer via the server
        '''
        
    #@TODO differentiate remote players from local and seek input accordingly
    def get_input_coords(self, adventurer):
        '''Seeks input coords via the server.
        
        Arguments
        adventurer takes a Cartolan.Adventurer
        '''
        return False



class PlayStatsVisualisation:
    '''A set of methods for drawing charts that report summary statistics from many simulations of Cartolan - Trade Winds
    
    Methods:
    __init__ takes a Pandas.DataFrame of play statistics to render
    ... various methods render the statistics as histograms
    '''
    def __init__(self, play_stats):
        self.visual_area_width = self.get_screen_width()/120.0 #iPython defaults visuals to @80dpi 
        self.play_stats = play_stats
        self.fig = self.pyplot.figure(num="Statistics for all simulated games that ended", figsize=(self.visual_area_width, self.visual_area_width), clear=True )
    
    def get_screen_width(self):
        root = tkinter.Tk()
        return root.winfo_screenwidth()
#         return 1366
    
    def win_type_comparison(self):
        '''win counts for different win conditions'''
        ax = self.fig.add_subplot(521, title="#Wins by win condition")
        ax = self.pyplot.hist(self.play_stats["win_type"])
    
    def turns_to_win(self):
        '''win counts for different numbers of turns to win'''
        ax = self.fig.add_subplot(522, title="#Wins by # turns to win")
        ax = self.pyplot.hist(self.play_stats["turns"])
    
    def player_type_comparison(self):
        '''win counts for different player types'''
        ax = self.fig.add_subplot(523, title="#Wins by winning player type")
        ax = self.pyplot.hist(self.play_stats["winning_player_type"])
    
    def player_order_comparison(self):
        '''win counts for different player starting positions'''
        ax = self.fig.add_subplot(524, title="#Wins by winner's position in play order", xticks=[1,2,3,4])
        ax = self.pyplot.hist(self.play_stats["winning_player_order"])
    
    def wealth_comparison(self):
        '''distribution of winning player wealth vs average wealth across games'''
#         self.play_stats["max_wealth_share"] = self.play_stats["max_wealth_final"!=0]["max_wealth_final"]/self.play_stats[["wealth_p1", "wealth_p2", "wealth_p3", "wealth_p4"]].sum(axis=1)
        self.play_stats["max_wealth_share"] = self.play_stats["max_wealth_final"]/self.play_stats[["wealth_p1", "wealth_p2", "wealth_p3", "wealth_p4"]].sum(axis=1)
        ax = self.fig.add_subplot(525, title="#Wins by winner's share of total vault wealth")
        ax = self.pyplot.hist(self.play_stats["max_wealth_share"])
    
    def route_comparison(self):
        '''distribution of winning player route length vs average route length across games'''
        self.play_stats["avg_route_share"] = self.play_stats["winning_player_route"]/self.play_stats[["avg_route_p1", "avg_route_p2", "avg_route_p3", "avg_route_p4"]].sum(axis=1)
        ax = self.fig.add_subplot(526, title="#Wins by winner's share of total moves travelled")
        ax = self.pyplot.hist(self.play_stats["avg_route_share"])
        
    def token_comparison(self):
        # distribution of final agent numbers and final adventurer numbers
        ax = self.fig.add_subplot(527, title="#Wins by winner's final number of agents and adventurers")
#         ax = self.pyplot.hist(self.play_stats[["winning_player_agents","winning_player_adventurers"]], label=["#Agents","#Adventurers"], color=["yellow","red"], histtype='bar')
        ax = self.pyplot.hist([self.play_stats["winning_player_agents"].to_list(),self.play_stats["winning_player_adventurers"].to_list()], label=["#Agents","#Adventurers"], color=["yellow","red"], histtype='bar')
        self.pyplot.legend()
        
    def tile_comparison(self):
        # distribution of remaining water and land tiles across games
        ax = self.fig.add_subplot(528, title="#Remaining water and land tiles at game end")
#         ax = self.pyplot.hist(self.play_stats[["remaining_water_tiles","remaining_land_tiles"]], label=["# remaining water","# remaining land"], color=["blue","green"], histtype='bar')
        ax = self.pyplot.hist([self.play_stats["remaining_water_tiles"].to_list(),self.play_stats["remaining_land_tiles"].to_list()], color=["blue","green"], label=["Water","Land"], histtype='bar')
        self.pyplot.legend()

    def discards_comparison(self):
        # distribution of final agent numbers
        ax = self.fig.add_subplot(529, title="#Numbers of discards per game and failed explorations")
#         ax = self.pyplot.hist(self.play_stats[["exploration_attempts", "failed_explorations"]], label=["# discarded tiles","# failed explorations"], color=["purple","pink"], histtype='bar')
        ax = self.pyplot.hist([self.play_stats["exploration_attempts"].to_list(), self.play_stats["failed_explorations"].to_list()], label=["Discards", "Failures"], histtype='bar')
        self.pyplot.legend()
        
    def remaining_tiles_distribution(self, edge_list):
        ax = self.fig.add_subplot(529, title="#Leftover tile edge combinations")
        ax.hist(edge_list)
#         ax.set_xticklabels(rotation=45)
        self.pyplot.xticks(rotation='vertical')