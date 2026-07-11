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
  static INN_OFFSET        = [0.5, 0.5];
  static ADVENTURER_OFFSETS  = [[0.0, 0.0], [0.1, -0.1], [-0.1, 0.1], [-0.1, -0.1], [0.1, 0.1]];
  static TILE_BORDER         = 0.02;
  static LEFT_MENU_SCALE     = 0.13;
  static RIGHT_MENU_SCALE    = 0.13;
  static MENU_TILE_COLS      = 2;
  static MENU_FONT_SCALE   = 0.04;
  static OFFER_SCALE         = 0.15;
  static ROUTE_THICKNESS     = 4.0;
  static TOKEN_SCALE         = 0.15;
  static INN_SCALE         = 1.75;
  static TOKEN_OUTLINE_SCALE = 0.25;
  static TOKEN_FONT_SCALE    = 0.2;
  static TOKEN_FONT_COLOURS  = { yellow: 'black' };
  static SCORES_POSITION     = [0.0, 0.0];
  static SCORES_FONT_SCALE   = 0.04;
  static CARD_HEADER_SHARE   = 0.15;
  static CARD_BODY_START     = 0.7;
  static CARD_RATIO          = 1.75;
  static PROMPT_POSITION     = [0.0, 0.95];
  static PROMPT_FONT_SCALE   = 0.04;
  static TOGGLE_HIGHLIGHTS   = ['buy_rest', 'attack', 'rest'];

  static HIGHLIGHT_TOOLTIPS = {
    move:           'Move adventurer here',
    abandon:        'Abandon expedition at this city',
    buy:            'Act here',
    attack:         'Attack here',
    rest:           'Rest at own Inn here',
    buy_rest:       'Pay to rest at Inn here',
    move_inn:     'Move Inn from here',
    inn_transfer: 'Transfer Silk to Inn here',
    invalid:        'Cannot move here',
  };

  static TOGGLE_TOOLTIPS = {
    buy_rest: 'Auto: always pay to rest at Inns',
    attack:   'Auto: always attack enemy adventurers',
    rest:     'Auto: always rest for free at own Inns',
  };

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
    move_inn:     './img/highlights/option_valid_move.png',
    inn_transfer: './img/highlights/option_buy.png',
  };

  // ── Card display text (mirrored from live_visuals.py) ────────────────────
  static CARD_TITLES = {
    'companion':     "Companion",
    'cul+rests':     "The Intrepid Academy",
    'cul+transfers': "The Great Company",
    'cul+earning':   "The Merchants' Guild",
    'cul+arrest':    "The Harbour Authority",
    'cul+refurnish': "The Privateer Brethren",
    'cul+pool':      "Order of the Lightbrary",
  };
  static CARD_TEXTS = {
    'companion':     "Scales trade earnings and rest costs by one character.",
    'chr+inns':    "Can place and immediately rest with Inns on existing tiles, for 3 silks.",
    'chr+attack':    "Needs only win or draw Rock, Paper, Scissors to attack successfully.",
    'chr+bank':      "Can transfer silks to your Inns when visiting anyone's Inn.",
    'chr+damage':    "Successfully attacked Adventurers are returned to their last city, and Inns are fully removed.",
    'chr+defence':   "Attacking opponents have to win Rock, Paper, Scissors twice to succeed.",
    'chr+downwind':  "Can move up to three times riding the wind after tiring, each turn and after resting.",
    'chr+upwind':    "Can move three times in any direction before getting tired, then one riding the wind, each turn or after resting.",
    'chr+maps':      "Carries up to three map tiles in Chest.",
    'man+inns':    "This Adventurer can place Inns on existing tiles and immediately rest with them, for 3 silks.",
    'man+attack':    "This Adventurer needs only win or draw Rock, Paper, Scissors to attack successfully.",
    'man+bank':      "This Adventurer can transfer silks to your Inns when visiting anyone's Inn.",
    'man+damage':    "Successfully attacked Adventurers are returned to their last city, and Inns are removed.",
    'man+defence':   "Attacking opponents have to win an extra round of Rock, Paper, Scissors to succeed.",
    'man+downwind':  "This Adventurer can move once more riding the wind after tiring, each turn and after resting.",
    'man+upwind':    "This Adventurer can move once more before tiring, rather than after, each turn and after resting.",
    'man+maps':      "This Adventurer carries an extra map tile in their chest.",
    'cul+rests':     "Your Adventurers can rest with other Adventurers like Inns. Draw 3 Adventurers.",
    'cul+transfers': "Silks earned by your Inns goes to your Vault. Draw 3 Manuscripts.",
    'cul+earning':   "Your Inns earn 1 silks when opponents trade on their tile. Draw 3 Manuscripts.",
    'cul+arrest':    "Your Inns try to arrest pirates landing on their tile. Draw 3 Adventurers.",
    'cul+refurnish': "Your Adventurers can lose the pirate token by resting. Draw 3 Adventurers.",
    'cul+pool':      "Anyone's Inns can swap your Adventures' maps for 1 silks. Draw 3 Manuscripts.",
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

    // Card type and id currently shown in full-screen preview (null = none)
    this._previewedCardType = null;
    this._previewedCardId   = null;

    // Route display mode: 'focus' (current/viewed player only), 'all', or 'none'
    this._routesMode = 'all';

    // Image caches
    this._tileSourceImages = {};  // filename → HTMLImageElement
    this._tileFilenames = {};  // tile_id → deterministically chosen filename
    this._highlightImages  = {};  // highlight_type → HTMLImageElement
    this._meterImages      = {};  // meter_name → HTMLImageElement
    this._cardImages       = {};  // filename → HTMLImageElement
    this._offerImages      = {};  // src url → HTMLImageElement (for offer overlay)

    // tile_name → [filename, ...] populated by _fetchTileManifest()
    this._tileVariants = {};
    // card_type → [filename, ...] populated by _fetchCardManifest()
    this._cardVariants = {};
    // card_type → chosen filename (fallback when server card_images mapping is absent)
    this._cardFilenames = {};

    // Optional send callback — set by caller after construction (e.g. gameVis.sendFn = send)
    this.sendFn = null;

    // Move timer — animated by a setInterval when a deadline is active
    this._timerInterval = null;
    this.moveDeadline   = null;
    this.moveTimerLimit = 30;

    // Asset loading progress
    this._pendingAssets        = 0;
    this._totalAssetsRequested = 0;
    this._totalAssetsLoaded    = 0;
    this._gameReady            = false;  // true once all initial assets are loaded

    // Wrap canvas in a relative container so the scores overlay can sit on top
    const wrapper = document.createElement('div');
    wrapper.style.cssText = 'position:relative;display:block;line-height:0';
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
      'position:absolute;left:0;overflow:hidden;pointer-events:auto;box-sizing:border-box';
    wrapper.appendChild(this._cardsEl);

    // Floating tooltip — follows cursor, hidden by default
    this._tooltipEl = document.createElement('div');
    this._tooltipEl.style.cssText =
      'position:absolute;display:none;pointer-events:none;z-index:20;' +
      'background:rgba(0,0,0,0.78);color:#fff;font:12px sans-serif;' +
      'padding:3px 7px;border-radius:3px;max-width:200px;white-space:normal;line-height:1.3';
    wrapper.appendChild(this._tooltipEl);

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

    // Tooltip hover — check _clickableAreas on every move
    this.canvas.addEventListener('pointermove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this._handleHover(
        Math.round(e.clientX - rect.left),
        Math.round(e.clientY - rect.top),
        e.clientX, e.clientY,
      );
    });
    this.canvas.addEventListener('pointerleave', () => {
      this._tooltipEl.style.display = 'none';
    });
  }

  // ── Public entry point ────────────────────────────────────────────────────

  applyState(state) {
    this.state = state;
    // Update timer state before _render() so _drawTimerBar() sees the new deadline
    this.moveDeadline   = state.move_deadline || null;
    this.moveTimerLimit = state.move_timer_limit || 30;
    this._recalcLayout();
    this._render();

    if (this._timerInterval) {
      clearInterval(this._timerInterval);
      this._timerInterval = null;
    }
    if (this.moveDeadline && this.moveDeadline > Date.now()) {
      this._timerInterval = setInterval(() => {
        if (!this.moveDeadline || Date.now() >= this.moveDeadline) {
          clearInterval(this._timerInterval);
          this._timerInterval = null;
        }
        this._render();
      }, 500);
    }

    // If all assets already cached (e.g. page refresh), signal ready immediately
    if (!this._gameReady && this._pendingAssets === 0 && this.sendFn) {
      this._gameReady = true;
      this.sendFn('READY[00100]');
    }
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
    this._pendingAssets++; this._totalAssetsRequested++;
    fetch(GameVisualisation.TILE_PATH + 'tile_manifest.json')
      .then(r => r.json())
      .then(manifest => {
        this._tileVariants = manifest;
        this._tileSourceImages = {};
        this._tileFilenames = {};
        if (this.state) this._render();
        this._onAssetLoaded();
      })
      .catch(() => { this._onAssetLoaded(); });
  }

  _fetchCardManifest() {
    this._pendingAssets++; this._totalAssetsRequested++;
    fetch(GameVisualisation.CARDS_PATH + 'card_manifest.json')
      .then(r => r.json())
      .then(manifest => {
        this._cardVariants = manifest;
        this._cardFilenames = {};  // evict cached selections so new variants are picked
        if (this.state) this._render();
        this._onAssetLoaded();
      })
      .catch(() => { this._onAssetLoaded(); });
  }

  // Returns the filename for a specific card instance, using the server-assigned mapping when
  // available and falling back to a random per-type selection from the manifest otherwise.
  _cardFilename(cardId, cardType) {
    const serverMap = this.state && this.state.card_images;
    if (serverMap && serverMap[cardId]) return serverMap[cardId];
    if (!this._cardFilenames[cardType]) {
      const variants = this._cardVariants[cardType];
      this._cardFilenames[cardType] = variants && variants.length
        ? variants[Math.floor(Math.random() * variants.length)]
        : cardType + '.png';
    }
    return this._cardFilenames[cardType];
  }

  // Returns a deterministic filename for a tile instance based on a hash of its tile_id.
  // The same tile_id always maps to the same variant on every client, requiring no server coordination.
  _tileFilename(tile) {
    const id = tile.tile_id;
    if (this._tileFilenames[id]) return this._tileFilenames[id];
    const variants = this._tileVariants[tile.tile_name];
    let filename;
    if (!variants || !variants.length) {
      filename = tile.tile_name + '.jpg';
    } else if (!id) {
      filename = variants[0];
    } else {
      const idStr = String(id);
      let hash = 0;
      for (let i = 0; i < idStr.length; i++) {
        hash = (hash * 31 + idStr.charCodeAt(i)) >>> 0;
      }
      filename = variants[hash % variants.length];
    }
    this._tileFilenames[id] = filename;
    return filename;
  }

  // Returns a cached HTMLImageElement for a tile object, keyed by filename.
  _tileSourceImage(tile) {
    const filename = this._tileFilename(tile);
    if (!this._tileSourceImages[filename]) {
      this._pendingAssets++; this._totalAssetsRequested++;
      const img = new Image();
      img.src = GameVisualisation.TILE_PATH + filename;
      img.onload  = () => { this._onAssetLoaded(); this._render(); };
      img.onerror = () => { this._onAssetLoaded(); };
      this._tileSourceImages[filename] = img;
    }
    return this._tileSourceImages[filename];
  }

  // Returns a cached HTMLImageElement for a filename, loading on first use.
  _cardImage(filename) {
    if (!this._cardImages[filename]) {
      this._pendingAssets++; this._totalAssetsRequested++;
      const img = new Image();
      img.src = GameVisualisation.CARDS_PATH + filename;
      img.onload  = () => { this._onAssetLoaded(); this._render(); };
      img.onerror = () => { this._onAssetLoaded(); };
      this._cardImages[filename] = img;
    }
    return this._cardImages[filename];
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
      const n       = tile.tile_name;
      const isCity   = n === 'home_city' || n === 'mythical_city';
      const isWonder = !isCity && n[4] === 't';
      const WATER = '#336699', LAND = '#669933', WHITE = '#ffffff';
      const half = size / 2;

      if (isCity) {
        ctx.fillStyle = n === 'home_city' ? WATER : LAND;
        ctx.fillRect(-half, -half, size, size);
      } else {
        const edgeTop    = n[3] === 't';  // downwind_anti  = North in NE baseline
        const edgeRight  = n[2] === 't';  // downwind_clock = East
        const edgeBottom = n[1] === 't';  // upwind_anti    = South
        const edgeLeft   = n[0] === 't';  // upwind_clock   = West
        const tris = [
          { pts: [[ 0, 0], [-half, -half], [ half, -half]], water: edgeTop    },
          { pts: [[ 0, 0], [ half, -half], [ half,  half]], water: edgeRight  },
          { pts: [[ 0, 0], [ half,  half], [-half,  half]], water: edgeBottom },
          { pts: [[ 0, 0], [-half,  half], [-half, -half]], water: edgeLeft   },
        ];
        for (const { pts, water } of tris) {
          ctx.beginPath();
          ctx.moveTo(...pts[0]);
          ctx.lineTo(...pts[1]);
          ctx.lineTo(...pts[2]);
          ctx.closePath();
          ctx.fillStyle = water ? WATER : LAND;
          ctx.fill();
        }
      }

      // Corner indicator — top-right in NE baseline = actual downwind corner after rotation
      const pad  = size * 0.05;
      const tip  = { x:  half - pad,      y: -half + pad      };
      const tail = { x:  half - pad * 7,  y: -half + pad * 7  };
      const aw   = size * 0.06;
      const cr   = size * 0.18;
      const cx   = half - pad * 4;
      const cy   = -half + pad * 4;

      if (isCity) {
        const outerR = cr, innerR = cr * 0.38;
        ctx.beginPath();
        for (let i = 0; i < 16; i++) {
          const angle = (i * Math.PI / 8) - Math.PI / 2;
          const r = i % 2 === 0 ? outerR : innerR;
          const px = cx + Math.cos(angle) * r;
          const py = cy + Math.sin(angle) * r;
          i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fillStyle = WHITE;
        ctx.fill();
      } else if (isWonder) {
        ctx.beginPath();
        ctx.arc(cx, cy, cr, 0, Math.PI * 2);
        ctx.fillStyle = WHITE;
        ctx.fill();

        const dx = (tip.x - tail.x) / Math.hypot(tip.x - tail.x, tip.y - tail.y);
        const dy = (tip.y - tail.y) / Math.hypot(tip.x - tail.x, tip.y - tail.y);
        const al = cr * 0.55, hw = cr * 0.28;
        const at = { x: cx + dx * al, y: cy + dy * al };
        const ab = { x: cx - dx * al, y: cy - dy * al };

        ctx.strokeStyle = WATER;
        ctx.lineWidth = size * 0.03;
        ctx.beginPath();
        ctx.moveTo(ab.x, ab.y);
        ctx.lineTo(at.x - dx * al * 0.5, at.y - dy * al * 0.5);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(at.x, at.y);
        ctx.lineTo(at.x - dx * hw * 1.4 + dy * hw, at.y - dy * hw * 1.4 - dx * hw);
        ctx.lineTo(at.x - dx * hw * 1.4 - dy * hw, at.y - dy * hw * 1.4 + dx * hw);
        ctx.closePath();
        ctx.fillStyle = WATER;
        ctx.fill();
      } else {
        const dx = (tip.x - tail.x) / Math.hypot(tip.x - tail.x, tip.y - tail.y);
        const dy = (tip.y - tail.y) / Math.hypot(tip.x - tail.x, tip.y - tail.y);

        ctx.strokeStyle = WHITE;
        ctx.lineWidth = size * 0.03;
        ctx.beginPath();
        ctx.moveTo(tail.x, tail.y);
        ctx.lineTo(tip.x - dx * aw * 1.5, tip.y - dy * aw * 1.5);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(tip.x, tip.y);
        ctx.lineTo(tip.x - dx * aw * 2 + dy * aw, tip.y - dy * aw * 2 - dx * aw);
        ctx.lineTo(tip.x - dx * aw * 2 - dy * aw, tip.y - dy * aw * 2 + dx * aw);
        ctx.closePath();
        ctx.fillStyle = WHITE;
        ctx.fill();
      }
    }
    ctx.restore();
  }

  // Draws a card image or a text placeholder, at the given bounds.
  _drawCardAt(card, x, y, w, h) {
    const ctx = this.context;
    const GV  = GameVisualisation;
    const img = this._cardImage(this._cardFilename(card.card_id, card.card_type));
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

  _pixelToTile(x, y) {
    const lon = Math.floor((x - this.playAreaStart) / this.tileSize) - this.origin[0];
    const lat = this.dimensions[1] - this.origin[1] - 1 - Math.floor(y / this.tileSize);
    return [lon, lat];
  }

  _findRouteTarget(x, y) {
    const s = this.state;
    if (!s || this._routesMode === 'none') return null;
    const [lon, lat] = this._pixelToTile(x, y);
    for (const playerName of s.players) {
      if (this._routesMode === 'focus'
          && playerName !== s.current_player_name
          && playerName !== s.viewed_player_name) continue;
      const advs = s.adventurers[playerName] || [];
      for (let advIdx = 0; advIdx < advs.length; advIdx++) {
        const route = advs[advIdx].route || [];
        for (const [rLon, rLat] of route) {
          if (rLon === lon && rLat === lat) {
            return { player: playerName, advIdx, lon, lat };
          }
        }
      }
    }
    return null;
  }

  _handleClick(x, y) {
    if (!this.sendFn || !this.state || !this._gameReady) return;
    // Any canvas click dismisses the card preview
    if (this._previewedCardType !== null) {
      this._previewedCardType = null;
      this._previewedCardId   = null;
      this._render();
      return;
    }
    for (const area of this._clickableAreas) {
      if (x >= area.x && x <= area.x + area.w && y >= area.y && y <= area.y + area.h) {
        if (area.action === 'ROUTES') {
          const modes = ['focus', 'all', 'none'];
          this._routesMode = modes[(modes.indexOf(this._routesMode) + 1) % modes.length];
          this._render();
        } else {
          this.sendFn(area.action + '[00100]' + area.data);
        }
        return;
      }
    }
    // Fallback: play area click — check for a route tile first, otherwise generic play signal
    if (x >= this.playAreaStart && x < this.rightMenuStart) {
      const rt = this._findRouteTarget(x, y);
      if (rt) {
        this.sendFn(`ROUTEFOLLOW[00100]${rt.player}[55555]${rt.advIdx}[44444]${rt.lon}[66666]${rt.lat}`);
      } else {
        this.sendFn('PLAY[00100]');
      }
    }
  }

  _onAssetLoaded() {
    this._pendingAssets--;
    this._totalAssetsLoaded++;
    if (this._pendingAssets === 0 && !this._gameReady && this.sendFn && this.state) {
      this._gameReady = true;
      this.sendFn('READY[00100]');
    }
  }

  _handleHover(x, y, clientX, clientY) {
    for (const area of this._clickableAreas) {
      if (area.tooltip && x >= area.x && x < area.x + area.w && y >= area.y && y < area.y + area.h) {
        this._tooltipEl.textContent = area.tooltip;
        this._tooltipEl.style.display = 'block';
        const wRect = this.canvas.parentNode.getBoundingClientRect();
        let tx = clientX - wRect.left + 14;
        let ty = clientY - wRect.top  - 10;
        // Flip left if near right edge; flip up if near bottom edge
        const tipW = this._tooltipEl.offsetWidth  || 160;
        const tipH = this._tooltipEl.offsetHeight || 22;
        if (tx + tipW > wRect.width)  tx = clientX - wRect.left - tipW - 6;
        if (ty + tipH > wRect.height) ty = clientY - wRect.top  - tipH - 6;
        if (ty < 0) ty = 2;
        this._tooltipEl.style.left = tx + 'px';
        this._tooltipEl.style.top  = ty + 'px';
        return;
      }
    }
    this._tooltipEl.style.display = 'none';
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

    this._drawMoveCount();
    this._drawToggleMenu();
    if (!s.features || s.features.maps) {
      this._drawChestTiles();
      this._drawTilePiles();
      this._drawDiscardPile();
    }
    this._updateCardsPanel();

    this._drawUndoButton();
    this._drawPrompt();
    this._drawOffersPanel();
    this._drawCardPreview();
    this._drawTimerBar();
    console.log(this._clickableAreas);
  }

  _drawTimerBar() {
    const ctx      = this.context;
    const barH     = 8;
    const barLeft  = this.playAreaStart;
    const barWidth = this.rightMenuStart - this.playAreaStart;
    const barTop   = this.canvas.height - barH;

    if (this.moveDeadline && this._gameReady) {
      const remaining = this.moveDeadline - Date.now();
      if (remaining > 0) {
        const fraction = Math.min(1, remaining / (this.moveTimerLimit * 1000));
        const r = Math.round(255 * (1 - fraction));
        const g = Math.round(255 * fraction);
        ctx.fillStyle = `rgb(${r},${g},0)`;
        ctx.fillRect(barLeft, barTop, barWidth * fraction, barH);
        return;
      }
    }

    if (this._pendingAssets > 0) {
      const fraction = this._totalAssetsRequested > 0
        ? this._totalAssetsLoaded / this._totalAssetsRequested : 0;
      // dark trough
      ctx.fillStyle = 'rgba(0,0,0,0.4)';
      ctx.fillRect(barLeft, barTop, barWidth, barH);
      // blue fill
      ctx.fillStyle = 'rgb(80,160,255)';
      ctx.fillRect(barLeft, barTop, barWidth * fraction, barH);
      // label
      const fontSize = barH * 1.8;
      ctx.font = `${fontSize}px sans-serif`;
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      ctx.fillText('Loading assets…', barLeft + 4, barTop - 2);
    }
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

        if (tile.dropped_silks > 0) {
          const fontSize = Math.round(this.tileSize * GameVisualisation.TOKEN_FONT_SCALE);
          ctx.font      = `${fontSize}px ${GameVisualisation.MENU_FONT}`;
          ctx.textAlign = 'center';
          ctx.fillStyle = tile.tile_name.endsWith('t')
            ? GameVisualisation.WONDER_TEXT_COLOUR
            : GameVisualisation.PLAIN_TEXT_COLOUR;
          ctx.fillText(String(tile.dropped_silks), x + size / 2, y + size / 2);
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
          tooltip: GameVisualisation.HIGHLIGHT_TOOLTIPS[hType] || null,
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
            tooltip: `View ${playerName}'s adventurer #${advIdx + 1}`,
          });
        }
      });

      for (const inn of (s.inns[playerName] || [])) {
        if (inn.longitude === null || inn.latitude === null) continue;
        const aOff    = GameVisualisation.INN_OFFSET;
        const ax      = this._colToPixelX(inn.longitude) + aOff[0] * this.tileSize;
        const ay      = this._rowToPixelY(inn.latitude)  + aOff[1] * this.tileSize;
        const innSz = GameVisualisation.INN_SCALE * this.tokenSize;

        if (inn.is_ransacked) {
          ctx.strokeStyle = colour;
          ctx.lineWidth   = this.outlineWidth;
          ctx.strokeRect(ax, ay, innSz, innSz);
        } else {
          ctx.fillStyle = colour;
          ctx.fillRect(ax, ay, innSz, innSz);
        }
        ctx.textAlign    = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle    = labelColour;
        ctx.fillText(String(inn.silks), ax + innSz / 2, ay + innSz / 2);
        ctx.textBaseline = 'alphabetic';
        ctx.textAlign    = 'left';
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
      if (this._routesMode === 'none') continue;
      if (this._routesMode === 'focus'
          && playerName !== s.current_player_name
          && playerName !== s.viewed_player_name) continue;

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
      const vault     = s.vault_silks[playerName];
      const advs      = s.adventurers[playerName] || [];
      const isCurrent = playerName === s.current_player_name;
      const ul        = isCurrent ? 'text-decoration:underline' : '';
      const cell      = `color:${esc(colour)};padding:${pad}px ${pad * 2}px;${ul}`;

      let name = esc(playerName);
      if (playerName === s.winning_player) name += `&nbsp;(+${s.silks_difference})`;

      let advCells = advs.map(adv => `<td style="${cell}">${adv.silks}</td>`).join('');
      for (let i = advs.length; i < maxAdvs; i++) advCells += `<td></td>`;

      rows += `<tr data-player="${esc(playerName)}" data-adv="0" style="cursor:pointer">
        <td style="${cell}">${name}</td>
        <td style="${cell}">${vault}</td>
        ${advCells}
      </tr>`;
      rowCount++;
    }

    el.innerHTML = `<table style="border-collapse:collapse;font-family:sans-serif;font-size:${fontSize}px;line-height:${ROW}px;pointer-events:auto">${rows}</table>`;
    this.scoresBottomY = el.offsetHeight;

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
    const pad      = Math.max(2, Math.round(fontSize * 0.2));
    const cardW    = this.playAreaStart;
    const innerW   = cardW - 2 * pad;
    const cardH    = Math.round(innerW * GV.CARD_RATIO);
    const headerH  = Math.round(cardH * GV.CARD_HEADER_SHARE);

    el.style.top     = this.scoresBottomY + 'px';
    el.style.width   = cardW + 'px';
    el.style.height  = (this.canvas.height - this.scoresBottomY) + 'px';
    el.style.padding = pad + 'px';

    if (s.features && !s.features.cards) { el.innerHTML = ''; return; }

    const viewedAdv = (s.adventurers[s.viewed_player_name] || [])[s.viewed_adventurer_index] || null;
    if (!viewedAdv) { el.innerHTML = ''; return; }

    // Collect all cards in display order
    const cards = [];
    const cultureCard = (s.assigned_cultures || {})[s.viewed_player_name];
    if (cultureCard) {
      cards.push({ cardType: cultureCard.card_type, cardId: cultureCard.card_id, action: 'CARDSEL', data: 'culture' });
    }
    (viewedAdv.manuscript_cards || []).forEach((card, idx) => {
      cards.push({ cardType: card.card_type, cardId: card.card_id, action: 'CARDSEL', data: String(idx) });
    });
    (viewedAdv.companion_cards || []).forEach((card, idx) => {
      cards.push({ cardType: card.card_type, cardId: card.card_id, action: 'COMPSEL', data: String(idx) });
    });
    if (viewedAdv.character_card) {
      cards.push({ cardType: viewedAdv.character_card.card_type, cardId: viewedAdv.character_card.card_id, action: 'CHARSEL', data: '' });
    }

    if (cards.length === 0) { el.innerHTML = ''; return; }

    // Stack: (n-1) header strips visible above each successive card, last card shows fully
    const stackH = (cards.length - 1) * headerH + cardH;

    let html = `<div style="position:relative;width:${innerW}px;height:${stackH}px">`;
    cards.forEach((card, i) => {
      const title    = esc(GV.CARD_TITLES[card.cardType] || '');
      const body     = esc(GV.CARD_TEXTS[card.cardType]  || card.cardType);
      const filename = this._cardFilename(card.cardId, card.cardType);
      html += `<div style="position:absolute;top:${i * headerH}px;left:0;width:${innerW}px;height:${cardH}px;overflow:hidden;cursor:pointer;z-index:${i + 1}"
                   data-action="${esc(card.action)}" data-data="${esc(card.data)}" data-card-type="${esc(card.cardType)}" data-card-id="${esc(card.cardId)}">
        <img src="${GV.CARDS_PATH}${esc(filename)}"
             data-title="${title}" data-body="${body}"
             style="width:100%;height:${cardH}px;object-fit:contain;display:block">
      </div>`;
    });
    html += '</div>';

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

    // Click a card to toggle full-screen preview (client-side only)
    el.querySelectorAll('[data-card-type]').forEach(div => {
      div.addEventListener('pointerdown', () => {
        const cardType = div.dataset.cardType;
        const cardId   = div.dataset.cardId;
        const toggling = this._previewedCardId === cardId;
        this._previewedCardType = toggling ? null : cardType;
        this._previewedCardId   = toggling ? null : cardId;
        this._render();
      });
    });
  }

  _drawCardPreview() {
    if (!this._previewedCardType) return;
    const s   = this.state;
    const ctx = this.context;
    const GV  = GameVisualisation;
    // Offers take priority — clear preview if they appear
    if ((s.offered_cards && s.offered_cards.length) || (s.offered_tiles && s.offered_tiles.length)) {
      this._previewedCardType = null;
      this._previewedCardId   = null;
      return;
    }
    const W        = this.canvas.width;
    const H        = this.canvas.height;
    const fontSize = Math.round(H * GV.SCORES_FONT_SCALE);
    const margin   = Math.round(Math.min(W, H) * 0.02);
    const maxItemH = H - 2 * margin - fontSize * 2;
    const maxFromW = Math.floor((W - 2 * margin) * GV.CARD_RATIO);
    const itemH    = Math.min(maxItemH, maxFromW);
    const itemW    = Math.round(itemH / GV.CARD_RATIO);
    const x        = Math.round((W - itemW) / 2);
    const y        = Math.max(margin + 2 * fontSize, Math.round((H - itemH) / 2));
    const cardType = this._previewedCardType;
    const filename = this._cardFilename(this._previewedCardId, cardType);
    const src      = GV.CARDS_PATH + filename;

    ctx.fillStyle = 'rgba(0,0,0,0.65)';
    ctx.fillRect(0, 0, W, H);

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
      const fs = Math.max(10, Math.round(itemH * 0.08));
      ctx.fillStyle = GV.CARD_BACKGROUND_COLOUR;
      ctx.fillRect(x, y, itemW, itemH);
      ctx.font      = `${fs}px ${GV.MENU_FONT}`;
      ctx.fillStyle = GV.CARD_TEXT_COLOUR;
      ctx.fillText(GV.CARD_TITLES[cardType] || cardType, x + 4, y + fs + 4);
      ctx.fillText(GV.CARD_TEXTS[cardType]  || '',        x + 4, y + Math.round(itemH * 0.6));
    }

    ctx.strokeStyle = 'white';
    ctx.lineWidth   = 3;
    ctx.strokeRect(x, y, itemW, itemH);
    ctx.lineWidth   = 1;

    ctx.font      = `${fontSize}px ${GV.MENU_FONT}`;
    ctx.fillStyle = GV.PLAIN_TEXT_COLOUR;
    ctx.textAlign = 'center';
    ctx.fillText(GV.CARD_TITLES[cardType] || '', W / 2, y - fontSize * 0.3);
    ctx.textAlign = 'left';
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

    const n          = items.length;
    const margin     = Math.round(Math.min(W, H) * 0.02);
    const gap        = Math.round(W * 0.02);
    const fontSize   = Math.round(H * GV.SCORES_FONT_SCALE);
    const maxItemH   = H - 2 * margin - fontSize * 2;
    const availW     = W - 2 * margin - (n - 1) * gap;

    let itemH, itemW;
    if (isCards) {
      // CARD_RATIO = height/width
      const maxFromW = Math.floor(availW / n * GV.CARD_RATIO);
      itemH = Math.min(maxItemH, maxFromW);
      itemW = Math.round(itemH / GV.CARD_RATIO);
    } else {
      const maxFromW = Math.floor(availW / n);
      itemH = Math.min(maxItemH, maxFromW);
      itemW = itemH;
    }

    const totalW = n * itemW + (n - 1) * gap;
    const startX = Math.max(margin, Math.round((W - totalW) / 2));
    // Clamp so the label (drawn one fontSize above startY) is always fully visible
    const startY = Math.max(margin + 2 * fontSize, Math.round((H - itemH) / 2));

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
        const filename = this._cardFilename(item.card_id, cardType);
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
    const autoActionsForPlayer = ((s.auto_actions || {})[s.viewed_player_name]
                                || (s.auto_actions || {})[s.current_player_name]
                                || {});
    for (const hType of GV.TOGGLE_HIGHLIGHTS) {
      const img = this._highlightImages[hType];
      if (img && img.complete && img.naturalWidth > 0) {
        ctx.drawImage(img, hx, y, hs, hs);
      } else {
        ctx.strokeStyle = GV.PLAIN_TEXT_COLOUR;
        ctx.lineWidth = 1;
        ctx.strokeRect(hx, y, hs, hs);
      }
      const toggleState = autoActionsForPlayer[hType];
      if (toggleState !== null && toggleState !== undefined) {
        ctx.globalAlpha = 0.4;
        ctx.fillStyle = toggleState ? GV.TOGGLE_TRUE_COLOUR : GV.TOGGLE_FALSE_COLOUR;
        ctx.fillRect(hx, y, hs, hs);
        ctx.globalAlpha = 1;
      }
      this._clickableAreas.push({ x: hx, y, w: hs, h: hs, action: 'TOGGLE', data: hType,
        tooltip: GameVisualisation.TOGGLE_TOOLTIPS[hType] || null });
      hx += hs;
    }
    y += hs + 4;

    // Route-visibility indicator: coloured lines below the toggle icons
    const routesAreaTop = y;
    if (this._routesMode !== 'none') {
      for (const pName of s.players) {
        if (this._routesMode === 'all' || pName === s.current_player_name || pName === s.viewed_player_name) {
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
    }
    // Clickable area covers the indicator lines section (min height hs so 'none' mode is still clickable)
    this._clickableAreas.push({
      x, y: routesAreaTop, w: this.rightMenuWidth, h: Math.max(y - routesAreaTop, hs),
      action: 'ROUTES', data: '',
      tooltip: 'Cycle route display: focus → all → none',
    });
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
    if (!viewedAdv || !viewedAdv.chest_maps || viewedAdv.chest_maps.length === 0) return;

    ctx.font = `${fontSize}px ${GV.MENU_FONT}`;
    const x = this.rightMenuStart;
    let y = this.rightMenuY + fontSize;

    ctx.fillStyle = s.player_colours[s.viewed_player_name] || GV.PLAIN_TEXT_COLOUR;
    ctx.fillText(`#${(s.viewed_adventurer_index || 0) + 1}'s chest maps:`, x, y);
    y += fontSize;

    const ts = this.menuTileSize;
    const border = Math.round(ts * GV.TILE_BORDER);
    const maxChest = viewedAdv.num_chest_maps || viewedAdv.chest_maps.length;
    const menuH = ts * Math.ceil(maxChest / GV.MENU_TILE_COLS);

    ctx.strokeStyle = GV.PLAIN_TEXT_COLOUR;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, this.rightMenuWidth, menuH);
    ctx.lineWidth = 1;

    viewedAdv.chest_maps.forEach((tile, idx) => {
      const tx = x + (idx % GV.MENU_TILE_COLS) * ts;
      const ty = y + Math.floor(idx / GV.MENU_TILE_COLS) * ts;
      this._drawTileAt(tile, tx + border / 2, ty + border / 2, ts - border);

      const isSelected = idx === viewedAdv.chosen_map_index;
      ctx.strokeStyle = isSelected ? GV.CHEST_HIGHLIGHT_COLOUR : GV.PLAIN_TEXT_COLOUR;
      ctx.lineWidth = 2;
      ctx.strokeRect(tx, ty, ts, ts);
      ctx.lineWidth = 1;

      if (isSelected) {
        // On the selected tile only: draw rotation corner zones at bottom-left and bottom-right
        const az = Math.round(ts * 0.35); // corner zone side length
        const as = Math.round(az * 0.4);  // arrow triangle half-size
        // Left corner background + left-pointing arrow (anticlockwise)
        ctx.fillStyle = 'rgba(0,0,0,0.45)';
        ctx.fillRect(tx, ty + ts - az, az, az);
        ctx.fillStyle = 'rgba(255,255,255,0.85)';
        const lx = tx + az * 0.5, ly = ty + ts - az * 0.5;
        ctx.beginPath();
        ctx.moveTo(lx - as, ly);
        ctx.lineTo(lx + as * 0.6, ly - as);
        ctx.lineTo(lx + as * 0.6, ly + as);
        ctx.closePath();
        ctx.fill();
        // Right corner background + right-pointing arrow (clockwise)
        ctx.fillStyle = 'rgba(0,0,0,0.45)';
        ctx.fillRect(tx + ts - az, ty + ts - az, az, az);
        ctx.fillStyle = 'rgba(255,255,255,0.85)';
        const rx = tx + ts - az * 0.5, ry = ty + ts - az * 0.5;
        ctx.beginPath();
        ctx.moveTo(rx + as, ry);
        ctx.lineTo(rx - as * 0.6, ry - as);
        ctx.lineTo(rx - as * 0.6, ry + as);
        ctx.closePath();
        ctx.fill();
        // Register corner zones before the full-tile CHEST zone so they take priority
        this._clickableAreas.push({ x: tx,           y: ty + ts - az, w: az, h: az, action: 'CHESTL', data: String(idx), tooltip: 'Rotate tile anticlockwise' });
        this._clickableAreas.push({ x: tx + ts - az, y: ty + ts - az, w: az, h: az, action: 'CHESTR', data: String(idx), tooltip: 'Rotate tile clockwise' });
      }
      // Full tile click = select (or deselect if already selected); lower priority than corner zones above
      this._clickableAreas.push({ x: tx, y: ty, w: ts, h: ts, action: 'CHEST', data: String(idx),
        tooltip: isSelected ? 'Deselect this chest map' : 'Select this chest map to place next' });
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

    // Culture / Culture card (just header strip)
    const cultureCard = (s.assigned_cultures || {})[s.viewed_player_name];
    if (cultureCard) {
      ctx.fillStyle = s.player_colours[s.viewed_player_name] || GV.PLAIN_TEXT_COLOUR;
      ctx.fillText(`${s.viewed_player_name}'s Culture card:`, 0, y);
      y += fontSize;
      this._drawCardAt(cultureCard, 0, y, cardW, cardH);
      const headerH = Math.round(cardH * GV.CARD_HEADER_SHARE);
      this._clickableAreas.push({ x: 0, y, w: cardW, h: headerH, action: 'CARDSEL', data: 'culture', tooltip: 'Preview Culture card' });
      y += headerH;
    }

    // Character, companion, and discovery cards
    const hasCards = viewedAdv.character_card
                  || (viewedAdv.manuscript_cards && viewedAdv.manuscript_cards.length > 0)
                  || (viewedAdv.companion_cards && viewedAdv.companion_cards.length > 0);
    if (hasCards) {
      ctx.fillStyle = GV.PLAIN_TEXT_COLOUR;
      ctx.fillText(`Adventurer #${(s.viewed_adventurer_index || 0) + 1} cards:`, 0, y);
      y += fontSize;

      // Manuscript cards — stacked so only header strip shows
      (viewedAdv.manuscript_cards || []).forEach((card, idx) => {
        this._drawCardAt(card, 0, y, cardW, cardH);
        const headerH = Math.round(cardH * GV.CARD_HEADER_SHARE);
        this._clickableAreas.push({ x: 0, y, w: cardW, h: headerH, action: 'CARDSEL', data: String(idx), tooltip: 'Preview manuscript card' });
        y += headerH;
      });

      // Companion cards — stacked so only header strip shows
      (viewedAdv.companion_cards || []).forEach((card, idx) => {
        this._drawCardAt(card, 0, y, cardW, cardH);
        const headerH = Math.round(cardH * GV.CARD_HEADER_SHARE);
        this._clickableAreas.push({ x: 0, y, w: cardW, h: headerH, action: 'COMPSEL', data: String(idx), tooltip: 'Preview companion card' });
        y += headerH;
      });

      // Character card — shown in full at the bottom
      if (viewedAdv.character_card) {
        this._drawCardAt(viewedAdv.character_card, 0, y, cardW, cardH);
        this._clickableAreas.push({ x: 0, y, w: cardW, h: cardH, action: 'CHARSEL', data: '', tooltip: 'Preview character card' });
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
    this._clickableAreas.push({ x: bx, y: by, w: metrics.width, h: fontSize + 4, action: 'UNDO', data: '',
      tooltip: 'Request to undo this turn — all players must agree' });
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
