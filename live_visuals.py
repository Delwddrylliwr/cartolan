'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import math
import pygame
#import pygame_menu
import sys
import os
import time
import base64
import random
import string
from PodSixNet.Connection import ConnectionListener, connection
from time import sleep
from base import CityTile, TileEdges, WindDirection
from regular import DisasterTile, AdventurerRegular, AgentRegular, MythicalTileRegular
from game import GameBeginner, GameRegular, GameAdvanced
from players_human import PlayerHuman
from players_heuristical import PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter
from players_heuristical import PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter, PlayerRegularPirate

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
    DIMENSION_BUFFER = 1 #the number of tiles by which the play area is extended when methods are called
    BACKGROUND_COLOUR = (38,50,66)
    PLAIN_TEXT_COLOUR = (255,255,255)
    TILE_BORDER = 0.02 #the share of grid width/height that is used for border
    TOKEN_SCALE = 0.2 #relative to tile sizes
    AGENT_SCALE = 1.75 #relative to Adventurer radius
    TOKEN_OUTLINE_SCALE = 0.25 #relative to token scale
    TOKEN_FONT_SCALE = 0.5 #relative to tile sizes
    SCORES_POSITION = [0.0, 0.0]
    SCORES_FONT_SCALE = 0.05 #relative to window size
    SCORES_SPACING = 1.5 #the multiple of the score pixel scale to leave for each number
    MOVE_COUNT_POSITION = [0.75, 0.0]
    PROMPT_POSITION = [0.0, 0.95]
    PROMPT_FONT_SCALE = 0.05 #relative to window size
    
    GENERAL_TILE_PATH = './images/'
    SPECIAL_TILE_PATHS = {"water_disaster":'./images/water_disaster.png'
                     , "land_disaster":'./images/land_disaster.png'
                     , "capital":'./images/capital.png'
                     , "mythical":'./images/mythical.png'
                     } #file paths for special tiles
    HIGHLIGHT_PATHS = {"move":'./images/option_valid_move.png'
                  , "invalid":'./images/option_invalid_move.png'
                  , "buy":'./images/option_buy.png'
                  , "attack":'./images/option_attack.png'
                  , "rest":'./images/option_rest.png'
                  }
    
    def __init__(self, game, dimensions, origin):
        #Retain game data
        self.players = game.players
        self.game = game
        self.dimensions = dimensions.copy()
        self.origin = origin.copy()
        
        print("Initialising state variables")
#        self.clock = pygame.time.Clock()
        self.move_timer = self.MOVE_TIME_LIMIT
        self.current_player_colour = "black"
        self.current_adventurer_number = 0
        self.highlights = {"move":[], "invalid":[], "buy":[], "attack":[]}
        self.current_move_count = None
        
        self.init_GUI()
        
    def init_GUI(self):
        print("Initialising the pygame window and GUI")
        pygame.init()
        self.window = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
        self.width, self.height = pygame.display.get_surface().get_size()
        pygame.display.set_caption("Cartolan - Trade Winds")
        self.window.fill(self.BACKGROUND_COLOUR) #fill the screen with white
#        self.window.fill(0) #fill the screen with black
#        self.backing_image = pygame.transform.scale(pygame.image.load('./images/cartolan_backing.png'), [self.width, self.height])
#        self.window.blit(self.backing_image, [0,0])
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
        #Import images
        self.init_graphics()
        #Update the display
        pygame.display.flip()
#        self.init_sound()
        
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
    
    def save_tile_rotations(self, tile_name, tile_image):
        '''For a particular tile image, adds all its rotations to the library
        '''
        #North East wind
        self.tile_image_library[tile_name+"TrueTrue"] = tile_image
        #South East wind
        self.tile_image_library[tile_name+"FalseTrue"] = pygame.transform.rotate(tile_image.copy(), -90)
        #South West wind
        self.tile_image_library[tile_name+"FalseFalse"] = pygame.transform.rotate(tile_image.copy(), 180)
        #North West wind
        self.tile_image_library[tile_name+"TrueFalse"] = pygame.transform.rotate(tile_image.copy(), 90)
    
    def rescale_images(self, image_library, new_size):
        '''For a particular image library, rescales all of the images
        '''
        for image_type in image_library:
            image = image_library[image_type]
            image_library[image_type] = pygame.transform.scale(image, [new_size, new_size])

    def init_graphics(self):
        '''Reads in the images for visualising play
        '''
        print("Importing tile and highlight images and establishing a mapping")
        self.tile_image_library = {}
        for tile_name in self.SPECIAL_TILE_PATHS:
            tile_image = pygame.image.load(self.SPECIAL_TILE_PATHS[tile_name])
            self.save_tile_rotations(tile_name, tile_image)
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
                            tile_image = pygame.image.load(self.GENERAL_TILE_PATH +filename+ '.png')
                            tile_name = str(uc_water)+str(ua_water)+str(dc_water)+str(da_water)+str(wonder)
                            #Rotate the image for different wind directions
                            self.save_tile_rotations(tile_name, tile_image)
        # import the masks used to highlight movement options
        self.highlight_library = {}
        for highlight_name in self.HIGHLIGHT_PATHS:
            highlight_image = self.HIGHLIGHT_PATHS[highlight_name]
            self.highlight_library[highlight_name] = pygame.image.load(highlight_image)
        #adjust the size of the imported images to fit the display size
        self.rescale_graphics()

    def rescale_graphics(self):
        '''Rescales images in response to updated dimensions for the play grid
        '''
        print("Updating the dimensions that will be used for drawing the play area")
#        self.dimensions = dimensions        
        #Tiles, tokens and text will need adjusting to the new dimensions
        #Tiles will be scaled to fit the smaller dimension
        max_tile_height = self.height // self.dimensions[1]
        max_tile_width = self.width // self.dimensions[0]
        if max_tile_height < max_tile_width:
            self.tile_size = max_tile_height
        else:
            self.tile_size = max_tile_width
        self.token_size = int(round(self.TOKEN_SCALE * self.tile_size)) #token size will be proportional to the tiles
        self.outline_width = math.ceil(self.TOKEN_OUTLINE_SCALE * self.token_size)
        self.token_font = pygame.font.SysFont(None, int(self.tile_size * self.TOKEN_FONT_SCALE)) #the font size for tokens will be proportionate to the window size
        #scale down the images as the dimensions of the grid are changed, rather than when placing
        #the tiles' scale will be slightly smaller than the space in the grid, to givea discernible margin
        bordered_tile_size = round(self.tile_size * (1 - self.TILE_BORDER))
        print("Updated tile size to be " +str(self.tile_size)+ " pixels, and with border: " +str(bordered_tile_size))
        self.rescale_images(self.tile_image_library, bordered_tile_size)
        self.rescale_images(self.highlight_library, self.tile_size)
    
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
    
    def rescale_as_needed(self):
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
        #@TODO introduce a check for changes needed, rather than always recalculating dimensions
#        if (self.dimensions[0] >= max_longitude - min_longitude + 1 + 2*self.DIMENSION_BUFFER
#            and self.origin[0] 
#            and self.dimensions[1] >= max_latitude - min_latitude + 1 + 2*self.DIMENSION_BUFFER
#            and ):
#            #No reason to change anything 
#            #@TODO may still need to update the origin
#            return False
        self.dimensions[0] = max_longitude - min_longitude + 1 + 2*self.DIMENSION_BUFFER
        self.dimensions[1] = max_latitude - min_latitude + 1 + 2*self.DIMENSION_BUFFER
        #Check whether the current dimensions are too great for the display size
        if (self.dimensions[0]*self.tile_size > self.width
                or self.dimensions[1]*self.tile_size > self.height):
#            print("Reducing the size of tile graphics to fit within the new dimensions")
            self.rescale_graphics()
        #Check whether one of the dimensions has slack space and displace the origin to centre the play
        #Set the origin so that the play will be as central as possible
        self.origin[0] = -min_longitude + self.DIMENSION_BUFFER
        width_needed = self.dimensions[0]*self.tile_size
        if width_needed + 2*self.tile_size < self.width:
#            print("Extending grid width because the screen width is more generous than needed")
            extra_cols = math.floor((self.width - width_needed)/self.tile_size) #the excess in tiles
            self.dimensions[0] += extra_cols
            self.origin[0] += extra_cols // 2
        self.origin[1] = -min_latitude + self.DIMENSION_BUFFER
        height_needed = self.dimensions[1]*self.tile_size
        if height_needed + 2*self.tile_size < self.height:
#            print("Extending grid height because the screen height is more generous than needed")
            extra_rows = math.floor((self.height - height_needed)/self.tile_size) #the excess in tiles
            self.dimensions[1] += extra_rows
            self.origin[1] += extra_rows // 2
#        print("Dimensions are now: "+str(self.dimensions[0])+", "+str(self.dimensions[1]))
#        print("Origin is now: "+str(self.origin[0])+", "+str(self.origin[1]))
        return True
        
    
    def window_resize(self, resize_event):
        '''Deals with resizing of the window
        '''
        new_width, new_height = resize_event.w, resize_event.h 
        reload_needed = False #keep track of whether graphics are being scaled up, which would need the original PNGs to be reloaded
        if new_width > self.width or new_height > self.height:
            reload_needed = True
        self.width, self.height = new_width, new_height
        pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
        if reload_needed:
            self.init_graphics() #reload the PNG images
        else:
            self.rescale_graphics()
        #Now update text sizes too
        self.scores_font = pygame.font.SysFont(None, round(self.height * self.SCORES_FONT_SCALE)) #the font size for scores will be proportionate to the window size
        self.prompt_font = pygame.font.SysFont(None, round(self.height * self.PROMPT_FONT_SCALE)) #the font size for prompt will be proportionate to the window size
        self.prompt_position = [self.PROMPT_POSITION[0]*self.width, self.PROMPT_POSITION[1]*self.height]
        pygame.font.init()
        self.draw_play_area()
        self.draw_move_options()
        self.draw_routes()
        self.draw_tokens()
        self.draw_scores()
        self.draw_prompt()
        pygame.display.flip()
       
            
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
        self.rescale_as_needed()
        #Clear what's already been drawn
        self.window.fill(self.BACKGROUND_COLOUR)
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
                        tile_name = "capital"
                    else:
                        tile_name = "mythical"
                elif isinstance(tile, DisasterTile):
                    if tile.tile_back == "water":
                        tile_name = "water_disaster"
                    else:
                        tile_name = "land_disaster"
                else:
                    wonder = str(tile.is_wonder)
                    uc = str(e.upwind_clock_water)
                    ua = str(e.upwind_anti_water)
                    dc = str(e.downwind_clock_water)
                    da = str(e.downwind_anti_water)
                    tile_name = uc + ua + dc + da + wonder
                north = str(tile.wind_direction.north)
                east = str(tile.wind_direction.east)
                tile_image = self.tile_image_library[tile_name + north + east]
                #place the tile image in the grid
                horizontal = self.get_horizontal(longitude)
                vertical = self.get_vertical(latitude)
#                print("Placing a tile at pixel coordinates " +str(horizontal*self.tile_size)+ ", " +str(vertical*self.tile_size))
                self.window.blit(tile_image, [horizontal*self.tile_size, vertical*self.tile_size])
        # # Keep track of what the latest play_area to have been visualised was
        # self.play_area = self.play_area_union(self.play_area, play_area_update)
        return True
    
    #@TODO highlight the particular token(s) that an action relates to
    #display the number of moves since resting
    def draw_move_options(self, moves_since_rest=None, valid_coords=None, invalid_coords=None, chance_coords=None
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
        #Report the number of moves that have been used so far:
        #@TODO report the number of tiles in each bag in the same part of the display
        if moves_since_rest:
            move_count = self.scores_font.render(str(moves_since_rest)+" moves since rest", 1, self.PLAIN_TEXT_COLOUR)
            displacement = len(self.game.tile_piles) * self.SCORES_FONT_SCALE * self.height
            move_count_position = [self.MOVE_COUNT_POSITION[0] * self.width, self.MOVE_COUNT_POSITION[1] * self.height + displacement]
            self.window.blit(move_count, move_count_position)
        
    
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
                token_label = self.token_font.render(str(adventurers.index(adventurer)+1), 1, self.PLAIN_TEXT_COLOUR)
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
                  , self.AGENT_SCALE*self.token_size, self.AGENT_SCALE*self.token_size)
                # we'll only outline the Agents that are dispossessed
                if isinstance(agent, AgentRegular) and agent.is_dispossessed:
                        pygame.draw.rect(self.window, colour, agent_shape, self.outline_width)
                else:
                    #for a filled rectangle the fill method could be quicker: https://www.pygame.org/docs/ref/draw.html#pygame.draw.rect
                    self.window.fill(colour, rect=agent_shape)
                token_label = self.token_font.render(str(agent.wealth), 1, self.PLAIN_TEXT_COLOUR)
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
        score_title = self.scores_font.render("Vault", 1, self.PLAIN_TEXT_COLOUR)
        scores_position = [self.SCORES_POSITION[0] * self.width, self.SCORES_POSITION[1] * self.height]
        self.window.blit(score_title, scores_position)
        #Work out the maximum number of Adventurers in play, to only draw this many columns
        max_num_adventurers = 1
        for player in self.players:
            if len(game.adventurers[player]) > max_num_adventurers:
                max_num_adventurers = len(game.adventurers[player])
        for adventurer_num in range(1, max_num_adventurers + 1):
                score_title = self.scores_font.render("Chest #"+str(adventurer_num), 1, self.PLAIN_TEXT_COLOUR)
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
        #Draw the numbers of tiles in each pile
        displacement = 0
        for tile_back in self.game.tile_piles:
            tiles = self.game.tile_piles[tile_back].tiles
            tile_count = self.scores_font.render(str(len(tiles))+" tiles left in "+tile_back+" bag", 1, self.PLAIN_TEXT_COLOUR)
            tile_count_position = [self.MOVE_COUNT_POSITION[0] * self.width, self.MOVE_COUNT_POSITION[1] * self.height + displacement]
            self.window.blit(tile_count, tile_count_position)
            displacement += self.SCORES_FONT_SCALE * self.height
    
    def draw_prompt(self):
        '''Prints a prompt on what moves/actions are available to the current player
        '''        
#        print("Creating a prompt for the current player")
        #Establish the colour (as the current player's)
        prompt = self.prompt_font.render(self.prompt_text, 1, pygame.Color(self.current_player_colour))
        self.window.blit(prompt, self.prompt_position)
    
    def start_turn(self, player_colour):
        '''Identifies the current player by their colour, affecting prompts
        '''
        self.current_player_colour = player_colour
    
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
            if event.type == pygame.VIDEORESIZE:
                self.window_resize(event)
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
        #at the point of seeking player input for an Adventurer for the first time this turn, clear its route history
        
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
#    GAME_TYPES = {"Beginner":GameBeginner, "Regular":GameRegular, "Advanced":GameAdvanced}
    GAME_MODES = { 'Beginner':{'game_type':GameBeginner, 'player_set':{"blue":PlayerBeginnerExplorer
                                                                   , "red":PlayerBeginnerTrader
                                                                   , "yellow":PlayerBeginnerRouter
#                                                                    , "green":PlayerBeginnerGenetic
                                                                   , "orange":PlayerBeginnerExplorer
                                                                      }}
              , 'Regular':{'game_type':GameRegular, 'player_set':{
                                                                  "orange":PlayerRegularPirate
                                                                    , "blue":PlayerRegularExplorer
                                                                   , "red":PlayerRegularTrader
                                                                   , "yellow":PlayerRegularRouter
#                                                                    , "green":PlayerRegularGenetic
                                                                  }}
        }
    UPDATE_DELAY = 0.01 #the time in seconds to wait between checking for messages from the server
    SERVER_PROMPT = "Hit enter to join the Fry Super Adventurers' Club Server, or type the address of another: "
    DEFAULT_SERVER = "51.38.83.99", 8000
    
    def __init__(self):
        #Network state data:
        self.local_player_turn = False # Keep track of whether to wait on local player input for updates to visuals, 
        self.local_win = False
        self.running = False
        self.shared_play_area = {}
        self.shared_tokens = {"adventurers":{}, "agents":{}}
        self.shared_scores = {}
        self.shared_move_count = None
        self.moves_since_rest = None
        #@TODO provide a simple window for exchanges with the server
        
        #Establish connection to the server
        address = input(self.SERVER_PROMPT)
        try:
            if not address:
                host, port = self.DEFAULT_SERVER
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
            sleep(self.UPDATE_DELAY)
    
    def Network_handshake(self, data):
        '''Confirms to the server that this is a Cartolan client, not a random ping.
        '''
        #@TODO add version information into handshake, to allow compatibility check
        self.Send({"action":"handshake", "handshake":"handshake"})
    
    def update(self):
        '''Redraws visuals and seeks player input, passing it to the server to pass to the server-side Player
        '''
        #Process any messages from the server
        connection.Pump()
        self.Pump()
        #clear the window and redraw everything (using super methods to avoid trying to update the server when it was the one to pass info)
        self.window.fill(self.BACKGROUND_COLOUR)
        super().draw_play_area()
        super().draw_tokens()
        self.draw_routes()
        super().draw_scores()
        self.draw_prompt()
        self.draw_move_options(moves_since_rest=self.moves_since_rest)
        #If the game has ended then stop player input and refreshing
        if self.game.game_over:
            self.game_vis.give_prompt(self.game.winning_player.colour+" player won the game (click to close)")
            self.get_input_coords()
            self.close()
        #Check whether the player has decided to quit while waiting
        events = pygame.event.get()
        event_types = [event.type for event in events]
        if pygame.QUIT in event_types:
            self.close()
        if pygame.VIDEORESIZE in event_types:
            for event in reversed(events):
                if event.type == pygame.VIDEORESIZE:
                    self.window_resize(event)

        #Update the display
        pygame.display.flip()
    
    def Network_input(self, data):
        '''Responds to requests from the server for input.
        '''
        print("Received request for simple input from server")
        response = ''
        while response not in data["valid_options"]:
            response = input(data["input_prompt"])
            print("Responding to the server: '"+response+"'")
        self.Send({"action":"input", "input":response})
        
    
    #Now for a set of methods that will use PodSixNet to respond to messages from the server to progress the game
    def Network_start_game(self, data):
        '''Initiates network game based on data following an {"action":"start_game"} message from the server
        '''
        self.local_player_colours = data["local_player_colours"]
        print("Setting up the local version of the game:")
        print(data)
        game_type = self.GAME_MODES[data["game_type"]]["game_type"] #needed to identify the class of other elements like Adventurers and Agents
        self.players = [] #to capture order of play
        self.player_colours = {} #to access Player objects quickly based on colour
        self.virtual_players = data["virtual_players"]
        for player_colour in data["player_colours"]:
            if player_colour in self.virtual_players:
                player = self.GAME_MODES[data["game_type"]]["player_set"][player_colour](player_colour)
            else:
                player = PlayerHuman(player_colour)
            self.players.append(player)
            self.player_colours[player_colour] = player 
        
        game = game_type(self.players)
        self.game = game
        #Informing players of this game visualisation
        for player in self.players:
            player.games[game.game_id]["game_vis"] = self
            self.shared_tokens["adventurers"][player.colour] = []
            self.shared_tokens["agents"][player.colour] = []
            self.shared_scores[player.colour] = 0
        print("Building the tile piles")
        game.setup_tile_pile("water")
        if isinstance(game, GameRegular):
            game.setup_tile_pile("land")
            game.tile_piles["land"].tiles.append(MythicalTileRegular(game))
        print("Placing the initial tiles and adventurers")
        self.Network_place_tiles({"tiles":data["initial_tiles"]})
        #@TODO adapt to use the Network_move_tokens method
        initial_adventurers = data["initial_adventurers"] #expects a dict of colours and list of 2-tuples giving the placement(s) of initial Adventurers for each player
        if not len(self.players) == len(initial_adventurers):
            raise Exception("Player attributes from Host have different lengths")
        for player in self.players:
            for adventurer_location in initial_adventurers[player.colour]:
                longitude = game.play_area.get(int(adventurer_location[0]))
                if longitude:
                    adventurer_tile = longitude.get(int(adventurer_location[1]))
                    if adventurer_tile:
                        adventurer = game_type.ADVENTURER_TYPE(game, player, adventurer_tile)
                    else:
                        raise Exception("Server tried to place on Adventurer where there was no tile")
        
        print("With proxy game and players set up, continuing the startup of a normal visual")
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
        origin = [-min_longitude + self.DIMENSION_BUFFER
                  , -min_latitude + self.DIMENSION_BUFFER
                  ]
        dimensions = [max_longitude + origin[0] + self.DIMENSION_BUFFER
                      , max_latitude + origin[1] + self.DIMENSION_BUFFER
                      ]
        super().__init__(game, dimensions, origin)
        
        #keep track of whether the game is active or waiting for the server to collect enough players
        self.running = True
        self.game.turn = 1
        self.current_player_colour = data["current_player_colour"]
        if self.current_player_colour in self.local_player_colours:
            self.local_player_turn = True
        else:
            self.local_player_turn = False
        
        print("Waiting and watching for it to be a local player's turn, before switching to local control and execution of the game")
        self.game.game_over = False
        while not self.game.game_over:
            #distinguish between local and remote play and hand control of the game to the remote player's computer as needed, through the server    
            while not self.local_player_turn:
                self.update()
                sleep(self.UPDATE_DELAY)
            
            print("Switching to local execution of the game, now it is a local player's turn")
            current_player = self.player_colours[self.current_player_colour]
            adventurers = self.game.adventurers[current_player]
            for adventurer in adventurers:
                print("Starting the turn for " +current_player.colour+ " Adventurer #" +str(adventurers.index(adventurer) + 1))
                self.Send({"action":"prompt", "prompt_text":self.current_player_colour +" player is moving their Adventurer #" +str(adventurers.index(adventurer)+1)})
                if adventurer.turns_moved < self.game.turn:
                    current_player.continue_turn(adventurer)
                    print() #to help log readability
                    
                    #check whether this adventurer's turn has won them the game
                    if self.game.check_win_conditions():
                        self.game.game_over = True
                        break
            #Make sure visuals are up to date and all changes have been shared to the server
            self.draw_play_area()
            #for virtual players, share their route
            if current_player.colour in self.virtual_players:
                for adventurer in adventurers:
                    for tile in adventurer.route:
                        adventurers_routes = [{} for i in range(len(adventurers))] #this adventurer#s moves are shared by their position in a list
                        adventurers_routes[adventurers.index(adventurer)] = {"longitude":tile.tile_position.longitude, "latitude":tile.tile_position.latitude}
                        self.Send({"action":"move_tokens", "changes":{"adventurers":{current_player.colour:adventurers_routes}, "agents":{}}})
            self.draw_routes()
            self.draw_tokens()
            self.draw_scores()
            if self.game.game_over:
                self.Send({"action":"declare_win", "winning_player_colour":self.game.winning_player.colour})
                connection.Pump()
                self.Pump()
                self.Network_declare_win({"winning_player_colour":self.game.winning_player.colour})
            print("Passing play to the next player")
            if self.players.index(current_player) < len(self.players) - 1:
                current_player = self.players[self.players.index(current_player) + 1]
                self.current_player_colour = current_player.colour
            else:
                #If this was the last player in the play order then the turn increases by 1
                current_player = self.players[0]
                self.game.turn += 1
                self.current_player_colour = current_player.colour
            if self.current_player_colour not in self.local_player_colours:
                #Reset the route to be visualised for this non-local player
                for adventurer in self.game.adventurers[current_player]:
                    adventurer.route = [adventurer.current_tile]
                self.local_player_turn = False
            if self.current_player_colour in self.virtual_players:
                #Reset the route to be visualised for this virtual player
                for adventurer in self.game.adventurers[current_player]:
                    adventurer.route = [adventurer.current_tile]
            self.clear_prompt()
            self.Send({"action":"new_turn", "turn":self.game.turn, "current_player_colour":self.current_player_colour})
    
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
        '''Informs local player(s) which player is currently expected to be moving
        '''
#        self.local_player_turn = data["local_player_turn"]
        self.game.turn = data["turn"]
        self.current_player_colour = data["current_player_colour"]
        print("Server has relayed that it is now the "+self.current_player_colour+" player's turn "+str(self.game.turn))
        if self.current_player_colour in self.local_player_colours:
            self.local_player_turn = True
            if self.current_player_colour in self.virtual_players:
                #Reset the route to be visualised for this virtual player
                current_player = self.player_colours[self.current_player_colour]
                for adventurer in self.game.adventurers[current_player]:
                    adventurer.route = [adventurer.current_tile]
        else:
            #Reset the route to be visualised for this non-local player
            current_player = self.player_colours[self.current_player_colour]
            for adventurer in self.game.adventurers[current_player]:
                adventurer.route = [adventurer.current_tile]
            self.local_player_turn = False

    
    def Network_place_tiles(self, data):
        '''Places tiles based on data following an {"action":"place_tile"} message from the server
        '''
        for tile_data in data["tiles"]:
            #read location to place at
            longitude = int(tile_data["longitude"])
            latitude = int(tile_data["latitude"])
            #Check whether this space is already occupied
            if self.game.play_area.get(longitude):
                if self.game.play_area[longitude].get(latitude):
                    raise Exception("Server tried to place a tile on top of another")   
            #read tile characteristics to visualise
            tile_type = tile_data["tile_type"]
            tile_back = tile_data["tile_back"]
            tile_edges_data = tile_data["tile_edges"]
            tile_edges = TileEdges(bool(tile_edges_data["upwind_clock"])
                    , bool(tile_edges_data["upwind_anti"])
                    , bool(tile_edges_data["downwind_clock"])
                    , bool(tile_edges_data["downwind_anti"])
                    )
            wind_direction_data = tile_data["wind_direction"]
            wind_direction = WindDirection(bool(wind_direction_data["north"])
                    , bool(wind_direction_data["east"])
                    )
            #Place the tile in the play area
            placed_tile = self.game.TILE_TYPES[tile_type](self.game, tile_back, wind_direction, tile_edges)
            placed_tile.place_tile(longitude, latitude)
            #Remember that this is already synched with the server
            if not self.shared_play_area.get(longitude):
                self.shared_play_area[longitude] = {}
            self.shared_play_area[longitude][latitude] = placed_tile    
            #remove a matching tile from the tile pile, once the game is running
            if self.running:
                tile_removed = False
                tile_pile = self.game.tile_piles[tile_back]
                for tile in tile_pile.tiles:
                    if isinstance(placed_tile, MythicalTileRegular) and isinstance(tile, MythicalTileRegular):
                        print("arrived")
                    if placed_tile.compare(tile): 
                        if tile.compare(placed_tile):
                            tile_pile.tiles.remove(tile)
                            tile_removed = True
                            break
                if not tile_removed:
                    raise Exception("Server placed a tile that was not in the Tile Pile")
    
    #@TODO update the record of shared changes so that remote changes are not re-shared
    def Network_move_tokens(self, data):
        '''Moves an Adventurer or Agent based on data following an {"action":"move_token"} message from the server
        '''
        changes = data["changes"]
        for player_colour in self.player_colours:
            player = self.player_colours[player_colour]
            adventurers_data = changes["adventurers"].get(player_colour)
            if adventurers_data:
                for adventurer_num in range(len(adventurers_data)):
                    adventurer_data = adventurers_data[adventurer_num]
                    #check if this is a new token and add them if so
                    if len(self.game.adventurers[player]) < adventurer_num + 1:
                        adventurer = self.game.ADVENTURER_TYPE(self.game, player, self.game.play_area[0][0])
                    else:
                        adventurer = self.game.adventurers[player][adventurer_num]
                    #read location to move to
                    longitude = adventurer_data.get("longitude")
                    latitude = adventurer_data.get("latitude")
                    #Check that the tile exists before moving the token there
                    if longitude is not None and latitude is not None:
                        longitude = int(longitude)
                        latitude = int(latitude)
                        if self.game.play_area.get(longitude):
                            tile = self.game.play_area.get(longitude).get(latitude)
                            if not tile:
                                raise Exception("Server has tried to place a token on a tile that doesn't exist")
                        else:
                            raise Exception("Server has tried to place a token on a tile that doesn't exist")
                        #Place the token on the tile at the coordinates
                        tile.move_onto_tile(adventurer)
                    #check whether wealth has also changed
                    wealth = adventurer_data.get("wealth")
                    if not wealth is None:
                        adventurer.wealth = int(wealth)
                    #check whether turns moved has also changed
                    turns_moved = adventurer_data.get("turns_moved")
                    if not turns_moved is None:
                        adventurer.turns_moved = int(turns_moved)
                    #check whether pirate token has also changed
                    pirate_token = adventurer_data.get("pirate_token")
                    if pirate_token is not None and isinstance(self.game, GameRegular):
                        adventurer.pirate_token = bool(pirate_token)
            agents_data = changes["agents"].get(player_colour)
            if agents_data:
                #This is hacky, but if an Agent has been lost, after being displaced and replaced by opponents, then the indexing will have changed and the whole Agents vector will be replaced
                if len(agents_data) < len(self.game.agents[player]):
                    for agent in self.game.agents[player]:
                        agent.current_tile.move_off_tile(agent)
                        self.game.agents[player].remove(agent)
                for agent_num in range(len(agents_data)):
                    agent_data = agents_data[agent_num]
                    #read location to move to
                    longitude = agent_data.get("longitude")
                    latitude = agent_data.get("latitude")
                    #Check that the tile exists before moving the agent there
                    if longitude is not None and latitude is not None:
                        longitude = int(longitude)
                        latitude = int(latitude)
                        if self.game.play_area.get(longitude):
                            tile = self.game.play_area[longitude].get(latitude)
                            if not tile:
                                raise Exception("Server has tried to place a agent on a tile that doesn't exist")
                        else:
                            raise Exception("Server has tried to place a agent on a tile that doesn't exist")
                        #Place the agent on the tile at the coordinates
                        #check if this is a new token and add them if so
                        if len(self.game.agents[player]) < agent_num + 1:
                            agent = self.game.AGENT_TYPE(self.game, player, tile)
                        else:
                            agent = self.game.agents[player][agent_num]
                            tile.move_onto_tile(agent)
                    else:
                        agent = self.game.agents[player][agent_num]
                    #check whether wealth has also changed
                    wealth = agent_data.get("wealth")
                    if not wealth is None:
                        agent.wealth = int(wealth)
                    #check whether dispossession has also changed
                    is_dispossessed = agent_data.get("is_dispossessed")
                    if is_dispossessed is not None and isinstance(self.game, GameRegular):
                        agent.is_dispossessed = bool(is_dispossessed)
    
    def Network_prompt(self, data):
        '''Receives prompt information from the server.
        '''
        self.prompt_text = data["prompt_text"]
    
    def Network_update_move_count(self, data):
        '''Receives updates to the move count of the active remote player
        '''
        self.moves_since_rest = data["move_count"]
    
    def Network_update_scores(self, data):
        '''Recieves updates to the players' Vault wealth from remote players, via the server
        '''
        changes = data["changes"]
        for player_colour in changes:
            player = self.player_colours[player_colour]
            player.vault_wealth = changes[player_colour]
            #Remember that this has already been synched with the remote players
            self.shared_scores[player] = player.vault_wealth
     
    def Network_declare_win(self, data):
        '''Notifies player who won the game based on data following an {"action":"end_game"} message from the server
        '''
        self.current_player_colour = data["winning_player_colour"]
        self.give_prompt(self.current_player_colour+" won the game")
        self.window.fill(self.BACKGROUND_COLOUR)
        super().draw_play_area()
        self.draw_routes()
        super().draw_tokens()
        super().draw_scores()
        self.draw_prompt()
        pygame.display.flip()
        #Wait for click to close
        self.get_input_coords(self.game.adventurers[self.player_colours[self.current_player_colour]][0])
        self.close()
    
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
        tiles_json = []
        for longitude in play_area_update:
            for latitude in play_area_update[longitude]:
                tile = play_area_update[longitude][latitude]
                tile_type = "plain"
                if tile.is_wonder:
                    tile_type = "wonder"
                elif isinstance(tile, DisasterTile):
                    tile_type = "disaster"                    
                elif isinstance(tile, CityTile):
                    if tile.is_capital:
                        tile_type = "capital"
                    else:
                        tile_type = "mythical"

                #record all the tile information in a json form that can be shared with other players via the server
                tile_data = {"longitude":longitude
                             , "latitude":latitude
                             , "tile_type":tile_type 
                             , "tile_back":tile.tile_back
                             }
                #serialise and add the tile edge and wind direction information 
                tile_edges_data = {"upwind_clock":tile.tile_edges.upwind_clock_water
                                   , "upwind_anti":tile.tile_edges.upwind_anti_water
                                   , "downwind_clock":tile.tile_edges.downwind_clock_water
                                   , "downwind_anti":tile.tile_edges.downwind_anti_water
                                   }
                tile_data["tile_edges"] = tile_edges_data
                wind_direction_data = {"north":tile.wind_direction.north
                                       , "east":tile.wind_direction.east
                                       }
                tile_data["wind_direction"] = wind_direction_data
                tiles_json.append(tile_data)
                #remember that this tile has been serialised (and will be shared)
                if not self.shared_play_area.get(longitude):
                    self.shared_play_area[longitude] = {}
                self.shared_play_area[longitude][latitude] = tile_data         
        if play_area_update:    
            self.Send({"action":"place_tiles", "tiles":tiles_json})
            print("Drawing the play area, with " +str(len(self.game.play_area))+" columns of tiles")
        else:
            print("No changes to play area, so nothing updating local or server")
        #Process any messages to the server
        connection.Pump()
        self.Pump()
        #Now continue with displaying locally
        super().draw_play_area()
    
    def draw_tokens(self):
        '''Identifies which tokens have changed position/status and passing them to the server
        '''
        #print(Comparing two different states of Agents and Adventurers, and returns only those that differ)
        player_tokens_json = {"adventurers":{}, "agents":{}}
        player_tokens_changes_json = {"adventurers":{}, "agents":{}}
        exist_changes = False
        for player in self.game.adventurers:
            adventurers = self.game.adventurers[player]
            adventurers_json = []
            adventurers_changes_json = []
            exist_token_changes = False
            for adventurer in adventurers:
                #make sure that the turns moved are shared for new adventurers
                #serialise the current data for record and comparison
                new_longitude = adventurer.current_tile.tile_position.longitude
                new_latitude = adventurer.current_tile.tile_position.latitude
                new_wealth = adventurer.wealth
                new_turns_moved = adventurer.turns_moved
                if not isinstance(self.game, GameRegular):
                    new_pirate_token = False
                else:
                    new_pirate_token = adventurer.pirate_token
                adventurer_data = {"longitude":new_longitude
                                   , "latitude":new_latitude
                                   , "wealth":new_wealth
                                   , "turns_moved":new_turns_moved
                                   , "pirate_token":new_pirate_token
                                   }
                adventurers_json.append(adventurer_data)                    
                #identify the old serialisation of this adventurer's data and compare to the adventurer's data and share where it differs
                adventurer_index = adventurers.index(adventurer)
                old_adventurers_data = self.shared_tokens["adventurers"][player.colour]
                if adventurer_index < len(old_adventurers_data):
                    adventurer_changes_data = {}
                    old_adventurer_data = old_adventurers_data[adventurer_index]
                    old_longitude = int(old_adventurer_data["longitude"])
                    old_latitude = int(old_adventurer_data["latitude"])
                    if not (new_longitude == old_longitude 
                            and new_latitude == old_latitude):
                        adventurer_changes_data["longitude"] = new_longitude
                        adventurer_changes_data["latitude"] = new_latitude
                        exist_token_changes = True
                    old_wealth = int(old_adventurer_data["wealth"])
                    if not (new_wealth == old_wealth):
                        adventurer_changes_data["wealth"] = new_wealth
                        exist_token_changes = True
                    old_turns_moved = int(old_adventurer_data["turns_moved"])
                    if not (new_turns_moved == old_turns_moved):
                        adventurer_changes_data["turns_moved"] = new_turns_moved
                        exist_token_changes = True
                    old_pirate_token = int(old_adventurer_data["pirate_token"])
                    if not (new_pirate_token == old_pirate_token):
                        adventurer_changes_data["pirate_token"] = new_pirate_token
                        exist_token_changes = True
                    adventurers_changes_json.append(adventurer_changes_data)
                else:
                    adventurers_changes_json.append(adventurer_data)
                    exist_token_changes = True
            player_tokens_json["adventurers"][player.colour] = adventurers_json
            if exist_token_changes:
                player_tokens_changes_json["adventurers"][player.colour] = adventurers_changes_json
                exist_changes = True
        #repeat for Agents
        for player in self.game.agents:
            agents = self.game.agents[player]
            agents_json = []
            agents_changes_json = []
            exist_token_changes = False
            for agent in agents:
                agent_changes_data = {}
                #serialise the adventurer's data for comparison now and in future
                new_longitude = agent.current_tile.tile_position.longitude
                new_latitude = agent.current_tile.tile_position.latitude
                new_wealth = agent.wealth
                if not isinstance(self.game, GameRegular):
                    new_is_dispossessed = False
                else:
                    new_is_dispossessed = agent.is_dispossessed
                agent_data = {"longitude":new_longitude
                                   , "latitude":new_latitude
                                   , "wealth":new_wealth
                                   , "is_dispossessed":new_is_dispossessed
                                   }
                agents_json.append(agent_data)
                #identify the old serialisation of this adventurer's data
                agent_index = agents.index(agent)
                old_agents_data = self.shared_tokens["agents"][player.colour]
                if agent_index < len(old_agents_data):
                    old_agent_data = old_agents_data[agent_index]
                    old_longitude = int(old_agent_data["longitude"])
                    old_latitude = int(old_agent_data["latitude"])
                    if not (new_longitude == old_longitude 
                            and new_latitude == old_latitude):
                        agent_changes_data["longitude"] = new_longitude
                        agent_changes_data["latitude"] = new_latitude
                        exist_token_changes = True
                    old_wealth = int(old_agent_data["wealth"])
                    if not (new_wealth == old_wealth):
                        agent_changes_data["wealth"] = new_wealth
                        exist_token_changes = True
                    old_is_dispossessed = old_agent_data["is_dispossessed"]
                    if not (new_is_dispossessed == old_is_dispossessed):
                        agent_changes_data["is_dispossessed"] = new_is_dispossessed
                        exist_token_changes = True
                    agents_changes_json.append(agent_changes_data)
                else:
                    agents_changes_json.append(agent_data)
                    exist_token_changes = True
            player_tokens_json["agents"][player.colour] = agents_json
            if exist_token_changes:
                player_tokens_changes_json["agents"][player.colour] = agents_changes_json
                exist_changes = True
#        if player_token_changes_json["adventurers"] or player_token_changes_json["adventurers"] and self.running:
        if exist_changes and self.running:
            print("Having found changes to the tokens, sharing these with other players via the server")
            self.Send({"action":"move_tokens", "changes":player_tokens_changes_json})
            self.shared_tokens = player_tokens_json
        #Process any messages to the server
        connection.Pump()
        self.Pump()
        #Now continue with displaying locally
        super().draw_tokens()
    
    def draw_move_options(self, moves_since_rest=None, valid_coords=None, invalid_coords=None, chance_coords=None
                          , buy_coords=None, attack_coords=None, rest_coords=None):
        '''Passes changes in the number of remaining moves to the server
        '''
        #print("Comparing the last reported move count with the current move count")
        if not moves_since_rest == self.shared_move_count:
            self.Send({"action":"update_move_count", "move_count":moves_since_rest})
            self.shared_move_count = moves_since_rest
        #Process any messages to the server
        connection.Pump()
        self.Pump()
        #Now continue with displaying locally
        super().draw_move_options(moves_since_rest, valid_coords, invalid_coords, chance_coords
                          , buy_coords, attack_coords, rest_coords)
        
    
    def draw_scores(self):
        '''Passes changed scores to the server, before drawing a table locally
        '''        
        #print("Comparing local scores to what has previously been shared, and updating the server accordingly")
        player_wealths_json = {}
        player_wealth_changes_json = {}
        exist_changes = False
        for player in self.players:
            #serialise the players' Vault wealths and compare to historic
            if not self.shared_scores[player.colour] == player.vault_wealth:
                player_wealth_changes_json[player.colour] = player.vault_wealth
                exist_changes = True
            player_wealths_json[player.colour] = player.vault_wealth
        if exist_changes and self.running:
            self.Send({"action":"update_scores", "changes":player_wealth_changes_json})
            self.shared_scores = player_wealths_json
        #Process any messages to the server
        connection.Pump()
        self.Pump()
        #Now continue with displaying locally
        super().draw_scores()


class WebServerVisualisation(GameVisualisation):
    '''For a server-side game played in browser, shares image of play area and receives coords
    
    There will be a separate visual for each client.
    Because the clients all need to see every move, each visual will send for every player.
    But, only the moving player's visual will receive input. 
    '''
    TEMP_FILENAME_LEN = 6
    TEMP_FILE_EXTENSION = ".png"
    INPUT_DELAY = 0.1 #delay time between checking for input, in seconds
    
    def __init__(self, game, dimensions, origin, client, width, height):
        self.client = client
        self.width, self.height = width, height
        self.client_players = []
        super().__init__(game, dimensions, origin)
    
    def init_GUI(self):
        print("Initialising the pygame window and GUI")
        pygame.init()
        self.window = pygame.Surface((self.width, self.height))
        self.window.fill(self.BACKGROUND_COLOUR) #fill the screen with white
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
        #Import images
        self.init_graphics()
    
    #@TODO other clients are likely not updating because they are getting none of the visual updates prompted by their opponents' moves
    def update_web_display(self):
        '''For this client visualisation in particular, send out an image of the play area.
        '''
#        pygame.display.flip()
        #generate a random filename, to avoid thread conflicts
        randname = ( ''.join(random.choice(string.ascii_lowercase) for i in range(self.TEMP_FILENAME_LEN)) )
        #@TODO could reduce file size and latency by compressing into a lossy jpg
        pygame.image.save(self.window, randname + self.TEMP_FILE_EXTENSION)
        out = open(randname + self.TEMP_FILE_EXTENSION,"rb").read()
        self.client.sendMessage("IMAGE[00100]"+str(base64.b64encode(out)))
        print("data sent to client at "+str(self.client.address))
        os.remove(randname + self.TEMP_FILE_EXTENSION)
        
    
    def get_input_coords(self, adventurer):
        '''Sends an image of the latest play area, accepts input only from this visual's players.
        
        Arguments
        adventurer takes a Cartolan.Adventurer
        '''
        #print("Updating the display for all the other human players, whose visuals won't have been consulted.")
        for player in self.game.players:
            if isinstance(player, PlayerHuman):
                print("Updating visuals for player "+str(self.game.players.index(player)+1)+" with visual "+str(player.games[self.game.game_id]["game_vis"]))
                game_vis = player.games[self.game.game_id]["game_vis"]
                if not self.client == game_vis.client:
                    print("Recognised that this player is using a different client: "+str(game_vis.client.address))
                    game_vis.draw_play_area()
                    game_vis.draw_tokens()
                    game_vis.draw_routes()
                    game_vis.draw_scores()
                    moves_since_rest = adventurer.downwind_moves + adventurer.upwind_moves + adventurer.land_moves
                    game_vis.draw_move_options(moves_since_rest)
                game_vis.update_web_display()
        
        coords = None
        while coords is None:
            coords = self.client.get_coords()
            if coords is not None:
                horizontal, vertical = coords
                longitude = int(math.ceil((horizontal)/self.tile_size)) - self.origin[0] - 1
                latitude = self.dimensions[1] - int(math.ceil((vertical)/self.tile_size)) - self.origin[1]
                if True:
                    self.highlights = {"move":[], "invalid":[], "buy":[], "attack":[]} #clear the highlights until the server offers more
                    return [longitude, latitude]
            time.sleep(self.INPUT_DELAY)
#        print("Waiting for input from the user")
#        while True:
#            data = self.socket.recv()
#            code, value = data.split('[00100]')
#            
#            if code == "COORDS":
#                horizontal, vertical = value.split('[66666]')
#                self.move_timer = self.MOVE_TIME_LIMIT #reset the timelimit on moving
#                longitude = int(math.ceil((horizontal)/self.tile_size)) - self.origin[0] - 1
#                latitude = self.dimensions[1] - int(math.ceil((vertical)/self.tile_size)) - self.origin[1]
#                #check whether the click was within the highlighted space and whether it's a local turn
##                highlighted_option = self.check_highlighted(longitude, latitude)
##                print("Click was a valid option of type: " + highlighted_option)
#                if True:
##                if highlighted_option is not None:
#                    self.highlights = {"move":[], "invalid":[], "buy":[], "attack":[]} #clear the highlights until the server offers more
##                    print("Have identified a move available at " +str(longitude)+ ", " +str(latitude)+ " of type " +str(highlighted_option))
#                    return [longitude, latitude]

        #@TODO introduce move timer and compare to time limit
        
        return False


#class GameMenu():
#    '''Generates a standalone menu window for parametrising games.
#    '''
#    MENU_SHAPE = 0.5
#    
#    def __init__(self):
#        pygame.init()
#        self.window = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
#        pygame.display.set_caption("Setting up Cartolan - Trade Winds")
#        self.width, self.height = pygame.display.get_surface().get_size()
##        splash_image = pygame.image.load(self.GENERAL_TILE_PATH +'splash_screen.png')
##        if splash_image.width < self.width:
##            new_width = self.width
##            new_height = self.width * splash_image.height / splash_image.width
##            splash_image = pygame.transform.scale(splash_image, [new_width, new_height])
#                
#        self.menu = pygame_menu.Menu(self.MENU_SHAPE * self.width
#                                     , self.MENU_SHAPE * self.height, 'Configure game'
#                                     , theme=pygame_menu.themes.THEME_BLUE)