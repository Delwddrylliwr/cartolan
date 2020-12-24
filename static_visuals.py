import matplotlib.image as mpimg # for importing tile images
import math
import tkinter
from matplotlib import pyplot # for plotting the tiles in a grid
from scipy import ndimage # for rotating tiles
import numpy
from base import CityTile
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