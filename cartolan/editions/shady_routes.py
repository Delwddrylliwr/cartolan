'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com

Cartolan - Shady Routes: the piracy expansion on Lite Winds.

Adventurers can attack other Adventurers and Inns, becoming Pirates who cannot
trade or rest at other players' Inns until redeemed at a city or arrested.
Ransacked Inns give no rest until restored. Manuscript cards are bought at
cities or earned by well-connected exploration, and each player draws a
Culture card giving their whole colour a perk.
'''

import logging

from cartolan.core.tokens import Adventurer, Inn
from cartolan.core.tiles import CityTile, WindDirection, TileEdges
from cartolan.rules.ruleset import SHADY_ROUTES
from cartolan.editions.lite_winds import (GameLiteWinds, AdventurerLiteWinds, InnLiteWinds,
                                          CityTileLiteWinds, TradePortTile)

logger = logging.getLogger(__name__)


class AdventurerShadyRoutes(AdventurerLiteWinds):
    '''Extends the Lite Winds Adventurer with piracy, Manuscript cards, and card-modified rules.

    Methods:
    attack takes a Cartolan.Token object
    arrest takes a Cartolan.Adventurer
    restore_inn takes a Cartolan.Inn object
    '''
    def __init__(self, game, player, starting_city):
        super().__init__(game, player, starting_city)
        self.pirate_token = False

        #Mirror game variables, so that cards can modify them per token
        self.attack_die_bonus = game.attack_die_bonus
        self.defence_die_bonus = game.defence_die_bonus
        self.value_arrest = game.value_arrest
        self.value_ransack_inn = game.value_ransack_inn
        self.cost_inn_restore = game.cost_inn_restore
        self.rest_after_placing = game.rest_after_placing


        #Record some additional instructions
        self.attacked = 0
        self.restored = False

        #Prepare to hold Manuscript cards
        self.manuscript_cards = []

    # --- Manuscript cards ---

    def discover_card(self, card):
        '''Adds a Manuscript card to the Adventurer, modifying rules according to the card's buffs
        '''
        logger.debug(self.player.name+"'s Adventurer has received the card of type "+card.card_type)
        self.manuscript_cards.append(card)
        card.apply_buffs(self)
        self.replenish_chest_maps()  # in case the buffs increased the chest map capacity

    def lose_card(self, card):
        '''Removes a Manuscript card from the Adventurer, recomputing rules from the cards left
        '''
        logger.debug(self.player.name+"'s Adventurer has lost a card of type "+card.card_type)
        self.manuscript_cards.remove(card)
        self.recompute_card_buffs()

    def recompute_card_buffs(self):
        '''Resets every card-modifiable rule to the game's base value, then re-applies the
        modifiers of all cards still held (Culture, Character, Companions, Manuscripts).

        This keeps rules correct when cards are lost or stolen, even when several
        cards modified the same rule.
        '''
        modifiable = set()
        for modifiers in self.game.card_modifiers.values():
            modifiable.update(modifiers.keys())
        import copy as _copy
        for attr in modifiable:
            if hasattr(self, attr):
                setattr(self, attr, _copy.deepcopy(getattr(self.game, attr)))
        culture = self.game.assigned_cultures.get(self.player)
        cards = ([culture] if culture else []) + \
                ([self.character_card] if self.character_card else []) + \
                self.companion_cards + self.manuscript_cards
        for held_card in cards:
            held_card.apply_buffs(self)

    def _offer_manuscript_choice(self):
        '''Draws a filtered set of manuscript options, lets the player choose one, and applies it.
        Returns True if a card was awarded, False if none were available.
        '''
        available_cards = self.game.manuscript_cards
        rejected_cards = []
        card_options = []
        while len(card_options) < self.game.num_manuscript_choices[self.player] and available_cards:
            new_card = available_cards.pop(self.game.rng.randint(0, len(available_cards) - 1))
            # Reject cards whose one-time buffs duplicate something the Adventurer already has
            duplicate = False
            for buff_attr in new_card.buffs:
                if new_card.buffs[buff_attr]["buff_type"] == "new":
                    if self.character_card is not None and buff_attr in self.character_card.buffs:
                        duplicate = True
                        break
                    for existing_card in self.manuscript_cards + self.companion_cards:
                        if buff_attr in existing_card.buffs:
                            duplicate = True
                            break
            if duplicate:
                rejected_cards.append(new_card)
            else:
                card_options.append(new_card)
        awarded = False
        if card_options:
            chosen_card = self.player.choose_card(self, card_options)
            card_options.remove(chosen_card)
            self.discover_card(chosen_card)
            awarded = True
        available_cards += card_options   # return unchosen options to the deck
        available_cards += rejected_cards  # return unsuitable cards to the deck
        return awarded

    def discover(self, tile):
        '''Extends Lite Winds to award manuscript cards when filling well-connected gaps.'''
        super().discover(tile)
        if not isinstance(self.current_tile, CityTile):
            manuscripts = self.game.value_fill_gap_manuscripts[self.last_exploration_adjacents]
            for _ in range(manuscripts):
                self._offer_manuscript_choice()
        return True

    # --- Piracy ---

    def trade(self, tile):
        '''Extends Lite Winds by preventing pirates from trading, and letting Inns profit from trade

        Arguments
        tile should be a Cartolan.Tile
        '''
        #check whether this is a pirate and refuse them trade
        if self.pirate_token:
            return False

        if super().trade(tile):
             # check whether there is an Inn on the tile
            if tile.inn is not None:
                tile.inn.manage_trade(self)
            return True
        else: return False

    def can_rest(self, token):
        '''Extends Lite Winds by preventing pirates resting with others' Inns.'''
        if self.pirate_token and not self.player == token.player:
            return False
        return super().can_rest(token)

    def resolve_attack(self, defender):
        '''Resolves an attack like a die roll: 1-2 loss, 3-4 draw, 5-6 win; only a win succeeds.

        Card bonuses shift the roll in the attacker's or defender's favour.
        '''
        roll = self.game.rng.randint(1, 6)
        roll += self.attack_die_bonus - getattr(defender, "defence_die_bonus", 0)
        return roll >= 5

    def attack(self, token):
        '''Attacks another Adventurer or Inn on this tile (Shady Routes C.2).

        A successful attack on a non-pirate makes this Adventurer a Pirate. Success
        lets them take as many of the victim's Chest Silks as they choose, plus any
        one Chest map and/or one Manuscript card. Attacking a pirate is an arrest.
        Ransacking an Inn earns its Silks plus a bonus and flips it over.
        '''
        if isinstance(self.current_tile, CityTile): #there is no attacking at cities
            return False

        #Record the decision to attack this move
        self.attacked += 1

        success = self.resolve_attack(token)

        if isinstance(token, Adventurer):
            adventurer = token
            if adventurer.pirate_token:
                # attacking a pirate is an arrest, and doesn't make the attacker a pirate
                if success:
                    self.arrest(adventurer)
            elif success:
                logger.debug(self.player.name+" successfully attacked "+token.player.name+"'s Adventurer.")
                #a successful attack on polite society makes the attacker a Pirate
                self.pirate_token = True
                #take as many of the victim's Silks as chosen
                default_steal = adventurer.silks//2 + adventurer.silks%2
                chosen_steal = None
                while not chosen_steal in range(0, adventurer.silks + 1):
                    chosen_steal = self.player.check_steal_amount(adventurer, adventurer.silks, default_steal)
                self.silks += chosen_steal
                adventurer.silks -= chosen_steal
                #optionally take any one Chest map
                if (adventurer.chest_maps and len(self.chest_maps) < self.num_chest_maps
                        and self.player.check_steal_map(self, adventurer)):
                    stolen_index = adventurer.chest_maps.index(self.player.choose_tile(self, adventurer.chest_maps))
                    stolen_tile = adventurer.chest_maps.pop(stolen_index)
                    if stolen_index < len(adventurer.chest_map_offsets):
                        adventurer.chest_map_offsets.pop(stolen_index)
                    self.chest_maps.append(stolen_tile)
                    self.chest_map_offsets.append(0)
                #and/or any one Manuscript card
                if (getattr(adventurer, "manuscript_cards", None)
                        and self.player.check_steal_manuscript(self, adventurer)):
                    stolen_card = self.player.choose_card(self, adventurer.manuscript_cards)
                    adventurer.lose_card(stolen_card)
                    self.discover_card(stolen_card)
        elif isinstance(token, Inn):
            inn = token
            if not inn.is_ransacked and success:
                logger.debug(self.player.name+" successfully attacked "+token.player.name+"'s Inn.")
                self.pirate_token = True
                #take as many of the Inn's Silks as chosen, plus the ransacking bonus
                default_steal = inn.silks
                chosen_steal = None
                while not chosen_steal in range(0, inn.silks + 1):
                    chosen_steal = self.player.check_steal_amount(inn, inn.silks, default_steal)
                self.silks += chosen_steal + self.value_ransack_inn
                inn.silks -= chosen_steal
                inn.is_ransacked = True
        else: raise Exception("Not able to deal with this kind of token.")

        #Keep track of attacks for static visualisation
        attack_history = self.player.attack_history.get(self.game)
        if not attack_history:
            attack_history = self.player.attack_history[self.game] = []
        attack_history.append([self.current_tile, success])
        return success

    def arrest(self, pirate):
        '''Arrests a pirate: a reward to the Chest, while the pirate's Silks are lost
        and they retreat to their last-visited city (Shady Routes C.2).
        '''
        logger.debug(self.player.name+" successfully arrested "+pirate.player.name+"'s Adventurer.")
        self.silks += self.value_arrest # get a reward
        pirate.end_expedition()

    def end_expedition(self, city=None):
        '''Extends to deal with piracy
        '''
        self.pirate_token = False
        return super().end_expedition(city)

    def check_tile_available(self, tile):
        '''Extends Lite Winds to keep track of whether existing Inns have been ransacked when placing on a tile
        '''
        if self.pirate_token:
            return False
        elif isinstance(tile, CityTile):
            return False
        elif tile.inn is None:
            return True
        elif tile.inn.is_ransacked:
            return True
        else:
            return False

    def restore_inn(self, inn):
        '''Pays to restore a ransacked Inn, with card-modified same-turn resting.'''
        #Record the decision to restore this move
        self.restored = True

        if inn.is_ransacked:
            if self.cost_inn_restore <= self.silks:
                logger.debug("Paying " +str(self.cost_inn_restore)+ " to restore "
                      +inn.player.name+"'s Inn at position "
                      +str(inn.current_tile.tile_position.longitude)
                     +","+ str(inn.current_tile.tile_position.latitude))
                self.silks -= self.cost_inn_restore
                inn.is_ransacked = False
                #the Inn can't give rest until after the turn it was restored
                inn.restored_on_turn = self.game.turn
                self.inns_rested.append(inn)
                return True
            else:
                logger.debug("Cannot afford to restore an inn")
                return False
        else:
            logger.debug("Didn't need to restore this Inn")
            return False

    def offer_hire_inn(self):
        '''Extends to allow same-turn resting after placing an inn (rest_after_placing buff)
        '''
        super().offer_hire_inn()
        if (self.rest_after_placing
                and self.current_tile.inn is not None
                and self.current_tile.inn in self.inns_rested):
            self.inns_rested.remove(self.current_tile.inn)

    def offer_attack(self):
        '''Offers attacks against Adventurers and Inns on this tile (Shady Routes C.1-2).'''
        #check whether there is an adventurer here and attack if the player wants
        if self.current_tile.adventurers:
            for adventurer in self.current_tile.adventurers:
                if (adventurer.player != self.player
                    and (adventurer.silks > 0 or adventurer.pirate_token)):
                    if self.player.check_attack_adventurer(self, adventurer):
                        self.attack(adventurer)

        #check whether there is an active opponent Inn here to attack
        if self.current_tile.inn:
            inn = self.current_tile.inn
            if not inn.is_ransacked and inn.player != self.player:
                if inn.silks + self.value_ransack_inn > 0:
                    if self.player.check_attack_inn(self, inn):
                        self.attack(inn)

    def offer_rest(self):
        '''Extends resting with ransack-awareness and restoration by visitors.'''
        if self.current_tile.inn:
            inn = self.current_tile.inn
            if not inn.is_ransacked:
                super().offer_rest()
            #Any visitor except a pirate can pay to restore a ransacked Inn
            elif not self.pirate_token and self.silks >= self.cost_inn_restore:
                if self.player.check_restore_inn(self, inn):
                    self.restore_inn(inn)

        #Card-modified: move silks to the player's Inns
        if self.current_tile.inn is not None:
            if (self.transfer_inn_earnings_available()
                and len(self.game.inns[self.player]) > 0
                and self.silks > 0):
                self.transfer_to_inn()

    def transfer_inn_earnings_available(self):
        '''Whether this player's Culture sends earnings via their Inns.'''
        return self.game.transfer_inn_earnings.get(self.player, False)

    def transfer_to_inn(self):
        '''Offers the opportunity to transfer current silks to any of the player's Inns
        '''
        transfer_inn = self.player.check_transfer_inn(self)
        while isinstance(transfer_inn, InnShadyRoutes):
            #Check the amount to transfer and move it
            transfer_amount = self.player.check_bank_amount(self, self.silks, -transfer_inn.silks)
            self.silks -= transfer_amount
            transfer_inn.silks += transfer_amount
            #See if another transfer is desired
            transfer_inn = self.player.check_transfer_inn(self)

    def to_json(self):
        d = super().to_json()
        d.update({
            "pirate_token": self.pirate_token,
            "manuscript_cards": [c.to_json() for c in self.manuscript_cards],
        })
        return d


class InnShadyRoutes(InnLiteWinds):
    '''Extends the Lite Winds Inn with ransacking and card-modified behaviours'''
    def __init__(self, game, player, tile):
        super().__init__(game, player, tile)
        # Need to keep track of whether this Inn has been ransacked, and when restored
        self.is_ransacked = False
        self.restored_on_turn = None
        #Inherit player-specific characteristics that have been buffed
        self.value_inn_trade = game.value_inn_trade[player]
        self.transfer_inn_earnings = game.transfer_inn_earnings[player]

    def give_rest(self, adventurer):
        '''Takes into account ransacking: no rest while ransacked, nor until after the
        turn a visitor restored the Inn (Shady Routes C.2).
        '''
        if self.is_ransacked:
            return False
        if self.restored_on_turn is not None and not self.game.turn > self.restored_on_turn:
            return False
        if super().give_rest(adventurer):
            rest_cost = self.game.cost_inn_rest * adventurer.num_characters
            if self.transfer_inn_earnings and self.silks > 0:
                logger.debug("Inn is moving income from providing rest directly to player's Vault")
                self.game.vault_silks[self.player] += rest_cost
                self.silks -= rest_cost
            return True
        else:
            return False

    def manage_trade(self, adventurer):
        '''Receives silks when trade takes place on its tile, either keeping this or giving it to the player's Vault

        Arguments:
        Cartolan.Adventurer the Adventurer making the trade
        '''
        #check whether ransacked
        if self.is_ransacked:
            return False
        #check whether Adventurer trading is from the same player
        elif adventurer.player == self.player:
            if self.transfer_inn_earnings:
                logger.debug("Inn on tile "+str(self.current_tile.tile_position.longitude)+", "+str(self.current_tile.tile_position.latitude)+
                      " has transferred trade income direct to the bank instead of to the Adventurer")
                adventurer.silks -= adventurer.value_trade
                self.game.vault_silks[adventurer.player] += adventurer.value_trade
        else:
            # retain silks if they are a different player
            logger.debug("Inn on tile " +str(self.current_tile.tile_position.longitude)+","
                  +str(self.current_tile.tile_position.longitude)+ " has kept monopoly bonus")
            self.silks += self.value_inn_trade
        return True

    def dismiss(self):
        '''Takes this Inn off a tile fully and out of the game
        '''
        self.game.inns[self.player].remove(self)
        self.current_tile.move_off_tile(self)

    def to_json(self):
        d = super().to_json()
        d["is_ransacked"] = self.is_ransacked
        return d


class CityTileShadyRoutes(CityTileLiteWinds):
    '''City tile for Shady Routes: behaviour lives on GameShadyRoutes.'''


class HomeCityTileShadyRoutes(CityTileShadyRoutes):
    def __init__(self, game, tile_back = "water"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(True,True,True,True)):
        super().__init__(game, wind_direction, tile_edges, True, True)


class MythicalCityTileShadyRoutes(CityTileShadyRoutes):
    def __init__(self, game, tile_back = "land"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(False,False,False,False)):
        super().__init__(game, wind_direction, tile_edges, False, False)


class GameShadyRoutes(GameLiteWinds):
    '''Extends the Lite Winds game with piracy, Manuscript cards, and Culture cards.

    Methods:
    __init__ takes a List of Cartolan.Player objects and two Strings
    choose_culture takes a Cartolan.Player
    '''
    TILE_TYPES = {"plain":GameLiteWinds.TILE_TYPES["plain"],
                  "home_city":HomeCityTileShadyRoutes,
                  "mythical_city":MythicalCityTileShadyRoutes,
                  "trade_port":TradePortTile}
    ADVENTURER_TYPE = AdventurerShadyRoutes
    INN_TYPE = InnShadyRoutes
    CITY_TYPE = CityTileShadyRoutes

    RULESET = SHADY_ROUTES
    #Shady Routes C.1: attacking slots in after trading and before resting
    ACTION_ORDER = ("trade", "attack", "rest", "hire_inn")

    def __init__(self, players, rng=None):
        super().__init__(players, rng)

        #Some rule values apply per player, so they can be modified by Culture cards
        self.num_manuscript_choices = {}
        self.value_inn_trade = {}
        self.transfer_inn_earnings = {}
        #And a placeholder for players to choose a Culture
        self.assigned_cultures = {}
        for player in players:
            self.num_manuscript_choices[player] = self.ruleset.num_manuscript_choices
            self.value_inn_trade[player] = self.ruleset.value_inn_trade
            self.transfer_inn_earnings[player] = self.ruleset.transfer_inn_earnings
            self.assigned_cultures[player] = None

        #Rebuild the card decks so that Culture and Manuscript cards join the Character deck
        self.card_count = 0
        self.culture_cards = [self.CARD_TYPE(self, card_type) for card_type in self.ruleset.culture_cards]
        self.character_cards = [self.CARD_TYPE(self, card_type) for card_type in self.ruleset.character_cards]
        self.manuscript_cards = [self.CARD_TYPE(self, card_type) for card_type in self.ruleset.manuscript_cards]

    def start_game(self):
        '''Extends to draw Culture cards at the start of the game (Shady Routes C.4:
        each player draws 2 Culture cards and keeps 1).'''
        for player in self.players:
            if self.assigned_cultures.get(player) is None:
                self.choose_culture(player)
        return super().start_game()

    def run_city_visit(self, adventurer, city, abandoned=False):
        '''Extends to redeem pirates when they visit a city
        '''
        #Cities provide the Adventurer with civilised clothes so they can be redeemed from piracy
        if adventurer.pirate_token:
            adventurer.pirate_token = False

        return super().run_city_visit(adventurer, city, abandoned)

    def buy_manuscripts(self, adventurer):
        '''Offers the visiting Adventurer the chance to upgrade themselves.

        Args:
            adventurer: the visiting adventurer
        '''
        logger.debug(
            "Offering " + adventurer.player.name + "'s adventurer the chance to upgrade the Adventurer with a Manuscript card")
        while (self.manuscript_cards
               and self.vault_silks[adventurer.player] >= self.cost_manuscript
               and adventurer.player.check_buy_manuscript(adventurer)):
            logger.debug(adventurer.player.name + "'s has chosen to buy a Manuscript card")
            if adventurer._offer_manuscript_choice():
                self.vault_silks[adventurer.player] -= self.cost_manuscript

    def offer_purchases(self, adventurer, city):
        '''Extends to offer Manuscript cards
        '''
        self.buy_adventurers(adventurer, city)
        self.hire_companion(adventurer)
        if self.inns_from_city:
            self.buy_inns(adventurer, city)
        self.buy_manuscripts(adventurer)
        self.buy_maps(adventurer)

    def choose_culture(self, player):
        '''Lets the player choose a Culture card from a random subset
        '''
        culture_cards = self.culture_cards
        card_options = self.rng.sample(culture_cards, k=self.num_culture_choices)
        logger.debug("Offering a selection of Culture cards:")
        for card in card_options:
            logger.debug(card.card_type)
        self.assigned_cultures[player] = player.choose_card(self.adventurers[player][0], card_options)
        culture_cards.remove(self.assigned_cultures[player])
        #Take on the changes to rules based on the Culture card
        self.assigned_cultures[player].apply_buffs(player) #for all Adventurers and Inns created after this point
        for adventurer in self.adventurers[player]: #For all existing Adventurers
            self.assigned_cultures[player].apply_buffs(adventurer)

    def to_json(self):
        d = super().to_json()
        d["game_mode"] = "ShadyRoutes"
        d["assigned_cultures"] = {
            p.name: card.to_json()
            for p, card in self.assigned_cultures.items()
            if card is not None
        }
        return d
