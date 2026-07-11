'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import json
import math
import os
import time

import pygame

from cartolan import REPO_ROOT
from cartolan.editions.modes import GameAdvanced
from cartolan.players.base import Player
from cartolan.ui.live_visuals import GameVisualisation

class WebServerVisualisation(GameVisualisation):
    '''For a server-side game played in browser, shares image of play area and receives coords
    
    There will be a separate visual for each client.
    Because the clients all need to see every move, each visual will send for every player.
    But, only the moving player's visual will receive input. 
    '''
    TEMP_FILENAME_LEN = 6
    TEMP_FILE_EXTENSION = ".png"
    INPUT_DELAY = 0.1 #delay time between checking for input, in seconds
    MOVE_TIME_LIMIT = 30  # seconds per input prompt; separate from Pygame's constant

    def __init__(self, game, peer_visuals, player_colours, client, width, height):
        self.peer_visuals = peer_visuals
        self.client = client
        self.width, self.height = width, height
        self.client_players = []
        self._move_deadline = None
        self._client_ready = False  # set True when client sends READY after loading assets
        super().__init__(game, peer_visuals, player_colours)
    
    def init_GUI(self):
        '''Computes layout constants needed for serialisation; no pygame rendering.'''
        print("Initialising layout for web server visualisation (no pygame), window "
              + str(self.width) + "x" + str(self.height))
        # Layout variables mirrored in the JS _recalcLayout()
        self.play_area_width = round(self.width * (1 - self.LEFT_MENU_SCALE - self.RIGHT_MENU_SCALE))
        self.play_area_start = round(self.width * self.LEFT_MENU_SCALE)
        self.right_menu_width = round(self.width * self.RIGHT_MENU_SCALE)
        self.right_menu_start = self.play_area_start + self.play_area_width
        self.right_text_start = self.MOVE_COUNT_POSITION[0] * self.width
        self.menu_highlight_size = round(self.RIGHT_MENU_SCALE * self.width) // len(self.TOGGLE_HIGHLIGHTS)
        self.menu_route_thickness = self.ROUTE_THICKNESS
        self.menu_spacing = self.menu_route_thickness
        self.menu_tile_size = round(self.RIGHT_MENU_SCALE * self.width) // self.MENU_TILE_COLS
        self.offer_tile_size = round(self.OFFER_SCALE * self.width)
        dim_h = max(self.dimensions[1], 1)
        dim_w = max(self.dimensions[0], 1)
        self.tile_size = self.height // dim_h
        if self.play_area_width < self.tile_size * dim_w:
            self.tile_size = self.play_area_width // dim_w
        self.token_size = int(round(self.TOKEN_SCALE * self.tile_size))
        self.outline_width = math.ceil(self.TOKEN_OUTLINE_SCALE * self.token_size)
        self.prompt_text = ""
        # Placeholder rect bounds (not used for click-detection with JS client)
        self.scores_rect = (0, 0, 0, 0)
        self.score_rects = []
        self.stack_rect = (0, 0, 0, 0)
        self.current_move_count = None
        self.move_count_rect = (self.right_menu_start, 0, 0,
                                round(self.height * self.SCORES_FONT_SCALE) + self.menu_tile_size)
        self.toggles_rect = (self.right_menu_start,
                              self.move_count_rect[1] + self.move_count_rect[3]
                              + round(self.height * self.SCORES_FONT_SCALE) + self.menu_highlight_size,
                              self.right_menu_width,
                              self.menu_tile_size + round(self.height * self.SCORES_FONT_SCALE))
        self.chest_rect = (self.right_menu_start,
                           self.toggles_rect[1] + self.toggles_rect[3]
                           + round(self.height * self.SCORES_FONT_SCALE),
                           self.right_menu_width, self.menu_tile_size)
        self.piles_rect = (self.right_menu_start,
                           self.chest_rect[1] + self.chest_rect[3], 0, 0)
        self.undo_rect = (self.width, self.height, 0, 0)
        self.adventurer_centres = []
        self.inn_rects = []
        self.highlight_rects = {}
        self.drawn_routes = []
        self.action_rects = []
        self.offered_cards = None  # set by draw_card_offers, included in serialised state
        self.offered_tiles = None  # set by draw_tile_offers, included in serialised state
        # Image mappings are stored on self.game so all client viz instances share one assignment.
        if not hasattr(self.game, '_viz_card_images'):
            self.game._viz_card_images = {}
            self.game._viz_card_type_cursors = {}
            self.game._viz_card_variants = self._load_card_manifest()

    # ── Card image mapping ────────────────────────────────────────────────────

    def _load_card_manifest(self):
        manifest_path = os.path.join(REPO_ROOT,
                                     'cartolan_web', 'public_html', 'img', 'cards', 'card_manifest.json')
        try:
            with open(manifest_path) as f:
                return json.load(f)
        except Exception:
            return {}

    def _assign_card_image(self, card):
        images = self.game._viz_card_images
        if card.card_id in images:
            return
        variants = self.game._viz_card_variants.get(card.card_type, [])
        if not variants:
            images[card.card_id] = card.card_type + '.png'
            return
        cursors = self.game._viz_card_type_cursors
        cursor = cursors.get(card.card_type, 0)
        images[card.card_id] = variants[cursor % len(variants)]
        cursors[card.card_type] = cursor + 1

    def _assign_all_card_images(self):
        if hasattr(self.game, 'assigned_cultures'):
            for card in self.game.assigned_cultures.values():
                if card is not None:
                    self._assign_card_image(card)
        for advs in self.game.adventurers.values():
            for adv in advs:
                if hasattr(adv, 'character_card') and adv.character_card is not None:
                    self._assign_card_image(adv.character_card)
                for card in getattr(adv, 'manuscript_cards', []):
                    self._assign_card_image(card)

    # ── pygame-free overrides ─────────────────────────────────────────────────

    def rescale_as_needed(self):
        '''Updates grid dimensions and origin without touching pygame graphics.'''
        min_lon = min_lat = 0
        max_lon = max_lat = 0
        for lon in self.game.play_area:
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)
            for lat in self.game.play_area[lon]:
                min_lat = min(min_lat, lat)
                max_lat = max(max_lat, lat)
        self.dimensions[0] = max_lon - min_lon + 1 + 2 * self.DIMENSION_BUFFER
        self.dimensions[1] = max_lat - min_lat + 1 + 2 * self.DIMENSION_BUFFER
        self.origin[0] = -min_lon + self.DIMENSION_BUFFER
        self.origin[1] = -min_lat + self.DIMENSION_BUFFER

    def give_prompt(self, prompt_text):
        '''Stores the prompt text; rendering is done client-side.'''
        self.prompt_text = prompt_text

    def draw_move_options(self, highlight_coords={}):
        '''Updates self.highlights from highlight_coords; no pygame rendering.'''
        self.highlight_rects = {}
        for ht in self.highlights:
            coords = highlight_coords.get(ht)
            self.highlights[ht] = coords if coords else []

    def clear_move_options(self):
        for ht in self.highlights:
            self.highlights[ht] = []

    def draw_play_area(self): pass
    def draw_tokens(self): pass
    def draw_routes(self): pass
    def draw_scores(self): pass
    def draw_move_count(self): pass
    def draw_toggle_menu(self, fixed_responses={}): pass
    def draw_routes_menu(self): pass
    def draw_chest_maps(self): pass
    def draw_tile_piles(self): pass
    def draw_discard_pile(self): pass
    def draw_undo_button(self): pass
    def draw_cards(self): pass
    def draw_card_offers(self, cards):
        for card in cards:
            self._assign_card_image(card)
        self.offered_cards = [c.to_json() for c in cards]
    def draw_tile_offers(self, tiles):
        self.offered_tiles = [t.to_json() for t in tiles]
    def draw_prompt(self): pass
    def clear_prompt(self): self.prompt_text = ""

    # ─────────────────────────────────────────────────────────────────────────

    def serialize_state(self):
        '''Assembles the complete game and UI state as a JSON-serialisable dict.'''
        self._assign_all_card_images()
        state = self.game.to_json()
        state["player_colours"] = {p.name: c for p, c in self.player_colours.items()}
        current_adv = self.current_adventurer
        viewed_adv = self.viewed_adventurer
        state["current_player_name"] = current_adv.player.name if current_adv else None
        state["current_adventurer_index"] = self.current_adventurer_number
        state["viewed_player_name"] = viewed_adv.player.name if viewed_adv else None
        state["viewed_adventurer_index"] = self.viewed_adventurer_number
        state["highlights"] = {ht: coords for ht, coords in self.highlights.items() if coords}
        state["draw_all_routes"] = self.draw_all_routes
        state["undo_agreed"] = self.undo_agreed
        state["undo_asked"] = any(pv.undo_agreed for pv in self.peer_visuals if pv is not self)
        state["prompt"] = "Loading assets, please wait..." if not self._client_ready else self.prompt_text
        state["offered_cards"] = self.offered_cards or []
        state["offered_tiles"] = self.offered_tiles or []
        state["card_images"] = self.game._viz_card_images
        state["auto_actions"] = {
            player.name: dict(player.auto_actions)
            for player in self.client_players
            if hasattr(player, 'auto_actions')
        }
        state["move_deadline"] = int(self._move_deadline * 1000) if self._move_deadline else None
        state["move_timer_limit"] = self.MOVE_TIME_LIMIT
        return state

    def update_web_display(self):
        '''Sends the current game state as JSON to this client.'''
        self.client.sendMessage("STATE[00100]" + json.dumps(self.serialize_state()))
        print("State sent to client at " + str(self.client.address))
    
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
        '''Sends the current game state to this peer; rendering is done client-side.'''
        adv = self.current_adventurer
        if adv is None:
            return
        if input_type == "move":
            prompt = adv.player.name + " is moving their Adventurer #" + str(self.current_adventurer_number + 1)
        elif input_type == "text":
            prompt = adv.player.name + " is choosing a Silk amount for their Adventurer #" + str(self.current_adventurer_number + 1)
        elif input_type == "choose_tile":
            prompt = adv.player.name + " is choosing a tile for their Adventurer #" + str(self.current_adventurer_number + 1)
        elif input_type == "choose_discovery":
            prompt = adv.player.name + " is choosing a Manuscript card for their Adventurer #" + str(self.current_adventurer_number + 1)
        elif input_type == "choose_company":
            prompt = adv.player.name + " is choosing their Culture card"
        else:
            prompt = adv.player.name + " is choosing a Character card for their Adventurer #" + str(self.current_adventurer_number + 1)
        self.give_prompt(prompt)
    
    def check_peer_input(self):
        '''Cycles through remote players besides the active one, checking whether clicks have been registered and updating their private visuals accordingly
        '''
        checked_visuals = []
        for game_vis in self.peer_visuals:
            if not self.client == game_vis.client and game_vis not in checked_visuals:
                checked_visuals.append(game_vis)
                coords = game_vis.client.get_coords()
                if coords is None:
                    continue
                if isinstance(coords, dict):
                    if 'ready' in coords:
                        game_vis._client_ready = True
                    else:
                        result = game_vis._dispatch_semantic(coords, game_vis.current_adventurer)
                        if result is not None:
                            game_vis.update_web_display()
                elif isinstance(coords, list) and len(coords) == 2:
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

    def draw_showcase_tile(self):
        '''For spectators enlarges a tile chosen from the play area
        '''
        # For each location in the play area draw the tile
        if self.viewed_longitude in self.game.play_area:
            if self.viewed_latitude in self.game.play_area[self.viewed_longitude]:
                self.draw_tile_offers([self.game.play_area[self.viewed_longitude][self.viewed_latitude]])

    def check_update_focus(self, horizontal, vertical):
        '''Checks whether click coordinates were within the superficial visual elements that need no game response but should revise the client's visuals
        '''
#        if (horizontal in range(int(self.scores_rect[0]), int(self.scores_rect[0] + self.scores_rect[2]))
#            and vertical in range(int(self.scores_rect[1]), int(self.scores_rect[1] + self.scores_rect[3]))):
#            print("Player chose coordinates within the scores table, with vertical: "+str(vertical))
        #Check whether the click was on one of the scores in the table (check them individually straight away, to avoid masking clicks on highlights under the scores table)
        for score in self.score_rects:
            score_rect = score[0]
            if (horizontal in range(int(score_rect[0]), int(score_rect[0] + score_rect[2]))
                and vertical in range(int(score_rect[1]), int(score_rect[1] + score_rect[3]))):
                print("Having found the click within a particular player/adventurer's score, need to update the focus of the card stacks")
                if isinstance(score[1], Player):
                    #just choose the first adventurer if it was the player's vault silks selected
                    self.viewed_player_colour = self.player_colours[score[1]]
                    self.viewed_adventurer_number = 0
                    self.viewed_adventurer = self.game.adventurers[score[1]][0]
                else:
                    self.viewed_player_colour = self.player_colours[score[1].player]
                    self.viewed_adventurer_number = self.game.adventurers[score[1].player].index(score[1])
                    self.viewed_adventurer = score[1]
                print("Updated focus for card visuals to "+self.viewed_adventurer.player.name+"'s Adventurer #"+str(self.viewed_adventurer_number+1))
                return True
        # Check whether the click was within the Culture/Culture Card
        if (horizontal in range(int(self.culture_card_rect[0]), int(self.culture_card_rect[0]+self.culture_card_rect[2]))
                and vertical in range(int(self.culture_card_rect[1]), int(self.culture_card_rect[1]+self.culture_card_rect[3]))):
            print("Click was within the Culture Card")
            self.selected_culture_card = True
            self.selected_character_card = False
            self.selected_card_num = None
            return True
        # Check whether the click was within the card stack, and update the index of the selected card
        elif (horizontal in range(int(self.stack_rect[0]), int(self.stack_rect[0] + self.stack_rect[2]))
                and vertical in range(int(self.stack_rect[1]), int(self.stack_rect[1] + self.stack_rect[3]))):
            print("Player chose coordinates within the card stack, with vertical: " + str(vertical))
            if vertical - self.stack_rect[1] < self.stack_rect[3] - self.card_height:
                print("The click was within a Manuscript Card")
                self.selected_culture_card = False
                self.selected_character_card = False
                self.selected_card_num = int(vertical - self.stack_rect[1]) // int(self.card_height * self.CARD_HEADER_SHARE)
            else:
                print("The click was within the Character Card")
                self.selected_culture_card = False
                self.selected_character_card = True
                self.selected_card_num = None
            return True
        #Check for clicks in the toggle menu, for changing route drawing mode
        elif (horizontal in range(int(self.toggles_rect[0]), int(self.toggles_rect[0] + self.toggles_rect[2]))
            and vertical in range(int(self.toggles_rect[1]), int(self.toggles_rect[1] + self.toggles_rect[3]))):
            self.draw_all_routes = not self.draw_all_routes
            return True
        #Check for clicks among the chest maps to highlight them
        elif (horizontal in range(int(self.chest_rect[0]), int(self.chest_rect[0] + self.chest_rect[2]))
                  and vertical in range(int(self.chest_rect[1]), int(self.chest_rect[1] + self.chest_rect[3]))):
            menu_row = (vertical - int(self.chest_rect[1])) // self.menu_tile_size
            menu_column = (horizontal - int(self.chest_rect[0])) // self.menu_tile_size
            self.viewed_tile_num = menu_row * self.MENU_TILE_COLS + menu_column
            return True
        elif (isinstance(self.game, GameAdvanced) and (self.selected_culture_card or self.selected_character_card or self.selected_card_num is not None
                                                       or self.viewed_tile_num is not None or self.viewed_longitude is not None)):
            # Remove focus on any card
            # None of the cards were selected
            self.selected_culture_card = False
            self.selected_character_card = False
            self.selected_card_num = None
            self.viewed_tile_num = None
            self.viewed_longitude = None
            self.viewed_latitude = None
            return True
        else:
            #Check the various Adventurer and Inn shapes for a click and use this to select the Adventurer to focus on
            for centre in self.adventurer_centres:
                if (horizontal - centre[0][0])**2 + (vertical - centre[0][1])**2 < self.token_size**2:
                    print("Click detected within one of the Adventurers' areas, with centre: "+str(centre[0]))
                    self.viewed_player_colour = self.player_colours[centre[1].player]
                    self.viewed_adventurer_number = self.game.adventurers[centre[1].player].index(centre[1])
                    self.viewed_adventurer = centre[1]
                    return True
            for rect in self.inn_rects:
                if (horizontal in range(int(rect[0][0]), int(rect[0][0] + rect[0][2]))
                    and vertical in range(int(rect[0][1]), int(rect[0][1] + rect[0][3]))):
                    print("Click detected within one of the Inns' areas for "+self.player_colours[rect[1]]+" player.")
                    self.viewed_player_colour = self.player_colours[rect[1]]
                    self.viewed_adventurer_number = 0
                    self.viewed_adventurer = self.game.adventurers[rect[1]][0]
                    return True
            # Check for clicks among the play_area tiles to showcase them
            if (self.current_adventurer.player not in self.client_players
                    and horizontal in range(int(self.play_area_start), int(self.right_menu_start))
                    and vertical in range(0, int(self.prompt_position[1]))):
                longitude = int(math.ceil((horizontal - self.play_area_start) / self.tile_size)) - self.origin[
                    0] - 1
                latitude = self.dimensions[1] - int(math.ceil((vertical) / self.tile_size)) - self.origin[1]
                if self.game.play_area.get(longitude) is not None:
                    if self.game.play_area.get(longitude).get(latitude) is not None:
                        #
                        # Remember to showcase the tile at this position
                        self.viewed_longitude = longitude
                        self.viewed_latitude = latitude
                        # Don't showcase anything else
                        self.selected_culture_card = False
                        self.selected_character_card = False
                        self.selected_card_num = None
                        self.viewed_tile_num = None
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
        #Only start the countdown once the client has finished loading assets
        self._move_deadline = time.time() + self.MOVE_TIME_LIMIT if self._client_ready else None
        #Update the visuals to prompt input (deadline included so client sees it immediately)
        self.update_web_display()
        #Update the visuals for the remote players who aren't active
        self.refresh_peers(adventurer)

        coords = None
        while coords is None:
            if self._move_deadline is not None and time.time() >= self._move_deadline:
                self._move_deadline = None
                return {"timeout": True}
            coords = self.client.get_coords()
            if coords is not None:
                if isinstance(coords, dict):
                    # Semantic message already parsed by handleMessage
                    result = self._dispatch_semantic(coords, adventurer)
                    if result is not None:
                        self._move_deadline = None
                        return result
                    coords = None  # keep polling if dispatch returned nothing actionable
                else:
                    # Legacy pixel-coordinate fallback (should not occur with JS client)
                    horizontal, vertical = coords
                    for highlight_type in self.highlight_rects:
                        for highlight_rect in self.highlight_rects[highlight_type]:
                            if (horizontal in range(int(highlight_rect[0])
                                    , int(highlight_rect[0]) + int(highlight_rect[2]))
                                and vertical in range(int(highlight_rect[1])
                                    , int(highlight_rect[1]) + int(highlight_rect[3]))):
                                longitude = int(math.ceil((horizontal - self.play_area_start)/self.tile_size)) - self.origin[0] - 1
                                latitude = self.dimensions[1] - int(math.ceil((vertical)/self.tile_size)) - self.origin[1]
                                self._move_deadline = None
                                return {highlight_type:[longitude, latitude]}
                    coords = None
            #Check for input from the other clients to their visuals and update their view
            self.check_peer_input()
            if self.check_peers_undo():
                print("Confirmed with all clients that turn can be undone.")
                self._move_deadline = None
                return {"undo":"undo"}
            #Wait before checking again
            time.sleep(self.INPUT_DELAY)

        return {"Nothing":"Nothing"}

    def _dispatch_semantic(self, sem, adventurer):
        '''Translates a semantic dict from the browser into a get_input_coords return value.'''
        if not self._client_ready and 'ready' not in sem:
            return None  # discard game input until client has finished loading assets
        if 'chosen_map' in sem:
            return sem
        if 'chest_rotate_anti' in sem:
            return sem
        if 'chest_rotate_clock' in sem:
            return sem
        if 'toggle' in sem:
            return sem
        if 'routes_toggle' in sem:
            self.draw_all_routes = not self.draw_all_routes
            return {"update_visuals":"update_visuals"}
        if 'undo_request' in sem:
            self.undo_agreed = not self.undo_agreed
            self.refresh_peers(adventurer)
            return {"update_cards":"update_cards"}
        if 'focus' in sem:
            player_name, adv_idx = sem['focus']
            for p in self.game.players:
                if p.name == player_name:
                    advs = self.game.adventurers[p]
                    if adv_idx < len(advs):
                        self.viewed_adventurer = advs[adv_idx]
                        self.viewed_adventurer_number = adv_idx
                        self.viewed_player_colour = self.player_colours.get(p, 'white')
                    break
            return {"update_visuals":"update_visuals"}
        if 'route_follow' in sem:
            rf = sem['route_follow']
            dest_lon, dest_lat = rf['dest']
            for player in self.game.players:
                if player.name == rf['player']:
                    advs = self.game.adventurers.get(player, [])
                    if rf['adv_idx'] < len(advs):
                        route_tiles = list(advs[rf['adv_idx']].route)
                        if route_tiles:
                            return {'route': route_tiles, 'destination': [dest_lon, dest_lat]}
                    break
            return {"update_visuals": "update_visuals"}
        if 'play' in sem:
            return {"Nothing": "Nothing"}
        if 'ready' in sem:
            self._client_ready = True
            self._move_deadline = time.time() + self.MOVE_TIME_LIMIT
            self.update_web_display()
            return None  # keep polling; client now has a fresh deadline
        # highlight_type: [lon, lat] — direct game move/action from JS
        return sem if sem else None

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
        
        while True:
            coords = self.client.get_coords()
            if isinstance(coords, dict) and 'offer_select' in coords:
                idx = coords['offer_select']
                if 0 <= idx < len(cards):
                    self.offered_cards = None
                    self.offered_tiles = None
                    return idx
            self.check_peer_input()
            time.sleep(self.INPUT_DELAY)