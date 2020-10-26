import matplotlib.image as mpimg # for importing tile images
import tkinter
import pandas
from matplotlib import pyplot # for plotting the tiles in a grid
from scipy import ndimage # for rotating tiles
import numpy
import pygame
import json
from types import SimpleNamespace
from PodSixNet.Connection import ConnectionListener, connection
from time import sleep
from base import Game, Player, CityTile, Tile, WindDirection, TileEdges
from regular import DisasterTile
from game import GameBeginner, GameRegular, GameAdvanced
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
    
    def __init__(self, dimensions = [33, 21], origin = [15, 15], title = None):
        
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
    def draw_play_area(self, play_area_to_add):
        '''Renders the tiles that have been laid in a particular game of Cartolan - Trade Winds
        
        Arguments:
        Dict of Dict of Cartolan.Tiles, both indexed with Ints, giving the Tiles at different coordinates for the current state of play
        Dict of Dict of Cartolan.Tiles, both indexed with Ints, giving the Tiles at different coordinates that have been added since last drawing and need to be rendered
        '''
        
        #Make sure duplicate tiles aren't added, by getting the difference between the play area being drawn and that already drawn
        play_area_update = self.play_area_difference(play_area_to_add, self.play_area)
                                       
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
    def draw_routes(self, players):
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
    
        for player in players:
            player_offset = self.PLAYER_OFFSETS[players.index(player)]
            for adventurer in player.adventurers:
                if adventurer.route:
                    adventurer_offset = player_offset + player.adventurers.index(adventurer)*self.ADVENTURER_OFFSET
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
            
#             for agent in player.agents: 
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
        
        
    def draw_tokens(self, players):
        '''Illustrates the current location of Adventurers and Agents in a game
        
        Arguments:
        List of Carolan.Players the Adventurers and Agents will be rendered for
        '''
        from matplotlib import pyplot
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
        
        for player in players:
            player_offset = self.PLAYER_OFFSETS[players.index(player)]
            for adventurer in player.adventurers:
                # we want to draw a circle anywhere an Adventurer is
                tile = adventurer.current_tile
                location = [self.origin[0] + tile.tile_position.longitude
                            , self.origin[1] + tile.tile_position.latitude]
                edge_colour = player.colour
                if type(adventurer.game) in [GameRegular, GameAdvanced]:
                    if adventurer.pirate_token:
                        edge_colour = "black" # we'll outline pirates in black
                adventurer_offset = player_offset + player.adventurers.index(adventurer)*self.ADVENTURER_OFFSET
                tokenax.scatter([location[0]+adventurer_offset[0]],[location[1]+adventurer_offset[1]]
                              , edgecolors=edge_colour, facecolor=player.colour, marker="o"
                               , linewidth=3, s=self.token_width)
                tokenax.annotate(str(player.adventurers.index(adventurer)+1)
                                 ,(location[0]+adventurer_offset[0], location[1]+adventurer_offset[1])
                                 , color='white', family='Comic Sans MS'
                                , horizontalalignment="center", verticalalignment="center")
            
            for agent in player.agents: 
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
        
        print("Creating a table of the wealth held by Players and their Adventurers")
        max_num_adventurers = 1
        for player in players:
            if len(player.adventurers) > max_num_adventurers:
                max_num_adventurers = len(player.adventurers)
        scores = []
        for player in players:
            new_row = [str(player.vault_wealth)]
            for adventurer_num in range(0, max_num_adventurers):
                if adventurer_num < len(player.adventurers):
                    new_row.append(str(player.adventurers[adventurer_num].wealth))
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
        wealth_table.auto_set_column_width(col=range(0,players[0].adventurers[0].game.MAX_AGENTS+1))
        for player in players:
            cell = wealth_table[(players.index(player)+1,0)]
            cell.get_text().set_family("Comic Sans MS")
            cell.get_text().set_fontsize(round(12 * self.TEXT_SCALE))
            cell.get_text().set_weight('bold')
            cell.get_text().set_color(player.colour)
            for adventurer in player.adventurers:
                # we want to record the Chest wealth for each Adventurer
                cell = wealth_table[(players.index(player)+1,player.adventurers.index(adventurer)+1)]
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
        
    def draw_wealth_scores(self, players):
        '''Prints a table of current wealth scores in players' Vaults and Adventurers' Chests
        
        Arguments:
        List of Cartolan.Players
        '''        
#         create a set of overarching axes, for highlighting movement options
#         self.moveax = self.fig.add_subplot(111)
        self.scoreax.set_ylim([0,self.dimensions[1]])
        self.scoreax.set_xlim([0,self.dimensions[0]])
        self.scoreax.axis("off")
        
        scoreax = self.scoreax
        scoreax.clear()
        
        print("Creating a table of the wealth held by Players and their Adventurers")
        scores = [["Vault wealth", "Adventurer\n #1 wealth", "Adventurer\n #2 wealth", "Adventurer\n #3 wealth"]]
        pyplot.sca(self.scoreax)
        wealth_table = pyplot.table(cellText=scores, edges="open", loc='top left')
        wealth_table.auto_set_column_width(col=range(0,players[0].adventurers[0].game.MAX_AGENTS+1))
        for player in players:
            cell = wealth_table.add_cell(players.index(player)+1, 0, width=5, height=5
#                                          , fontproperties={"color":player.colour, "fontsize":20} #Set row colours to match player colours, and enlarge the first column's text size
                                         , text=str(player.vault_wealth)) #width and height are arbitrary and should be overruled by the auto column width
            cell.get_text().set_fontsize(20)
            cell.get_text().set_color(player.colour)
            for adventurer in player.adventurers:
                # we want to record the Chest wealth for each Adventurer
                cell = wealth_table.add_cell(players.index(player)+1, player.adventurers.index(adventurer)+1, 0, height=5
#                                             , fontproperties={"color":player.colour, "fontsize":16} #Set row colours to match player colours, and enlarge the first column's text size
                                            , text=str(adventurer.wealth)) #width and height are arbitrary and should be overruled by the auto column width
                cell.get_text().set_fontsize(16)
                cell.get_text().set_color(player.colour)

#         scoreax.add_table(wealth_table)
        
        scoreax.set_ylim([0,self.dimensions[1]])
        scoreax.set_xlim([0,self.dimensions[0]])
        scoreax.axis("off")
        scoreax.set_zorder(2.5)
        pyplot.show(block=False)

        
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


class ClientGameVisualisation(ConnectionListener, Game):
    '''A pygame-based interactive visualisation serving as client to a remote game.
    
    Architecture:
    Server Side             |    Client Side
    Game       ->  Server  <->   Visualisation -> Player -> Adventurer
    |             /\                                |
    \/             |                               \/
                  \/                            
    Adventurer -> Player                         Agent
    
    Client side Player, Adventurer, and Agent, used for data storage but not methods
    
    Methods:
    draw_move_options
    draw_tokens
    draw_play_area
    draw_wealth_scores
    '''
    #define some constants that will not vary game by game
    MOVE_TIME_LIMIT = 10 #To force a timeout if players aren't responding
    PLAYER_OFFSETS = [[0.25, 0.25],  [0.25, 0.75],  [0.75, 0.25], [0.75, 0.75]]
    AGENT_OFFSET = [0.5, 0.5] #the placement of agents on the tile, the same for all players and agents, because there will only be one per tile
    ADVENTURER_OFFSETS = [[0.0, 0.0], [0.1, -0.1], [-0.1, 0.1], [-0.1, -0.1], [0.1, 0.1]] #the offset to differentiate multiple adventurers on the same tile
    DIMENSION_INCREMENT = 5 #the number of tiles by which the play area is extended when methods are called
    TILE_BORDER = 0.02 #the share of grid width/height that is used for border
    TOKEN_SCALE = 0.2 #relative to tile sizes
    TOKEN_FONT_SCALE = 0.5 #relative to tile sizes
    SCORES_POSITION = (0, 0)
    SCORES_FONT_SCALE = 0.02 #relative to window size
    SCORES_SPACING = 3 #the multiple of the score pixel scale to leave for each number
    
    def __init__(self, players, local_player_colours, dimensions, origin):
        
        #Initialise the pygame window and GUI
        pygame.init()
        pygame.font.init()
        self.init_graphics()
        self.init_sound()
        self.width = tkinter.Tk().winfo_screenwidth()
        self.height = tkinter.Tk().winfo_screenheight()
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Cartolan - Trade Winds")
        self.dimensions = dimensions
        self.origin = origin
        #Initialise visuals scale variables
        if self.height < self.width:
            #Tiles will be scaled to fit the smaller dimension
            self.tile_size = self.height // dimensions[1]
        else:
            self.tile_size = self.width // dimensions[0]
        self.token_size = self.TOKEN_SCALE * self.tile_size #token size will be proportional to the tiles
        self.token_font = pygame.font.SysFont(None, self.tile_size * self.TOKEN_FONT_SCALE) #the font size for tokens will be proportionate to the window size
        self.scores_font = pygame.font.SysFont(None, self.height * self.SCORES_FONT_SCALE) #the font size for scores will be proportionate to the window size
        #Initialise state variables
        self.clock = pygame.time.Clock()
        self.move_timer = self.MOVE_TIME_LIMIT
        self.local_player_colours = local_player_colours
        self.highlights = {"valid_move":[], "invalid_move":[], "buy":[], "attack":[]}
        self.play_area = {}
        self.local_player_turn = False
        self.local_win = False
        self.running = False
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
        self.running = False
        #Keep the connection live until the game is active?
        while not self.running:
            self.Pump()
            connection.Pump()
            sleep(0.01)
        
    
#    def init_sound(self):
#        '''Imports sounds to accompany play
#        '''
#        self.winSound = pygame.mixer.Sound('win.wav')
#        self.loseSound = pygame.mixer.Sound('lose.wav')
#        self.placeSound = pygame.mixer.Sound('place.wav')
#        # pygame.mixer.music.load("music.wav")
#        # pygame.mixer.music.play()
    
    def init_graphics(self):
        '''Reads in the images for visualising play
        '''
        # import tile images and establish a mapping
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
                            tile_image = mpimg.imread('./images/' +filename+ '.png')
                            #Rotate the image for different wind directions
                            #North East wind
                            self.tile_image_library[str(uc_water)+str(ua_water)
                                +str(dc_water)+str(da_water)+str(wonder)+True+True] = tile_image
                            #South East wind
                            self.tile_image_library[str(uc_water)+str(ua_water)
                                +str(dc_water)+str(da_water)+str(wonder)+False+True] = pygame.transform.rotate(tile_image, 90)
                            #South West wind
                            self.tile_image_library[str(uc_water)+str(ua_water)
                                +str(dc_water)+str(da_water)+str(wonder)+False+False] = pygame.transform.rotate(tile_image, 180)
                            #North West wind
                            self.tile_image_library[str(uc_water)+str(ua_water)
                                +str(dc_water)+str(da_water)+str(wonder)+True+False] = pygame.transform.rotate(tile_image, -90)
        #rescale the tiles to match the current play area dimensions now, it will only be scaled down and lose more fidelity with subsequent resizing
        bordered_tile_size = round(self.tile_size * (1 - self.TILE_BORDER))
        for tile_image in self.tile_image_library:
            tile_image = pygame.transform.scale(tile_image, [bordered_tile_size, bordered_tile_size])
        
        # import the masks used to highlight movement options
        self.highlight_library = {}
        self.highlight_library["valid_move"] = mpimg.imread('./images/option_valid_move.png')
        self.highlight_library["invalid_move"] = mpimg.imread('./images/option_invalid_move.png')
        self.highlight_library["buy"] = mpimg.imread('./images/option_buy.png')
        self.highlight_library["attack"] = mpimg.imread('./images/option_attack.png')
        #rescale the tiles to match the current play area dimensions now, it will only be scaled down and lose more fidelity with subsequent resizing
        for highlight_image in self.highlight_image_library:
            highlight_image = pygame.transform.scale(highlight_image, [self.tile_size, self.tile_size])
    
    def rescale_graphics(self, dimensions):
        '''Rescales images in response to updated dimensions for the play grid
        
        Arguments:
        dimensions should be a 2-tuple of positive integers, denoting the [horizontal, vertical] grid dimensions
        '''
        #Update the dimensions that will be used for drawing the play area
        self.dimensions = dimensions        
        #Tiles, tokens and text will need adjusting to the new dimensions
        if self.height < self.width:
            #Tiles will be scaled to fit the smaller dimension
            self.tile_size = self.height // dimensions[1]
        else:
            self.tile_size = self.width // dimensions[0]
        self.token_size = self.TOKEN_SCALE * self.tile_size #token size will be proportional to the tiles
        self.token_font = pygame.font.SysFont(None, self.tile_size * self.TOKEN_FONT_SCALE) #the font size for tokens will be proportionate to the window size
        self.scores_font = pygame.font.SysFont(None, self.height * self.SCORES_FONT_SCALE) #the font size for scores will be proportionate to the window size
        #As the dimensions of the grid are changed, scale down the images rather than when placing
        bordered_tile_size = round(self.tile_size * (1 - self.TILE_BORDER))
        for tile_image in self.tile_image_library:
            tile_image = pygame.transform.scale(tile_image, [bordered_tile_size, bordered_tile_size])
        for highlight_image in self.highlight_library:
            highlight_image = pygame.transform.scale(highlight_image, [self.tile_size, self.tile_size])
    
    #Now for a set of methods that will use PodSixNet to respond to messages from the server to progress the game
    def Network_start_game(self, data):
        '''Initiates network game based on data following an {"action":"start_game"} message from the server
        '''
        self.running = True #keep track of active games
        self.game_id = data["game_id"] #allow game state to be synched between server and client
        self.game_type = data["game_type"] #needed to identify the class of other elements like Adventurers and Agents
        #place the initial tiles and identify the Capital for player placement
        #@TODO genericise this to allow multiple starting cities or be robust to city coordinates not being 0, 0
        initial_tiles = data["initial_tiles"]
        for tile_json in initial_tiles:
            self.Network_place_tile(tile_json)
        starting_city = self.play_area[0][0]
        #player data could alternatively be structured as a dict, for better data integrity
        player_colours = data["player_colours"] #expects a list of colours for players in the order of play
        player_is_locals = data["player_is_locals"] #expects a list of Booleans giving the status of whether each player is local to this GUI 
        player_adventurers = data["player_adventurers"] #expects a list of ints giving the number of initial Adventurers for each player
        if not (len(player_colours) == len(player_is_locals)
            and len(player_colours) == len(player_adventurers)):
            raise Exception("Player attributes from Host have different lengths")
        for player_num in range(len(player_colours)):
            player = PlayerClient(player_colours[player_num], player_is_locals[player_num])
            self.players.append(player)
            num_adventurers = range(player_adventurers[player_num])
            for adventurer_num in range(num_adventurers):
                adventurer = self.game_type.ADVENTURER_TYPE(self, player, starting_city)
                player.adventurers.append(adventurer)
            
         
    
    def Network_close(self, data):
        '''Allows remote closing of game through an {"action":"close"} message from the server
        '''
        exit()
    
    def Network_local_turn(self, data):
        '''Switches to local game control based on data following an {"action":"move_token"} message from the server
        '''
        self.local_player_turn = data["local_player_turn"]
        self.current_player_colour = data["current_player_colour"]
        if not self.local_player_turn or self.current_player_colour not in self.local_player_colours:
            pass # handle a remote turn, unless this gets handled elsewhere
    
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
        #Place the tile in the play area
        self.play_area[longitude][latitude] = Tile(None, tile_back, wind_direction, tile_edges, is_wonder)
        
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
            
            token = player.adventurers[token_num]
        else:
            token = player.agents[token_num]
        #Check that the tile exists before moving the token there
        if self.game.play_area.get(longitude):
            tile = self.game.play_area.get(longitude).get(latitude)
            if tile:
                tile.move_onto_tile(token)
#        else:
            #@TODO returna  message to the server complaining that it wasn't a valid tile provided
        
    def Network_end_game(self, data):
        '''Notifies player who won the game based on data following an {"action":"end_game"} message from the server
        '''
        #add one point to my score
        self.winSound.play()
        self.me+=1
        #@TODO prompt a mouse click to quit
        exit()
    
    def draw_play_area(self):
        '''Renders the tiles that have been laid in a particular game of Cartolan - Trade Winds
        '''
        # #Make sure duplicate tiles aren't added, by getting the difference between the play area being drawn and that already drawn
        # play_area_update = self.play_area_difference(play_area_to_add, self.play_area)
        play_area_update = self.play_area
        #For each location in the play area draw the tile, rotating as needed
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
                            north = tile.wind_direction.north
                            east = tile.wind_direction.east
                            tile_image = self.tile_image_library[str(e.upwind_clock_water)+str(e.upwind_anti_water)
                                                                 +str(e.downwind_clock_water)+str(e.downwind_anti_water)
                                                                 +str(wonder)+str(north)+str(east)]
                        #place the rescaled tile image in the grid
                        horizontal = self.origin[0] + longitude
                        vertical = self.dimensions[1] - self.origin[1] - latitude
                        self.window.blit(tile_image, [longitude*self.tile_width, latitude*self.tile_height])
        # # Keep track of what the latest play_area to have been visualised was
        # self.play_area = self.play_area_union(self.play_area, play_area_update)
        return True
     
    def draw_move_options(self):
        '''Outlines tiles where moves or actions are possible, designated by colour
        '''
        # cycle through the various highlights' grid coordinates, outlining the tiles that can and can't be subject to moves
        for highlight_type in highlights:
            if highlights[highlight_type]:
                scaled_highlight = pygame.transform.scale(highlight_library[highlight_type]
                    , [self.tile_width, self.tile_height])
                for tile_coords in highlights[highlight_type]:
                    self.window.blit(scaled_highlight, tile_coords)
    
    def draw_tokens(self):
        '''Illustrates the current location of Adventurers and Agents in a game, along with their paths over the last turn
        '''
        # cycle through the players, drawing the adventurers and agents as markers
        players = self.players
        for player in players:
            #We'll want to differentiate players by colour and the offset from the tile location
            colour = player.colour
            player_offset = self.PLAYER_OFFSETS[players.index(player)]
            #Each player may have multiple Adventurers to draw
            adventurers = player.adventurers
            for adventurer in player.adventurers:
                # we want to draw a circle anywhere an Adventurer is, differentiating with offsets
                tile = adventurer.current_tile
                location = [self.origin[0] + tile.tile_position.longitude
                            , self.origin[1] + tile.tile_position.latitude]
                adventurer_offset = player_offset + self.ADVENTURER_OFFSETS[adventurers.index(adventurer)]
                # we want it to be coloured differently for each player
                # draw the filled circle 
                pygame.draw.circle(self.window, colour, location + adventurer_offset, self.token_size)
                token_label = token_font.render(str(adventurers.index(adventurer)+1), 1, (255,255,255))
                self.window.blit(token_label, location - (self.token_size // 2, self.token_size // 2))
                if type(adventurer) in [AdventurerRegular, AdventurerAdvanced]:
                    if adventurer.pirate_token:
                        # we'll outline pirates in black
                        pygame.draw.circle(self.window, (255, 255, 255), location + adventurer_offset, self.token_size // 2, width=self.outline_width)
            
            for agent in player.agents: 
                # we want to draw a square anywhere that an agent is
                tile = agent.current_tile
                location = [self.origin[0] + tile.tile_position.longitude
                            , self.origin[1] + tile.tile_position.latitude]
                #Agents will be differentiated by colour, but they will always have the same position because there will only be one per tile
                colour = player.colour
                agent_shape = pygame.Rect(location[0]*self.tile_width + self.AGENT_OFFSET[0]
                  , location[1]*self.tile_height + self.AGENT_OFFSET[1]
                  , 2.0*self.token_size, 2.0*self.token_size)
                # we'll only outline the Agents that are dispossessed
                if type(agent) in [AgentRegular, AgentAdvanced] and agent.is_dispossessed:
                        pygame.draw.rect(self.window, colour, agent_shape, width=self.outline_width)
                else:
                    #for a filled rectangle the fill method could be quicker: https://www.pygame.org/docs/ref/draw.html#pygame.draw.rect
                    self.window.fill(color, rect=agent_shape)
                token_label = token_font.render(str(agent.wealth), 1, (255,255,255))
                self.window.blit(token_label, location)
        return True
        
    def draw_scores(self):
        '''Prints a table of current wealth scores in players' Vaults and Adventurers' Chests
        '''        
        print("Creating a table of the wealth held by Players and their Adventurers")
        #Draw the column headings
        score_title = scores_font.render("Vault", 1, (255,255,255))
        self.window.blit(score_title, self.SCORES_POSITION)
        #Work out the maximum number of Adventurers in play, to only draw this many columns
        max_num_adventurers = 1
        score_title = scores_font.render("Chest #1", 1, (255,255,255))
        self.window.blit(score_title, self.SCORES_POSITION 
                         + (self.SCORES_FONT_SCALE * self.SCORES_SPACING, 0))
        for player in players:
            if len(player.adventurers) > max_num_adventurers:
                max_num_adventurers = len(player.adventurers)
                score_title = scores_font.render("Chest #"+str(max_num_adventurers)
                                                 , 1, (255,255,255))
                self.window.blit(score_title, self.SCORES_POSITION 
                    + (self.SCORES_FONT_SCALE * self.SCORES_SPACING * max_num_adventurers, 0))
        row_position = self.SCORES_POSITION[1]
        for player in players:
            #Shift to a new row
            row_position += self.SCORES_FONT_SCALE
            score_value = scores_font.render(str(player.vault_wealth), 1, player.colour)
            self.window.blit(score_value, self.SCORES_POSITION 
                             + (0, row_position))
            col_position = self.SCORES_POSITION[0]
            for adventurer in player.adventurers:
                    #Shift to a new column
                    col_position += self.SCORES_FONT_SCALE * self.SCORES_SPACING
                    score_value = scores_font.render(str(adventurer.wealth), 1, player.colour)
                    self.window.blit(score_value, self.SCORES_POSITION 
                                     + (col_position, row_position))

    def update(self):
        '''
        '''
        if self.me+self.otherplayer==36:
            self.didiwin=True if self.me>self.otherplayer else False
            return 1
        #sleep to make the game 60 fps
        self.move_timer -= 1
        self.clock.tick(60)
        connection.Pump()
        self.Pump()
        #clear the window
        self.window.fill(0)
        self.draw_play_area()
        self.draw_tokens()
        self.draw_scores()

        for event in pygame.event.get():
            #quit if the quit button was pressed
            if event.type == pygame.QUIT:
                exit()
     
        #update the window
        #@TODO at the point of seeking player input for an Adventurer for the first time this turn, clear its route history
        #Get mouse input and translate this into tile coordinates
        mouse = pygame.mouse.get_pos()
        xpos = int(math.ceil((mouse[0])/self.tile_width))
        ypos = int(math.ceil((mouse[1])/self.tile_height))
        #Highlight potential placements and place tiles, in response to mouse position and clicks
        try: 
            if not board[ypos][xpos]: self.window.blit(self.hoverlineh if is_horizontal else self.hoverlinev, [xpos*64+5 if is_horizontal else xpos*64, ypos*64 if is_horizontal else ypos*64+5])
        except:
            isoutofbounds=True
            pass
        if not isoutofbounds:
            alreadyplaced=board[ypos][xpos]
        else:
            alreadyplaced=False
        if pygame.mouse.get_pressed()[0] and not alreadyplaced and not isoutofbounds and self.turn and self.justplaced<=0:
            self.move_timer = MOVE_TIME_LIMIT
            if is_horizontal:
                self.boardh[ypos][xpos]=True
                self.Send({"action": "place", "x":xpos, "y":ypos, "is_horizontal": is_horizontal, "num": self.num, "gameid": self.gameid})
            else:
                self.boardv[ypos][xpos]=True
                self.Send({"action": "place", "x":xpos, "y":ypos, "is_horizontal": is_horizontal, "num": self.num, "gameid": self.gameid})
        pygame.display.flip()
    
    def finished(self):
        self.window.blit(self.gameover if not self.local_win else self.winningscreen, (0,0))
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
            pygame.display.flip()
    

    
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