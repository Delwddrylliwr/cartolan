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
from collections import deque
#from PodSixNet.Connection import ConnectionListener, connection
#from time import sleep
from base import Player, CityTile #, TileEdges, WindDirection
from regular import DisasterTile, AdventurerRegular, AgentRegular #, MythicalTileRegular
from advanced import AdventurerAdvanced
from game import GameBeginner, GameRegular, GameAdvanced
from players_human import PlayerHuman
#from players_heuristical import PlayerBeginnerExplorer, PlayerBeginnerTrader, PlayerBeginnerRouter
#from players_heuristical import PlayerRegularExplorer, PlayerRegularTrader, PlayerRegularRouter, PlayerRegularPirate
#from players_heuristical import PlayerAdvancedExplorer, PlayerAdvancedTrader, PlayerAdvancedRouter, PlayerAdvancedPirate

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
    BACKGROUND_COLOUR = (38,50,60) #(38,50,66)
    PLAIN_TEXT_COLOUR = (255,255,255)
    WONDER_TEXT_COLOUR = (0,0,0)
    ACCEPT_UNDO_COLOUR = (255, 0, 0)
    CARD_TEXT_COLOUR = (0,0,0)
    CARD_BACKGROUND_COLOUR = (255,255,255)
    CHEST_HIGHLIGHT_COLOUR = (0, 255, 0)
    TOGGLE_TRUE_COLOUR = (0, 255, 0)
    TOGGLE_FALSE_COLOUR = (255, 0, 0)
    TILE_BORDER = 0.02 #the share of grid width/height that is used for border
    CARD_HEADER_SHARE = 0.15 # the share of card images that is the header, visually summarising the buffs of the card with colour and a logo
    CARD_BODY_START = 0.7 # the share of the card before text starts
    LEFT_MENU_SCALE = 0.13
    MENU_TILE_COLS = 2
    RIGHT_MENU_SCALE = 0.13
    OFFER_SCALE = 0.15
    ROUTE_THICKNESS = 4.0
    TOKEN_SCALE = 0.2 #relative to tile sizes
    AGENT_SCALE = 1.75 #relative to Adventurer radius
    TOKEN_OUTLINE_SCALE = 0.25 #relative to token scale
    TOKEN_FONT_SCALE = 0.5 #relative to tile sizes
    TOKEN_FONT_COLOURS = {"yellow":"black"}
    SCORES_POSITION = [0.0, 0.0]
    SCORES_FONT_SCALE = 0.05 #relative to window size
    SCORES_SPACING = 1.5 #the multiple of the score pixel scale to leave for each number
    CARD_FONT_SCALE = 0.03
    MOVE_COUNT_POSITION = [0.8, 0.0]
    PROMPT_SHARE = 0 #@TODO move prompt into the bottom right corner, with multi-line
    PROMPT_POSITION = [0.0, 0.95]
    PROMPT_FONT_SCALE = 0.05 #relative to window size
    
    GENERAL_TILE_PATH = './images/'
    CARDS_PATH = './images/cards/'
    SPECIAL_TILE_PATHS = {"water_disaster":'./images/water_disaster.png'
                     , "land_disaster":'./images/land_disaster.png'
                     , "capital":'./images/capital.png'
                     , "mythical":'./images/mythical.png'
                     } #file paths for special tiles
    HIGHLIGHT_PATHS = {"move":'./images/option_valid_move.png'
                  , "abandon":'./images/option_abandon.png'
                  , "invalid":'./images/option_invalid_move.png'
                  , "buy":'./images/option_buy.png'
                  , "attack":'./images/option_attack.png'
                  , "rest":'./images/option_rest.png'
                  , "move_agent":'./images/option_valid_move.png'
                  , "agent_transfer":'./images/option_buy.png'
                  }
    TOGGLE_HIGHLIGHTS = ["buy", "attack", "rest"]
    CARD_TITLES = {"com+rests":"The Inrepid Academy"
            , "com+transfers":"The Great Company"
            , "com+earning":"The Merchants' Guild"
            , "com+arrest":"The Harbour Authority"
            , "com+refurnish":"The Privateer Brethren"
            , "com+pool":"Order of the Lightbrary"
            }
    CARD_TEXTS = {"adv+agents":"Place and immediately rest with Agents on existing tiles, for 3 treasure."
             , "adv+attack":"Need only win or draw Rock-Paper-Scissors to be successful when attacking."
             , "adv+bank":"Treasure can be moved at any time to any Agent."
             , "adv+damage":"Losing opponents are returned to the last city visited, and Agents are fully removed."
             , "adv+defence":"When defending, opponents have to win Rock-Paper-Scissors twice to succeed."
             , "adv+downwind":"Up to six moves each turn and after resting."
             , "adv+upwind":"The first three moves can be in any direction, each turn or after resting."
             , "adv+maps":"Carry up to three map tiles in Chest."
             , "dis+agents":"Place and immediately rest with Agents on existing tiles, for 3 treasure."
             , "dis+attack":"Need only win or draw Rock-Paper-Scissors to be successful when attacking."
             , "dis+bank":"Treasure can be moved at any time to any Agent."
             , "dis+damage":"Losing opponents are returned to the last city visited, and Agents are fully removed."
             , "dis+defence":"When defending, opponents have to win an extra round of Rock-Paper-Scissors to succeed."
             , "dis+downwind":"Two more moves each turn and after resting."
             , "dis+upwind":"One more move can be in any direction, each turn and after resting."
             , "dis+maps":"Carry an extra map tile in their chest."
             , "com+rests":"Adventurers can rest with Adventurers. Draw 3 Adventurers."
            , "com+transfers":"Treasure earned by Agents goes to the Vault. Draw 3 Manuscript cards."
            , "com+earning":"Agents earn 1 treasure when opponents trade on their tile. Draw 3 Manuscript cards."
            , "com+arrest":"Agents try to arrest pirates landing on their tile. Arresting takes the Pirate’s treasure as well as the reward. Draw 3 Adventurers."
            , "com+refurnish":"The pirate token can be lost by resting. Draw 3 Adventureres."
            , "com+pool":"Map tiles are pooled across all Adventurers. Maps can be swapped at Agents for 1 treasure. Draw 3 Manuscript cards."
            }
    
    def __init__(self, game, peer_visuals, player_colours):
        #Retain game data
        self.player_colours = player_colours
        self.game = game
        self.dimensions = [len(game.play_area), max([len(game.play_area[longitude]) for longitude in game.play_area])]
        self.origin = [dimension // 2 for dimension in self.dimensions]
        self.peer_visuals = peer_visuals
        
        print("Initialising state variables")
#        self.clock = pygame.time.Clock()
        self.move_timer = self.MOVE_TIME_LIMIT
        self.current_player_colour = "black"
        self.current_adventurer_number = 0
        self.current_adventurer = None
        self.viewed_player_colour = "black"
        self.viewed_adventurer_number = 0
        self.viewed_adventurer = None
        self.highlights = {highlight_type:[] for highlight_type in self.HIGHLIGHT_PATHS}
        self.highlight_rects = []
        self.drawn_routes = []
        self.offer_rects = []
        #Placeholders for the various GUI elements
        self.scores_rect = (0, 0, 0, 0)
        self.stack_rect = (0, 0, 0, 0)
        self.current_move_count = None
        self.move_count_rect = (self.MOVE_COUNT_POSITION[0], self.MOVE_COUNT_POSITION[1], 0, 0)
        self.chest_rect = (self.MOVE_COUNT_POSITION[0], self.MOVE_COUNT_POSITION[1], 0, 0)
        self.toggles_rect = (self.MOVE_COUNT_POSITION[0], self.MOVE_COUNT_POSITION[1], 0, 0)
        self.toggle_rects = []
        self.piles_rect = (self.MOVE_COUNT_POSITION[0], self.MOVE_COUNT_POSITION[1], 0, 0)
        self.undo_rect = (self.width, self.height, 0, 0)
        self.undo_agreed = False
        self.adventurer_centres = []
        self.agent_rects = []
        if isinstance(self.game, GameAdvanced):
            self.selected_card_num = None
            self.card_images = {}
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
        #We'll have a different tile size for dicards
        self.menu_tile_size = round(self.RIGHT_MENU_SCALE * self.width) // self.MENU_TILE_COLS
        #Where piracy is possible, we'll have a different tile size for 
        self.offer_tile_size = round(self.OFFER_SCALE * self.width)
        #Before sizing against the horizontal dimension, we'll work out how much space the menus will take away
        self.play_area_width = round(self.width * (1 - self.LEFT_MENU_SCALE - self.RIGHT_MENU_SCALE))
        self.play_area_start = round(self.width * self.LEFT_MENU_SCALE)
        self.right_menu_width = round(self.width * self.RIGHT_MENU_SCALE)
        self.right_menu_start = self.play_area_start + self.play_area_width
        self.right_text_start = self.MOVE_COUNT_POSITION[0] * self.width #All text indicators in the right menu will follow the same indent
        self.menu_highlight_size = round(self.RIGHT_MENU_SCALE * self.width) // len(self.TOGGLE_HIGHLIGHTS)
        #Tiles will be scaled to fit the smaller dimension
        if self.play_area_width < self.tile_size * self.dimensions[0]:
            self.tile_size = self.play_area_width // self.dimensions[0]
        self.token_size = round(self.TOKEN_SCALE * self.tile_size) #token size will be proportional to the tiles
        self.outline_width = math.ceil(self.TOKEN_OUTLINE_SCALE * self.token_size)
        self.token_font = pygame.font.SysFont(None, round(self.tile_size * self.TOKEN_FONT_SCALE)) #the font size for tokens will be proportionate to the window size
        self.scores_font = pygame.font.SysFont(None, round(self.height * self.SCORES_FONT_SCALE)) #the font size for scores will be proportionate to the window size
        self.card_font = pygame.font.SysFont(None, round(self.height * self.CARD_FONT_SCALE)) #the font size for scores will be proportionate to the window size
        self.prompt_font = pygame.font.SysFont(None, round(self.height * self.PROMPT_FONT_SCALE)) #the font size for prompt will be proportionate to the window size
        self.prompt_position = [self.play_area_start + self.PROMPT_POSITION[0]*self.width
                                , self.PROMPT_POSITION[1]*self.height]
        pygame.font.init()
        self.prompt_text = ""
        #Make sure that the GUI menus are drawn on the correct sides from the start
        self.scores_rect = (0, 0, 0, 0)
        self.stack_rect = (0, 0, 0, 0)
        self.current_move_count = None
        self.move_count_rect = (self.MOVE_COUNT_POSITION[0]*self.width, self.MOVE_COUNT_POSITION[1]*self.height, 0, round(self.height * self.SCORES_FONT_SCALE))
        self.toggles_rect = (self.right_menu_start, self.move_count_rect[1]+self.move_count_rect[3], 0, self.menu_tile_size+round(self.height * self.SCORES_FONT_SCALE))
        self.chest_rect = (self.right_menu_start, self.toggles_rect[1]+self.toggles_rect[3]+round(self.height * self.SCORES_FONT_SCALE), 0, self.menu_tile_size)
        self.piles_rect = (self.right_menu_start, self.toggles_rect[1]+self.toggles_rect[3]+round(self.height * self.SCORES_FONT_SCALE), 0, 0)
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
        # duplicate these tiles at a smaller size for use in menus
        self.menu_tile_library = {}
        for tile_name in self.tile_image_library:
            tile_image = self.tile_image_library[tile_name]
            self.menu_tile_library[tile_name] = pygame.transform.scale(tile_image, [self.menu_tile_size, self.menu_tile_size])
        self.toggle_library = {}
        for highlight_name in self.highlight_library:
            highlight_image = self.highlight_library[highlight_name]
            self.toggle_library[highlight_name] = pygame.transform.scale(highlight_image, [self.menu_highlight_size, self.menu_highlight_size])
        if isinstance(self.game, GameRegular):
            #duplicate tiles for use in selection mennu after piracy
            self.offer_tile_library = {}
            for tile_name in self.tile_image_library:
                tile_image = self.tile_image_library[tile_name]
                self.offer_tile_library[tile_name] = pygame.transform.scale(tile_image, [self.offer_tile_size, self.offer_tile_size])
        #import the cards that will award various rule buffs
        if isinstance(self.game, GameAdvanced):
            self.card_image_library = {}
#            self.used_card_images = {} #just in case the images available don't provide enough unique versions of each card type
            card_image_names = [filename for filename in os.listdir(self.CARDS_PATH) if ".png" in filename]
            card_image_names.sort() #Ensure it's deterministic which specific cards are assigned to each adventurer, so that this is consistent with the game's other visuals
            for card_image_name in card_image_names:
                card_type = card_image_name.split("_")[0] #assumes that the card type will be the image filename will start with the type as recognised by the game
                card_image = pygame.image.load(self.CARDS_PATH +card_image_name)
                #Resize the card image to fit in the menu
                new_width = self.play_area_start
                new_height = int(card_image.get_height() * new_width / card_image.get_width())
                self.card_height = new_height
                self.card_width = new_width
                card_type_set = self.card_image_library.get(card_type)
                if card_type_set is None:
                    scaled_image = pygame.transform.scale(card_image, [new_width, new_height])
                    self.update_card_text(scaled_image, card_type)
                    self.card_image_library[card_type] = [scaled_image]
                    #just in case the images available don't provide enough unique versions of each card type for what the game allocates
#                    self.used_card_images[card_type] = []
                else:
                    scaled_image = pygame.transform.scale(card_image, [new_width, new_height])
                    self.update_card_text(scaled_image, card_type)
                    card_type_set.append(scaled_image)
            #Now supplement with the card types that don't have images
            for card_type in self.CARD_TITLES:
                if not card_type in self.card_image_library.keys():
                    print("With no card image for type "+card_type+", creating one...")
                    self.card_image_library[card_type] = [self.create_card(card_type)]
        #adjust the size of the imported images to fit the display size
        self.rescale_graphics()
    
    def create_card(self, card_type):
        '''For cards with no image, creates a placeholder.
        '''
        #@TODO differentiate Cadre vs Character/Manuscript cards, to determine orientation
        card_width = self.play_area_start
        card_height = self.play_area_start * self.play_area_start // self.card_height
        card = pygame.Surface((card_width, card_height))
        card.fill(self.CARD_BACKGROUND_COLOUR)
        card_title = self.CARD_TITLES[card_type]
        card_text = self.CARD_TEXTS[card_type]
        #Create the text objects to add to the card
        rendered_title = self.card_font.render(card_title, 1, self.CARD_TEXT_COLOUR)
        rendered_text = self.wrap_text(card_text, card_width, self.card_font, self.CARD_TEXT_COLOUR, self.CARD_BACKGROUND_COLOUR)
        #Work out positions that will centre the title as well as possible and place it on the card
        title_horizontal = (card_width - rendered_title.get_width()) // 2
        title_vertical = 0
        card.blit(rendered_title, [title_horizontal, title_vertical])
        #Work out positions that will centre the text as well as possible and place it on the card
        if card_width - rendered_text.get_width() > 0:
            text_horizontal = (card_width - rendered_text.get_width()) // 2
        else:
            text_horizontal = 0
        if card_height - rendered_text.get_height():
            text_vertical = rendered_title.get_height() + (card_height - rendered_title.get_height() - rendered_text.get_height()) // 2
        else:
            text_vertical = rendered_title.get_height()
        card.blit(rendered_text, [text_horizontal, text_vertical])
        return card

    def update_card_text(self, card_image, card_type, orientation="vertical"):
        '''Writes text over the top of that already on a card image
        '''
        card_text = self.CARD_TEXTS[card_type]
        rendered_text = self.wrap_text(card_text, card_image.get_width()
                            , self.card_font, self.CARD_TEXT_COLOUR, self.CARD_BACKGROUND_COLOUR)
        card_image.blit(rendered_text
                  , [(card_image.get_width() - rendered_text.get_width())//2
                     , self.CARD_BODY_START*card_image.get_height()])
        return card_image
    
    def wrap_text(self, text, width, font, text_colour, background_colour):
        '''Given a particular width, introduces line breaks and returns a text surface.
        
        Arguments:
        text takes a string to be rendered
        width takes an int maximum width in pixels for the rendered image
        '''
        text_fits = False
        last_line_fits = False
        lines = [deque(text.split())]
        line_num = 0
        max_line_width = 0
        max_line_height = 0
        while not text_fits:
#            print("Text has structure...")
#            for line in lines:
#                print(len(line))
#                if len(line)==0:
#                    print("Empty line of text when wrapping "+text)
#                    exit()
            while not last_line_fits:
                #Check whether the current line of text will fit within the speicfied width when rendered
                line_width, line_height = font.size(" ".join(lines[line_num]))
                if line_width < width:
                    last_line_fits = True
                    line_num += 1
                    #Before proceeding, check whether this line was any higher than others
                    if line_width > max_line_width:
#                        print("Updating line width to "+str(line_width))
                        max_line_width = line_width
                    if line_height > max_line_height:
#                        print("Updating line height to "+str(line_height))
                        max_line_height = line_height
                else:
                    #Try moving the last word of the current line to the next line
                    last_word = lines[line_num].pop()
                    if line_num+1 < len(lines):
                        lines[line_num+1].appendleft(last_word)
                    else:
                        lines.append(deque([last_word]))
            #Check whether there are any more lines to render
            if line_num >= len(lines):
                text_fits = True
            else:
                last_line_fits = False
        paragraph = pygame.Surface((max_line_width, max_line_height * len(lines)))
        paragraph.fill(background_colour)
        line_vertical = 0
        for line in lines:
            rendered_line = font.render(" ".join(line), 1, pygame.Color(text_colour))
            line_horizontal = (paragraph.get_width() - rendered_line.get_width()) // 2
#            print("Adding line to paragraph with position: "+str(line_horizontal)+", "+str(line_vertical))
            paragraph.blit(rendered_line, (line_horizontal, line_vertical))
            line_vertical += max_line_height
        return paragraph
    
    def rescale_graphics(self):
        '''Rescales images in response to updated dimensions for the play grid
        '''
        print("Updating the dimensions that will be used for drawing the play area")
#        self.dimensions = dimensions        
        #Tiles, tokens and text will need adjusting to the new dimensions
        #Tiles will be scaled to fit the smaller dimension
        max_tile_height = self.height // self.dimensions[1]
        max_tile_width = self.play_area_width // self.dimensions[0]
        if max_tile_height < max_tile_width:
            self.tile_size = max_tile_height
        else:
            self.tile_size = max_tile_width
        self.token_size = round(self.TOKEN_SCALE * self.tile_size) #token size will be proportional to the tiles
        self.outline_width = math.ceil(self.TOKEN_OUTLINE_SCALE * self.token_size)
        self.route_thickness = self.ROUTE_THICKNESS
        self.chest_highlight_thickness = int(self.route_thickness)
        self.token_font = pygame.font.SysFont(None, int(self.tile_size * self.TOKEN_FONT_SCALE)) #the font size for tokens will be proportionate to the window size
        #scale down the images as the dimensions of the grid are changed, rather than when placing
        #the tiles' scale will be slightly smaller than the space in the grid, to givea discernible margin
        bordered_tile_size = round(self.tile_size * (1 - self.TILE_BORDER))
        print("Updated tile size to be " +str(self.tile_size)+ " pixels, and with border: " +str(bordered_tile_size))
        self.rescale_images(self.tile_image_library, bordered_tile_size)
        self.rescale_images(self.highlight_library, self.tile_size)
#        self.rescale_images(self.menu_tile_library, self.menu_tile_size)
    
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
        self.dimensions[0] = max_longitude - min_longitude + 1 + 2*self.DIMENSION_BUFFER
        self.dimensions[1] = max_latitude - min_latitude + 1 + 2*self.DIMENSION_BUFFER
        #Check whether the current dimensions are too great for the display size
        if (self.dimensions[0]*self.tile_size > self.play_area_width
                or self.dimensions[1]*self.tile_size > self.height):
#            print("Reducing the size of tile graphics to fit within the new dimensions")
            self.rescale_graphics()
        #Check whether one of the dimensions has slack space and displace the origin to centre the play
        #Set the origin so that the play will be as central as possible
        self.origin[0] = -min_longitude + self.DIMENSION_BUFFER
        width_needed = self.dimensions[0]*self.tile_size
        if width_needed + 2*self.tile_size < self.play_area_width:
#            print("Extending grid width because the screen width is more generous than needed")
            extra_cols = math.floor((self.play_area_width - width_needed)/self.tile_size) #the excess in tiles
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
        self.prompt_position = [self.play_area_start + self.PROMPT_POSITION[0]*self.width
                                , self.PROMPT_POSITION[1]*self.height]
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
    
    def establish_tilename(self, tile):
        '''Works out what the image file will be called, corresponding to a Cartolan tile
        '''
        e = tile.tile_edges
        if isinstance(tile, CityTile):
            if tile.is_capital:
                return "capital"
            else:
                return "mythical"
        elif isinstance(tile, DisasterTile):
            if tile.tile_back == "water":
                return "water_disaster"
            else:
                return "land_disaster"
        else:
            wonder = str(tile.is_wonder)
            uc = str(e.upwind_clock_water)
            ua = str(e.upwind_anti_water)
            dc = str(e.downwind_clock_water)
            da = str(e.downwind_anti_water)
            return uc + ua + dc + da + wonder
    
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
                tile_name = self.establish_tilename(tile)
                north = str(tile.wind_direction.north)
                east = str(tile.wind_direction.east)
                tile_image = self.tile_image_library[tile_name + north + east]
                #place the tile image in the grid
                horizontal = self.play_area_start + self.get_horizontal(longitude) * self.tile_size
                vertical = self.get_vertical(latitude) *self.tile_size
#                print("Placing a tile at pixel coordinates " +str(horizontal*self.tile_size)+ ", " +str(vertical*self.tile_size))
                self.window.blit(tile_image, [horizontal, vertical])
                #Print a number on this tile showing the dropped wealth there
                if tile.dropped_wealth > 0:
                    if tile.is_wonder:
                        text_colour = self.WONDER_TEXT_COLOUR
                    else:
                        text_colour = self.PLAIN_TEXT_COLOUR
                    horizontal += int(self.tile_size * (1 - self.TOKEN_FONT_SCALE/2) / 2)
                    vertical += int(self.tile_size * (1 - self.TOKEN_FONT_SCALE/2) / 2)
                    wealth_label = self.token_font.render(str(tile.dropped_wealth), 1, text_colour)
                    self.window.blit(wealth_label, [horizontal, vertical])
        # # Keep track of what the latest play_area to have been visualised was
        # self.play_area = self.play_area_union(self.play_area, play_area_update)
        return True
    
    #@TODO highlight the particular token(s) that an action relates to
    #display the number of moves since resting
    def draw_move_options(self, highlight_coords={}):
        '''Outlines tiles where moves or actions are possible, designated by colour
        
        Arguments:
        moves_since_rest expects an integer
        highlight_coords expects a library of strings mapped to lists of integer 2-tuples
        '''
#        print("Updating the dict of highlight positions, based on optional arguments")
#        highlight_count = 0
        self.highlight_rects = {} #Reset the record of where highlights have been drawn for click detection
        for highlight_type in self.highlights:
            coords = highlight_coords.get(highlight_type)
            if coords:
                self.highlights[highlight_type] = coords
#                print(highlight_type + " highlight provided coords at "+str(coords) )
#                highlight_count += len(coords)
            else:
#                print("No coords provided for highight type: "+highlight_type)
                self.highlights[highlight_type] = []
#        print("Cycling through the various highlights' grid coordinates, outlining the " +str(highlight_count)+ " tiles that can and can't be subject to moves")
        for highlight_type in self.highlight_library:
            if self.highlights[highlight_type]:
                self.highlight_rects[highlight_type] = []
                highlight_image = self.highlight_library[highlight_type]
                for tile_coords in self.highlights[highlight_type]:
                    #place the highlight image on the grid
#                    print(highlight_type + " has coords "+str(tile_coords))
                    horizontal = self.play_area_start + self.get_horizontal(tile_coords[0]) *self.tile_size
                    vertical = self.get_vertical(tile_coords[1]) *self.tile_size
#                    print("Drawing a highlight at pixel coordinates " +str(horizontal*self.tile_size)+ ", " +str(vertical*self.tile_size))
                    self.window.blit(highlight_image, [horizontal, vertical])
                    #remember where this highlight was drawn, to detect input later
                    self.highlight_rects[highlight_type].append((horizontal, vertical, highlight_image.get_width(), highlight_image.get_height()))
        
    def draw_move_count(self):
        '''report the number of moves that have been used so far:
        '''
        moves_since_rest = self.current_adventurer.downwind_moves + self.current_adventurer.upwind_moves + self.current_adventurer.land_moves
        horizontal = self.MOVE_COUNT_POSITION[0] * self.width
#            vertical = self.MOVE_COUNT_POSITION[1] * self.height + len(self.game.tile_piles) * self.SCORES_FONT_SCALE * self.height
        vertical = 0
        if self.current_adventurer == self.viewed_adventurer:
            if moves_since_rest != 0:
                move_count = self.scores_font.render(str(moves_since_rest)+" of "+str(self.current_adventurer.max_downwind_moves)+" moves since rest", 1, self.PLAIN_TEXT_COLOUR)
            else:
                report = "No moves since rest"
                move_count = self.scores_font.render(report, 1, self.PLAIN_TEXT_COLOUR)
        else:
            report = "Not "+self.current_adventurer.player.name+"'s Adventurer's turn"
            move_count = self.scores_font.render(report, 1, self.viewed_player_colour)
        if move_count.get_width() > self.right_text_start:
            self.right_text_start = move_count.get_width() #permanently adjust the text margin on this setup if it doesn't fit
        self.window.blit(move_count, [horizontal, vertical])
        self.move_count_rect = (horizontal, vertical, move_count.get_width(), move_count.get_height())
        
    def draw_discard_pile(self):
        '''Draw small versions of the tiles that have been discarded so far
        '''
        horizontal = self.right_text_start
        vertical = self.piles_rect[1] + self.piles_rect[3]
        discard_title = self.scores_font.render("Failed mapping attempts:", 1, self.PLAIN_TEXT_COLOUR)
        self.window.blit(discard_title, [horizontal, vertical])
        horizontal = self.right_menu_start
        vertical += self.SCORES_FONT_SCALE * self.height
        tile_count = 0
        for discard_pile in list(self.game.discard_piles.values()):
            for tile in discard_pile.tiles:
                tile_name = self.establish_tilename(tile)
                north = str(tile.wind_direction.north)
                east = str(tile.wind_direction.east)
                tile_image = self.menu_tile_library[tile_name + north + east]
    #                print("Placing a tile at pixel coordinates " +str(horizontal*self.tile_size)+ ", " +str(vertical*self.tile_size))
                self.window.blit(tile_image, [horizontal, vertical])
                #Draw a frame to keep distinct from play area
                pygame.draw.rect(self.window, self.PLAIN_TEXT_COLOUR
                                 , (horizontal, vertical, self.menu_tile_size, self.menu_tile_size)
                                 , self.chest_highlight_thickness)
                tile_count += 1
                if tile_count % self.MENU_TILE_COLS == 0:
                    vertical += self.menu_tile_size
                    horizontal = self.right_menu_start
                else:
                    horizontal += self.menu_tile_size
                #If the vertical is encroaching on the prompt area then stop
                if vertical > (1 - self.PROMPT_SHARE) * self.height:
                    return False
        return True #confirm that all the discarded tiles were drawn
     
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
        players = self.game.players
        #Reset the records of where Agents and Adventurers have been
        self.adventurer_centres = []
        self.agent_rects = []
        for player in players:
            #We'll want to differentiate players by colour and the offset from the tile location
            colour = pygame.Color(self.player_colours[player])
            player_offset = self.PLAYER_OFFSETS[players.index(player)]
            token_label_colour = self.PLAIN_TEXT_COLOUR
            if self.TOKEN_FONT_COLOURS.get(self.player_colours[player]) is not None:
                token_label_colour = self.TOKEN_FONT_COLOURS[self.player_colours[player]]
            #Each player may have multiple Adventurers to draw
            adventurers = self.game.adventurers[player]
            for adventurer in adventurers:
                # we want to draw a circle anywhere an Adventurer is, differentiating with offsets
                tile = adventurer.current_tile
                adventurer_offset = self.ADVENTURER_OFFSETS[adventurers.index(adventurer)]
                location = [int(self.play_area_start + self.tile_size * (self.get_horizontal(tile.tile_position.longitude) + player_offset[0] + adventurer_offset[0]))
                            , int(self.tile_size * (self.get_vertical(tile.tile_position.latitude) + player_offset[1] + adventurer_offset[1]))]
                # we want it to be coloured differently for each player
#                print("Drawing the filled circle at " +str(location[0])+ ", " +str(location[1])+ " with radius " +str(self.token_size))
                pygame.draw.circle(self.window, colour, location, self.token_size)
                if isinstance(adventurer, AdventurerRegular):
                    if adventurer.pirate_token:
                        # we'll outline pirates in black
#                        print("Drawing an outline")
                        pygame.draw.circle(self.window, (0, 0, 0), location, self.token_size, self.outline_width)
#                if adventurer in (self.viewed_adventurer, self.current_adventurer):
                if adventurer == self.viewed_adventurer:
                    pygame.draw.circle(self.window, self.PLAIN_TEXT_COLOUR, location, self.token_size+self.outline_width, self.outline_width)
                else:
                    self.adventurer_centres.append([(location[0], location[1]), adventurer]) #We'll retain the centre, to contstruct a hit-box for selecting this Adventurer instead
                #For the text label we'll change the indent
                token_label = self.token_font.render(str(adventurers.index(adventurer)+1), 1, token_label_colour)
                location[0] -= self.token_size // 2
                location[1] -= self.token_size
                self.window.blit(token_label, location)
            # we want to draw a square anywhere that an agent is
            for agent in game.agents[player]: 
                tile = agent.current_tile
                if not tile:
                    continue
                agent_offset = self.AGENT_OFFSET
                location = [int(self.play_area_start + self.tile_size * (self.get_horizontal(tile.tile_position.longitude) + agent_offset[0]))
                            , int(self.tile_size * (self.get_vertical(tile.tile_position.latitude) + agent_offset[1]))]
                #Agents will be differentiated by colour, but they will always have the same position because there will only be one per tile
                agent_shape = pygame.Rect(location[0], location[1]
                  , self.AGENT_SCALE*self.token_size, self.AGENT_SCALE*self.token_size)
                if agent.player != self.viewed_adventurer.player:
                    self.agent_rects.append([(location[0], location[1]
                            , self.AGENT_SCALE*self.token_size, self.AGENT_SCALE*self.token_size)
                        , agent.player])
                # we'll only outline the Agents that are dispossessed
                if isinstance(agent, AgentRegular) and agent.is_dispossessed:
                        pygame.draw.rect(self.window, colour, agent_shape, self.outline_width)
                else:
                    #for a filled rectangle the fill method could be quicker: https://www.pygame.org/docs/ref/draw.html#pygame.draw.rect
                    self.window.fill(colour, rect=agent_shape)
                token_label = self.token_font.render(str(agent.wealth), 1, token_label_colour)
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
        self.drawn_routes = [] #Clear out old routes
        for player in players:
            player_offset = self.PLAYER_OFFSETS[players.index(player)]
            adventurers = self.game.adventurers[player]
            colour = pygame.Color(self.player_colours[player])
            for adventurer in adventurers:
                if adventurer.route:
                    adventurer_offset = self.ADVENTURER_OFFSETS[adventurers.index(adventurer)]
                    adventurer_offset = [adventurer_offset[i] + player_offset[i] for i in [0, 1]]
                    previous_step = [int(self.play_area_start + self.tile_size * (self.get_horizontal(adventurer.route[0].tile_position.longitude) + adventurer_offset[0]))
                            , int(self.tile_size * (self.get_vertical(adventurer.route[0].tile_position.latitude) + adventurer_offset[1]))]
                    # we'll introduce a gradual offset during the course of the game, to help keep track of when a route was travelled
                    move = 0
                    drawn_route = []
                    for tile in adventurer.route:
                        # you'll need to get the centre-point for each tile_image
                        offset = [0.5 + float(move)/float(len(adventurer.route))*(x - 0.5) for x in adventurer_offset]
                        step = [int(self.play_area_start + self.tile_size * (self.get_horizontal(tile.tile_position.longitude) + offset[0]))
                                , int(self.tile_size * (self.get_vertical(tile.tile_position.latitude) + offset[1]))]
                        segment = pygame.draw.line(self.window, colour
                                         , [previous_step[0], previous_step[1]]
                                         , [step[0], step[1]]
                                         , math.ceil(self.route_thickness 
                                                     * float(move)/float(len(adventurer.route))
                                                     )
                                         )
                        previous_step = step
                        drawn_route.append(segment)
                        move += 1
                    #retain this for detecting clicks, providing it doesn't end with abandoning
                    route_to_follow = adventurer.route[:]
                    if (drawn_route[-1][2] > self.tile_size and drawn_route[-1][3] > self.tile_size):
                        route_to_follow.pop()
                    if len(drawn_route) > 1:
#                        print("Recording route of "+self.player_colours[adventurer.player]+" player, for fast travel.")
#                        print("Route length: "+str(len(drawn_route)))
                        self.drawn_routes.append([drawn_route, route_to_follow])
            
#            if isinstance(player, PlayerRegularExplorer):
#                for attack in player.attack_history: 
#                    # we want to draw a cross anywhere that an attack happened, the attack_history is full of pairs with a tile and a bool for the attack's success
#                    if attack[1]:
#                        face_colour = self.player_colours[player]
#                    else:
#                        face_colour = "none"
#                    tile = attack[0]
#                    location = [self.origin[0] + tile.tile_position.longitude + player_offset[0]
#                                , self.origin[1] + tile.tile_position.latitude + player_offset[1]]
#                    routeax.scatter([location[0]],[location[1]]
#                                  , linewidth=1, edgecolors=self.player_colours[player], facecolor=face_colour, marker="X", s=self.token_width)
    
    def draw_scores(self):
        '''Prints a table of current wealth scores in players' Vaults and Adventurers' Chests
        '''        
#        print("Creating a table of the wealth held by Players and their Adventurers")
        #Draw the column headings
        game = self.game
        horizontal = self.SCORES_POSITION[0] * self.width
        vertical = self.SCORES_POSITION[1] * self.height
        score_title = self.scores_font.render("Treasure in...", 1, self.PLAIN_TEXT_COLOUR)
        self.window.blit(score_title, [horizontal, vertical])
        vertical += score_title.get_height()
        horizontal += self.SCORES_FONT_SCALE * self.SCORES_SPACING * self.width // 2
        score_title = self.scores_font.render("Vault", 1, self.PLAIN_TEXT_COLOUR)
        self.window.blit(score_title, [horizontal, vertical])
        #Start recording the surrounding rect for click detection, but will need to count max adventurers below to finalise this
        self.scores_rect = (horizontal, vertical, 0, 0)
        self.score_rects = []
        #Work out the maximum number of Adventurers in play, to only draw this many columns
        max_num_adventurers = 1
        for player in self.game.players:
            if len(game.adventurers[player]) > max_num_adventurers:
                max_num_adventurers = len(game.adventurers[player])
        for adventurer_num in range(1, max_num_adventurers + 1):
                score_title = self.scores_font.render("Chest #"+str(adventurer_num), 1, self.PLAIN_TEXT_COLOUR)
                horizontal += self.SCORES_FONT_SCALE * self.SCORES_SPACING * self.width
                self.window.blit(score_title, [horizontal, vertical])
        for player in self.game.players:
            colour = pygame.Color(self.player_colours[player])
            horizontal = self.SCORES_POSITION[0] * self.width #reset the scores position before going through other rows below
            vertical += self.SCORES_FONT_SCALE * self.height #increment the vertical position to a new row
            score_value = self.scores_font.render(player.name, 1, colour)
            self.window.blit(score_value, [horizontal, vertical])
            score_value = self.scores_font.render(str(self.game.player_wealths[player]), 1, colour)
            horizontal += self.SCORES_FONT_SCALE * self.SCORES_SPACING * self.width - score_value.get_width()
            self.window.blit(score_value, [horizontal, vertical])
            #Record this space for click detection
#            self.score_rects.append([(horizontal, vertical, self.SCORES_FONT_SCALE * self.SCORES_SPACING * self.width, self.SCORES_FONT_SCALE * self.height), player])
            self.score_rects.append([(horizontal, vertical, score_value.get_width(), score_value.get_height()), player])
            for adventurer in game.adventurers[player]:
                horizontal += self.SCORES_FONT_SCALE * self.SCORES_SPACING * self.width #Shift to a new column
                score_value = self.scores_font.render(str(adventurer.wealth), 1, colour)
                self.window.blit(score_value, [horizontal, vertical])
                #If this is the moving Adventurer, then highlight their score
                if adventurer == self.current_adventurer:
                    pygame.draw.rect(self.window, self.PLAIN_TEXT_COLOUR
                                 , (horizontal
                                    , vertical + score_value.get_height()
                                    , score_value.get_width()
                                    , 0)
                                 , self.chest_highlight_thickness)
                #If this is the Adventurer whose cards are being viewed then mark with a dot underneath
                if adventurer == self.viewed_adventurer:
                    pygame.draw.circle(self.window, self.PLAIN_TEXT_COLOUR
                                 , (horizontal + score_value.get_width()//2
                                    , vertical + score_value.get_height())
                                 , self.chest_highlight_thickness)
                #Record this space for click detection
#                self.score_rects.append([(horizontal, vertical, self.SCORES_FONT_SCALE * self.SCORES_SPACING * self.width, self.SCORES_FONT_SCALE * self.height), adventurer])
                self.score_rects.append([(horizontal, vertical, score_value.get_width(), score_value.get_height()), adventurer])
        #State the current player and Adventurer
        vertical += self.SCORES_FONT_SCALE * self.height
        horizontal = self.SCORES_POSITION[0] * self.width
        active_prompt = self.scores_font.render(self.current_adventurer.player.name+"'s Adventurer #"+str(self.current_adventurer_number+1)+"'s turn", 1, pygame.Color(self.current_player_colour))
        self.window.blit(active_prompt, [horizontal, vertical])
        #Finish recording the surrounding rect for click detection, but will need to count max adventurers below to finalise this
        self.scores_rect = (self.scores_rect[0]
            , self.scores_rect[1]
            , self.SCORES_FONT_SCALE * self.SCORES_SPACING * self.width * (max_num_adventurers + 1)
            , vertical + self.SCORES_FONT_SCALE * self.height - self.scores_rect[1])
        
    def draw_tile_piles(self):
        '''Draw the numbers of tiles in each pile
        '''
        horizontal = self.right_text_start
        vertical = self.chest_rect[1] + self.chest_rect[3]
        #Start recording the surrounding rect for click detection, but will need to count max adventurers below to finalise this
        self.piles_rect = (horizontal, vertical, 0, 0)
        max_pile_width = 0
        for tile_back in self.game.tile_piles:
            tiles = self.game.tile_piles[tile_back].tiles
            tile_count = self.scores_font.render(str(len(tiles))+" maps left in "+tile_back+" bag", 1, self.PLAIN_TEXT_COLOUR)
            if tile_count.get_width() > max_pile_width:
                max_pile_width = tile_count.get_width()
            tile_count_position = [horizontal, vertical]
            self.window.blit(tile_count, tile_count_position)
            vertical += self.SCORES_FONT_SCALE * self.height
        #Finish recording the surrounding rect for click detection, but will need to count max adventurers below to finalise this
        self.piles_rect = (self.piles_rect[0]
            , self.piles_rect[1]
            , max_pile_width
            , vertical - self.piles_rect[1])   
    
    def draw_toggle_menu(self, fixed_responses):
        '''Visualises a set of highlights for action prompts that can have a fixed True/False response set for them 
        '''
        self.toggle_rects = [] #Reset the record of where the toggle menu buttons have been drawn
        #Establish the top left coordinate below the table of treasure scores
#        horizontal = self.MOVE_COUNT_POSITION[0] * self.width
#        vertical = self.SCORES_FONT_SCALE * self.height * (len(self.game.tile_piles) + 1)
        horizontal = self.right_menu_start
        vertical = self.move_count_rect[1] + self.move_count_rect[3] 
        toggle_title = self.scores_font.render("Auto-Actions:", 1, self.PLAIN_TEXT_COLOUR)
        self.window.blit(toggle_title, (horizontal, vertical))
        #Draw a box to surround the Chest menu, and remember its coordinates for player input
        #@TODO allow the Chest tiles menu to vary in size depending on Adventurer
        horizontal = self.right_menu_start
        vertical += self.SCORES_FONT_SCALE * self.height
        self.toggles_rect = (horizontal, vertical, self.play_area_start, self.menu_highlight_size)
#        print("Chest map menu corners defined at pixels...")
#        print(self.chest_rect)
#        pygame.draw.rect(self.window, self.PLAIN_TEXT_COLOUR
#                                 , self.chest_rect
#                                 , self.chest_highlight_thickness)
        #Cycle through the chest tiles, drawing them
        for highlight_type in fixed_responses:
            #If there is a fixed response set for this action type, then give it a colour to indicate True / False
            if fixed_responses[highlight_type]:
                pygame.draw.rect(self.window, self.TOGGLE_TRUE_COLOUR
                                 , (horizontal, vertical, self.menu_highlight_size, self.menu_highlight_size))
            elif fixed_responses[highlight_type] is not None:
                pygame.draw.rect(self.window, self.TOGGLE_FALSE_COLOUR
                                 , (horizontal, vertical, self.menu_highlight_size, self.menu_highlight_size))
            else:
                pygame.draw.rect(self.window, self.BACKGROUND_COLOUR
                                 , (horizontal, vertical, self.menu_highlight_size, self.menu_highlight_size))
            #Now draw the highlight over the top
            highlight_image = self.toggle_library[highlight_type]
            self.window.blit(highlight_image, [horizontal, vertical])
            #Remember the position of this highlight's toggle
            self.toggle_rects.append([(horizontal, vertical, self.menu_highlight_size, self.menu_highlight_size), highlight_type])
            horizontal += self.menu_highlight_size #increment the horizontal placement before the next toggle is drawn
    
    def draw_undo_button(self):
        '''Adds an undo button and a click hit-box that will allow the game to be reset to a preceding state, providing all players agree.
        '''
        #Check whether the other clients to the game have proposed/agreed to an undo
        undo_asked = False
        for peer in self.peer_visuals:
            if not peer == self and peer.undo_agreed:
                undo_asked = True
                break
        if self.undo_agreed:
            undo_button = self.scores_font.render("Reject undo", 1, self.ACCEPT_UNDO_COLOUR)
        elif undo_asked:
            undo_button = self.scores_font.render("Accept undo?", 1, self.ACCEPT_UNDO_COLOUR)
        else:
            undo_button = self.scores_font.render("Undo turn?", 1, self.PLAIN_TEXT_COLOUR)
        horizontal = self.width - undo_button.get_width()
        vertical = self.height - undo_button.get_height()
        self.window.blit(undo_button, (horizontal, vertical))
        self.undo_rect = (horizontal, vertical, undo_button.get_width(), undo_button.get_height())
            
    def draw_chest_tiles(self):
        '''Visualises a set of tiles in the Adventurer's Chest, and highlights one if it is selected for use
        '''
        #Get the information from the viewed adventurer
        if self.viewed_adventurer is None:
            return
        chest_tiles = self.viewed_adventurer.chest_tiles
        preferred_tile_num = self.viewed_adventurer.preferred_tile_num
        max_chest_tiles = self.viewed_adventurer.num_chest_tiles
        #Establish the top left coordinate of the column of tiles to choose from, below the table of treasure scores
#        vertical = self.SCORES_FONT_SCALE * self.height * (len(self.game.players) + 1)
        horizontal = self.right_text_start
#        vertical = (len(self.game.players) + 1) * self.SCORES_FONT_SCALE * self.height
        vertical = self.toggles_rect[1] + self.toggles_rect[3] 
        title_text = "Adventurer #"+str(self.viewed_adventurer_number+1)+"'s chest maps:"
        chest_title = self.scores_font.render(title_text, 1, self.viewed_player_colour)
        self.window.blit(chest_title, (horizontal, vertical))
        #Draw a box to surround the Chest menu, and remember its coordinates for player input
        horizontal = self.right_menu_start
        vertical += self.SCORES_FONT_SCALE * self.height
        menu_size = self.menu_tile_size * math.ceil(max_chest_tiles / self.MENU_TILE_COLS)
        self.chest_rect = (horizontal, vertical, self.play_area_start, menu_size)
#        print("Chest map menu corners defined at pixels...")
#        print(self.chest_rect)
        pygame.draw.rect(self.window, self.PLAIN_TEXT_COLOUR
                                 , self.chest_rect
                                 , self.chest_highlight_thickness)
        #Cycle through the chest tiles, drawing them
        for tile in chest_tiles:
            e = tile.tile_edges
            wonder = str(tile.is_wonder)
            uc = str(e.upwind_clock_water)
            ua = str(e.upwind_anti_water)
            dc = str(e.downwind_clock_water)
            da = str(e.downwind_anti_water)
            tile_name = uc + ua + dc + da + wonder
            north = str(tile.wind_direction.north)
            east = str(tile.wind_direction.east)
            tile_image = self.menu_tile_library[tile_name + north + east]
#                print("Placing a tile at pixel coordinates " +str(horizontal*self.tile_size)+ ", " +str(vertical*self.tile_size))
            horizontal = self.chest_rect[0] + (chest_tiles.index(tile) % self.MENU_TILE_COLS) * self.menu_tile_size
#            vertical += (chest_tiles.index(tile) // self.MENU_TILE_COLS) * self.menu_tile_size
            vertical = self.chest_rect[1] + (chest_tiles.index(tile) // self.MENU_TILE_COLS) * self.menu_tile_size
            self.window.blit(tile_image, [horizontal, vertical])
            #If this is the tile selected then highlight this with a hollow rectangle
            if chest_tiles.index(tile) == preferred_tile_num:
                pygame.draw.rect(self.window, self.CHEST_HIGHLIGHT_COLOUR
                                 , (horizontal, vertical, self.menu_tile_size, self.menu_tile_size)
                                 , self.chest_highlight_thickness)
            else:
                pygame.draw.rect(self.window, self.PLAIN_TEXT_COLOUR
                                 , (horizontal, vertical, self.menu_tile_size, self.menu_tile_size)
                                 , self.chest_highlight_thickness)
    
    def draw_cards(self):
        '''Adds images of the current Adventurer's character and discovery cards to the menu below their Chest
        
        Arguments:
        Adventurer takes a Cartolan Adventurer
        '''
        #Identify the adventurer that has been selected to focus on in this visual
        game = self.game
        for player in game.players:
            if player == self.viewed_adventurer.player:
                break
        adventurer = game.adventurers[player][self.viewed_adventurer_number]
        #Establish the top left coordinate of the stack of cards
        horizontal = 0
#        vertical = self.SCORES_FONT_SCALE * self.height * (len(self.game.players) + 1) 
        vertical = self.scores_rect[1] + self.scores_rect[3]
#        vertical = self.chest_rect[1] + self.chest_rect[3]
        #draw the Adventurer's Player's Cadre Card        
        if self.game.assigned_cadres.get(adventurer.player) is not None:
            card_title = self.scores_font.render(adventurer.player.name+"'s Cadre card:", 1, self.PLAIN_TEXT_COLOUR)
            self.window.blit(card_title, [horizontal, vertical])
            #Now draw the card itself
            card = self.game.assigned_cadres.get(adventurer.player)
            card_image = self.get_card_image(adventurer, card)
            vertical += self.SCORES_FONT_SCALE * self.height
            self.window.blit(card_image, [horizontal, vertical])
            vertical += card_image.get_height()
        #Procede to draw any other cards
        if adventurer.character_card is not None:
            card_title = self.scores_font.render("Adventurer #"+str(self.game.adventurers[adventurer.player].index(adventurer)+1)+" cards:", 1, self.PLAIN_TEXT_COLOUR)
            self.window.blit(card_title, [horizontal, vertical])
        vertical += self.SCORES_FONT_SCALE * self.height
#        stack_size = self.card_height * (1 + self.CARD_HEADER_SHARE * len(adventurer.character_cards))
        stack_size = self.card_height + self.card_height * self.CARD_HEADER_SHARE * len(adventurer.discovery_cards)  #one character card plus all the manuscripts
        self.stack_rect = (horizontal, vertical, self.play_area_start, stack_size)
#        print("Card stack corners defined at pixels...")
#        print(self.stack_rect)
                
        #Cycle through the Discovery Cards, drawing them
        for card in adventurer.discovery_cards:
            if self.selected_card_num is not None:
                if adventurer.discovery_cards.index(card) == self.selected_card_num:
                    break
#            print("Drawing a card of type "+card.card_type)
            card_image = self.get_card_image(adventurer, card)
            self.window.blit(card_image, [horizontal, vertical])
            vertical += self.CARD_HEADER_SHARE * card_image.get_height() 
        
        #Draw the Adventurer's Character Card over the top
        if adventurer.character_card is not None:
            card_image = self.get_card_image(adventurer, adventurer.character_card)
    #        card_horizontal = 0
            vertical = self.stack_rect[1] + card_image.get_height() * self.CARD_HEADER_SHARE * len(adventurer.discovery_cards)
            self.window.blit(card_image, [horizontal, vertical])
#        card_rect = (0, card_stack_position, self.play_area_start, stack_size)
#        pygame.draw.rect(self.window, self.PLAIN_TEXT_COLOUR
#                                 , self.chest_rect
#                                 , self.chest_highlight_thickness)
        #If one of the discovery/manuscript cards has been selected then draw cards back over the current ones in reverse up to that one
        if self.selected_card_num is not None:
            for card in reversed(adventurer.discovery_cards):
                vertical -= self.CARD_HEADER_SHARE * card_image.get_height()
#                print("Drawing a card of type "+card.card_type)
                card_image = self.get_card_image(adventurer, card)
                self.window.blit(card_image, [horizontal, vertical])
                if adventurer.discovery_cards.index(card) == self.selected_card_num:
                    break
                
    
    def get_card_image(self, card_holder, card):
        '''Draws a Character or Discovery card
        '''
        card_image = self.card_images.get(card)
        if card_image is None:
            available_cards = self.card_image_library[card.card_type]
#            if not available_cards: #if all the card images have been used then recycle
#                self.card_image_library[card.card_type] = self.used_card_images[card.card_type]
#                available_cards = self.card_image_library[card.card_type]
#                self.used_card_images[card.card_type] = []
            card_image = self.card_images[card] = available_cards.pop()
#            self.used_card_images[card.card_type].append(card_image)
            available_cards.insert(0, card_image) #Prepend this image back into the library so that it won't get used again unless other images run out
        return card_image   

    def draw_card_offers(self, cards):
        '''Prominently displays an array of cards from which the player can choose
        
        Arguments:
        Cards takes a list of Cartolan Cards
        '''
        self.offer_images = [] #reset the record of card images in use
        self.offer_rects = [] #reset the record of card positions for selection
        #Cycle through the offered Cards, drawing them
        horizontal_increment = self.width // (len(cards) + 1)
        card_horizontal = horizontal_increment
        card_vertical = (self.height - self.card_height) // 2 #Centre the cards vertically
        for card in cards:
            print("Drawing a card of type "+card.card_type)
            card_image = self.get_card_image(None, card)
#            card_type = card.card_type
#            available_cards = self.card_image_library[card_type]
#            if available_cards:
#                card_image =  available_cards[0] #Choose the first image available
#            else:
#                card_image = self.used_card_images[card_type][0]
            adjusted_horizontal = card_horizontal - card_image.get_width() // 2
            self.window.blit(card_image, [adjusted_horizontal, card_vertical])
            card_horizontal += horizontal_increment
            self.offer_images.append(card_image)
            self.offer_rects.append((adjusted_horizontal, card_vertical, card_image.get_width(), card_image.get_height()))
    
    #@TODO combine the two methods for choosing cards and tiles, once there are multiple tile images too
    def draw_tile_offers(self, tiles):
        '''Prominently displays an array of tiles from which the player can choose
        
        Arguments:
        tiles takes a list of Cartolan Tiles
        '''
        self.offer_images = [] #reset the record of card images in use
        self.offer_rects = [] #reset the record of card positions for selection
        #Cycle through the offered Cards, drawing them
        horizontal_increment = self.width // (len(tiles) + 1)
        tile_horizontal = horizontal_increment
        tile_vertical = (self.height - self.offer_tile_size) // 2 #Centre the cards vertically
        for tile in tiles:
            e = tile.tile_edges
            wonder = str(tile.is_wonder)
            uc = str(e.upwind_clock_water)
            ua = str(e.upwind_anti_water)
            dc = str(e.downwind_clock_water)
            da = str(e.downwind_anti_water)
            tile_name = uc + ua + dc + da + wonder
            north = str(tile.wind_direction.north)
            east = str(tile.wind_direction.east)
            tile_image = self.offer_tile_library[tile_name + north + east]
#                print("Placing a tile at pixel coordinates " +str(horizontal*self.tile_size)+ ", " +str(vertical*self.tile_size))
            print("Drawing a tile of type "+tile_name + north + east)
            adjusted_horizontal = tile_horizontal - self.offer_tile_size // 2
            self.window.blit(tile_image, [adjusted_horizontal, tile_vertical])
            tile_horizontal += horizontal_increment
            self.offer_images.append(tile_image)
            self.offer_rects.append((adjusted_horizontal, tile_vertical, self.offer_tile_size, self.offer_tile_size))
    
    def draw_prompt(self):
        '''Prints a prompt on what moves/actions are available to the current player
        '''        
#        print("Creating a prompt for the current player")
        #Establish the colour (as the current player's)
#        prompt = self.prompt_font.render(self.prompt_text, 1, pygame.Color(self.current_player_colour))
        prompt_width = self.width - self.play_area_start - self.right_menu_width
        prompt = self.wrap_text(self.prompt_text, prompt_width, self.prompt_font, pygame.Color(self.current_player_colour), self.BACKGROUND_COLOUR)
        self.window.blit(prompt, (self.play_area_start, self.height - prompt.get_height()))
        
    def start_turn(self, adventurer):
        '''Identifies the current player by their colour, affecting prompts
        '''
        player_colour = self.player_colours[adventurer.player]
        adventurer_number = self.game.adventurers[adventurer.player].index(adventurer)
#        #Reset the request for an undo
#        self.undo_agreed = False
#        self.undo_asked = False
        for game_vis in self.peer_visuals:
            game_vis.current_player_colour = player_colour
            game_vis.current_adventurer_number = adventurer_number
            game_vis.current_adventurer = adventurer
            #Also reset which adventurer's cards are being viewed
            game_vis.viewed_player_colour = player_colour
            game_vis.viewed_adventurer_number = adventurer_number
            game_vis.viewed_adventurer = adventurer
            #Reset the request for an undo
            game_vis.undo_agreed = False
    
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
        
    #@TODO introduce text input in pygame window
    def get_input_value(self, prompt_text, maximum):
        '''ends a prompt to the player, and waits for numerical input.
        
        Arguments
        prompt takes a string
        '''
        return None
        
        
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
                #check whether the click was within the menu, and return the index within the chest
                if (event.pos[0] in range(self.chest_rect[0], self.chest_rect[2])
                    and event.pos[1] in range(self.chest_rect[1], self.chest_rect[3])):
                    menu_row = (event.pos[1] - self.chest_rect[1]) // self.menu_tile_size
                    menu_column = (event.pos[0] - self.chest_rect[0]) // self.menu_tile_size
                    return self.MENU_TILE_COLS * menu_row + menu_column
                #Check whether the click was within the card stack, and update the index of the selected card
                if (event.pos[0] in range(self.stack_rect[0], self.stack_rect[2])
                    and event.pos[1] in range(self.stack_rect[1], self.stack_rect[3])):
                    if self.selected_card_num is None: #The Character card at the bottom will be on top
                        if event.pos[1] < self.stack_rect[3] - self.card_height:
                            self.selected_card_num = (event.pos[1] - self.stack_rect[1]) // (self.card_height * self.CARD_HEADER_SHARE)
                    else:
                        selected_card_top = self.stack_rect[1] + (self.selected_card_num - 1) * self.card_height * self.CARD_HEADER_SHARE
                        selected_card_bottom = selected_card_top + self.card_height
                        if event.pos[1] > self.stack_rect[3] - self.card_height * self.CARD_HEADER_SHARE:
                            self.selected_card_num = None
                        elif event.pos[1] < selected_card_top:
                            self.selected_card_num = (event.pos[1] - self.stack_rect[1]) // (self.card_height * self.CARD_HEADER_SHARE)
                        elif event.pos[1] > selected_card_bottom:
                            self.selected_card_num += (event.pos[1] - selected_card_bottom) // (self.card_height * self.CARD_HEADER_SHARE)
                #Otherwise return the coordinates
                longitude = int(math.ceil((event.pos[0])/self.tile_size)) - self.origin[0] - 1
                latitude = self.dimensions[1] - int(math.ceil((event.pos[1])/self.tile_size)) - self.origin[1]
                #check whether the click was within the highlighted space and whether it's a local turn
#                highlighted_option = self.check_highlighted(longitude, latitude)
#                print("Click was a valid option of type: " + highlighted_option)
                if True:
#                if highlighted_option is not None:
                    self.highlights = {highlight_type:[] for highlight_type in self.HIGHLIGHT_PATHS} #clear the highlights until the server offers more
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


class WebServerVisualisation(GameVisualisation):
    '''For a server-side game played in browser, shares image of play area and receives coords
    
    There will be a separate visual for each client.
    Because the clients all need to see every move, each visual will send for every player.
    But, only the moving player's visual will receive input. 
    '''
    TEMP_FILENAME_LEN = 6
    TEMP_FILE_EXTENSION = ".png"
    INPUT_DELAY = 0.1 #delay time between checking for input, in seconds
    
    def __init__(self, game, peer_visuals, player_colours, client, width, height):
        self.peer_visuals = peer_visuals
        self.client = client
        self.width, self.height = width, height
        self.client_players = []
        super().__init__(game, peer_visuals, player_colours)
    
    def init_GUI(self):
        print("Initialising the pygame window and GUI")
        pygame.init()
        self.window = pygame.Surface((self.width, self.height))
        self.window.fill(self.BACKGROUND_COLOUR) #fill the screen with white
        print("Initialising visual scale variables, to fit window of size "+str(self.width)+"x"+str(self.height))
        self.tile_size = self.height // self.dimensions[1]
        #We'll have a different tile size for dicards and menu highlights
        self.play_area_width = round(self.width * (1 - self.LEFT_MENU_SCALE - self.RIGHT_MENU_SCALE))
        self.play_area_start = round(self.width * self.LEFT_MENU_SCALE)
        self.right_menu_width = round(self.width * self.RIGHT_MENU_SCALE)
        self.right_menu_start = self.play_area_start + self.play_area_width
        self.right_text_start = self.MOVE_COUNT_POSITION[0] * self.width #All text indicators in the right menu will follow the same indent
        self.menu_highlight_size = round(self.RIGHT_MENU_SCALE * self.width) // len(self.TOGGLE_HIGHLIGHTS)
        self.menu_tile_size = round(self.RIGHT_MENU_SCALE * self.width) // self.MENU_TILE_COLS
        #Before sizing against the horizontal dimension, we'll work out how much space the menus will take away
        self.play_area_width = round(self.width * (1 - self.LEFT_MENU_SCALE - self.RIGHT_MENU_SCALE))
        self.play_area_start = round(self.width * self.LEFT_MENU_SCALE)
        #Tiles will be scaled to fit the smaller dimension
        if self.play_area_width < self.tile_size * self.dimensions[0]:
            self.tile_size = self.play_area_width // self.dimensions[0]
        #Where piracy is possible, we'll have a different tile size for 
        self.offer_tile_size = round(self.OFFER_SCALE * self.width)
        self.token_size = int(round(self.TOKEN_SCALE * self.tile_size)) #token size will be proportional to the tiles
        self.outline_width = math.ceil(self.TOKEN_OUTLINE_SCALE * self.token_size)
        self.token_font = pygame.font.SysFont(None, round(self.tile_size * self.TOKEN_FONT_SCALE)) #the font size for tokens will be proportionate to the window size
        self.scores_font = pygame.font.SysFont(None, round(self.height * self.SCORES_FONT_SCALE)) #the font size for scores will be proportionate to the window size
        self.card_font = pygame.font.SysFont(None, round(self.height * self.CARD_FONT_SCALE)) #the font size for scores will be proportionate to the window size
        self.prompt_font = pygame.font.SysFont(None, round(self.height * self.PROMPT_FONT_SCALE)) #the font size for prompt will be proportionate to the window size
        self.prompt_position = [self.play_area_start + self.PROMPT_POSITION[0]*self.width
                                , self.PROMPT_POSITION[1]*self.height]
        pygame.font.init()
        self.prompt_text = ""
        #Make sure that the GUI menus are drawn on the correct sides from the start
        self.scores_rect = (0, 0, 0, 0)
        self.stack_rect = (0, 0, 0, 0)
        self.current_move_count = None
        self.move_count_rect = (self.MOVE_COUNT_POSITION[0]*self.width, self.MOVE_COUNT_POSITION[1]*self.height, 0, round(self.height * self.SCORES_FONT_SCALE))
        self.toggles_rect = (self.right_menu_start, self.move_count_rect[1]+self.move_count_rect[3], 0, self.menu_tile_size+round(self.height * self.SCORES_FONT_SCALE))
        self.chest_rect = (self.right_menu_start, self.toggles_rect[1]+self.toggles_rect[3]+round(self.height * self.SCORES_FONT_SCALE), 0, self.menu_tile_size)
        self.piles_rect = (self.right_menu_start, self.toggles_rect[1]+self.toggles_rect[3]+round(self.height * self.SCORES_FONT_SCALE), 0, 0)
        
        #Import images
        self.init_graphics()
    
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
    
    def get_input_value(self, adventurer, prompt_text, maximum, minimum = 0):
        '''Sends a prompt to the player, and waits for numerical input.
        
        Arguments
        adventurer takes a Cartolan Adventurer from which to draw values for updating visuals
        prompt_text takes a string
        maximum and minimum take int values setting limits on the numerical value that can be input
        '''
        #Update the visuals for the remote players who aren't active
        self.refresh_peers(adventurer, input_type="value")
        print("Prompting client at " +str(self.client.address)+ " with: " +prompt_text)
        self.client.sendMessage("PROMPT[00100]"+prompt_text)
        input_value = None
        while not input_value:
            input_value = self.client.get_text()
            if input_value:
#                print("Trying to interpret "+input_value+" as a number")
                try:
#                    print("Checking that "+input_value+" is between 0 and "+str(maximum))
                    if int(input_value) in range(minimum, maximum+1):
                        return int(input_value)
                    self.client.sendMessage("PROMPT[00100]"+prompt_text)
                    input_value = None
                except:
#                    print("Decided it wasn't a number so interpretting as nothing")
                    return None
            input_value = None
            #@TODO check for input from the other clients to their visuals and update their view
            #Wait before checking again
            time.sleep(self.INPUT_DELAY)
        return None
        
    def refresh_peers(self, adventurer, choices=None, input_type="move"):
        '''Cycles through clients to the same game, besides the active player, updating their visuals
        '''
        #print("Updating the display for all the other human players, whose visuals won't have been consulted.")
        refreshed_visuals = []
        for game_vis in self.peer_visuals:
            if not self.client == game_vis.client and game_vis not in refreshed_visuals:
                refreshed_visuals.append(game_vis)
                game_vis.refresh_visual(choices, input_type)
                game_vis.update_web_display()
    
    def refresh_visual(self, choices=None, input_type="move"):
        '''Updates all elements of this visual, as required when not the active player
        '''
        #Update visuals to keep them informed of action
        self.draw_play_area()
        self.draw_tokens()
        self.draw_routes()
        #Draw the right menu items
        if not input_type in ["choose_company", "choose_character"]:
            self.draw_move_count()
            if isinstance(self.current_adventurer, AdventurerRegular):
                if not input_type == "choose_tile": #Don't draw the chest tiles when the players are first picking companies and adventurers 
                    self.draw_chest_tiles()
            self.draw_tile_piles()
            self.draw_discard_pile()
        #Draw the left menu items and any offers over the top
        self.draw_scores()
        if isinstance(self.current_adventurer, AdventurerAdvanced):
            self.draw_cards()
            #If offers are being made then draw these on top of everything else
            if choices is not None:
                if input_type=="choose_tile":
                    self.draw_tile_offers(choices)
                else:
                    self.draw_card_offers(choices)
        self.draw_undo_button()
        #Prompt the player
        if input_type == "move":
            prompt = self.current_adventurer.player.name+"'s is moving their Adventurer #"+str(self.current_adventurer_number+1)
        elif input_type == "text":
            prompt = self.current_adventurer.player.name+"'s is choosing a treasure amount for their Adventurer #"+str(self.current_adventurer_number+1)
        elif input_type == "choose_tile":
            prompt = self.current_adventurer.player.name+" is choosing a tile for their Adventurer #"+str(self.current_adventurer_number+1)
        elif input_type == "choose_discovery":
            prompt = self.current_adventurer.player.name+" is choosing a Manuscript card for their Adventurer #"+str(self.current_adventurer_number+1)
        elif input_type == "choose_company":
            prompt = self.current_adventurer.player.name+" is choosing their Cadre card"
        else:
            prompt = self.current_adventurer.player.name+" is choosing a Character card for their Adventurer #"+str(self.current_adventurer_number+1)
        self.give_prompt(prompt)
    
    def check_peer_input(self):
        '''Cycles through remote players besides the active one, checking whether clicks have been registered and updating their private visuals accordingly
        '''
        checked_visuals = []
        for game_vis in self.peer_visuals:
            if not self.client == game_vis.client and game_vis not in checked_visuals:
                checked_visuals.append(game_vis)
                coords = game_vis.client.get_coords()
                if coords is not None:
                    horizontal, vertical = coords
                    if game_vis.check_update_focus(horizontal, vertical):
                        game_vis.refresh_visual()
                        game_vis.update_web_display()
                    #Check whether this player wants/agrees to an undo
                    elif game_vis.check_undo(horizontal, vertical):
                        game_vis.refresh_visual()
                        game_vis.update_web_display()
    
    def check_peers_undo(self):
        '''Cycles through all clients of the game to see whether they all agree to undo this turn
        '''
        #Any one player disagreeing will mean the undo isn't agreed yet
        for game_vis in self.peer_visuals:
            if not game_vis.undo_agreed:
                return False
        return True
    
    def reset_peer_undos(self):
        '''Cycles through all clients to the game, making sure they don't continue to vote for resetting the turn
        '''
        #If all rejected then this will be fed back to the game, but all will need to be reset
        for game_vis in self.peer_visuals:
            game_vis.undo_agreed = False
        return True
    
    def check_undo(self, horizontal, vertical):
        '''Checks whether click coordinates were within the undo button's click-box
        '''
        if (horizontal in range(int(self.undo_rect[0]), int(self.undo_rect[0] + self.undo_rect[2]))
            and vertical in range(int(self.undo_rect[1]), int(self.undo_rect[1] + self.undo_rect[3]))):
            print("Player chose coordinates within the undo button, with vertical: "+str(vertical))
            if self.undo_agreed:
                self.undo_agreed = False
            else:
                self.undo_agreed = True
            return True
        else:
            return False
    
    def check_update_focus(self, horizontal, vertical):
        '''Checks whether click coordinates were within the superficial visual elements that need no game response but should revise the client's visuals
        '''
        if (horizontal in range(int(self.scores_rect[0]), int(self.scores_rect[0] + self.scores_rect[2]))
            and vertical in range(int(self.scores_rect[1]), int(self.scores_rect[1] + self.scores_rect[3]))):
            print("Player chose coordinates within the scores table, with vertical: "+str(vertical))
            for score in self.score_rects:
                score_rect = score[0]
                if (horizontal in range(int(score_rect[0]), int(score_rect[0] + score_rect[2]))
                    and vertical in range(int(score_rect[1]), int(score_rect[1] + score_rect[3]))):
                    #Having found the click within a particular player/adventurer's score, need to update the focus of the card stacks
                    if isinstance(score[1], Player):
                        #just choose the first adventurer if it was the player's vault wealth selected
                        self.viewed_player_colour = self.player_colours[score[1]]
                        self.viewed_adventurer_number = 0
                        self.viewed_adventurer = self.game.adventurers[score[1]][0]
                    else:
                        self.viewed_player_colour = self.player_colours[score[1].player]
                        self.viewed_adventurer_number = self.game.adventurers[score[1].player].index(score[1])
                        self.viewed_adventurer = score[1]
                    print("Updated focus for card visuals to "+self.viewed_adventurer.player.name+"'s Adventurer #"+str(self.viewed_adventurer_number+1))
            return True
        #Check whether the click was within the card stack, and update the index of the selected card
        elif (horizontal in range(int(self.stack_rect[0]), int(self.stack_rect[0] + self.stack_rect[2]))
            and vertical in range(int(self.stack_rect[1]), int(self.stack_rect[1] + self.stack_rect[3]))):
            print("Player chose coordinates within the card stack, with vertical: "+str(vertical))
            if self.selected_card_num is None: #The Character card at the bottom will be on top
#                print("Stack top is "+str(int(self.stack_rect[1] + self.stack_rect[3])))
#                print("Card height is "+str(self.card_height))
                if vertical < int(self.stack_rect[1] + self.stack_rect[3]) - self.card_height:
                    self.selected_card_num = int(vertical - self.stack_rect[1]) // int(self.card_height * self.CARD_HEADER_SHARE)
                    print("Updated the selected card to number "+str(self.selected_card_num))
            else:
                selected_card_top = int(self.stack_rect[1] + (self.selected_card_num - 1) * self.card_height * self.CARD_HEADER_SHARE)
                selected_card_bottom = selected_card_top + self.card_height
                if vertical > int(self.stack_rect[1] + self.stack_rect[3]) - self.card_height * self.CARD_HEADER_SHARE:
                    self.selected_card_num = None                            
                elif selected_card_top < vertical < selected_card_bottom:
                    self.selected_card_num = None #clicking on the selected card de-selects it
                elif vertical < selected_card_top:
                    self.selected_card_num = (vertical - int(self.stack_rect[1])) // int(self.card_height * self.CARD_HEADER_SHARE)
                elif vertical > selected_card_bottom:
                    self.selected_card_num += (vertical - selected_card_bottom) // int(self.card_height * self.CARD_HEADER_SHARE)
#                        print("Updated the selected card to number "+str(self.selected_card_num))
            return True
        else:
            #Check the various Adventurer and Agent shapes for a click and use this to select the Adventurer to focus on
            for centre in self.adventurer_centres:
                if (horizontal - centre[0][0])**2 + (vertical - centre[0][1])**2 < self.token_size**2:
                    print("Click detected within one of the Adventurers' areas, with centre: "+str(centre[0]))
                    self.viewed_player_colour = self.player_colours[centre[1].player]
                    self.viewed_adventurer_number = self.game.adventurers[centre[1].player].index(centre[1])
                    self.viewed_adventurer = centre[1]
                    return True
            for rect in self.agent_rects:
                if (horizontal in range(int(rect[0][0]), int(rect[0][0] + rect[0][2]))
                    and vertical in range(int(rect[0][1]), int(rect[0][1] + rect[0][3]))):
                    print("Click detected within one of the Agents' areas for "+self.player_colours[rect[1]]+" player.")
                    self.viewed_player_colour = self.player_colours[rect[1]]
                    self.viewed_adventurer_number = 0
                    self.viewed_adventurer = self.game.adventurers[rect[1]][0]
                    return True
            return False
    
    def get_input_coords(self, adventurer):
        '''Sends an image of the latest play area, accepts input only from this visual's players.
        
        Arguments
        adventurer takes a Cartolan.Adventurer
        '''
        #Make sure that the current adventurer is up to date
        if self.current_adventurer is None:
            self.start_turn(adventurer)
        #Update the visuals to prompt input
        self.update_web_display()
        #Update the visuals for the remote players who aren't active
        self.refresh_peers(adventurer)
        
        coords = None
        while coords is None:
            coords = self.client.get_coords()
            if coords is not None:
                horizontal, vertical = coords
                #check whether the click was within the Chest menu, and return the index within the chest
                if (horizontal in range(int(self.chest_rect[0])
                        , int(self.chest_rect[0]) + int(self.chest_rect[2]))
                    and vertical in range(int(self.chest_rect[1])
                        , int(self.chest_rect[1]) + int(self.chest_rect[3]))):
#                    print("Player chose coordinates within the menu")
                    menu_row = (vertical - int(self.chest_rect[1])) // self.menu_tile_size
                    menu_column = (horizontal - int(self.chest_rect[0])) // self.menu_tile_size
                    return {"preferred_tile":self.MENU_TILE_COLS * menu_row + menu_column}
                #Check whether the click was irrelevant to gameplay but changes the focus of the active player's visuals
                elif self.check_update_focus(horizontal, vertical):
                    return {"update_visuals":"update_visuals"}
                #Check whether the click was within the toggle menu, and update the index of the selected card
                elif (horizontal in range(int(self.toggles_rect[0]), int(self.toggles_rect[0] + self.toggles_rect[2]))
                    and vertical in range(int(self.toggles_rect[1]), int(self.toggles_rect[1] + self.toggles_rect[3]))):
#                    print("Player chose coordinates within the toggle menu, with vertical: "+str(vertical))
                    #Check which highlight was clicked and return it
                    for highlight in self.toggle_rects:
                        highlight_rect = highlight[0]
                        if (horizontal in range(int(highlight_rect[0])
                                , int(highlight_rect[0]) + int(highlight_rect[2]))
                            and vertical in range(int(highlight_rect[1])
                                , int(highlight_rect[1]) + int(highlight_rect[3]))):
#                            print("Identified coordinates within one of the auto-response toggles.")
                            return {"toggle":highlight[1]}
                elif self.check_undo(horizontal, vertical):
                    self.refresh_peers(adventurer) #Update peers' displays to show that the undo request has been made
                    return {"update_cards":"update_cards"} #Get the player to prompt again and refresh their own visuals              
                else:
                    #Otherwise check whether the click was within a highlighted cell and return the coordinates
                    for highlight_type in self.highlight_rects:
                        for highlight_rect in self.highlight_rects[highlight_type]:
                            if (horizontal in range(int(highlight_rect[0])
                                    , int(highlight_rect[0]) + int(highlight_rect[2]))
                                and vertical in range(int(highlight_rect[1])
                                    , int(highlight_rect[1]) + int(highlight_rect[3]))):
                                longitude = int(math.ceil((horizontal - self.play_area_start)/self.tile_size)) - self.origin[0] - 1
                                latitude = self.dimensions[1] - int(math.ceil((vertical)/self.tile_size)) - self.origin[1]
#                                print("Identified coordinates within a highlighted option.")
                                return {highlight_type:[longitude, latitude]}
                    #Also check whether the click was on a drawn route
                    for route in self.drawn_routes:
                        for segment in route[0]:
                            if (horizontal in range(int(segment[0])
                                , int(segment[0]) + int(segment[2]))
                            and vertical in range(int(segment[1])
                                , int(segment[1]) + int(segment[3]))):
                                longitude = int(math.ceil((horizontal - self.play_area_start)/self.tile_size)) - self.origin[0] - 1
                                latitude = self.dimensions[1] - int(math.ceil((vertical)/self.tile_size)) - self.origin[1]
#                                print("Identified coordinates on a route of length "+str(len(route[1])))
                                return {"route":route[1], "destination":[longitude, latitude]}
#                coords = None
            #Check for input from the other clients to their visuals and update their view
            self.check_peer_input()
            if self.check_peers_undo():
                print("Confirmed with all clients that turn can be undone.")
                return {"undo":"undo"}
            #Wait before checking again            
            time.sleep(self.INPUT_DELAY)
        
        return {"Nothing":"Nothing"}

    def get_input_choice(self, adventurer, cards, offer_type="card"):
        '''Sends an image of the latest play area, accepts input only from this visual's players.
        
        Arguments
        adventurer takes a Cartolan.adventurer
        cards takes a list of Cartolan.card
        '''
        #Update the visuals to prompt input
        self.update_web_display()
        #Make sure that the current adventurer is up to date
        if self.current_adventurer is None:
            self.start_turn(adventurer)
        #Update the visuals for the remote players who aren't active
        if offer_type == "card":
            if cards[0].card_type[:3] == "com":
                input_type = "choose_company"
            elif cards[0].card_type[:3] == "dis":
                input_type = "choose_discovery"
            elif cards[0].card_type[:3] == "adv":
                input_type = "choose_adventurer"
        else:
            input_type = "choose_tile"
        self.refresh_peers(adventurer, choices=cards, input_type=input_type)
        
        coords = None
        while coords is None:
            coords = self.client.get_coords()
            if coords is not None:
                horizontal, vertical = coords
                #check whether the click was within each of the card areas, and return the index
                for offer_rect in self.offer_rects:
                    if (horizontal in range(int(offer_rect[0])
                            , int(offer_rect[0]) + int(offer_rect[2]))
                        and vertical in range(int(offer_rect[1])
                            , int(offer_rect[1]) + int(offer_rect[3]))):
#                        print("Player chose coordinates within a card")
                        selected_index = self.offer_rects.index(offer_rect)
                        return selected_index
                coords = None #Let them try again
            #Check for input from the other clients to their visuals and update their view
            self.check_peer_input()
            time.sleep(self.INPUT_DELAY)
        
        return False