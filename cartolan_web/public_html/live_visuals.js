/**
 * @fileoverview A collection of methods that render server-side games of Cartolan to an HTML page, and provide various player input back to the server.
 * Dependencies: canvas
 * @package cartolan
 *
 * Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
 */

/** A class that does something. */
class GameVisualisation extends SomeBaseClass {
    /**
     * Operates on an instance of MyClass and returns something.
     * @param {!MyClass} obj An object that for some reason needs detailed
     *     explanation that spans multiple lines.
     * @param {!OtherClass} obviousOtherClass
     * @return {boolean} Whether something occurred.
     */
    someMethod(obj, obviousOtherClass) { ... }

    /** @override */
    overriddenMethod(param) { ... }
}

/**
 * Demonstrates how top-level functions follow the same rules.  This one
 * makes an array.
 * @param {TYPE} arg
 * @return {!Array<TYPE>}
 * @template TYPE
 */

/**A canvas-based interactive visualisation for games of Cartolan, expecting socket interaction with a remote server running the game logic

* Methods:
* draw_move_options
* draw_tokens
* draw_play_area
* draw_wealth_scores
* draw_routes
* draw_prompt
*/
class GameVisualisation {
    //functionine some constants that will not vary game by game
var MOVE_TIME_LIMIT = 10 //To force a timeout if players aren't responding
var PLAYER_OFFSETS = [[0.25, 0.25], [0.25, 0.75], [0.75, 0.25], [0.75, 0.75]]
var AGENT_OFFSET = [0.5, 0.5] //the placement of agents on the tile, the same for all players and agents, because there will only be one per tile
var ADVENTURER_OFFSETS = [[0.0, 0.0], [0.1, -0.1], [-0.1, 0.1], [-0.1, -0.1], [0.1, 0.1]] //the offset to differentiate multiple adventurers on the same tile
var DIMENSION_BUFFER = 1 //the number of tiles by which the play area is extended when methods are called
var BACKGROUND_COLOUR = (255, 255, 255, 0) //(38, 50, 60) //(38, 50, 66)
var PLAIN_TEXT_COLOUR = (255, 255, 255)
var WONDER_TEXT_COLOUR = (0, 0, 0)
var ACCEPT_UNDO_COLOUR = (255, 0, 0)
var CARD_TEXT_COLOUR = (0, 0, 0)
var CARD_BACKGROUND_COLOUR = (255, 255, 255)
var CHEST_HIGHLIGHT_COLOUR = (0, 255, 0)
var TOGGLE_TRUE_COLOUR = (0, 255, 0)
var TOGGLE_FALSE_COLOUR = (255, 0, 0)
var TILE_BORDER = 0.02 //the share of grid width / height that is used for border
var CARD_HEADER_SHARE = 0.15 // the share of card images that is the header, visually summarising the buffs of the card with colour and a logo
var CARD_BODY_START = 0.7 // the share of the card before text starts
var MENU_FONT = "stmary10" //The system font to try and match
var LEFT_MENU_SCALE = 0.13
var MENU_TILE_COLS = 2
var RIGHT_MENU_SCALE = 0.13
var OFFER_SCALE = 0.15
var ROUTE_THICKNESS = 4.0
var NUM_DASHES = 10
var TOKEN_SCALE = 0.2 //relative to tile sizes
var AGENT_SCALE = 1.75 //relative to Adventurer radius
var TOKEN_OUTLINE_SCALE = 0.25 //relative to token scale
var TOKEN_FONT_SCALE = 0.5 //relative to tile sizes
var TOKEN_FONT_COLOURS = { "yellow": "black" }
var SCORES_POSITION = [0.0, 0.0]
var SCORES_FONT_SCALE = 0.05 //relative to window size
var SCORES_SPACING = 1.5 //the multiple of the score pixel scale to leave for each number
var CARD_FONT_SCALE = 0.03
var MOVE_COUNT_POSITION = [0.8, 0.0]
var METER_OPACITY = 128
var ANY_DIRECTION_METER_COLOUR = (0, 0, 0)
var DOWNWIND_WATER_METER_COLOUR = (0, 0, 0)
var PROMPT_SHARE = 0 //@TODO move prompt into the bottom right corner, with multi - line
var PROMPT_POSITION = [0.0, 0.95]
var PROMPT_FONT_SCALE = 0.05 //relative to window size

var TILE_PATH = './img/map_tiles/tiles/'
var CARDS_PATH = './img/map_tiles/cards/'
var METERS_PATHS = {
        "any_direction": './img/move_meters/any_direction.png'
        , "downwind_water": './img/move_meters/downwind_water.png'
    }
var HIGHLIGHT_PATHS = {
        "move": './img/highlights/option_valid_move.png'
        , "abandon": './img/highlights/option_abandon.png'
        , "invalid": './img/highlights/option_invalid_move.png'
        , "buy": './img/highlights/option_buy.png'
        , "attack": './img/highlights/option_attack.png'
        , "rest": './img/highlights/option_rest.png'
        , "buy_rest": './img/highlights/option_buy.png'
        , "move_agent": './img/highlights/option_valid_move.png'
        , "agent_transfer": './img/highlights/option_buy.png'
    }
var TOGGLE_HIGHLIGHTS = ["buy", "attack", "rest"]
var CARD_TITLES = {
    "com+rests": "The Inrepid Academy"
    , "com+transfers": "The Great Company"
    , "com+earning": "The Merchants' Guild"
    , "com+arrest": "The Harbour Authority"
    , "com+refurnish": "The Privateer Brethren"
    , "com+pool": "Order of the Lightbrary"
}
var CARD_TEXTS = {
    "adv+agents": "Can place and immediately rest with Inns on existing tiles, for 3 treasure."
    , "adv+attack": "Needs only win or draw Rock, Paper, Scissors to attack successfully."
    , "adv+bank": "Can transfer treasure to your Inns when visiting anyone's Inn."
    , "adv+damage": "Successfully attacked Adventurers are returned to their last city, and Inns are fully removed."
    , "adv+functionence": "Attacking opponents have to win Rock, Paper, Scissors twice to succeed."
    , "adv+downwind": "Can move up to three times riding the wind after tiring, each turn and after resting."
    , "adv+upwind": "Can move three times in any direction before getting tired, then one riding the wind, each turn or after resting."
    , "adv+maps": "Carries up to three map tiles in Chest."
    , "dis+agents": "This Adventurer can place Inns on existing tiles and immediately rest with them, for 3 treasure."
    , "dis+attack": "This Adventurer needs only win or draw Rock, Paper, Scissors to attack successfully."
    , "dis+bank": "This Adventurer can transfer treasure to your Inns when visiting anyone's Inn."
    , "dis+damage": "Successfully attacked Adventurers are returned to their last city, and Inns are removed."
    , "dis+functionence": "Attacking opponents have to win an extra round of Rock, Paper, Scissors to succeed."
    , "dis+downwind": "This Adventurer can move once more riding the wind after tiring, each turn and after resting."
    , "dis+upwind": "This Adventurer can move once more before tiring, rather than after, each turn and after resting."
    , "dis+maps": "This Adventurer carries an extra map tile in their chest."
    , "com+rests": "Your Adventurers can rest with other Adventurers like Inns. Draw 3 Adventurers."
    , "com+transfers": "Treasure earned by your Inns goes to your Vault. Draw 3 Manuscripts."
    , "com+earning": "Your Inns earn 1 treasure when opponents trade on their tile. Draw 3 Manuscripts."
    , "com+arrest": "Your Inns try to arrest pirates landing on their tile. Draw 3 Adventurers."
    , "com+refurnish": "Your Adventurers can lose the pirate token by resting. Draw 3 Adventurers."
    , "com+pool": "Anyone's Inns can swap your Adventures' maps for 1 treasure. Draw 3 Manuscripts."
}

var dimensions = [len(game.play_area), max([len(game.play_area[longitude]) for longitude in game.play_area])]
var origin = [dimension / 2 for dimension in dimensions]
        
console.log("Initialising state variables")
//        clock = pygame.time.Clock()
var move_timer = MOVE_TIME_LIMIT
var current_player_colour = "black"
var current_adventurer_number = 0
var current_adventurer = None
var viewed_player_colour = "black"
var viewed_adventurer_number = 0
var viewed_adventurer = None
var highlights = { highlight_type{ [] for highlight_type in HIGHLIGHT_PATHS }
var highlight_rects = []
var drawn_routes = []
var offer_rects = []
//Placeholders for the various GUI elements
var scores_rect = (0, 0, 0, 0)
var stack_rect = (0, 0, 0, 0)
var current_move_count = None
var move_count_rect = (MOVE_COUNT_POSITION[0], MOVE_COUNT_POSITION[1], 0, 0)
var chest_rect = (MOVE_COUNT_POSITION[0], MOVE_COUNT_POSITION[1], 0, 0)
var toggles_rect = (MOVE_COUNT_POSITION[0], MOVE_COUNT_POSITION[1], 0, 0)
var action_rects = []
var piles_rect = (MOVE_COUNT_POSITION[0], MOVE_COUNT_POSITION[1], 0, 0)
var discard_pile = []
var discarding_adventurer = None
var undo_rect = (width, height, 0, 0)
var undo_agreed = False
var adventurer_centres = []
var agent_rects = []
var selected_card_num = None
var card_images = {}
var draw_all_routes = True
//Libraries for cached versions of the various images used
var tile_images = {} //a dict of lists of tile images with a particular combination of land, sea and wind
var tile_image_library = {} //a dict pairing particular tiles with particular art for the play area itself
var menu_tile_library = {} //a dict pairing particular tiles with their art at a scale for the chest and discard piles
var offer_tile_library = {} //duplicate tile art for use in selection menu after 
var highlight_library = {}
var toggle_library = {} // duplicate these tiles at a different size for use in menus
var card_image_library = {}

init_GUI()

function init_GUI(){
  console.log("Initialising the canvasses for background and foregrounds")
  var background = document.createElement("background").getContext("2d"); //For opaque slow-changing content
  var turn_fground = document.createElement("turn_foreground").getContext("2d"); //For fast-changing content with transparency
  var move_fground = document.createElement("move_foreground").getContext("2d"); //For very-fast-changing content with transparency
  //Now add all of these to the DOM, with absolute positioning so that they overlap
  for (canvas_name in ["background", "turn_foreground", "move_foreground"]) {
    canvas = document.getElementById(canvas_name);
    canvas.style.position = "absolute";
    canvas.style.top = "0px";
    canvas.style.left = "0px";
    canvas.width = window.innerWidth; //get this from the browser window size
    canvas.height = Math.round(heightShare * window.innerHeight); //get this from the browser window size
    document.body.insertBefore(canvas, document.body.childNodes[0]);
  }
  background.fillStyle = BACKGROUND_COLOUR;  // fill completely with a default background colour
  background.globalAlpha = 0.5;
  background.fillRect(left, top, width, height);
  //        background.drawImage(backing_image, [0, 0])
  console.log("Initialising visual scale variables, to fit window of size " + str(width) + "x" + str(height))
  var tile_size = Math.floor(height / dimensions[1])
        //We'll have a different tile size for dicards and chest tiles
  var menu_tile_size = Math.floor(RIGHT_MENU_SCALE * width / MENU_TILE_COLS)
        //Where piracy is possible, we'll have a different tile size for choosing stolen ones
  var offer_tile_size = Math.floor(OFFER_SCALE * width)
  //Before sizing against the horizontal dimension, we'll work out how much space the menus will take away
  var play_area_width = Math.ceil(width * (1 - LEFT_MENU_SCALE - RIGHT_MENU_SCALE))
  var play_area_start = Math.floor(width * LEFT_MENU_SCALE)
  var right_menu_width = Math.floor(width * RIGHT_MENU_SCALE)
  var right_menu_start = play_area_start + play_area_width
  var right_text_start = Math.floor(MOVE_COUNT_POSITION[0] * width) //All text indicators in the right menu will follow the same indent
  var menu_highlight_size = Math.floor(RIGHT_MENU_SCALE * width) // len(TOGGLE_HIGHLIGHTS)
  var menu_route_thickness = ROUTE_THICKNESS
  var menu_spacing = menu_route_thickness
  //Tiles will be scaled to fit the smaller dimension
  if play_area_width < tile_size * dimensions[0]{
    tile_size = Math.floor(play_area_width / dimensions[0])
  }
  var token_size = Math.round(TOKEN_SCALE * tile_size) //token size will be proportional to the tiles
  var outline_width = Math.ceil(TOKEN_OUTLINE_SCALE * token_size)
  var token_font = pygame.font.SysFont(None, Math.round(tile_size * TOKEN_FONT_SCALE)) //the font size for tokens will be proportionate to the window size
  var scores_font = Math.round(height * SCORES_FONT_SCALE).toString() + "px " + MENU_FONT //the font size for scores will be proportionate to the window size
  var card_font = Math.round(height * CARD_FONT_SCALE).toString() + "px " + MENU_FONT //the font size for scores will be proportionate to the window size
  var prompt_font = Math.round(height * PROMPT_FONT_SCALE).toString() + "px " + MENU_FONT //the font size for prompt will be proportionate to the window size
  var prompt_position = [play_area_start + PROMPT_POSITION[0] * width, PROMPT_POSITION[1] * height]
  var prompt_text = ""
  //Make sure that the GUI menus are drawn on the correct sides from the start
  var scores_rect = [0, 0, 0, 0]
  var stack_rect = [0, 0, 0, 0]
  var current_move_count = None
  var move_count_rect = [MOVE_COUNT_POSITION[0] * width, MOVE_COUNT_POSITION[1] * height, 0, Math.round(height * SCORES_FONT_SCALE) + menu_tile_size]
  var toggles_rect = [right_menu_start, move_count_rect[1] + move_count_rect[3] + Math.round(height * SCORES_FONT_SCALE) + menu_highlight_size, 0, menu_tile_size + Math.round(height * SCORES_FONT_SCALE)]
  var chest_rect = [right_menu_start, toggles_rect[1] + toggles_rect[3] + Math.round(height * SCORES_FONT_SCALE), 0, menu_tile_size]
  var piles_rect = [right_menu_start, toggles_rect[1] + toggles_rect[3] + Math.round(height * SCORES_FONT_SCALE), 0, 0]
  //Import images
  init_graphics()
//        init_sound()
        
    //    function init_sound(){
//        /**Imports sounds to accompany play
//        */
//        winSound = pygame.mixer.Sound('win.wav')
//        loseSound = pygame.mixer.Sound('lose.wav')
//        placeSound = pygame.mixer.Sound('place.wav')
//        // pygame.mixer.music.load("music.wav")
//        // pygame.mixer.music.play()
    
        //Set the visual running
//        while not game.game_over{
//            update()

  /**Translates a tile's wind direction into a rotation of its image
  */
  function rotate_tile_image(tile, tile_image){
    wind_direction = tile[wind_direction]
    if wind_direction["north"] and wind_direction["east"]{
      rotation = 0; //North East
    } else if not wind_direction["north"] and wind_direction["east"]{
      rotation = -Math.PI / 2; //South East wind
    } else if not wind_direction["north"] and not wind_direction["east"]{
      rotation = Math.PI; //South West wind
    } else {
      rotation = Math.PI / 2; //North West wind by exclusion
    }
    //Create a new canvas for the rotated version of the image
    background.offscreenCanvas = document.createElement('canvas');
    background.offscreenCanvas.width = tile_image.width;
    background.offscreenCanvas.height = tile_image.height;
    background.offscreenCanvas.drawImage(tile_image, 0, 0);
    // rotate the canvas to the specified degrees
    background.offscreenCanvas.rotate(rotation);
    return background.offscreenCanvas;
  }

  /**For a particular image library, rescales all of the images
  */
  function rescale_images(image_library, new_size) {
    for (image_type in image_library) {
      image = image_library.image_type
      background.offscreenCanvas = document.createElement('canvas');
      background.offscreenCanvas.width = image.width;
      background.offscreenCanvas.height = image.height;
      background.offscreenCanvas.drawImage(image, 0, 0);
      background.offscreenCanvas.getContext.scale(new_size[0], new_size[1]);
      image_library.image_type = background.offscreenCanvas;
    }
  }


  /**Caches an image offscreen for a given canvas
  */
  function cache_offscreen(parentCanvas, image, width, height) {
    parentCanvas.offscreenCanvas = document.createElement('canvas');
    parentCanvas.offscreenCanvas.width = image.width;
    parentCanvas.offscreenCanvas.height = image.height;
    parentCanvas.offscreenCanvas.drawImage(image, 0, 0);
    parentCanvas.offscreenCanvas.getContext.scale(width, height);
    return parentCanvas.offscreenCanvas;
  };

  /**Reads in the images for visualising play, caching
  */
  //@TODO cache all the images in off-screen canvases (although with higher-res versions you may only want to cache the rotations of chest tiles)
  function cache_menu_graphics() {
    console.log("Importing tile and highlight images and establishing a mapping")
    var tile_image_names = [filename for filename in os.listdir(TILE_PATH) if ".png" in filename] //@TODO this list may need to be sent separately from the server: we can't presume that all the images will have loaded when we get here
    var tile_image_names.sort() //Ensure it's deterministic which specific cards are assigned to each adventurer, so that this is consistent with the game's other visuals
    //Resize the tile image to the smallest that will still fit in each of its roles
    var max_size = max(tile_size, menu_tile_size, offer_tile_size);
    //console.log(tile_image_names)
    for (tile_image_name in tile_image_names) {
      tile_type = tile_image_name.split(".")[0].split("_")[0] //assumes that the tile type will be the image filename will start with the type as recognised by the game
      let tile_image = new Image;
      tile_image.onload = function () {
        offscreenCanvas = cache_offscreen(background, tile_image, max_size, max_size);
        tile_type_set = tile_images.get(tile_type)
        if (tile_type_set is null) {
          tile_images.tile_type = [offscreenCanvas]
        } else {
          tile_type_set.push(offscreenCanvas)
        };
      }
      tile_image.src = TILE_PATH + tile_image_name;
    }
    // import the masks used to highlight movement options
    for (highlight_name in HIGHLIGHT_PATHS) {
      let highlight_image = new Image;
      highlight_image.onload = function () {
        highlight_library.highlight_name = cache_offscreen(move_fground, highlight_image, tile_size, tile_size);
        // duplicate these tiles at a different size for use in menus
        toggle_library.highlight_name = cache_offscreen(move_fground, highlight_image, menu_highlight_size, menu_highlight_size);
        };
      highlight_path = HIGHLIGHT_PATHS[highlight_name];
      highlight_image.src = highlight_path
    };
    // import the graphics for meters showing the remaining moves until rest
    meters_library = {}
    for (meter_name in METERS_PATHS) {
      let meter_image = new Image;
      meter_image.onload = function () {
        meters_library.meter_name = cache_offscreen(move_fground, meter_image, menu_tile_size, menu_tile_size);
      };
      meter_path = METER_PATHS[meter_name];
      meter_image.src = meter_path;
    }
    //import the cards that will award various rule buffs
    //            used_card_images = {} //just in case the images available don't provide enough unique versions of each card type
    card_image_names = [filename for filename in os.listdir(CARDS_PATH) if ".png" in filename]
    card_image_names.sort() //Ensure it's deterministic which specific cards are assigned to each adventurer, so that this is consistent with the game's other visuals
    for (card_image_name in card_image_names) {
      card_type = card_image_name.split("_")[0] //assumes that the card type will be the image filename will start with the type as recognised by the game
      card_image = pygame.image.load(CARDS_PATH + card_image_name)
      //Resize the card image to fit in the menu
      new_width = play_area_start
      new_height = int(card_image.get_height() * new_width / card_image.get_width())
      card_height = new_height
      card_width = new_width
      card_type_set = card_image_library.get(card_type)
      console.log("Adding text to card of type '" + card_type + "'")
      if (card_type_set is null) {
        scaled_image = pygame.transform.scale(card_image, [new_width, new_height])
        update_card_text(scaled_image, card_type)
        card_image_library[card_type] = [scaled_image]
        //just in case the images available don't provide enough unique versions of each card type for what the game allocates
        //                    used_card_images[card_type] = []
      } else {
        scaled_image = pygame.transform.scale(card_image, [new_width, new_height])
        update_card_text(scaled_image, card_type)
        card_type_set.push(scaled_image)
        //                 //Resize the card image to be displayed more prominently
        //                 new_width = card
        //                 new_height = int(card_image.get_height() * new_width / card_image.get_width())
        //                 card_height = new_height
        //                 card_width = new_width
        //                 card_type_set = card_image_library.get(card_type)
        //                 console.log("Adding text to card of type '" + card_type + "'")
        //                 if card_type_set is None{
        //                     scaled_image = pygame.transform.scale(card_image, [new_width, new_height])
        //                     update_card_text(scaled_image, card_type)
        //                     card_image_library[card_type] = [scaled_image]
        //                     //just in case the images available don't provide enough unique versions of each card type for what the game allocates
        // //                    used_card_images[card_type] = []
        //                 else{
        //                     scaled_image = pygame.transform.scale(card_image, [new_width, new_height])
        //                     update_card_text(scaled_image, card_type)
        //                     card_type_set.push(scaled_image)
        //Now supplement with the card types that don't have images
        for (card_type in CARD_TITLES) {
          if (not card_type in card_image_library.keys()) {
            console.log("With no card image for type " + card_type + ", creating one...")
            card_image_library[card_type] = [create_card(card_type)]
          }
        }
      }
    }
    rescale_graphics() //adjust the size of the imported images to fit the display size
  }

  /**For cards with no image, creates a placeholder.
  */
  //@TODO differentiate Cadre vs Character / Manuscript cards, to determine orientation
  function create_card(card_type) {
    card_width = play_area_start
    card_height = play_area_start * play_area_start // card_height
    card = pygame.Surface((card_width, card_height))
    card.fill(CARD_BACKGROUND_COLOUR)
    card_title = CARD_TITLES[card_type]
    card_text = CARD_TEXTS[card_type]
    //Create the text objects to add to the card
    rendered_title = card_font.render(card_title, 1, CARD_TEXT_COLOUR)
    rendered_text = wrap_text(card_text, card_width, card_height, card_font, CARD_TEXT_COLOUR, CARD_BACKGROUND_COLOUR)
    //Work out positions that will centre the title as well as possible and place it on the card
    title_horizontal = (card_width - rendered_title.get_width()) // 2
    title_vertical = 0
    card.putImageData(rendered_title, [title_horizontal, title_vertical])
    //Work out positions that will centre the text as well as possible and place it on the card
    if (card_width - rendered_text.get_width() > 0) {
      text_horizontal = (card_width - rendered_text.get_width()) // 2
    } else {
      text_horizontal = 0
    }
    if (card_height - rendered_text.get_height()) {
      text_vertical = rendered_title.get_height() + (card_height - rendered_title.get_height() - rendered_text.get_height()) // 2
    } else {
      text_vertical = rendered_title.get_height()
    }
    card.putImageData(rendered_text, [text_horizontal, text_vertical])
    return card
  }

  /**Writes text over the top of that already on a card image
    */
  function update_card_text(card_image, card_type, orientation = "vertical") {
    card_text = CARD_TEXTS[card_type]
    rendered_text = wrap_text(card_text, card_image.get_width()
      , card_image.get_height() - CARD_BODY_START * card_image.get_height()
      , card_font, CARD_TEXT_COLOUR, CARD_BACKGROUND_COLOUR)
    card_image.putImageData(rendered_text
      , [(card_image.get_width() - rendered_text.get_width())//2
        , CARD_BODY_START * card_image.get_height()])
    return card_image
  }

  /**Rescales images in response to updated dimensions for the play grid
  */
  function rescale_graphics() {
    console.log("Updating the dimensions that will be used for drawing the play area")
    //        dimensions = dimensions        
    //Tiles, tokens and text will need adjusting to the new dimensions
    //Tiles will be scaled to fit the smaller dimension
    max_tile_height = height // dimensions[1]
    max_tile_width = play_area_width // dimensions[0]
    if (max_tile_height < max_tile_width) {
      tile_size = max_tile_height
    } else {
      tile_size = max_tile_width
    }
    token_size = Math.round(TOKEN_SCALE * tile_size) //token size will be proportional to the tiles
    outline_width = math.ceil(TOKEN_OUTLINE_SCALE * token_size)
    route_thickness = ROUTE_THICKNESS
    chest_highlight_thickness = int(route_thickness)
    token_font = pygame.font.SysFont(None, int(tile_size * TOKEN_FONT_SCALE)) //the font size for tokens will be proportionate to the window size
    //scale down the images as the dimensions of the grid are changed, rather than when placing
    //the tiles' scale will be slightly smaller than the space in the grid, to givea discernible margin
    bordered_tile_size = Math.round(tile_size * (1 - TILE_BORDER))
    console.log("Updated tile size to be " + str(tile_size) + " pixels, and with border: " + str(bordered_tile_size))
    rescale_images(tile_image_library, bordered_tile_size)
    rescale_images(highlight_library, tile_size)
    //        rescale_images(menu_tile_library, menu_tile_size)
  }

    /**Checks the extremes of the play_area and rescales visual elements as needed
  */
  //        console.log("Checking whether the current play area needs a bigger visuals grid")
function rescale_as_needed(){
min_longitude, max_longitude = 0, 0
min_latitude, max_latitude = 0, 0
  for (longitude in game.play_area) {
    if (longitude < min_longitude) {
      min_longitude = longitude
    } else if (longitude > max_longitude) {
      max_longitude = longitude
      for (latitude in game.play_area[longitude]) {
        if (latitude < min_latitude) {
          min_latitude = latitude
        }
      }
    } else if (latitude > max_latitude) {
      max_latitude = latitude
    }
    dimensions[0] = max_longitude - min_longitude + 1 + 2 * DIMENSION_BUFFER
    dimensions[1] = max_latitude - min_latitude + 1 + 2 * DIMENSION_BUFFER
    //Check whether the current dimensions are too great for the display size
    if (dimensions[0] * tile_size > play_area_width || dimensions[1] * tile_size > height) {
      //            console.log("Reducing the size of tile graphics to fit within the new dimensions")
      rescale_graphics()
    }
    //Check whether one of the dimensions has slack space and displace the origin to centre the play
    //Set the origin so that the play will be as central as possible
    origin[0] = -min_longitude + DIMENSION_BUFFER
    width_needed = dimensions[0] * tile_size
    if (width_needed + 2 * tile_size < play_area_width) {
      //            console.log("Extending grid width because the screen width is more generous than needed")
      extra_cols = math.floor((play_area_width - width_needed) / tile_size) //the excess in tiles
      dimensions[0] += extra_cols
      origin[0] += Math.floor(extra_cols / 2)
      origin[1] = -min_latitude + DIMENSION_BUFFER
      height_needed = dimensions[1] * tile_size
    }
    if (height_needed + 2 * tile_size < height) {
      //            console.log("Extending grid height because the screen height is more generous than needed")
      extra_rows = math.floor((height - height_needed) / tile_size) //the excess in tiles
      dimensions[1] += extra_rows
      origin[1] += Math.floor(extra_rows / 2)
    }
    //        console.log("Dimensions are now: " + str(dimensions[0]) + ", " + str(dimensions[1]))
    //        console.log("Origin is now: " + str(origin[0]) + ", " + str(origin[1]))
    return True
  }


  /**Deals with resizing of the window
  */
  function window_resize(resize_event) {
    new_width, new_height = resize_event.w, resize_event.h
    reload_needed = False //keep track of whether graphics are being scaled up, which would need the original PNGs to be reloaded
    if (new_width > width || new_height > height) {
      reload_needed = True
      width, height = new_width, new_height
    }
    pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE, depth = 32)
    if (reload_needed) {
      init_graphics() //reload the PNG images
    } else {
      rescale_graphics()
    }
    //Now update text sizes too
    scores_font = pygame.font.SysFont(None, Math.round(height * SCORES_FONT_SCALE)) //the font size for scores will be proportionate to the window size
    prompt_font = pygame.font.SysFont(None, Math.round(height * PROMPT_FONT_SCALE)) //the font size for prompt will be proportionate to the window size
    prompt_position = [play_area_start + PROMPT_POSITION[0] * width
      , PROMPT_POSITION[1] * height]
    pygame.font.init()
    draw_play_area()
    draw_move_options()
    draw_routes()
    draw_tokens()
    draw_scores()
    draw_prompt()
    pygame.display.flip()
  }

  /**Translates a play area horiztonal position into visual grid position
  */
  function get_horizontal(longitude) {
    return origin[0] + longitude
  }

  /**Translates a play area vertical position into visual grid position
  */
  function get_vertical(latitude) {
    return dimensions[1] - origin[1] - latitude - 1
  }

  /**Works out how the image file will be prepended, corresponding to a Cartolan tile
  */
  function establish_tile_type(tile) {
    e = tile.tile_edges
    if (isinstance(tile, CityTile)) {
      if (tile.is_capital) {
        return "capital"
      } else {
        return "mythical"
      }
    } else {
      uc = str(e.upwind_clock_water)[0].lower()
      ua = str(e.upwind_anti_water)[0].lower()
      dc = str(e.downwind_clock_water)[0].lower()
      da = str(e.downwind_anti_water)[0].lower()
      wonder = str(tile.is_wonder)[0].lower()
      return uc + ua + dc + da + wonder
    }
  }


  /**Assigns a suitable tile image for a particular tile and cache it ready for use
   *
   * Assumes that all images will have been loaded before this point, so that the same images are assigned to tiles for all clients
  */
  function assign_tile_image(tile) {
    tile_type = establish_tile_type(tile)
    available_tiles = tile_images.tile_type
    tile_name = available_tiles.pop()
    //Register the image against the tile in question, and cache it if not already
    let tile_image;
    if (!tile_name in cached_tile_images) {
      tile_image = new Image;
      tile_image.onload = function () {
        bordered_tile_size = Math.round(tile_size * (1 - TILE_BORDER))
        //Cache this image for every time it's shown in the Chest or the Play Area is rescaled
        tile_image_library[tile] = cache_offscreen(background, tile_image, bordered_tile_size, bordered_tile_size);
        cached_tile_images.tile_name.play_image = tile_image_library[tile]
        menu_tile_library[tile] = cache_offscreen(background, tile_image, menu_tile_size, menu_tile_size);
        cached_tile_images.tile_name.menu_image = menu_tile_library[tile]
        offer_tile_library[tile] = cache_offscreen(background, tile_image, offer_tile_size, offer_tile_size);
        cached_tile_images.tile_name.offer_image = offer_tile_library[tile]
      }
      tile_image.src = TILE_PATH + tile_name;
    } else {
      //If the image has already been cached then reference this same offscreen canvas
      tile_image_library[tile] = cached_tile_images.tile_name.play_image
      menu_tile_library[tile] = cached_tile_images.tile_name.menu_image
      offer_tile_library[tile] = cached_tile_images.tile_name.offer_image
    }
    available_tiles.insert(0, tile_name) //Prepend this image back into the list so that it won't get used again unless other images run out
  }

  /**Renders the tiles that have been laid in a particular game of Cartolan - Trade Winds
  */
function draw_play_area(){
play_area_update = game.play_area
//        console.log("Drawing the play area, with " + str(len(play_area_update)) + " columns of tiles")
        //Check whether the visuals need to be rescaled
rescale_as_needed()
        //Clear what's already been drawn
  background.fillStyle = BACKGROUND_COLOUR;  // fill completely with a default background colour
  background.fill();
//        background.drawImage(backing_image, [0, 0])
        //For each location in the play area draw the tile
for longitude in play_area_update{
    for latitude in play_area_update[longitude]{
                //bring in the relevant image from the library
tile = play_area_update[longitude][latitude]
tile_image = tile_image_library.get(tile)
if tile_image is None{
assign_tile_image(tile)
tile_image = tile_image_library.get(tile)
rotated_image = rotate_tile_image(tile, tile_image)
                //place the tile image in the grid
horizontal = play_area_start + get_horizontal(longitude) * tile_size
vertical = get_vertical(latitude) * tile_size
//                console.log("Placing a tile at pixel coordinates " + str(horizontal * tile_size) + ", " + str(vertical * tile_size))
background.drawImage(rotated_image, [horizontal, vertical])
                //Print a number on this tile showing the dropped wealth there
if tile.dropped_wealth > 0{
    if tile.is_wonder{
        text_colour = WONDER_TEXT_COLOUR
    else{
    text_colour = PLAIN_TEXT_COLOUR
horizontal += int(tile_size * (1 - TOKEN_FONT_SCALE / 2) / 2)
vertical += int(tile_size * (1 - TOKEN_FONT_SCALE / 2) / 2)
wealth_label = token_font.render(str(tile.dropped_wealth), 1, text_colour)
move_fground.putImageData(wealth_label, [horizontal, vertical])
        // // Keep track of what the latest play_area to have been visualised was
        // play_area = play_area_union(play_area, play_area_update)
return True
    
    //@TODO highlight the particular token(s) that an action relates to
    //display the number of moves since resting
function draw_move_options(highlight_coords = {}){
/**Outlines tiles where moves or actions are possible, designated by colour

Arguments{
moves_since_rest expects an integer
highlight_coords expects a library of strings mapped to lists of integer 2 - tuples
*/
//        console.log("Updating the dict of highlight positions, based on optional arguments")
//        highlight_count = 0
highlight_rects = {} //Reset the record of where highlights have been drawn for click detection
        for highlight_type in highlights{
        coords = highlight_coords.get(highlight_type)
if coords{
    highlights[highlight_type] = coords
//                console.log(highlight_type + " highlight provided coords at " + str(coords))
//                highlight_count += len(coords)
            else{
//                console.log("No coords provided for highight type: " + highlight_type)
highlights[highlight_type] = []
//        console.log("Cycling through the various highlights' grid coordinates, outlining the " + str(highlight_count) + " tiles that can and can't be subject to moves")
for highlight_type in highlight_library{
    if highlights[highlight_type]{
        highlight_rects[highlight_type] = []
highlight_image = highlight_library[highlight_type]
for tile_coords in highlights[highlight_type]{
                    //place the highlight image on the grid
//                    console.log(highlight_type + " has coords " + str(tile_coords))
horizontal = play_area_start + get_horizontal(tile_coords[0]) * tile_size
vertical = get_vertical(tile_coords[1]) * tile_size
//                    console.log("Drawing a highlight at pixel coordinates " + str(horizontal * tile_size) + ", " + str(vertical * tile_size))
move_fground.putImageData(highlight_image, [horizontal, vertical])
                    //remember where this highlight was drawn, to detect input later
highlight_rects[highlight_type].push((horizontal, vertical, highlight_image.get_width(), highlight_image.get_height()))

function draw_move_count(){
/**report the number of moves that have been used so far{
*/
        // horizontal = MOVE_COUNT_POSITION[0] * width
horizontal = right_menu_start
//            vertical = MOVE_COUNT_POSITION[1] * height + len(game.tile_piles) * SCORES_FONT_SCALE * height
vertical = 0
        //Only show moves available in meters if the current player is viewed
if current_adventurer == viewed_adventurer{
            //Work out how many moves remain of each type, and get ready to overlay the move type icon with a greyed - out meter and numbers
report = "Moves until rest:"
move_title = scores_font.render(report, 1, viewed_player_colour)
moves_since_rest = current_adventurer.downwind_moves + current_adventurer.upwind_moves + current_adventurer.land_moves
            // any_direction_moves = current_adventurer.upwind_moves + current_adventurer.land_moves
max_any_direction_moves = current_adventurer.max_upwind_moves
only_downwind_moves = current_adventurer.max_downwind_moves - max_any_direction_moves
extra_downwind_moves = max(moves_since_rest - max_any_direction_moves, 0)
any_direction_share = min(moves_since_rest / max_any_direction_moves, 1)
any_direction_meter = pygame.Surface((int(round(any_direction_share * menu_tile_size)), menu_tile_size))
count = str(max(max_any_direction_moves - moves_since_rest, 0)) + " / " + str(max_any_direction_moves)
any_direction_text = scores_font.render(count, 1, PLAIN_TEXT_COLOUR)
try{
downwind_water_share = extra_downwind_moves / only_downwind_moves
except{
downwind_water_share = 1.0
downwind_water_meter = pygame.Surface((int(round(downwind_water_share * menu_tile_size)), menu_tile_size))
count = str(only_downwind_moves - extra_downwind_moves) + " / " + str(only_downwind_moves)
downwind_water_text = scores_font.render(count, 1, PLAIN_TEXT_COLOUR)
        else{
report = "Not #" + str(viewed_adventurer_number + 1) + "'s turn"
move_title = scores_font.render(report, 1, viewed_player_colour)
any_direction_meter = pygame.Surface((menu_tile_size, menu_tile_size))
any_direction_text = scores_font.render("", 1, PLAIN_TEXT_COLOUR)
downwind_water_meter = pygame.Surface((menu_tile_size, menu_tile_size))
downwind_water_text = scores_font.render("", 1, PLAIN_TEXT_COLOUR)
move_fground.fillStyle = DOWNWIND_WATER_METER_COLOUR;  // fill completely with a default background colour
move_fground.globalAlpha = METER_OPACITY;
move_fground.fillRect(left, top, width, height);
any_direction_meter.set_alpha(METER_OPACITY)
any_direction_meter.fill(ANY_DIRECTION_METER_COLOUR)
downwind_water_meter.set_alpha(METER_OPACITY)
downwind_water_meter.fill(DOWNWIND_WATER_METER_COLOUR)
if move_title.get_width() > right_text_start{
    right_text_start = move_title.get_width() //permanently adjust the text margin on this setup if it doesn't fit
turn_fground.putImageData(move_title, [horizontal, vertical])
move_count_rect = (horizontal, vertical, move_title.get_width(), move_title.get_height() + menu_tile_size)
        //Render the icons for each move type, greyed out to the extent that they are still available
vertical += move_title.get_height()
background.drawImage(meters_library["any_direction"], (horizontal, vertical))
move_fground.putImageData(any_direction_meter, (horizontal, vertical))
move_fground.putImageData(any_direction_text, (horizontal, vertical))
horizontal += menu_tile_size
background.drawImage(meters_library["downwind_water"], (horizontal, vertical))
move_fground.putImageData(downwind_water_meter, (horizontal, vertical))
move_fground.putImageData(downwind_water_text, (horizontal, vertical))

function draw_discard_pile(){
/**Draw small versions of the tiles that have been discarded so far
*/
        //If the player has changed then empty the discard list
if not discarding_adventurer == current_adventurer{
discard_pile = []
horizontal = right_menu_start
vertical = piles_rect[1] + piles_rect[3]
discard_title = scores_font.render("Failed map draws:", 1, PLAIN_TEXT_COLOUR)
background.putImageData(discard_title, [horizontal, vertical])
horizontal = right_menu_start
vertical += SCORES_FONT_SCALE * height
tile_count = 0
for pile in list(game.discard_piles.values()){
    new_discards = [tile for tile in pile.tiles if not tile in discard_pile]
discard_pile += new_discards
for tile in reversed(discard_pile){
    tile_image = menu_tile_library.get(tile)
if tile_image is None{
assign_tile_image(tile)
tile_image = menu_tile_library.get(tile)
rotated_image = rotate_tile_image(tile, tile_image)
//                console.log("Placing a tile at pixel coordinates " + str(horizontal * tile_size) + ", " + str(vertical * tile_size))
background.drawImage(rotated_image, [horizontal, vertical])
            //Draw a frame to keep distinct from play area
pygame.draw.rect(window, PLAIN_TEXT_COLOUR
    , (horizontal, vertical, menu_tile_size, menu_tile_size)
    , chest_highlight_thickness)
tile_count += 1
if tile_count % MENU_TILE_COLS == 0{
    vertical += menu_tile_size
horizontal = right_menu_start
            else{
horizontal += menu_tile_size

function check_highlighted(input_longitude, input_latitude){
/**Given play area grid coordinates, checks whether this is highlighted as a valid move/action
*/
//        console.log("Checking whether there is a valid move option at: " + str(input_longitude) + ", " + str(input_latitude))
is_option_available = False
for highlight_type in highlight_library{
//            console.log("There are " + str(len(highlights[highlight_type])) + " options of type " + highlight_type)
if highlights[highlight_type]{
    is_option_available = True
for tile_coords in highlights[highlight_type]{
                    //compare the input coordinates to the highlighted tile's coordinates
longitude = tile_coords[0]
latitude = tile_coords[1]
if longitude == input_longitude and latitude == input_latitude{
return highlight_type
if is_option_available{
    return None
else{
return "confirmed"

function clear_move_options(){
/**
*/
//        console.log("Clearing out the list of valid moves")
for highlight_type in highlight_library{
    highlights[highlight_type] = []

function draw_tokens(){
/**Illustrates the current location of Adventurers and Agents in a game, along with their paths over the last turn
*/
//        console.log("Cycling through the players, drawing the adventurers and agents as markers")
game = game
players = game.players
        //Reset the records of where Agents and Adventurers have been
adventurer_centres = []
agent_rects = []
for player in players{
            //We'll want to differentiate players by colour and the offset from the tile location
colour = pygame.Color(player_colours[player])
player_offset = PLAYER_OFFSETS[players.index(player)]
token_label_colour = PLAIN_TEXT_COLOUR
if TOKEN_FONT_COLOURS.get(player_colours[player]) is not None{
token_label_colour = TOKEN_FONT_COLOURS[player_colours[player]]
            //Each player may have multiple Adventurers to draw
adventurers = game.adventurers[player]
for adventurer in adventurers{
                // we want to draw a circle anywhere an Adventurer is, differentiating with offsets
                tile = adventurer.current_tile
adventurer_offset = ADVENTURER_OFFSETS[adventurers.index(adventurer)]
location = [int(play_area_start + tile_size * (get_horizontal(tile.tile_position.longitude) + player_offset[0] + adventurer_offset[0]))
    , int(tile_size * (get_vertical(tile.tile_position.latitude) + player_offset[1] + adventurer_offset[1]))]
                // we want it to be coloured differently for each player
//                console.log("Drawing the filled circle at " + str(location[0]) + ", " + str(location[1]) + " with radius " + str(token_size))
pygame.draw.circle(window, colour, location, token_size)
if isinstance(adventurer, AdventurerRegular){
    if adventurer.pirate_token{
                        // we'll outline pirates in black
//                        console.log("Drawing an outline")
pygame.draw.circle(window, (0, 0, 0), location, token_size, outline_width)
//                if adventurer in (viewed_adventurer, current_adventurer){
    if adventurer == viewed_adventurer{
        pygame.draw.circle(window, PLAIN_TEXT_COLOUR, location, token_size + outline_width, outline_width)
    else{
    adventurer_centres.push([(location[0], location[1]), adventurer]) //We'll retain the centre, to contstruct a hit-box for selecting this Adventurer instead
                //For the text label we'll change the indent
token_label = token_font.render(str(adventurers.index(adventurer) + 1), 1, token_label_colour)
location[0] -= Math.floor(token_size / 2)
location[1] -= token_size
move_fground.putImageData(token_label, location)
            // we want to draw a square anywhere that an agent is
for agent in game.agents[player]{
    tile = agent.current_tile
if not tile{
    continue
agent_offset = AGENT_OFFSET
location = [int(play_area_start + tile_size * (get_horizontal(tile.tile_position.longitude) + agent_offset[0]))
    , int(tile_size * (get_vertical(tile.tile_position.latitude) + agent_offset[1]))]
                //Agents will be differentiated by colour, but they will always have the same position because there will only be one per tile
agent_shape = pygame.Rect(location[0], location[1]
    , AGENT_SCALE * token_size, AGENT_SCALE * token_size)
if agent.player != viewed_adventurer.player{
    agent_rects.push([(location[0], location[1]
        , AGENT_SCALE * token_size, AGENT_SCALE * token_size)
        , agent.player])
                // we'll only outline the Agents that are dispossessed
if isinstance(agent, AgentRegular) and agent.is_dispossessed{
pygame.draw.rect(window, colour, agent_shape, outline_width)
                else{
                    //for a filled rectangle the fill method could be quicker{ https{//www.pygame.org/docs/ref/draw.html//pygame.draw.rect
move_fground.fill(colour, rect = agent_shape)
token_label = token_font.render(str(agent.wealth), 1, token_label_colour)
location[0] += token_size // 2
move_fground.putImageData(token_label, location)
return True
    
    // it will be useful to see how players moved around the play area during the game, and relative to agents

  /**Illustrates the paths that different Adventurers have taken during the course of a game, and the location of Agents
      
  Arguments{
  List of Carolan.Players the Adventurers and Agents that will be rendered
  */
  function draw_routes() {
players = game.players
drawn_routes = [] //Clear out old routes
for player in players{
            //only draw routes for the current and viewed adventurers' players
if not(draw_all_routes 
                    or player in [current_adventurer.player
    , viewed_adventurer.player]){
    continue
player_offset = PLAYER_OFFSETS[players.index(player)]
adventurers = game.adventurers[player]
colour = player_colours[player]
for adventurer in adventurers{
    adventurer_offset = ADVENTURER_OFFSETS[adventurers.index(adventurer)]
adventurer_offset = [adventurer_offset[i] + player_offset[i] for i in [0, 1]]
                //Draw the route for this expedition, between City visits
if adventurer.route{
    previous_step = [int(play_area_start + tile_size * (get_horizontal(adventurer.route[0].tile_position.longitude) + adventurer_offset[0]))
        , int(tile_size * (get_vertical(adventurer.route[0].tile_position.latitude) + adventurer_offset[1]))]
move = 0
  drawn_route = []
  // @TODO do all these draw operations in one go, before context.stroke() ...https://www.html5rocks.com/en/tutorials/canvas/performance/#toc-batch
for tile in adventurer.route{
    step = [int(play_area_start + tile_size * (get_horizontal(tile.tile_position.longitude) + adventurer_offset[0]))
        , int(tile_size * (get_vertical(tile.tile_position.latitude) + adventurer_offset[1]))]
segment = draw_dash_line(window, colour
    , [previous_step[0], previous_step[1]]
    , [step[0], step[1]]
    , math.ceil(route_thickness
        * float(move) / float(len(adventurer.route))
    )
)
                        // console.log(segment)
previous_step = step
drawn_route.push(segment)
move += 1
                    //retain this for detecting clicks, providing it doesn't end with abandoning
route_to_follow = adventurer.route[{]
if (drawn_route[-1][2] > tile_size and drawn_route[-1][3] > tile_size){
route_to_follow.pop()
if len(drawn_route) > 1{
//                        console.log("Recording route of " + player_colours[adventurer.player] + " player, for fast travel.")
//                        console.log("Route length: " + str(len(drawn_route)))
drawn_routes.push([drawn_route, route_to_follow])
                //Draw the route for the latest turn
  //@TODO animate the drawing of this, with the Adventurer token moving, by caching the frames in advance ...https://www.html5rocks.com/en/tutorials/canvas/performance/#toc-pre-render
                if adventurer.turn_route{
        previous_step = [int(play_area_start + tile_size * (get_horizontal(adventurer.turn_route[0].tile_position.longitude) + adventurer_offset[0]))
            , int(tile_size * (get_vertical(adventurer.turn_route[0].tile_position.latitude) + adventurer_offset[1]))]
move = 0
for tile in adventurer.turn_route{
                        // you'll need to get the centre-point for each tile_image
step = [int(play_area_start + tile_size * (get_horizontal(tile.tile_position.longitude) + adventurer_offset[0]))
    , int(tile_size * (get_vertical(tile.tile_position.latitude) + adventurer_offset[1]))]
segment = pygame.draw.line(window, colour
    , [previous_step[0], previous_step[1]]
    , [step[0], step[1]]
    , math.ceil(route_thickness
        * float(len(adventurer.route) - len(adventurer.turn_route) + move) / float(len(adventurer.route))
    )
)
previous_step = step
move += 1
            
//            if isinstance(player, PlayerRegularExplorer){
//                for attack in player.attack_history{ 
//                    // we want to draw a cross anywhere that an attack happened, the attack_history is full of pairs with a tile and a bool for the attack's success
//                    if attack[1]{
//                        face_colour = player_colours[player]
//                    else{
//                        face_colour = "none"
//                    tile = attack[0]
//                    location = [origin[0] + tile.tile_position.longitude + player_offset[0]
//, origin[1] + tile.tile_position.latitude + player_offset[1]]
//                    routeax.scatter([location[0]], [location[1]]
//, linewidth = 1, edgecolors = player_colours[player], facecolor = face_colour, marker = "X", s = token_width)

function draw_scores(){
/**Prints a table of current wealth scores in players' Vaults and Adventurers' Chests
*/        
//        console.log("Creating a table of the wealth held by Players and their Adventurers")
        //Draw the column headings
game = game
horizontal = SCORES_POSITION[0] * width
vertical = SCORES_POSITION[1] * height
score_title = scores_font.render("Turn " + str(game.turn) + ", treasure in...", 1, PLAIN_TEXT_COLOUR)
turn_fground.putImageData(score_title, [horizontal, vertical])
vertical += score_title.get_height()
scores_texts = [[], [], []] //Start with three columns{ name, vault treasure, 1st adventurer's chest treasure
scores_widths = []
        //Leave the top cell of the names column blank
scores_texts[0].push([scores_font.render("", 1, PLAIN_TEXT_COLOUR), None]) //2 - array kept to allow click - detection
scores_widths.push(0)
        //Label the Vault column
score_text = scores_font.render("  Vault", 1, PLAIN_TEXT_COLOUR)
scores_texts[1].push([score_text, None]) //2 - array kept to allow click - detection
scores_widths.push(score_text.get_width())
        //Label the first Adventurer Chest column, as there will always be one
score_text = scores_font.render("  Chest #1", 1, PLAIN_TEXT_COLOUR)
scores_texts[2].push([score_text, None]) //2 - array kept to allow click - detection
scores_widths.push(score_text.get_width())
        //Work out the maximum number of Adventurers in play, to only draw this many columns
max_num_adventurers = 1
for player in game.players{
    if len(game.adventurers[player]) > max_num_adventurers{
        max_num_adventurers = len(game.adventurers[player])
if max_num_adventurers > 1{
    for adventurer_num in range(2, max_num_adventurers + 1){
        score_title = scores_font.render("  #" + str(adventurer_num) + "  ", 1, PLAIN_TEXT_COLOUR)
scores_texts.push([[score_title, None]]) //2 - array kept to allow click - detection
scores_widths.push(score_title.get_width())
        //There will now be a row for each player
        for player in game.players{
        colour = pygame.Color(player_colours[player])
            //First we have the Player's name
score_text = scores_font.render(player.name, 1, colour)
scores_texts[0].push([score_text, player])
            //Update the column width if needed
            if score_text.get_width() > scores_widths[0]{
        scores_widths[0] = score_text.get_width()
            //Now the Player's Vault treasure (score)  
if player == game.winning_player{
    text = " " + str(game.player_wealths[player]) + " (+" + str(game.wealth_difference) + ")"
            //Highlight the second placed player too, because lower ranked players can behave differently
elif(game.winning_player is not None 
                  and game.player_wealths[game.winning_player] - game.player_wealths[player] == game.wealth_difference){
text = " " + str(game.player_wealths[player]) + " (2nd)"
            // elif game.winning_player is not None{
            //     text = str(game.player_wealths[player]) + " (-" + str(game.player_wealths[game.winning_player] - game.player_wealths[player]) + ")"
            else{
text = " " + str(game.player_wealths[player])
score_text = scores_font.render("  " + text, 1, colour)
scores_texts[1].push([score_text, player])
            //Update the column width if needed
            if score_text.get_width() > scores_widths[1]{
        scores_widths[1] = score_text.get_width()
            //Now the Player's first Adventurer's Chest
adventurer = game.adventurers[player][0]
score_text = scores_font.render("  " + str(adventurer.wealth), 1, colour)
scores_texts[2].push([score_text, adventurer])
            //Update the column width if needed
            if score_text.get_width() > scores_widths[2]{
        scores_widths[2] = score_text.get_width()
            //Now any further Adventurers
for adventurer_num in range(2, max_num_adventurers + 1){
    if len(game.adventurers[player]) >= adventurer_num{
        adventurer = game.adventurers[player][adventurer_num - 1]
score_text = scores_font.render("  " + str(adventurer.wealth), 1, colour)
                else{
adventurer = None
score_text = scores_font.render("", 1, colour)
scores_texts[adventurer_num + 1].push([score_text, adventurer])
                //Update the column width if needed
                if score_text.get_width() > scores_widths[adventurer_num + 1]{
        scores_widths[adventurer_num + 1] = score_text.get_width()
                
        //Add all of the table cells to the canvas
left_edge = right_edge = horizontal = SCORES_POSITION[0] * width //reset the scores position before going through other rows below
        //Start recording the surrounding rect for click detection, but will need to count max adventurers below to finalise this
scores_rect = [horizontal, vertical, 0, 0]
score_rects = []
for column in scores_texts{
            //Calculate the right edge of this column
right_edge += scores_widths[scores_texts.index(column)]
            //Reset the vertical position
vertical = SCORES_POSITION[1] * height //reset the scores position before going through other rows below
for score_text, score_owner in column{
    vertical += SCORES_FONT_SCALE * height //increment the vertical position to a new row
                //Draw this in the window
if scores_texts.index(column) > 1{
    horizontal = right_edge - score_text.get_width() //Right - align Chest treasure
                else{
horizontal = left_edge
move_fground.putImageData(score_text, [horizontal, vertical])
                //Remember where for click detection
                score_rects.push([(horizontal, vertical, score_text.get_width(), score_text.get_height()), score_owner])
                //If this is the moving Adventurer, then highlight their score
if score_owner == current_adventurer{
    pygame.draw.rect(window, PLAIN_TEXT_COLOUR
        , (horizontal
            , vertical + score_text.get_height()
            , score_text.get_width()
            , 0)
        , chest_highlight_thickness)
                //If this is the Adventurer whose cards are being viewed then mark with a dot underneath
if score_owner == viewed_adventurer{
    pygame.draw.circle(window, PLAIN_TEXT_COLOUR
        , (horizontal + score_text.get_width()//2
            , vertical + score_text.get_height())
        , chest_highlight_thickness)
            //Update the left edge for the next column
            left_edge += scores_widths[scores_texts.index(column)]
        //Remember the outer dimensions of the whole table
scores_rect[2] = right_edge
scores_rect[3] = vertical + SCORES_FONT_SCALE * height
                
        //State the current player and Adventurer
vertical += SCORES_FONT_SCALE * height
horizontal = SCORES_POSITION[0] * width
active_prompt = scores_font.render(current_adventurer.player.name + "'s Adventurer #" + str(current_adventurer_number + 1) + "'s turn", 1, pygame.Color(current_player_colour))
turn_fground.putImageData(active_prompt, [horizontal, vertical])
        //Finish recording the surrounding rect for click detection, but will need to count max adventurers below to finalise this
scores_rect = (scores_rect[0]
    , scores_rect[1]
    , SCORES_FONT_SCALE * SCORES_SPACING * width * (max_num_adventurers + 1)
    , vertical + SCORES_FONT_SCALE * height - scores_rect[1])

function draw_tile_piles(){
/**Draw the numbers of tiles in each pile
*/
horizontal = right_menu_start
vertical = chest_rect[1] + chest_rect[3]
        //Start recording the surrounding rect for click detection, but will need to count max adventurers below to finalise this
piles_rect = (horizontal, vertical, 0, 0)
piles_title = scores_font.render("Maps to draw:", 1, PLAIN_TEXT_COLOUR)
background.putImageData(piles_title, (horizontal, vertical))
vertical += piles_title.get_height()
for tile_back in game.tile_piles{
    tiles = game.tile_piles[tile_back].tiles
tile_count = len(tiles)
pile_size = game.NUM_TILES[tile_back]
pile_share = 1 - tile_count / pile_size
tile_meter = pygame.Surface((menu_tile_size, Math.round(pile_share * menu_tile_size)))
tile_meter.set_alpha(METER_OPACITY)
count = str(tile_count) + " / " + str(pile_size)
pile_text = scores_font.render(count, 1, PLAIN_TEXT_COLOUR)
tile_count_position = [horizontal, vertical]
tile_back_image = pygame.transform.scale(tile_images[tile_back][0].copy(), [menu_tile_size, menu_tile_size])
background.drawImage(tile_back_image, tile_count_position)
move_fground.putImageData(tile_meter, tile_count_position)
move_fground.putImageData(pile_text, tile_count_position)
horizontal += tile_meter.get_width()
        //Finish recording the surrounding rect for click detection, but will need to count max adventurers below to finalise this
piles_rect = (piles_rect[0]
    , piles_rect[1]
    , 2 * menu_tile_size
    , piles_title.get_height() + menu_tile_size)

function draw_toggle_menu(fixed_responses = {}){
/**Visualises a set of highlights for action prompts that can have a fixed True/False response set for them 
*/
        //Draw a box to surround the toggle menu, and remember its coordinates for player input
        horizontal = right_menu_start
        vertical = move_count_rect[1] + move_count_rect[3]
menu_height = SCORES_FONT_SCALE * height + menu_highlight_size + menu_spacing
if draw_all_routes{
            //If all players' routes are to be drawn then there will need to be space for a horizontal line each in the toggle menu
menu_height += len(player_colours) * menu_route_thickness
        else{
menu_height += menu_route_thickness
if not current_adventurer.player == viewed_adventurer.player{
menu_height += menu_route_thickness //two routes will be drawn if the viewed Adventurer is for another player
        toggles_rect = (horizontal, vertical, play_area_start, menu_height)
        if not current_adventurer.player == viewed_adventurer.player{
return //This menu isn't relevant if the adventurer doesn't belong to the player viewing
action_rects = [] //Reset the record of where the toggle menu buttons have been drawn
        //Establish the top left coordinate below the table of treasure scores
//        horizontal = MOVE_COUNT_POSITION[0] * width
//        vertical = SCORES_FONT_SCALE * height * (len(game.tile_piles) + 1)
toggle_title = scores_font.render("Auto-Actions{", 1, PLAIN_TEXT_COLOUR)
background.putImageData(toggle_title, (horizontal, vertical))

//        console.log("Chest map menu corners functionined at pixels...")
//        console.log(chest_rect)
//        pygame.draw.rect(window, PLAIN_TEXT_COLOUR
//, chest_rect
//, chest_highlight_thickness)
        //Cycle through the auto - actions, drawing their highlight over the toggle button that will decide their auto - response
horizontal = right_menu_start
vertical += SCORES_FONT_SCALE * height
for highlight_type in fixed_responses{
            //If there is a fixed response set for this action type, then give it a colour to indicate True / False
if fixed_responses[highlight_type]{
    pygame.draw.rect(window, TOGGLE_TRUE_COLOUR
        , (horizontal, vertical, menu_highlight_size, menu_highlight_size))
elif fixed_responses[highlight_type] is not None{
pygame.draw.rect(window, TOGGLE_FALSE_COLOUR
    , (horizontal, vertical, menu_highlight_size, menu_highlight_size))
            else{
pygame.draw.rect(window, BACKGROUND_COLOUR
    , (horizontal, vertical, menu_highlight_size, menu_highlight_size))
            //Now draw the highlight over the top
highlight_image = toggle_library[highlight_type]
move_fground.putImageData(highlight_image, [horizontal, vertical])
            //Remember the position of this highlight's toggle
action_rects.push([(horizontal, vertical, menu_highlight_size, menu_highlight_size), highlight_type])
horizontal += menu_highlight_size //increment the horizontal placement before the next toggle is drawn

function draw_routes_menu(){
/**'Add a toggle below the auto - actions menu for whether to draw all routes, or just the current and viewed players'
*/
horizontal = right_menu_start
vertical = move_count_rect[1] + move_count_rect[3]
vertical += SCORES_FONT_SCALE * height
vertical += menu_highlight_size + menu_spacing //increment down below the highlighht menu with a space
for player in player_colours{
    if (draw_all_routes 
                or current_adventurer.player == player
or viewed_adventurer.player == player){
colour = player_colours[player]
pygame.draw.line(window, colour
    , [horizontal, vertical]
    , [width, vertical]
    , math.ceil(menu_route_thickness)
)
vertical += menu_route_thickness


function draw_undo_button(){
/**Adds an undo button and a click hit-box that will allow the game to be reset to a preceding state, providing all players agree.
*/
        //Check whether the other clients to the game have proposed / agreed to an undo
undo_asked = False
for peer in peer_visuals{
    if not peer == self and peer.undo_agreed{
undo_asked = True
break
if undo_agreed{
    undo_button = scores_font.render("Reject undo", 1, ACCEPT_UNDO_COLOUR)
elif undo_asked{
undo_button = scores_font.render("Accept undo?", 1, ACCEPT_UNDO_COLOUR)
        else{
undo_button = scores_font.render("Undo turn?", 1, PLAIN_TEXT_COLOUR)
horizontal = width - undo_button.get_width()
vertical = height - undo_button.get_height()
background.putImageData(undo_button, (horizontal, vertical))
undo_rect = (horizontal, vertical, undo_button.get_width(), undo_button.get_height())

function draw_chest_tiles(){
/**Visualises a set of tiles in the Adventurer's Chest, and highlights one if it is selected for use
        */
        //Get the information from the viewed adventurer
if viewed_adventurer is None{
return
chest_tiles = viewed_adventurer.chest_tiles
preferred_tile_num = viewed_adventurer.preferred_tile_num
max_chest_tiles = viewed_adventurer.num_chest_tiles
        //Establish the top left coordinate of the column of tiles to choose from, below the table of treasure scores
//        vertical = SCORES_FONT_SCALE * height * (len(game.players) + 1)
        // horizontal = right_text_start
horizontal = right_menu_start
//        vertical = (len(game.players) + 1) * SCORES_FONT_SCALE * height
vertical = toggles_rect[1] + toggles_rect[3]
title_text = "#" + str(viewed_adventurer_number + 1) + "'s chest maps:"
chest_title = scores_font.render(title_text, 1, viewed_player_colour)
turn_fground.putImageData(chest_title, (horizontal, vertical))
        //Draw a box to surround the Chest menu, and remember its coordinates for player input
        horizontal = right_menu_start
        vertical += SCORES_FONT_SCALE * height
menu_size = menu_tile_size * math.ceil(max_chest_tiles / MENU_TILE_COLS)
chest_rect = (horizontal, vertical, play_area_start, menu_size)
//        console.log("Chest map menu corners functionined at pixels...")
//        console.log(chest_rect)
pygame.draw.rect(window, PLAIN_TEXT_COLOUR
    , chest_rect
    , chest_highlight_thickness)
        //Cycle through the chest tiles, drawing them
for tile in chest_tiles{
    tile_image = menu_tile_library.get(tile)
if tile_image is None{
assign_tile_image(tile)
tile_image = menu_tile_library.get(tile)
rotated_image = rotate_tile_image(tile, tile_image)
//                console.log("Placing a tile at pixel coordinates " + str(horizontal * tile_size) + ", " + str(vertical * tile_size))
horizontal = chest_rect[0] + (chest_tiles.index(tile) % MENU_TILE_COLS) * menu_tile_size
//            vertical += (chest_tiles.index(tile) // MENU_TILE_COLS) * menu_tile_size
            vertical = chest_rect[1] + (chest_tiles.index(tile) // MENU_TILE_COLS) * menu_tile_size
            move_fground.drawImage(rotated_image, [horizontal, vertical])
            //If this is the tile selected then highlight this with a hollow rectangle
if chest_tiles.index(tile) == preferred_tile_num{
    pygame.draw.rect(window, CHEST_HIGHLIGHT_COLOUR
        , (horizontal, vertical, menu_tile_size, menu_tile_size)
        , chest_highlight_thickness)
else{
pygame.draw.rect(window, PLAIN_TEXT_COLOUR
    , (horizontal, vertical, menu_tile_size, menu_tile_size)
    , chest_highlight_thickness)

function draw_cards(){
/**Adds images of the current Adventurer's character and discovery cards to the menu below their Chest

Arguments{
Adventurer takes a Cartolan Adventurer
*/
        //Identify the adventurer that has been selected to focus on in this visual
game = game
for player in game.players{
    if player == viewed_adventurer.player{
        break
adventurer = game.adventurers[player][viewed_adventurer_number]
        //Establish the top left coordinate of the stack of cards
horizontal = 0
//        vertical = SCORES_FONT_SCALE * height * (len(game.players) + 1)
vertical = scores_rect[1] + scores_rect[3]
//        vertical = chest_rect[1] + chest_rect[3]
        //draw the Adventurer's Player's Cadre Card
if game.assigned_cadres.get(adventurer.player) is not None{
card_title = scores_font.render(adventurer.player.name + "'s Cadre card:", 1, PLAIN_TEXT_COLOUR)
turn_fground.putImageData(card_title, [horizontal, vertical])
            //Now draw the card itself
card = game.assigned_cadres.get(adventurer.player)
card_image = get_card_image(adventurer, card)
vertical += SCORES_FONT_SCALE * height
turn_fground.drawImage(card_image, [horizontal, vertical])
vertical += card_image.get_height()
        //Procede to draw any other cards
if adventurer.character_card is not None{
card_title = scores_font.render("Adventurer #" + str(game.adventurers[adventurer.player].index(adventurer) + 1) + " cards:", 1, PLAIN_TEXT_COLOUR)
turn_fground.putImageData(card_title, [horizontal, vertical])
vertical += SCORES_FONT_SCALE * height
//        stack_size = card_height * (1 + CARD_HEADER_SHARE * len(adventurer.character_cards))
stack_size = card_height + card_height * CARD_HEADER_SHARE * len(adventurer.discovery_cards)  //one character card plus all the manuscripts
stack_rect = (horizontal, vertical, play_area_start, stack_size)
//        console.log("Card stack corners functionined at pixels...")
//        console.log(stack_rect)
                
        //Cycle through the Discovery Cards, drawing them
for card in adventurer.discovery_cards{
    if selected_card_num is not None{
if adventurer.discovery_cards.index(card) == selected_card_num{
    break
//            console.log("Drawing a card of type " + card.card_type)
card_image = get_card_image(adventurer, card)
turn_fground.drawImage(card_image, [horizontal, vertical])
vertical += CARD_HEADER_SHARE * card_image.get_height() 
        
        //Draw the Adventurer's Character Card over the top
if adventurer.character_card is not None{
card_image = get_card_image(adventurer, adventurer.character_card)
    //        card_horizontal = 0
vertical = stack_rect[1] + card_image.get_height() * CARD_HEADER_SHARE * len(adventurer.discovery_cards)
turn_fground.drawImage(card_image, [horizontal, vertical])
//        card_rect = (0, card_stack_position, play_area_start, stack_size)
//        pygame.draw.rect(window, PLAIN_TEXT_COLOUR
//, chest_rect
//, chest_highlight_thickness)
        //If one of the discovery / manuscript cards has been selected then draw cards back over the current ones in reverse up to that one
if selected_card_num is not None{
for card in reversed(adventurer.discovery_cards){
    vertical -= CARD_HEADER_SHARE * card_image.get_height()
//                console.log("Drawing a card of type " + card.card_type)
card_image = get_card_image(adventurer, card)
turn_fground.drawImage(card_image, [horizontal, vertical])
if adventurer.discovery_cards.index(card) == selected_card_num{
    break


function get_card_image(card_holder, card){
/**Draws a Character or Discovery card
*/
card_image = card_images.get(card)
if card_image is None{
available_cards = card_image_library[card.card_type]
//            if not available_cards{ //if all the card images have been used then recycle
//                card_image_library[card.card_type] = used_card_images[card.card_type]
//                available_cards = card_image_library[card.card_type]
//                used_card_images[card.card_type] = []
card_image = card_images[card] = available_cards.pop()
//            used_card_images[card.card_type].push(card_image)
available_cards.insert(0, card_image) //Prepend this image back into the library so that it won't get used again unless other images run out
return card_image

function draw_card_offers(cards){
/**Prominently displays an array of cards from which the player can choose

Arguments{
Cards takes a list of Cartolan Cards
*/
        // offer_images = [] //reset the record of card images in use
offer_rects = [] //reset the record of card positions for selection
        //Cycle through the offered Cards, drawing them
horizontal_increment = width // (len(cards) + 1)
card_horizontal = horizontal_increment
card_vertical = (height - card_height) // 2 //Centre the cards vertically
for card in cards{
    console.log("Drawing a card of type " + card.card_type)
card_image = get_card_image(None, card)
//            card_type = card.card_type
//            available_cards = card_image_library[card_type]
//            if available_cards{
//                card_image = available_cards[0] //Choose the first image available
//            else{
//                card_image = used_card_images[card_type][0]
adjusted_horizontal = card_horizontal - card_image.get_width() // 2
turn_fground.drawImage(card_image, [adjusted_horizontal, card_vertical])
card_horizontal += horizontal_increment
            // offer_images.push(card_image)
offer_rects.push((adjusted_horizontal, card_vertical, card_image.get_width(), card_image.get_height()))
    
    //@TODO combine the two methods for choosing cards and tiles, once there are multiple tile images too
function draw_tile_offers(tiles){
/**Prominently displays an array of tiles from which the player can choose

Arguments{
tiles takes a list of Cartolan Tiles
*/
        // offer_images = [] //reset the record of card images in use
offer_rects = [] //reset the record of card positions for selection
        //Cycle through the offered Cards, drawing them
horizontal_increment = width // (len(tiles) + 1)
tile_horizontal = horizontal_increment
tile_vertical = (height - offer_tile_size) // 2 //Centre the cards vertically
for tile in tiles{
    tile_image = offer_tile_library.get(tile)
if tile_image is None{
assign_tile_image(tile)
tile_image = offer_tile_library.get(tile)
rotated_image = rotate_tile_image(tile, tile_image)
//                console.log("Placing a tile at pixel coordinates " + str(horizontal * tile_size) + ", " + str(vertical * tile_size))
adjusted_horizontal = tile_horizontal - offer_tile_size // 2
move_fground.drawImage(rotated_image, [adjusted_horizontal, tile_vertical])
tile_horizontal += horizontal_increment
            // offer_images.push(tile_image)
offer_rects.push((adjusted_horizontal, tile_vertical, offer_tile_size, offer_tile_size))

function draw_prompt(){
/**Prints a prompt on what moves/actions are available to the current player
*/        
//        console.log("Creating a prompt for the current player")
        //Establish the colour(as the current player's)
//        prompt = prompt_font.render(prompt_text, 1, pygame.Color(current_player_colour))
        prompt_width = width - play_area_start - right_menu_width
        prompt = wrap_text(prompt_text, prompt_width, height, prompt_font, pygame.Color(current_player_colour), BACKGROUND_COLOUR)
        move_fground.putImageData(prompt, (play_area_start, height - prompt.get_height()))
        
    function start_turn(adventurer){
    /**Identifies the current player by their colour, affecting prompts
        */
        player_colour = player_colours[adventurer.player]
        adventurer_number = game.adventurers[adventurer.player].index(adventurer)
//        //Reset the request for an undo
//        undo_agreed = False
//        undo_asked = False
for game_vis in peer_visuals{
    game_vis.current_player_colour = player_colour
game_vis.current_adventurer_number = adventurer_number
game_vis.current_adventurer = adventurer
game_vis.current_adventurer.preferred_tile_num = None //deselect any chest map
            //Also reset which adventurer's cards are being viewed
game_vis.viewed_player_colour = player_colour
game_vis.viewed_adventurer_number = adventurer_number
game_vis.viewed_adventurer = adventurer
            //Reset the request for an undo
            game_vis.undo_agreed = False
    
    function give_prompt(prompt_text){
/**Pushes text to the prompt buffer for the visual

Arguments{
prompt_text should be a string
*/
prompt_text = prompt_text
        //Replace all the visuals, rather than overlaying text on old text
//        draw_play_area()
//        draw_tokens()
//        draw_routes()
//        draw_move_options()
draw_prompt()


function clear_prompt(){
/**Empties the prompt buffer for the visual
*/
promp_text = ""
        
    //@TODO introduce text input in pygame window
function get_input_value(prompt_text, maximum){
/**ends a prompt to the player, and waits for numerical input.

Arguments
prompt takes a string
*/
return None


function get_input_coords(adventurer){
/**Passes mouseclick input from the user and converts it into the position of a game tile.

Arguments
adventurer takes a Cartolan.Adventurer
*/
//        console.log("Waiting for input from the user")
pygame.display.flip()
while True{
    event = pygame.event.wait()
            //quit if the quit button was pressed
if event.type == pygame.QUIT{
    pygame.quit()
sys.exit()
if event.type == pygame.VIDEORESIZE{
    window_resize(event)
if event.type == pygame.MOUSEBUTTONDOWN{
    move_timer = MOVE_TIME_LIMIT //reset the timelimit on moving
                //check whether the click was within the menu, and return the index within the chest
if (event.pos[0] in range(chest_rect[0], chest_rect[2])
                    and event.pos[1] in range(chest_rect[1], chest_rect[3])){
menu_row = (event.pos[1] - chest_rect[1]) // menu_tile_size
menu_column = (event.pos[0] - chest_rect[0]) // menu_tile_size
return MENU_TILE_COLS * menu_row + menu_column
                //Check whether the click was within the card stack, and update the index of the selected card
if (event.pos[0] in range(stack_rect[0], stack_rect[2])
                    and event.pos[1] in range(stack_rect[1], stack_rect[3])){
if selected_card_num is None{ //The Character card at the bottom will be on top
if event.pos[1] < stack_rect[3] - card_height{
    selected_card_num = (event.pos[1] - stack_rect[1]) // (card_height * CARD_HEADER_SHARE)
else{
selected_card_top = stack_rect[1] + (selected_card_num - 1) * card_height * CARD_HEADER_SHARE
selected_card_bottom = selected_card_top + card_height
if event.pos[1] > stack_rect[3] - card_height * CARD_HEADER_SHARE{
    selected_card_num = None
elif event.pos[1] < selected_card_top{
selected_card_num = (event.pos[1] - stack_rect[1]) // (card_height * CARD_HEADER_SHARE)
elif event.pos[1] > selected_card_bottom{
selected_card_num += (event.pos[1] - selected_card_bottom) // (card_height * CARD_HEADER_SHARE)
                //Otherwise return the coordinates
longitude = int(math.ceil((event.pos[0]) / tile_size)) - origin[0] - 1
latitude = dimensions[1] - int(math.ceil((event.pos[1]) / tile_size)) - origin[1]
                //check whether the click was within the highlighted space and whether it's a local turn
//                highlighted_option = check_highlighted(longitude, latitude)
//                console.log("Click was a valid option of type: " + highlighted_option)
if True{
//                if highlighted_option is not None{
highlights = { highlight_type{ [] for highlight_type in HIGHLIGHT_PATHS } //clear the highlights until the server offers more
//                    console.log("Have identified a move available at " + str(longitude) + ", " + str(latitude) + " of type " + str(highlighted_option))
return [longitude, latitude]
if move_timer < 0{
    return False
//                if local_player_turn and highlighted_option is not None{
//                    Send({ "action": highlighted_option, "longitude": longitude, "latitude": latitude, "player": current_player_colour, "adventurer": current_adventurer_number, "gameid": gameid })
//                    highlights = [] //clear the highlights until the server offers more
//       //Otherwise wait for suitable input
        
        //update the window
        //at the point of seeking player input for an Adventurer for the first time this turn, clear its route history
        
        //@TODO alternatively, take keyboard input from the cursor keys and Enter key
        
        //Refresh the display
pygame.display.flip()

return False

function close(){
/**Elegantly closes the application down.
*/
pygame.quit()
sys.exit()

function finished(){
move_fground.putImageData(gameover if not local_win else winningscreen, (0, 0))
while True{
    for event in pygame.event.get(){
        if event.type == pygame.QUIT{
            pygame.quit()
sys.exit()
pygame.display.flip()


class WebServerVisualisation(GameVisualisation){
/**For a server-side game played in browser, shares image of play area and receives coords

There will be a separate visual for each client.
    Because the clients all need to see every move, each visual will send for every player.
    But, only the moving player's visual will receive input. 
*/
TEMP_FILENAME_LEN = 6
TEMP_FILE_EXTENSION = ".png"
INPUT_DELAY = 0.1 //delay time between checking for input, in seconds
    
    function __init__(game, peer_visuals, player_colours, client, width, height){
peer_visuals = peer_visuals
client = client
width, height = width, height
client_players = []
super().__init__(game, peer_visuals, player_colours)

function init_GUI(){
console.log("Initialising the pygame window and GUI")
pygame.init()
window = pygame.Surface((width, height), pygame.SRCALPHA, 32)
background.fill(BACKGROUND_COLOUR) //fill the screen with a background colour / transparency
console.log("Initialising visual scale variables, to fit window of size " + str(width) + "x" + str(height))
tile_size = height // dimensions[1]
        //We'll have a different tile size for dicards and menu highlights
play_area_width = Math.round(width * (1 - LEFT_MENU_SCALE - RIGHT_MENU_SCALE))
play_area_start = Math.round(width * LEFT_MENU_SCALE)
right_menu_width = Math.round(width * RIGHT_MENU_SCALE)
right_menu_start = play_area_start + play_area_width
right_text_start = MOVE_COUNT_POSITION[0] * width //All text indicators in the right menu will follow the same indent
menu_highlight_size = Math.round(RIGHT_MENU_SCALE * width) // len(TOGGLE_HIGHLIGHTS)
menu_route_thickness = ROUTE_THICKNESS
menu_spacing = menu_route_thickness
menu_tile_size = Math.round(RIGHT_MENU_SCALE * width) // MENU_TILE_COLS
        //Before sizing against the horizontal dimension, we'll work out how much space the menus will take away
play_area_width = Math.round(width * (1 - LEFT_MENU_SCALE - RIGHT_MENU_SCALE))
play_area_start = Math.round(width * LEFT_MENU_SCALE)
        //Tiles will be scaled to fit the smaller dimension
if play_area_width < tile_size * dimensions[0]{
    tile_size = play_area_width // dimensions[0]
        //Where piracy is possible, we'll have a different tile size for 
offer_tile_size = Math.round(OFFER_SCALE * width)
token_size = int(round(TOKEN_SCALE * tile_size)) //token size will be proportional to the tiles
outline_width = math.ceil(TOKEN_OUTLINE_SCALE * token_size)
token_font = pygame.font.SysFont(None, Math.round(tile_size * TOKEN_FONT_SCALE)) //the font size for tokens will be proportionate to the window size
scores_font = pygame.font.SysFont(None, Math.round(height * SCORES_FONT_SCALE)) //the font size for scores will be proportionate to the window size
card_font = pygame.font.SysFont(None, Math.round(height * CARD_FONT_SCALE)) //the font size for scores will be proportionate to the window size
prompt_font = pygame.font.SysFont(None, Math.round(height * PROMPT_FONT_SCALE)) //the font size for prompt will be proportionate to the window size
prompt_position = [play_area_start + PROMPT_POSITION[0] * width
    , PROMPT_POSITION[1] * height]
pygame.font.init()
prompt_text = ""
        //Make sure that the GUI menus are drawn on the correct sides from the start
scores_rect = (0, 0, 0, 0)
stack_rect = (0, 0, 0, 0)
current_move_count = None
move_count_rect = (MOVE_COUNT_POSITION[0] * width, MOVE_COUNT_POSITION[1] * height, 0, Math.round(height * SCORES_FONT_SCALE))
toggles_rect = (right_menu_start, move_count_rect[1] + move_count_rect[3] + Math.round(height * SCORES_FONT_SCALE) + menu_highlight_size, 0, menu_tile_size + Math.round(height * SCORES_FONT_SCALE))
chest_rect = (right_menu_start, toggles_rect[1] + toggles_rect[3] + Math.round(height * SCORES_FONT_SCALE), 0, menu_tile_size)
piles_rect = (right_menu_start, toggles_rect[1] + toggles_rect[3] + Math.round(height * SCORES_FONT_SCALE), 0, 0)
        
        //Import images
init_graphics()

        //Keep track of which tiles and cards have been shared so far, to reduce the data stream
shared_tiles_cards = []

function update_web_display(){
/**For this client visualisation in particular, send out a JSON serialisation of the play area and player scores.
*/
//        pygame.display.flip()
        //generate a random filename, to avoid thread conflicts
randname = (''.join(random.choice(string.ascii_lowercase) for i in range(TEMP_FILENAME_LEN)) )
        //@TODO could reduce file size and latency by compressing into a lossy jpg
pygame.image.save(window, randname + TEMP_FILE_EXTENSION)
out = open(randname + TEMP_FILE_EXTENSION, "rb").read()
console.log("Image has a size of: " + str(sys.getsizeof(out)))
client.sendMessage("IMAGE[00100]" + str(base64.b64encode(out)))
console.log("Play area image sent to client at " + str(client.address))
os.remove(randname + TEMP_FILE_EXTENSION)

        // Before serialising the game objects for sharing to the JS frontend, we'll convert members to dicts and ignore Game objects because they contain an object-keyed list
shared_tiles_cards = []
function dict_reserve_tiles_cards(obj){
if isinstance(obj, Tile){
    if obj in shared_tiles_cards{
        return { "tile_id": obj.tile_id }
    else{
    shared_tiles_cards.push(obj)
return obj.__dict__
                //@TODO after a card has been shared once in a game, its perk details don't need to be shared again - indeed the card type should be enough in the first place
elif isinstance(obj, Card){
if obj in shared_tiles_cards{
    return { "card_id": obj.card_id }
else{
shared_tiles_cards.push(obj)
return { "card_id": obj.card_id, "card_type": obj.card_type }
elif isinstance(obj, Adventurer){
if obj.character_card in shared_tiles_cards{
    character_card = { "card_id": obj.character_card.card_id }
elif obj.character_card is not None{
shared_tiles_cards.push(obj.character_card)
character_card = { "card_id": obj.character_card.card_id, "card_type": obj.character_card.card_type }
                else{
character_card = None
return {
    "player": obj.player.name,
    "vault_wealth": game.player_wealths[obj.player],
    "cadre_card": game.assigned_cadres[obj.player],
    "num": game.adventurers[obj.player].index(obj),
    "wealth": obj.wealth,
    "pirate_token": obj.pirate_token,
    "route": obj.route,
    "character_card": character_card,
    "discovery_cards": obj.discovery_cards
}
elif isinstance(obj, Agent){
return {
    "player": obj.player.name,
    "wealth": obj.wealth,
    "is_dispossessed": obj.is_dispossessed
}
elif isinstance(obj, Game) or isinstance(obj, Player){
return None
            else{
return obj.__dict__

serialised_play_area = json.dumps(game.play_area, functionault=lambda obj{ dict_reserve_tiles_cards(obj), check_circular = False)
console.log("Serialised play-area has a size of: " + str(sys.getsizeof(serialised_play_area)))
console.log(serialised_play_area)
        // client.sendMessage("STATE[00100]" + serialised_play_area)
        //console.log("Play area data sent to client at " + str(client.address))
        // //@TODO now share any messages to the player


function get_input_value(adventurer, prompt_text, maximum, minimum = 0){
/**Sends a prompt to the player, and waits for numerical input.

Arguments
adventurer takes a Cartolan Adventurer from which to draw values for updating visuals
        prompt_text takes a string
maximum and minimum take int values setting limits on the numerical value that can be input
*/
        //Update the visuals for the remote players who aren't active
refresh_peers(adventurer, input_type = "value")
console.log("Prompting client at " + str(client.address) + " with: " + prompt_text)
client.sendMessage("PROMPT[00100]" + prompt_text)
input_value = None
while not input_value{
    input_value = client.get_text()
if input_value{
//                console.log("Trying to interpret " + input_value + " as a number")
try{
//                    console.log("Checking that " + input_value + " is between 0 and " + str(maximum))
if int(input_value) in range(minimum, maximum + 1){
    return int(input_value)
client.sendMessage("PROMPT[00100]" + prompt_text)
input_value = None
except{
//                    console.log("Decided it wasn't a number so interpretting as nothing")
return None
input_value = None
            //@TODO check for input from the other clients to their visuals and update their view
            //Wait before checking again
time.sleep(INPUT_DELAY)
return None

function refresh_peers(adventurer, choices = None, input_type = "move"){
/**Cycles through clients to the same game, besides the active player, updating their visuals
*/
        //console.log("Updating the display for all the other human players, whose visuals won't have been consulted.")
refreshed_visuals = []
for game_vis in peer_visuals{
    if not client == game_vis.client and game_vis not in refreshed_visuals{
refreshed_visuals.push(game_vis)
game_vis.refresh_visual(choices, input_type)
game_vis.update_web_display()

function refresh_visual(choices = None, input_type = "move"){
/**Updates all elements of this visual, as required when not the active player
*/
        //Update visuals to keep them informed of action
draw_play_area()
draw_tokens()
draw_routes()
        //Draw the right menu items
if not input_type in ["choose_company", "choose_character"]{
draw_move_count()
draw_toggle_menu()
draw_routes_menu()
if isinstance(current_adventurer, AdventurerRegular){
    if not input_type == "choose_tile"{ //Don't draw the chest tiles when the players are first picking companies and adventurers 
draw_chest_tiles()
draw_tile_piles()
draw_discard_pile()
        //Draw the left menu items and any offers over the top
draw_scores()
if isinstance(current_adventurer, AdventurerAdvanced){
    draw_cards()
            //If offers are being made then draw these on top of everything else
if choices is not None{
if input_type == "choose_tile"{
    draw_tile_offers(choices)
else{
draw_card_offers(choices)
draw_undo_button()
        //Prompt the player
if input_type == "move"{
    prompt = current_adventurer.player.name + " is moving their Adventurer //" + str(current_adventurer_number + 1)
elif input_type == "text"{
prompt = current_adventurer.player.name + " is choosing a treasure amount for their Adventurer //" + str(current_adventurer_number + 1)
elif input_type == "choose_tile"{
prompt = current_adventurer.player.name + " is choosing a tile for their Adventurer //" + str(current_adventurer_number + 1)
elif input_type == "choose_discovery"{
prompt = current_adventurer.player.name + " is choosing a Manuscript card for their Adventurer //" + str(current_adventurer_number + 1)
elif input_type == "choose_company"{
prompt = current_adventurer.player.name + " is choosing their Cadre card"
        else{
prompt = current_adventurer.player.name + " is choosing a Character card for their Adventurer //" + str(current_adventurer_number + 1)
give_prompt(prompt)

function check_peer_input(){
/**Cycles through remote players besides the active one, checking whether clicks have been registered and updating their private visuals accordingly
*/
checked_visuals = []
for game_vis in peer_visuals{
    if not client == game_vis.client and game_vis not in checked_visuals{
checked_visuals.push(game_vis)
coords = game_vis.client.get_coords()
if coords is not None{
horizontal, vertical = coords
if game_vis.check_update_focus(horizontal, vertical){
    game_vis.refresh_visual()
game_vis.update_web_display()
                    //Check whether this player wants / agrees to an undo
elif game_vis.check_undo(horizontal, vertical){
game_vis.refresh_visual()
game_vis.update_web_display()

function check_peers_undo(){
/**Cycles through all clients of the game to see whether they all agree to undo this turn
*/
        //Any one player disagreeing will mean the undo isn't agreed yet
for game_vis in peer_visuals{
    if not game_vis.undo_agreed{
return False
return True

function reset_peer_undos(){
/**Cycles through all clients to the game, making sure they don't continue to vote for resetting the turn
        */
        //If all rejected then this will be fed back to the game, but all will need to be reset
for game_vis in peer_visuals{
    game_vis.undo_agreed = False
return True

function check_undo(horizontal, vertical){
/**Checks whether click coordinates were within the undo button's click - box
*/
if (horizontal in range(int(undo_rect[0]), int(undo_rect[0] + undo_rect[2]))
            and vertical in range(int(undo_rect[1]), int(undo_rect[1] + undo_rect[3]))){
console.log("Player chose coordinates within the undo button, with vertical: " + str(vertical))
if undo_agreed{
    undo_agreed = False
else{
undo_agreed = True
return True
        else{
return False

function check_update_focus(horizontal, vertical){
/**Checks whether click coordinates were within the superficial visual elements that need no game response but should revise the client's visuals
*/
//        if (horizontal in range(int(scores_rect[0]), int(scores_rect[0] + scores_rect[2]))
//            and vertical in range(int(scores_rect[1]), int(scores_rect[1] + scores_rect[3]))){
//            console.log("Player chose coordinates within the scores table, with vertical: " + str(vertical))
        //Check whether the click was on one of the scores in the table(check them individually straight away, to avoid masking clicks on highlights under the scores table)
for score in score_rects{
    score_rect = score[0]
if (horizontal in range(int(score_rect[0]), int(score_rect[0] + score_rect[2]))
                and vertical in range(int(score_rect[1]), int(score_rect[1] + score_rect[3]))){
console.log("Having found the click within a particular player/adventurer's score, need to update the focus of the card stacks")
if isinstance(score[1], Player){
                    //just choose the first adventurer if it was the player's vault wealth selected
viewed_player_colour = player_colours[score[1]]
viewed_adventurer_number = 0
viewed_adventurer = game.adventurers[score[1]][0]
                else{
viewed_player_colour = player_colours[score[1].player]
viewed_adventurer_number = game.adventurers[score[1].player].index(score[1])
viewed_adventurer = score[1]
console.log("Updated focus for card visuals to " + viewed_adventurer.player.name + "'s Adventurer //" + str(viewed_adventurer_number + 1))
return True
        //Check whether the click was within the card stack, and update the index of the selected card
if (horizontal in range(int(stack_rect[0]), int(stack_rect[0] + stack_rect[2]))
            and vertical in range(int(stack_rect[1]), int(stack_rect[1] + stack_rect[3]))){
console.log("Player chose coordinates within the card stack, with vertical: " + str(vertical))
if selected_card_num is None{ //The Character card at the bottom will be on top
//                console.log("Stack top is " + str(int(stack_rect[1] + stack_rect[3])))
//                console.log("Card height is " + str(card_height))
if vertical < int(stack_rect[1] + stack_rect[3]) - card_height{
    selected_card_num = int(vertical - stack_rect[1]) // int(card_height * CARD_HEADER_SHARE)
console.log("Updated the selected card to number " + str(selected_card_num))
            else{
selected_card_top = int(stack_rect[1] + (selected_card_num - 1) * card_height * CARD_HEADER_SHARE)
selected_card_bottom = selected_card_top + card_height
if vertical > int(stack_rect[1] + stack_rect[3]) - card_height * CARD_HEADER_SHARE{
    selected_card_num = None
elif selected_card_top < vertical < selected_card_bottom{
selected_card_num = None //clicking on the selected card de - selects it
elif vertical < selected_card_top{
selected_card_num = (vertical - int(stack_rect[1])) // int(card_height * CARD_HEADER_SHARE)
elif vertical > selected_card_bottom{
selected_card_num += (vertical - selected_card_bottom) // int(card_height * CARD_HEADER_SHARE)
//                        console.log("Updated the selected card to number " + str(selected_card_num))
return True
        //Check for clicks in the toggle menu, for changing route drawing mode
elif(horizontal in range(int(toggles_rect[0]), int(toggles_rect[0] + toggles_rect[2]))
            and vertical in range(int(toggles_rect[1]), int(toggles_rect[1] + toggles_rect[3]))){
draw_all_routes = not draw_all_routes
return True
        else{
            //Check the various Adventurer and Agent shapes for a click and use this to select the Adventurer to focus on
for centre in adventurer_centres{
    if (horizontal - centre[0][0])** 2 + (vertical - centre[0][1]) ** 2 < token_size ** 2{
console.log("Click detected within one of the Adventurers' areas, with centre: " + str(centre[0]))
viewed_player_colour = player_colours[centre[1].player]
viewed_adventurer_number = game.adventurers[centre[1].player].index(centre[1])
viewed_adventurer = centre[1]
return True
for rect in agent_rects{
    if (horizontal in range(int(rect[0][0]), int(rect[0][0] + rect[0][2]))
                    and vertical in range(int(rect[0][1]), int(rect[0][1] + rect[0][3]))){
console.log("Click detected within one of the Inns' areas for " + player_colours[rect[1]] + " player.")
viewed_player_colour = player_colours[rect[1]]
viewed_adventurer_number = 0
viewed_adventurer = game.adventurers[rect[1]][0]
return True
return False

function get_input_coords(adventurer){
/**Sends an image of the latest play area, accepts input only from this visual's players.

    Arguments
adventurer takes a Cartolan.Adventurer
*/
        //Make sure that the current adventurer is up to date
if current_adventurer is None{
start_turn(adventurer)
        //Update the visuals to prompt input
update_web_display()
        //Update the visuals for the remote players who aren't active
refresh_peers(adventurer)

coords = None
while coords is None{
coords = client.get_coords()
if coords is not None{
horizontal, vertical = coords
                //check whether the click was within the Chest menu, and return the index within the chest
if (horizontal in range(int(chest_rect[0])
    , int(chest_rect[0]) + int(chest_rect[2]))
                    and vertical in range(int(chest_rect[1])
        , int(chest_rect[1]) + int(chest_rect[3]))){
//                    console.log("Player chose coordinates within the menu")
menu_row = (vertical - int(chest_rect[1])) // menu_tile_size
menu_column = (horizontal - int(chest_rect[0])) // menu_tile_size
return : "preferred_tile": MENU_TILE_COLS * menu_row + menu_column }
                //Check whether the click was within the toggle menu, and update the index of the selected card
elif(horizontal in range(int(toggles_rect[0]), int(toggles_rect[0] + toggles_rect[2]))
                    and vertical in range(int(toggles_rect[1]), int(toggles_rect[1] + toggles_rect[3]))){
//                    console.log("Player chose coordinates within the toggle menu, with vertical: " + str(vertical))
                    //Check which highlight was clicked and return it
for highlight in action_rects{
    highlight_rect = highlight[0]
if (horizontal in range(int(highlight_rect[0])
    , int(highlight_rect[0]) + int(highlight_rect[2]))
                            and vertical in range(int(highlight_rect[1])
        , int(highlight_rect[1]) + int(highlight_rect[3]))){
//                            console.log("Identified coordinates within one of the auto-response toggles.")
return { "toggle": highlight[1] }
                    //If the click wasn't in the rect around one of the highlight options, then assume it was a click to toggle route drawing
draw_all_routes = not draw_all_routes
return { "update_visuals": "update_visuals" } 
                //Check whether the click was irrelevant to gameplay but changes the focus of the active player's visuals
elif check_update_focus(horizontal, vertical){
return { "update_visuals": "update_visuals" }
                //Check whether the unod button was clicked
elif check_undo(horizontal, vertical){
refresh_peers(adventurer) //Update peers' displays to show that the undo request has been made
return { "update_cards": "update_cards" } //Get the player to prompt again and refresh their own visuals              
                else{
                    //Otherwise check whether the click was within a highlighted cell and return the coordinates
for highlight_type in highlight_rects{
    for highlight_rect in highlight_rects[highlight_type]{
        if (horizontal in range(int(highlight_rect[0])
            , int(highlight_rect[0]) + int(highlight_rect[2]))
                                and vertical in range(int(highlight_rect[1])
                , int(highlight_rect[1]) + int(highlight_rect[3]))){
longitude = int(math.ceil((horizontal - play_area_start) / tile_size)) - origin[0] - 1
latitude = dimensions[1] - int(math.ceil((vertical) / tile_size)) - origin[1]
//                                console.log("Identified coordinates within a highlighted option.")
return { highlight_type{ [longitude, latitude] }
                    //Also check whether the click was on a drawn route
for route in drawn_routes{
    for segment in route[0]{
        if (horizontal in range(int(segment[0] - ROUTE_THICKNESS)
            , int(segment[0]) + int(segment[2] + ROUTE_THICKNESS))
                            and vertical in range(int(segment[1] - ROUTE_THICKNESS)
                , int(segment[1]) + int(segment[3] + ROUTE_THICKNESS))){
longitude = int(math.ceil((horizontal - play_area_start) / tile_size)) - origin[0] - 1
latitude = dimensions[1] - int(math.ceil((vertical) / tile_size)) - origin[1]
//                                console.log("Identified coordinates on a route of length " + str(len(route[1])))
return { "route": route[1], "destination": [longitude, latitude] }
//                coords = None
            //Check for input from the other clients to their visuals and update their view
check_peer_input()
if check_peers_undo(){
    console.log("Confirmed with all clients that turn can be undone.")
return { "undo": "undo" }
            //Wait before checking again
time.sleep(INPUT_DELAY)

return { "Nothing": "Nothing" }

function get_input_choice(adventurer, cards, offer_type = "card"){
/**Sends an image of the latest play area, accepts input only from this visual's players.

    Arguments
adventurer takes a Cartolan.adventurer
cards takes a list of Cartolan.card
*/
        //Update the visuals to prompt input
update_web_display()
        //Make sure that the current adventurer is up to date
if current_adventurer is None{
start_turn(adventurer)
        //Update the visuals for the remote players who aren't active
if offer_type == "card"{
    if cards[0].card_type[{ 3] == "com"{
input_type = "choose_company"
elif cards[0].card_type[{ 3] == "dis"{
input_type = "choose_discovery"
elif cards[0].card_type[{ 3] == "adv"{
input_type = "choose_adventurer"
        else{
input_type = "choose_tile"
refresh_peers(adventurer, choices = cards, input_type = input_type)

coords = None
while coords is None{
coords = client.get_coords()
if coords is not None{
horizontal, vertical = coords
                //check whether the click was within each of the card areas, and return the index
for offer_rect in offer_rects{
    if (horizontal in range(int(offer_rect[0])
        , int(offer_rect[0]) + int(offer_rect[2]))
                        and vertical in range(int(offer_rect[1])
            , int(offer_rect[1]) + int(offer_rect[3]))){
//                        console.log("Player chose coordinates within a card")
selected_index = offer_rects.index(offer_rect)
return selected_index
coords = None //Let them try again
            //Check for input from the other clients to their visuals and update their view
check_peer_input()
time.sleep(INPUT_DELAY)

return False
