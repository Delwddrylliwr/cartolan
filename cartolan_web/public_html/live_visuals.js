/**
 * @fileoverview Canvas-based interactive visualisation for games of Cartolan,
 * consuming JSON game state from a WebSocket server.
 * Dependencies: HTML5 Canvas
 * @package cartolan
 *
 * Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
 */

class GameVisualisation {

  // ── Layout constants ──────────────────────────────────────────────────────
  static DIMENSION_BUFFER    = 1;
  static PLAYER_OFFSETS      = [[0.25, 0.25], [0.25, 0.75], [0.75, 0.25], [0.75, 0.75]];
  static AGENT_OFFSET        = [0.5, 0.5];
  static ADVENTURER_OFFSETS  = [[0.0, 0.0], [0.1, -0.1], [-0.1, 0.1], [-0.1, -0.1], [0.1, 0.1]];
  static TILE_BORDER         = 0.02;
  static LEFT_MENU_SCALE     = 0.13;
  static RIGHT_MENU_SCALE    = 0.13;
  static MENU_TILE_COLS      = 2;
  static MENU_FONT_SCALE   = 0.04;
  static OFFER_SCALE         = 0.15;
  static ROUTE_THICKNESS     = 4.0;
  static TOKEN_SCALE         = 0.15;
  static AGENT_SCALE         = 1.75;
  static TOKEN_OUTLINE_SCALE = 0.25;
  static TOKEN_FONT_SCALE    = 0.2;
  static TOKEN_FONT_COLOURS  = { yellow: 'black' };
  static SCORES_POSITION     = [0.0, 0.0];
  static SCORES_FONT_SCALE   = 0.04;
  static CARD_HEADER_SHARE   = 0.15;
  static CARD_BODY_START     = 0.7;
  static CARD_RATIO          = 1.75;
  static PROMPT_POSITION     = [0.0, 0.95];
  static PROMPT_FONT_SCALE   = 0.05;
  static TOGGLE_HIGHLIGHTS   = ['buy', 'attack', 'rest'];

  // ── Colours ───────────────────────────────────────────────────────────────
  static PLAIN_TEXT_COLOUR      = 'rgb(255,255,255)';
  static WONDER_TEXT_COLOUR     = 'rgb(0,0,0)';
  static ACCEPT_UNDO_COLOUR     = 'rgb(255,0,0)';
  static CARD_BACKGROUND_COLOUR = 'rgb(255,255,255)';
  static CARD_TEXT_COLOUR       = 'rgb(0,0,0)';
  static CHEST_HIGHLIGHT_COLOUR = 'rgb(0,255,0)';
  static TOGGLE_TRUE_COLOUR     = 'rgb(0,255,0)';
  static TOGGLE_FALSE_COLOUR    = 'rgb(255,0,0)';

  // ── Typography ────────────────────────────────────────────────────────────
  static MENU_FONT = 'stmary10, serif';

  // ── Asset paths ───────────────────────────────────────────────────────────
  static TILE_PATH  = './img/map_tiles/tiles/';
  static CARDS_PATH = './img/cards/';

  static METERS_PATHS = {
    any_direction:  './img/move_meters/any_direction.png',
    downwind_water: './img/move_meters/downwind_water.png',
  };
  static HIGHLIGHT_PATHS = {
    move:           './img/highlights/option_valid_move.png',
    abandon:        './img/highlights/option_abandon.png',
    invalid:        './img/highlights/option_invalid_move.png',
    buy:            './img/highlights/option_buy.png',
    attack:         './img/highlights/option_attack.png',
    rest:           './img/highlights/option_rest.png',
    buy_rest:       './img/highlights/option_buy.png',
    move_agent:     './img/highlights/option_valid_move.png',
    agent_transfer: './img/highlights/option_buy.png',
  };

  // ── Card display text (mirrored from live_visuals.py) ────────────────────
  static CARD_TITLES = {
    'com+rests':     "The Intrepid Academy",
    'com+transfers': "The Great Company",
    'com+earning':   "The Merchants' Guild",
    'com+arrest':    "The Harbour Authority",
    'com+refurnish': "The Privateer Brethren",
    'com+pool':      "Order of the Lightbrary",
  };
  static CARD_TEXTS = {
    'adv+agents':    "Can place and immediately rest with Inns on existing tiles, for 3 treasure.",
    'adv+attack':    "Needs only win or draw Rock, Paper, Scissors to attack successfully.",
    'adv+bank':      "Can transfer treasure to your Inns when visiting anyone's Inn.",
    'adv+damage':    "Successfully attacked Adventurers are returned to their last city, and Inns are fully removed.",
    'adv+defence':   "Attacking opponents have to win Rock, Paper, Scissors twice to succeed.",
    'adv+downwind':  "Can move up to three times riding the wind after tiring, each turn and after resting.",
    'adv+upwind':    "Can move three times in any direction before getting tired, then one riding the wind, each turn or after resting.",
    'adv+maps':      "Carries up to three map tiles in Chest.",
    'dis+agents':    "This Adventurer can place Inns on existing tiles and immediately rest with them, for 3 treasure.",
    'dis+attack':    "This Adventurer needs only win or draw Rock, Paper, Scissors to attack successfully.",
    'dis+bank':      "This Adventurer can transfer treasure to your Inns when visiting anyone's Inn.",
    'dis+damage':    "Successfully attacked Adventurers are returned to their last city, and Inns are removed.",
    'dis+defence':   "Attacking opponents have to win an extra round of Rock, Paper, Scissors to succeed.",
    'dis+downwind':  "This Adventurer can move once more riding the wind after tiring, each turn and after resting.",
    'dis+upwind':    "This Adventurer can move once more before tiring, rather than after, each turn and after resting.",
    'dis+maps':      "This Adventurer carries an extra map tile in their chest.",
    'com+rests':     "Your Adventurers can rest with other Adventurers like Inns. Draw 3 Adventurers.",
    'com+transfers': "Treasure earned by your Inns goes to your Vault. Draw 3 Manuscripts.",
    'com+earning':   "Your Inns earn 1 treasure when opponents trade on their tile. Draw 3 Manuscripts.",
    'com+arrest':    "Your Inns try to arrest pirates landing on their tile. Draw 3 Adventurers.",
    'com+refurnish': "Your Adventurers can lose the pirate token by resting. Draw 3 Adventurers.",
    'com+pool':      "Anyone's Inns can swap your Adventures' maps for 1 treasure. Draw 3 Manuscripts.",
  };

  // ── Constructor ───────────────────────────────────────────────────────────

  constructor(canvas, context) {
    this.canvas  = canvas;
    this.context = context;
    this.state   = null;

    // Derived layout — recalculated on every applyState()
    this.dimensions       = [0, 0];
    this.origin           = [0, 0];
    this.tileSize         = 0;
    this.menuTileSize     = 0;
    this.playAreaStart    = 0;
    this.playAreaWidth    = 0;
    this.rightMenuStart   = 0;
    this.rightMenuWidth   = 0;
    this.menuHighlightSize = 0;
    this.tokenSize        = 0;
    this.outlineWidth     = 0;

    // Running vertical position for right-menu stacking
    this.rightMenuY    = 0;
    // Bottom y of scores table, for left-menu card placement
    this.scoresBottomY = 0;

    // Clickable areas registered during render for click dispatch
    this._clickableAreas = [];

    // Image caches
    this._tileSourceImages = {};  // tile_id → HTMLImageElement
    this._highlightImages  = {};  // highlight_type → HTMLImageElement
    this._meterImages      = {};  // meter_name → HTMLImageElement
    this._cardImages       = {};  // card_type → HTMLImageElement
    this._offerImages      = {};  // src url → HTMLImageElement (for offer overlay)

    // tile_name → [filename, ...] populated by _fetchTileManifest()
    this._tileVariants = {};
    // card_type → [filename, ...] populated by _fetchCardManifest()
    this._cardVariants = {};
    // card_type → chosen filename (cached so the image stays stable across re-renders)
    this._cardFilenames = {};

    // Optional send callback — set by caller after construction (e.g. gameVis.sendFn = send)
    this.sendFn = null;

    // Wrap canvas in a relative container so the scores overlay can sit on top
    const wrapper = document.createElement('div');
    wrapper.style.cssText = 'position:relative;display:inline-block;line-height:0';
    this.canvas.parentNode.replaceChild(wrapper, this.canvas);
    wrapper.appendChild(this.canvas);

    // Scores table overlay — absolutely positioned, overlaps play area transparently
    this._scoresEl = document.createElement('div');
    this._scoresEl.style.cssText =
      'position:absolute;top:0;left:0;pointer-events:none;box-sizing:border-box';
    wrapper.appendChild(this._scoresEl);

    // Cards panel overlay — positioned below scores table
    this._cardsEl = document.createElement('div');
    this._cardsEl.style.cssText =
      'position:absolute;left:0;overflow-y:auto;pointer-events:auto;box-sizing:border-box';
    wrapper.appendChild(this._cardsEl);

    this._preloadHighlights();
    this._preloadMeters();
    this._fetchTileManifest();
    this._fetchCardManifest();

    // Forward canvas clicks to the semantic dispatcher
    this.canvas.addEventListener('pointerdown', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = Math.round(e.clientX - rect.left);
      const y = Math.round(e.clientY - rect.top);
      this._handleClick(x, y);
    });
  }

  // ── Public entry point ────────────────────────────────────────────────────

  applyState(state) {
    this.state = state;
    this._recalcLayout();
    this._render();
  }

  // ── Layout calculation ────────────────────────────────────────────────────

  _recalcLayout() {
    const s = this.state;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const GV = GameVisualisation;

    // Find the bounding box of placed tiles
    let minLon = Infinity, maxLon = -Infinity;
    let minLat = Infinity, maxLat = -Infinity;
    for (const lonStr of Object.keys(s.play_area)) {
      const lon = Number(lonStr);
      if (lon < minLon) minLon = lon;
      if (lon > maxLon) maxLon = lon;
      for (const latStr of Object.keys(s.play_area[lonStr])) {
        const lat = Number(latStr);
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;
      }
    }
    if (!isFinite(minLon)) { minLon = 0; maxLon = 0; minLat = 0; maxLat = 0; }

    const cols = maxLon - minLon + 1 + 2 * GV.DIMENSION_BUFFER;
    const rows = maxLat - minLat + 1 + 2 * GV.DIMENSION_BUFFER;

    this.playAreaStart  = Math.round(w * GV.LEFT_MENU_SCALE);
    this.rightMenuWidth = Math.round(w * GV.RIGHT_MENU_SCALE);
    this.playAreaWidth  = w - this.playAreaStart - this.rightMenuWidth;
    this.rightMenuStart = this.playAreaStart + this.playAreaWidth;
    this.menuTileSize   = Math.floor(this.rightMenuWidth / GV.MENU_TILE_COLS);
    this.menuHighlightSize = Math.floor(this.rightMenuWidth / GV.TOGGLE_HIGHLIGHTS.length);

    const maxTileW = Math.floor(this.playAreaWidth / cols);
    const maxTileH = Math.floor(h / rows);
    this.tileSize = Math.min(maxTileW, maxTileH);

    // Distribute slack space to centre the play area
    const extraCols = Math.floor((this.playAreaWidth - cols * this.tileSize) / this.tileSize);
    const extraRows = Math.floor((h - rows * this.tileSize) / this.tileSize);
    this.dimensions = [cols + extraCols, rows + extraRows];
    this.origin = [
      -minLon + GV.DIMENSION_BUFFER + Math.floor(extraCols / 2),
      -minLat + GV.DIMENSION_BUFFER + Math.floor(extraRows / 2),
    ];

    this.tokenSize    = Math.round(GV.TOKEN_SCALE * this.tileSize);
    this.outlineWidth = Math.ceil(GV.TOKEN_OUTLINE_SCALE * this.tokenSize);
  }

  // Translate grid coordinates to canvas pixels (top-left of tile cell)
  _colToPixelX(longitude) {
    return this.playAreaStart + (this.origin[0] + longitude) * this.tileSize;
  }

  _rowToPixelY(latitude) {
    return (this.dimensions[1] - this.origin[1] - latitude - 1) * this.tileSize;
  }

  // ── Image preloading ──────────────────────────────────────────────────────

  _preloadHighlights() {
    for (const [name, path] of Object.entries(GameVisualisation.HIGHLIGHT_PATHS)) {
      if (!this._highlightImages[name]) {
        const img = new Image();
        img.src = path;
        this._highlightImages[name] = img;
      }
    }
  }

  _preloadMeters() {
    for (const [name, path] of Object.entries(GameVisualisation.METERS_PATHS)) {
      const img = new Image();
      img.src = path;
      this._meterImages[name] = img;
    }
  }

  _fetchTileManifest() {
    fetch(GameVisualisation.TILE_PATH + 'tile_manifest.json')
      .then(r => r.json())
      .then(manifest => {
        this._tileVariants = manifest;
        this._tileSourceImages = {};
        if (this.state) this._render();
      })
      .catch(() => {});
  }

  _fetchCardManifest() {
    fetch(GameVisualisation.CARDS_PATH + 'card_manifest.json')
      .then(r => r.json())
      .then(manifest => {
        this._cardVariants = manifest;
        this._cardFilenames = {};  // evict cached selections so new variants are picked
        if (this.state) this._render();
      })
      .catch(() => {});
  }

  // Returns a stable filename for a card type, picking randomly from the manifest on first use.
  _cardFilename(cardType) {
    if (!this._cardFilenames[cardType]) {
      const variants = this._cardVariants[cardType];
      this._cardFilenames[cardType] = variants && variants.length
        ? variants[Math.floor(Math.random() * variants.length)]
        : cardType + '.png';
    }
    return this._cardFilenames[cardType];
  }

  // Returns a cached HTMLImageElement for a tile object, picking a random variant on
  // first use. Keyed by tile_id so each tile object (placed or unplaced) gets its own
  // stable image across all re-renders.
  _tileSourceImage(tile) {
    const key = tile.tile_id;
    if (!this._tileSourceImages[key]) {
      const variants = this._tileVariants[tile.tile_name];
      const filename = variants && variants.length
        ? variants[Math.floor(Math.random() * variants.length)]
        : tile.tile_name + '.jpg';
      const img = new Image();
      img.src = GameVisualisation.TILE_PATH + filename;
      img.onload = () => this._render();
      this._tileSourceImages[key] = img;
    }
    return this._tileSourceImages[key];
  }

  // Returns a cached HTMLImageElement for a card_type, loading on first use.
  _cardSourceImage(cardType) {
    if (!this._cardImages[cardType]) {
      const img = new Image();
      img.src = GameVisualisation.CARDS_PATH + cardType + '.png';
      img.onload = () => this._render();
      this._cardImages[cardType] = img;
    }
    return this._cardImages[cardType];
  }

  // ── Draw helpers ──────────────────────────────────────────────────────────

  _tileRotation(tile) {
    if ( tile.wind_north &&  tile.wind_east) return 0;           // NE → no rotation
    if (!tile.wind_north &&  tile.wind_east) return Math.PI / 2; // SE → CW 90°
    if (!tile.wind_north && !tile.wind_east) return Math.PI;     // SW → 180°
    return -Math.PI / 2;                                          // NW → CCW 90°
  }

  _drawTileAt(tile, x, y, size) {
    const ctx = this.context;
    const img = this._tileSourceImage(tile);
    ctx.save();
    ctx.translate(x + size / 2, y + size / 2);
    ctx.rotate(this._tileRotation(tile));
    if (img.complete && img.naturalWidth > 0) {
      ctx.drawImage(img, -size / 2, -size / 2, size, size);
    } else {
      ctx.fillStyle = tile.tile_back === 'water' ? '#336699' : '#669933';
      ctx.fillRect(-size / 2, -size / 2, size, size);
      img.onload = () => this._render();
    }
    ctx.restore();
  }

  // Draws a card image or a text placeholder, at the given bounds.
  _drawCardAt(card, x, y, w, h) {
    const ctx = this.context;
    const GV  = GameVisualisation;
    const img = this._cardSourceImage(card.card_type);
    if (img.complete && img.naturalWidth > 0) {
      ctx.drawImage(img, x, y, w, h);
    } else {
      const fs = Math.round(h * 0.12);
      ctx.fillStyle = GV.CARD_BACKGROUND_COLOUR;
      ctx.fillRect(x, y, w, h);
      ctx.font = `${fs}px ${GV.MENU_FONT}`;
      ctx.fillStyle = GV.CARD_TEXT_COLOUR;
      const title = GV.CARD_TITLES[card.card_type] || '';
      const body  = GV.CARD_TEXTS[card.card_type]  || card.card_type;
      ctx.fillText(title, x + 4, y + fs);
      ctx.fillText(body,  x + 4, y + Math.round(h * GV.CARD_BODY_START) + fs);
    }
  }

  // ── Click dispatch ────────────────────────────────────────────────────────

  _handleClick(x, y) {
    if (!this.sendFn || !this.state) return;
    for (const area of this._clickableAreas) {
      if (x >= area.x && x <= area.x + area.w && y >= area.y && y <= area.y + area.h) {
        this.sendFn(area.action + '[00100]' + area.data);
        return;
      }
    }
  }

  // ── Top-level render ──────────────────────────────────────────────────────

  _render() {
    const ctx = this.context;
    const s   = this.state;

    // Reset per-render state
    this._clickableAreas = [];
    this.rightMenuY = 0;

    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    this._drawPlayArea();
    this._drawRoutes();
    this._drawTokens();
    this._drawMoveOptions();
    this._updateScoresTable();

    if (s.game_mode !== 'Beginner') {
      this._drawMoveCount();
    }
    this._drawToggleMenu();
    if (s.game_mode !== 'Beginner') {
      this._drawChestTiles();
      this._drawTilePiles();
      this._drawDiscardPile();
    }
    this._updateCardsPanel();

    this._drawUndoButton();
    this._drawPrompt();
    this._drawOffersPanel();
    console.log(this._clickableAreas);
  }

  // ── Draw methods ──────────────────────────────────────────────────────────

  _drawPlayArea() {
    const ctx    = this.context;
    const s      = this.state;
    const border = Math.round(this.tileSize * GameVisualisation.TILE_BORDER);
    const size   = this.tileSize - border;

    for (const lonStr of Object.keys(s.play_area)) {
      const lon = Number(lonStr);
      for (const latStr of Object.keys(s.play_area[lonStr])) {
        const lat  = Number(latStr);
        const tile = s.play_area[lonStr][latStr];
        const x    = this._colToPixelX(lon) + Math.floor(border / 2);
        const y    = this._rowToPixelY(lat)  + Math.floor(border / 2);

        this._drawTileAt(tile, x, y, size);

        if (tile.dropped_wealth > 0) {
          const fontSize = Math.round(this.tileSize * GameVisualisation.TOKEN_FONT_SCALE);
          ctx.font      = `${fontSize}px ${GameVisualisation.MENU_FONT}`;
          ctx.textAlign = 'center';
          ctx.fillStyle = tile.tile_name.endsWith('t')
            ? GameVisualisation.WONDER_TEXT_COLOUR
            : GameVisualisation.PLAIN_TEXT_COLOUR;
          ctx.fillText(String(tile.dropped_wealth), x + size / 2, y + size / 2);
        }
      }
    }
    ctx.textAlign = 'left';
  }

  _drawMoveOptions() {
    const ctx = this.context;
    const s   = this.state;
    for (const [hType, coords] of Object.entries(s.highlights || {})) {
      const img = this._highlightImages[hType];
      for (const [lon, lat] of coords) {
        const px = this._colToPixelX(lon);
        const py = this._rowToPixelY(lat);
        if (img && img.complete && img.naturalWidth > 0) {
          ctx.drawImage(img, px, py, this.tileSize, this.tileSize);
        }
        // Register clickable area for every highlighted tile
        this._clickableAreas.push({
          x: px, y: py, w: this.tileSize, h: this.tileSize,
          action: 'COORDS',
          data: `${hType}[55555]${lon}[66666]${lat}`,
        });
      }
    }
  }

  _drawTokens() {
    const ctx = this.context;
    const s   = this.state;
    const playerIndex = {};
    s.players.forEach((name, i) => { playerIndex[name] = i; });

    for (const playerName of s.players) {
      const colour      = s.player_colours[playerName];
      const pOffset     = GameVisualisation.PLAYER_OFFSETS[playerIndex[playerName]];
      const labelColour = GameVisualisation.TOKEN_FONT_COLOURS[colour] || GameVisualisation.PLAIN_TEXT_COLOUR;
      const fontSize    = Math.round(this.tileSize * GameVisualisation.TOKEN_FONT_SCALE);
      ctx.font = `${fontSize}px ${GameVisualisation.MENU_FONT}`;

      (s.adventurers[playerName] || []).forEach((adv, advIdx) => {
        if (adv.longitude === null || adv.latitude === null) return;
        const aOffset = GameVisualisation.ADVENTURER_OFFSETS[advIdx] || [0, 0];
        const cx = this._colToPixelX(adv.longitude) + (pOffset[0] + aOffset[0]) * this.tileSize;
        const cy = this._rowToPixelY(adv.latitude)  + (pOffset[1] + aOffset[1]) * this.tileSize;

        ctx.beginPath();
        ctx.arc(cx, cy, this.tokenSize, 0, 2 * Math.PI);
        ctx.fillStyle = colour;
        ctx.fill();

        if (adv.pirate_token) {
          ctx.beginPath();
          ctx.arc(cx, cy, this.tokenSize, 0, 2 * Math.PI);
          ctx.strokeStyle = 'black';
          ctx.lineWidth   = this.outlineWidth;
          ctx.stroke();
        }

        const isViewed = playerName === s.viewed_player_name && advIdx === s.viewed_adventurer_index;
        if (isViewed) {
          ctx.beginPath();
          ctx.arc(cx, cy, this.tokenSize + this.outlineWidth, 0, 2 * Math.PI);
          ctx.strokeStyle = GameVisualisation.PLAIN_TEXT_COLOUR;
          ctx.lineWidth   = this.outlineWidth;
          ctx.stroke();
        }

        ctx.textAlign    = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle    = labelColour;
        ctx.fillText(String(advIdx + 1), cx, cy);
        ctx.textBaseline = 'alphabetic';
        ctx.textAlign    = 'left';

        // Clicking a non-viewed adventurer token focuses it
        if (!isViewed) {
          this._clickableAreas.push({
            x: cx - this.tokenSize, y: cy - this.tokenSize,
            w: 2 * this.tokenSize,  h: 2 * this.tokenSize,
            action: 'FOCUS',
            data: `${playerName}[55555]${advIdx}`,
          });
        }
      });

      for (const agent of (s.agents[playerName] || [])) {
        if (agent.longitude === null || agent.latitude === null) continue;
        const aOff    = GameVisualisation.AGENT_OFFSET;
        const ax      = this._colToPixelX(agent.longitude) + aOff[0] * this.tileSize;
        const ay      = this._rowToPixelY(agent.latitude)  + aOff[1] * this.tileSize;
        const agentSz = GameVisualisation.AGENT_SCALE * this.tokenSize;

        if (agent.is_dispossessed) {
          ctx.strokeStyle = colour;
          ctx.lineWidth   = this.outlineWidth;
          ctx.strokeRect(ax, ay, agentSz, agentSz);
        } else {
          ctx.fillStyle = colour;
          ctx.fillRect(ax, ay, agentSz, agentSz);
        }
        ctx.fillStyle = labelColour;
        ctx.fillText(String(agent.wealth), ax + this.tokenSize / 2, ay + this.tokenSize / 2);
      }
    }
    ctx.lineWidth = 1;
  }

  _drawRoutes() {
    const ctx = this.context;
    const s   = this.state;
    const playerIndex = {};
    s.players.forEach((name, i) => { playerIndex[name] = i; });

    for (const playerName of s.players) {
      const colour  = s.player_colours[playerName];
      const pOffset = GameVisualisation.PLAYER_OFFSETS[playerIndex[playerName]];

      (s.adventurers[playerName] || []).forEach((adv, advIdx) => {
        const aOffset  = GameVisualisation.ADVENTURER_OFFSETS[advIdx] || [0, 0];
        const combined = [pOffset[0] + aOffset[0], pOffset[1] + aOffset[1]];
        const totalLen = Math.max((adv.route || []).length, 1);

        if (adv.route && adv.route.length > 1) {
          ctx.strokeStyle = colour;
          ctx.setLineDash([4, 4]);
          for (let i = 1; i < adv.route.length; i++) {
            ctx.lineWidth = Math.max(Math.ceil(GameVisualisation.ROUTE_THICKNESS * i / totalLen), 1);
            ctx.beginPath();
            ctx.moveTo(
              this._colToPixelX(adv.route[i - 1][0]) + combined[0] * this.tileSize,
              this._rowToPixelY(adv.route[i - 1][1]) + combined[1] * this.tileSize,
            );
            ctx.lineTo(
              this._colToPixelX(adv.route[i][0]) + combined[0] * this.tileSize,
              this._rowToPixelY(adv.route[i][1]) + combined[1] * this.tileSize,
            );
            ctx.stroke();
          }
          ctx.setLineDash([]);
        }

        if (adv.turn_route && adv.turn_route.length > 1) {
          ctx.strokeStyle = colour;
          ctx.setLineDash([]);
          const offset = totalLen - (adv.turn_route || []).length;
          for (let i = 1; i < adv.turn_route.length; i++) {
            ctx.lineWidth = Math.max(
              Math.ceil(GameVisualisation.ROUTE_THICKNESS * (offset + i) / totalLen), 1,
            );
            ctx.beginPath();
            ctx.moveTo(
              this._colToPixelX(adv.turn_route[i - 1][0]) + combined[0] * this.tileSize,
              this._rowToPixelY(adv.turn_route[i - 1][1]) + combined[1] * this.tileSize,
            );
            ctx.lineTo(
              this._colToPixelX(adv.turn_route[i][0]) + combined[0] * this.tileSize,
              this._rowToPixelY(adv.turn_route[i][1]) + combined[1] * this.tileSize,
            );
            ctx.stroke();
          }
        }
      });
    }
    ctx.lineWidth = 1;
    ctx.setLineDash([]);
  }

  _updateScoresTable() {
    const s        = this.state;
    const el       = this._scoresEl;
    const GV       = GameVisualisation;
    const fontSize = Math.round(this.canvas.height * GV.SCORES_FONT_SCALE);
    const pad      = Math.max(1, Math.round(fontSize * 0.2));
    const ROW      = fontSize + 2 * pad;
    const esc = t => String(t)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');

    const maxAdvs = Math.max(0, ...s.players.map(n => (s.adventurers[n] || []).length));
    const colSpan = 2 + maxAdvs;
    const th      = `padding:${pad}px ${pad * 2}px;color:white;font-weight:bold;border-bottom:1px solid #888`;

    let advHeaders = '';
    for (let i = 1; i <= maxAdvs; i++) advHeaders += `<th style="${th}">#${i}</th>`;

    let rows = `<tr>
      <td colspan="${colSpan}" style="padding:${pad}px ${pad * 2}px;color:white">Turn ${s.turn}</td>
    </tr>
    <tr>
      <th style="${th}">Player</th>
      <th style="${th}">Vault</th>
      ${advHeaders}
    </tr>`;
    let rowCount = 2;

    for (const playerName of s.players) {
      const colour    = s.player_colours[playerName];
      const vault     = s.player_wealths[playerName];
      const advs      = s.adventurers[playerName] || [];
      const isCurrent = playerName === s.current_player_name;
      const ul        = isCurrent ? 'text-decoration:underline' : '';
      const cell      = `color:${esc(colour)};padding:${pad}px ${pad * 2}px;${ul}`;

      let name = esc(playerName);
      if (playerName === s.winning_player) name += `&nbsp;(+${s.wealth_difference})`;

      let advCells = advs.map(adv => `<td style="${cell}">${adv.wealth}</td>`).join('');
      for (let i = advs.length; i < maxAdvs; i++) advCells += `<td></td>`;

      rows += `<tr data-player="${esc(playerName)}" data-adv="0" style="cursor:pointer">
        <td style="${cell}">${name}</td>
        <td style="${cell}">${vault}</td>
        ${advCells}
      </tr>`;
      rowCount++;
    }

    el.innerHTML = `<table style="border-collapse:collapse;font-family:sans-serif;font-size:${fontSize}px;line-height:${ROW}px;pointer-events:auto">${rows}</table>`;
    this.scoresBottomY = rowCount * ROW;

    el.querySelectorAll('tr[data-player]').forEach(row => {
      row.addEventListener('pointerdown', e => {
        e.stopPropagation();
        if (this.sendFn) {
          this.sendFn(`FOCUS[00100]${row.dataset.player}[55555]${row.dataset.adv}`);
        }
      });
    });
  }

  _updateCardsPanel() {
    const s   = this.state;
    const el  = this._cardsEl;
    const GV  = GameVisualisation;
    const esc = t => String(t)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;').replace(/"/g,'&quot;');

    const fontSize = Math.round(this.canvas.height * GV.SCORES_FONT_SCALE);
    const pad      = Math.max(1, Math.round(fontSize * 0.2));
    const cardW    = this.playAreaStart;
    const cardH    = Math.round(cardW * this.CARD_RATIO);
    const headerH  = Math.round(cardH * GV.CARD_HEADER_SHARE);

    el.style.top    = this.scoresBottomY + 'px';
    el.style.width  = cardW + 'px';
    el.style.height = (this.canvas.height - this.scoresBottomY) + 'px';

    if (s.game_mode !== 'Advanced') { el.innerHTML = ''; return; }

    const viewedAdv = (s.adventurers[s.viewed_player_name] || [])[s.viewed_adventurer_index] || null;
    if (!viewedAdv) { el.innerHTML = ''; return; }

    const label = (text, colour) =>
      `<div style="padding:${pad}px ${pad * 2}px;font-family:sans-serif;font-size:${fontSize}px;color:${esc(colour || 'white')}">${text}</div>`;

    const cardImg = (cardType, h, action, data) => {
      const title    = esc(GV.CARD_TITLES[cardType] || '');
      const body     = esc(GV.CARD_TEXTS[cardType]  || cardType);
      const filename = this._cardFilename(cardType);
      return `<div style="height:${h}px;overflow:hidden;cursor:pointer;flex-shrink:0"
                   data-action="${action}" data-data="${esc(data)}">
        <img src="${GV.CARDS_PATH}${esc(filename)}"
             data-title="${title}" data-body="${body}"
             style="width:100%;height:${cardH}px;object-fit:contain;display:block">
      </div>`;
    };

    let html = '';

    const cadreCard = (s.assigned_cadres || {})[s.viewed_player_name];
    if (cadreCard) {
      const colour = s.player_colours[s.viewed_player_name] || 'white';
      html += label(`${esc(s.viewed_player_name)}'s Culture card:`, colour);
      html += cardImg(cadreCard.card_type, headerH, 'CARDSEL', 'cadre');
    }

    const hasCards = viewedAdv.character_card
                  || (viewedAdv.discovery_cards && viewedAdv.discovery_cards.length > 0);
    if (hasCards) {
      html += label(`Adventurer #${(s.viewed_adventurer_index || 0) + 1} cards:`);
      (viewedAdv.discovery_cards || []).forEach((card, idx) => {
        html += cardImg(card.card_type, headerH, 'CARDSEL', String(idx));
      });
      if (viewedAdv.character_card) {
        html += cardImg(viewedAdv.character_card.card_type, cardH, 'CHARSEL', '');
      }
    }

    el.innerHTML = html;

    // Fallback: replace broken card images with text placeholders
    el.querySelectorAll('img').forEach(img => {
      const showFallback = () => {
        const title = img.dataset.title;
        const body  = img.dataset.body;
        img.parentElement.innerHTML =
          `<div style="background:#fff;padding:4px;font-size:11px;color:#000;height:100%;box-sizing:border-box;overflow:hidden">
             <strong>${title}</strong><br><small>${body}</small>
           </div>`;
      };
      img.addEventListener('error', showFallback);
      if (img.complete && img.naturalWidth === 0) showFallback();
    });

    // // Click handlers
    // el.querySelectorAll('[data-action]').forEach(div => {
    //   div.addEventListener('pointerdown', e => {
    //     e.stopPropagation();
    //     if (this.sendFn) this.sendFn(`${div.dataset.action}[00100]${div.dataset.data}`);
    //   });
    // });
  }

  _drawOffersPanel() {
    const s   = this.state;
    const ctx = this.context;
    const GV  = GameVisualisation;

    const offeredCards = s.offered_cards && s.offered_cards.length > 0 ? s.offered_cards : null;
    const offeredTiles = !offeredCards && s.offered_tiles && s.offered_tiles.length > 0 ? s.offered_tiles : null;
    const items   = offeredCards || offeredTiles;
    const isCards = !!offeredCards;
    if (!items) return;

    const W = this.canvas.width;
    const H = this.canvas.height;

    // Dim the whole canvas
    ctx.fillStyle = 'rgba(0,0,0,0.65)';
    ctx.fillRect(0, 0, W, H);

    const n      = items.length;
    const itemH  = Math.round(H * 0.5);
    const itemW  = isCards ? Math.round(itemH * 0.65) : itemH;
    const gap    = Math.round(W * 0.02);
    const totalW = n * itemW + (n - 1) * gap;
    const startX = Math.max(0, Math.round((W - totalW) / 2));
    const startY = Math.round((H - itemH) / 2);

    const fontSize = Math.round(H * GV.SCORES_FONT_SCALE);
    ctx.font      = `${fontSize}px ${GV.MENU_FONT}`;
    ctx.fillStyle = GV.PLAIN_TEXT_COLOUR;
    ctx.textAlign = 'center';
    ctx.fillText(isCards ? 'Choose a card:' : 'Choose a tile:', W / 2, startY - fontSize);
    ctx.textAlign = 'left';

    items.forEach((item, idx) => {
      const x = startX + idx * (itemW + gap);
      const y = startY;

      if (isCards) {
        const cardType = item.card_type;
        const filename = this._cardFilename(cardType);
        const src      = GV.CARDS_PATH + filename;
        if (!this._offerImages[src]) {
          const img = new Image();
          img.src = src;
          img.onload = () => this._render();
          this._offerImages[src] = img;
        }
        const img = this._offerImages[src];
        if (img.complete && img.naturalWidth > 0) {
          ctx.drawImage(img, x, y, itemW, itemH);
        } else {
          ctx.fillStyle = GV.CARD_BACKGROUND_COLOUR;
          ctx.fillRect(x, y, itemW, itemH);
          const fs2 = Math.max(10, Math.round(itemH * 0.08));
          ctx.font      = `${fs2}px ${GV.MENU_FONT}`;
          ctx.fillStyle = GV.CARD_TEXT_COLOUR;
          ctx.fillText(GV.CARD_TITLES[cardType] || cardType, x + 4, y + fs2 + 4);
          ctx.fillText(GV.CARD_TEXTS[cardType] || '', x + 4, y + Math.round(itemH * 0.6));
          ctx.font = `${fontSize}px ${GV.MENU_FONT}`;
        }
      } else {
        this._drawTileAt(item, x, y, itemH);
      }

      ctx.strokeStyle = 'white';
      ctx.lineWidth   = 3;
      ctx.strokeRect(x, y, itemW, itemH);
      ctx.lineWidth   = 1;

      this._clickableAreas.unshift({ x, y, w: itemW, h: itemH, action: 'OFFERSEL', data: String(idx) });
    });
  }

  _drawMoveCount() {
    const ctx = this.context;
    const s   = this.state;
    const GV  = GameVisualisation;
    const h   = this.canvas.height;
    const fontSize = Math.round(h * GV.MENU_FONT_SCALE);
    ctx.font = `${fontSize}px ${GV.MENU_FONT}`;

    const x = this.rightMenuStart;
    let y = this.rightMenuY + fontSize;

    const viewedAdv = (s.adventurers[s.viewed_player_name] || [])[s.viewed_adventurer_index] || null;
    const isCurrentTurn = s.viewed_player_name === s.current_player_name
                       && s.viewed_adventurer_index === s.current_adventurer_index;

    let title, anyDirShare = 1, downwindShare = 1, anyDirCount = '', downwindCount = '';
    if (isCurrentTurn && viewedAdv && viewedAdv.max_upwind_moves != null) {
      const moved    = (viewedAdv.downwind_moves || 0) + (viewedAdv.upwind_moves || 0) + (viewedAdv.land_moves || 0);
      const maxAny   = viewedAdv.max_upwind_moves;
      const onlyDown = Math.max((viewedAdv.max_downwind_moves || 0) - maxAny, 0);
      const extraDown = Math.max(moved - maxAny, 0);
      anyDirShare   = maxAny > 0 ? Math.min(moved / maxAny, 1) : 1;
      downwindShare = onlyDown > 0 ? extraDown / onlyDown : 1;
      anyDirCount   = `${Math.max(maxAny - moved, 0)} / ${maxAny}`;
      downwindCount = `${Math.max(onlyDown - extraDown, 0)} / ${onlyDown}`;
      title = 'Moves until rest:';
    } else {
      title = `Not #${(s.viewed_adventurer_index || 0) + 1}'s turn`;
    }

    ctx.fillStyle = s.player_colours[s.viewed_player_name] || GV.PLAIN_TEXT_COLOUR;
    ctx.fillText(title, x, y);
    y += fontSize;

    const ts = this.menuTileSize;
    const drawMeter = (imgKey, mx, share, countText) => {
      const img = this._meterImages[imgKey];
      if (img && img.complete && img.naturalWidth > 0) {
        ctx.drawImage(img, mx, y, ts, ts);
      } else {
        ctx.fillStyle = '#444';
        ctx.fillRect(mx, y, ts, ts);
      }
      ctx.globalAlpha = 0.5;
      ctx.fillStyle = '#000';
      ctx.fillRect(mx, y, Math.round(share * ts), ts);
      ctx.globalAlpha = 1;
      ctx.font = `${fontSize}px ${GV.MENU_FONT}`;
      ctx.fillStyle = GV.PLAIN_TEXT_COLOUR;
      ctx.fillText(countText, mx, y + fontSize);
    };
    drawMeter('any_direction',  x,      anyDirShare,   anyDirCount);
    drawMeter('downwind_water', x + ts, downwindShare, downwindCount);

    this.rightMenuY = y + ts;
  }

  _drawToggleMenu() {
    const ctx = this.context;
    const s   = this.state;
    const GV  = GameVisualisation;
    const h   = this.canvas.height;
    const fontSize = Math.round(h * GV.MENU_FONT_SCALE);
    ctx.font = `${fontSize}px ${GV.MENU_FONT}`;

    const x = this.rightMenuStart;
    let y = this.rightMenuY + fontSize;

    ctx.fillStyle = GV.PLAIN_TEXT_COLOUR;
    ctx.fillText('Auto-Actions:', x, y);
    y += fontSize;

    const hs = this.menuHighlightSize;
    let hx = x;
    for (const hType of GV.TOGGLE_HIGHLIGHTS) {
      const img = this._highlightImages[hType];
      if (img && img.complete && img.naturalWidth > 0) {
        ctx.drawImage(img, hx, y, hs, hs);
      } else {
        ctx.strokeStyle = GV.PLAIN_TEXT_COLOUR;
        ctx.lineWidth = 1;
        ctx.strokeRect(hx, y, hs, hs);
      }
      this._clickableAreas.push({ x: hx, y, w: hs, h: hs, action: 'TOGGLE', data: hType });
      hx += hs;
    }
    y += hs + 4;

    // Route-visibility indicator: a coloured line per player whose routes are shown;
    // clicking anywhere in the toggle section toggles draw_all_routes
    const toggleTop = this.rightMenuY + fontSize * 2;
    this._clickableAreas.push({
      x, y: toggleTop, w: this.rightMenuWidth, h: hs,
      action: 'ROUTES', data: '',
    });

    for (const pName of s.players) {
      if (s.draw_all_routes || pName === s.current_player_name || pName === s.viewed_player_name) {
        ctx.strokeStyle = s.player_colours[pName] || GV.PLAIN_TEXT_COLOUR;
        ctx.lineWidth = 3;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + this.rightMenuWidth, y);
        ctx.stroke();
        y += 5;
      }
    }
    ctx.lineWidth = 1;

    this.rightMenuY = y;
  }

  _drawChestTiles() {
    const ctx = this.context;
    const s   = this.state;
    const GV  = GameVisualisation;
    const h   = this.canvas.height;
    const fontSize = Math.round(h * GV.MENU_FONT_SCALE);

    const viewedAdv = (s.adventurers[s.viewed_player_name] || [])[s.viewed_adventurer_index] || null;
    if (!viewedAdv || !viewedAdv.chest_tiles || viewedAdv.chest_tiles.length === 0) return;

    ctx.font = `${fontSize}px ${GV.MENU_FONT}`;
    const x = this.rightMenuStart;
    let y = this.rightMenuY + fontSize;

    ctx.fillStyle = s.player_colours[s.viewed_player_name] || GV.PLAIN_TEXT_COLOUR;
    ctx.fillText(`#${(s.viewed_adventurer_index || 0) + 1}'s chest maps:`, x, y);
    y += fontSize;

    const ts = this.menuTileSize;
    const border = Math.round(ts * GV.TILE_BORDER);
    const maxChest = viewedAdv.num_chest_tiles || viewedAdv.chest_tiles.length;
    const menuH = ts * Math.ceil(maxChest / GV.MENU_TILE_COLS);

    ctx.strokeStyle = GV.PLAIN_TEXT_COLOUR;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, this.rightMenuWidth, menuH);
    ctx.lineWidth = 1;

    viewedAdv.chest_tiles.forEach((tile, idx) => {
      const tx = x + (idx % GV.MENU_TILE_COLS) * ts;
      const ty = y + Math.floor(idx / GV.MENU_TILE_COLS) * ts;
      this._drawTileAt(tile, tx + border / 2, ty + border / 2, ts - border);
      ctx.strokeStyle = idx === viewedAdv.preferred_tile_num
        ? GV.CHEST_HIGHLIGHT_COLOUR : GV.PLAIN_TEXT_COLOUR;
      ctx.lineWidth = 2;
      ctx.strokeRect(tx, ty, ts, ts);
      ctx.lineWidth = 1;
      this._clickableAreas.push({ x: tx, y: ty, w: ts, h: ts, action: 'CHEST', data: String(idx) });
    });

    this.rightMenuY = y + menuH;
  }

  _drawTilePiles() {
    const ctx = this.context;
    const s   = this.state;
    const GV  = GameVisualisation;
    const h   = this.canvas.height;
    const fontSize = Math.round(h * GV.MENU_FONT_SCALE);
    ctx.font = `${fontSize}px ${GV.MENU_FONT}`;

    const x = this.rightMenuStart;
    let y = this.rightMenuY + fontSize;

    ctx.fillStyle = GV.PLAIN_TEXT_COLOUR;
    ctx.fillText('Maps to draw:', x, y);
    y += fontSize;

    const ts = this.menuTileSize;
    let hx = x;
    for (const [tileBack, pile] of Object.entries(s.tile_piles || {})) {
      const count = pile.tile_count;
      const total = (s.num_tiles || {})[tileBack] || count;
      const usedShare = total > 0 ? 1 - count / total : 1;

      ctx.fillStyle = tileBack === 'water' ? '#336699' : '#669933';
      ctx.fillRect(hx, y, ts, ts);
      ctx.globalAlpha = 0.5;
      ctx.fillStyle = '#000';
      ctx.fillRect(hx, y, ts, Math.round(usedShare * ts));
      ctx.globalAlpha = 1;
      ctx.font = `${fontSize}px ${GV.MENU_FONT}`;
      ctx.fillStyle = GV.PLAIN_TEXT_COLOUR;
      ctx.fillText(`${count}/${total}`, hx, y + fontSize);
      hx += ts;
    }

    this.rightMenuY = y + ts;
  }

  _drawDiscardPile() {
    const ctx = this.context;
    const s   = this.state;
    const GV  = GameVisualisation;
    const h   = this.canvas.height;
    const fontSize = Math.round(h * GV.MENU_FONT_SCALE);
    ctx.font = `${fontSize}px ${GV.MENU_FONT}`;

    const allDiscards = [];
    for (const pile of Object.values(s.discard_piles || {})) {
      allDiscards.push(...(pile.tiles || []));
    }
    if (allDiscards.length === 0) return;

    const x = this.rightMenuStart;
    let y = this.rightMenuY + fontSize;

    ctx.fillStyle = GV.PLAIN_TEXT_COLOUR;
    ctx.fillText('Failed map draws:', x, y);
    y += fontSize;

    const ts = this.menuTileSize;
    const border = Math.round(ts * GV.TILE_BORDER);
    [...allDiscards].reverse().forEach((tile, idx) => {
      const tx = x + (idx % GV.MENU_TILE_COLS) * ts;
      const ty = y + Math.floor(idx / GV.MENU_TILE_COLS) * ts;
      this._drawTileAt(tile, tx + border / 2, ty + border / 2, ts - border);
      ctx.strokeStyle = GV.PLAIN_TEXT_COLOUR;
      ctx.lineWidth = 2;
      ctx.strokeRect(tx, ty, ts, ts);
      ctx.lineWidth = 1;
    });

    this.rightMenuY = y + Math.ceil(allDiscards.length / GV.MENU_TILE_COLS) * ts;
  }

  _drawCards() {
    const ctx = this.context;
    const s   = this.state;
    const GV  = GameVisualisation;
    const h   = this.canvas.height;
    const cardW = this.playAreaStart;
    const fontSize = Math.round(h * GV.SCORES_FONT_SCALE);
    ctx.font = `${fontSize}px ${GV.MENU_FONT}`;

    const viewedAdv = (s.adventurers[s.viewed_player_name] || [])[s.viewed_adventurer_index] || null;
    if (!viewedAdv) return;

    let y = this.scoresBottomY + fontSize;
    const cardH = Math.round(cardW * 0.6);

    // Cadre / Culture card (just header strip)
    const cadreCard = (s.assigned_cadres || {})[s.viewed_player_name];
    if (cadreCard) {
      ctx.fillStyle = s.player_colours[s.viewed_player_name] || GV.PLAIN_TEXT_COLOUR;
      ctx.fillText(`${s.viewed_player_name}'s Culture card:`, 0, y);
      y += fontSize;
      this._drawCardAt(cadreCard, 0, y, cardW, cardH);
      const headerH = Math.round(cardH * GV.CARD_HEADER_SHARE);
      this._clickableAreas.push({ x: 0, y, w: cardW, h: headerH, action: 'CARDSEL', data: 'cadre' });
      y += headerH;
    }

    // Character and discovery cards
    const hasCards = viewedAdv.character_card
                  || (viewedAdv.discovery_cards && viewedAdv.discovery_cards.length > 0);
    if (hasCards) {
      ctx.fillStyle = GV.PLAIN_TEXT_COLOUR;
      ctx.fillText(`Adventurer #${(s.viewed_adventurer_index || 0) + 1} cards:`, 0, y);
      y += fontSize;

      // Discovery cards — stacked so only header strip shows except for last
      (viewedAdv.discovery_cards || []).forEach((card, idx) => {
        this._drawCardAt(card, 0, y, cardW, cardH);
        const headerH = Math.round(cardH * GV.CARD_HEADER_SHARE);
        this._clickableAreas.push({ x: 0, y, w: cardW, h: headerH, action: 'CARDSEL', data: String(idx) });
        y += headerH;
      });

      // Character card — shown in full at the bottom
      if (viewedAdv.character_card) {
        this._drawCardAt(viewedAdv.character_card, 0, y, cardW, cardH);
        this._clickableAreas.push({ x: 0, y, w: cardW, h: cardH, action: 'CHARSEL', data: '' });
      }
    }
  }

  _drawUndoButton() {
    const ctx      = this.context;
    const s        = this.state;
    const h        = this.canvas.height;
    const fontSize = Math.round(h * GameVisualisation.MENU_FONT_SCALE);
    ctx.font = `${fontSize}px ${GameVisualisation.MENU_FONT}`;

    let label;
    if (s.undo_agreed) {
      ctx.fillStyle = GameVisualisation.ACCEPT_UNDO_COLOUR;
      label = 'Reject undo';
    } else if (s.undo_asked) {
      ctx.fillStyle = GameVisualisation.ACCEPT_UNDO_COLOUR;
      label = 'Accept undo?';
    } else {
      ctx.fillStyle = GameVisualisation.PLAIN_TEXT_COLOUR;
      label = 'Undo turn?';
    }
    const metrics = ctx.measureText(label);
    const bx = this.canvas.width - metrics.width - 4;
    const by = h - fontSize - 4;
    ctx.fillText(label, bx, h - 4);
    this._clickableAreas.push({ x: bx, y: by, w: metrics.width, h: fontSize + 4, action: 'UNDO', data: '' });
  }

  _drawPrompt() {
    const ctx      = this.context;
    const s        = this.state;
    if (!s.prompt) return;
    const h        = this.canvas.height;
    const fontSize = Math.round(h * GameVisualisation.PROMPT_FONT_SCALE);
    ctx.font      = `${fontSize}px ${GameVisualisation.MENU_FONT}`;
    ctx.fillStyle = s.player_colours[s.current_player_name] || GameVisualisation.PLAIN_TEXT_COLOUR;
    ctx.fillText(
      s.prompt,
      this.playAreaStart + GameVisualisation.PROMPT_POSITION[0] * this.canvas.width,
      GameVisualisation.PROMPT_POSITION[1] * h,
    );
  }
}
