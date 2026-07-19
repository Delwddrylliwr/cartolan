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
        self.attack_success_prob = game.attack_success_prob
        self.value_arrest = game.value_arrest
        self.value_ransack_inn = game.value_ransack_inn
        self.cost_inn_restore = game.cost_inn_restore
        self.defence_rounds = game.defence_rounds
        self.rest_after_placing = game.rest_after_placing
        self.transfers_to_inns = game.transfers_to_inns
        self.attacks_abandon = game.attacks_abandon
        self.num_free_rests = game.num_free_rests
        self.free_rests = 0
        #Also player-specific characteristics
        self.rest_with_adventurers = game.rest_with_adventurers[player]
        self.confiscate_silks = game.confiscate_silks[player]
        self.pool_maps = game.pool_maps[player]
        self.rechoose_at_inns = game.rechoose_at_inns[player]


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
        '''Removes a Manuscript card from the Adventurer, reverting the buffs it was providing
        '''
        logger.debug(self.player.name+"'s Adventurer has lost a card of type "+card.card_type)
        self.manuscript_cards.remove(card)
        card.remove_buffs(self)
        self.replenish_chest_maps()

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
        '''Extends Lite Winds by preventing pirates resting with others' Inns, and
        allowing card-modified rests with Adventurers and free rests.'''
        restable = False
        scaled_cost = self.game.cost_inn_rest * self.num_characters
        #Make sure that silks aren't a barrier when free rests are available
        if self.free_rests > 0:
            self.silks += scaled_cost
        #check whether this is a pirate and refuse them rest, unless the Inn belongs to the same player
        if self.pirate_token and not self.player == token.player:
            restable = False
        elif super().can_rest(token):
            restable = True
        # can the adventurer rest with an adventurer instead?
        elif (self.rest_with_adventurers
              and isinstance(token, AdventurerShadyRoutes)
              and token not in self.inns_rested
              and not token == self):
            if (token.player == self.player
                or (self.silks >= scaled_cost
                and not self.pirate_token)
                or (self.free_rests > 0
                and not self.pirate_token)):
                restable = True
        else:
            restable = False
        if self.free_rests > 0:
            self.silks -= scaled_cost
        return restable

    def rest(self, token):
        '''Extends Lite Winds to allow for resting with Adventurers in some circumstances

        Arguments:
            token accepts a Cartolan Token
        '''
        scaled_cost = self.game.cost_inn_rest * self.num_characters
        #Ensure that silks aren't a barrier when free rests are available
        if self.free_rests > 0:
            self.silks += scaled_cost
        if isinstance(token, InnShadyRoutes):
            rested = token.give_rest(self)
        elif self.rest_with_adventurers and not callable(getattr(token, "give_rest", None)):
            token.cost_inn_rest = token.game.cost_inn_rest
            rested = InnLiteWinds._give_rest_core(token, self)
        else:
            rested = False
        #Remove any silks compensation for free rest
        if self.free_rests > 0:
            if rested and not token.player == self.player:
                self.free_rests -= 1
                token.silks -= scaled_cost  #If the rest was free then the Inn shouldn't be rewarded
            else:
                self.silks -= scaled_cost
        return rested

    def _attack_core(self, token):
        '''Resolves an attack against another token: piracy, arrest, or ransacking.
        '''
        #Record the decision to attack this move
        self.attacked += 1

        success = False
        # have opponent roll for defence, roll for attack, compare rolls
        if self.game.rng.random() < self.attack_success_prob:
            success = True

        # resolve conflict
        # check whether adventurer or inn
        if isinstance(token, Adventurer):
            adventurer = token
            # check whether the defender adventurer is a pirate, and remove the pirate token
            if adventurer.pirate_token:
                # arrest them
                if success:
                    self.arrest(adventurer)
            else: # rob them
                self.pirate_token = True #just trying will make them a pirate
                if success:
                    logger.debug(self.player.name+" successfully attacked "+token.player.name+"'s Adventurer.")
                    default_steal = adventurer.silks//2 + adventurer.silks%2
                    chosen_steal = None
                    while not chosen_steal in range(0, adventurer.silks + 1):
                        chosen_steal = self.player.check_steal_amount(adventurer, adventurer.silks, default_steal)
                    self.silks += chosen_steal
                    adventurer.silks -= chosen_steal
                    #Steal chest maps to top up
                    if isinstance(token, AdventurerLiteWinds):
                        if 0 < len(self.chest_maps) < self.num_chest_maps:
                            victim_chest = token.chest_maps
                            if len(victim_chest) > 0:
                                stolen_index = victim_chest.index(self.player.choose_tile(self, victim_chest))
                                stolen_tile = victim_chest.pop(stolen_index)
                                if stolen_index < len(token.chest_map_offsets):
                                    token.chest_map_offsets.pop(stolen_index)
                                self.chest_maps.append(stolen_tile)
                                self.chest_map_offsets.append(0)
        elif isinstance(token, Inn):
            if not token.is_ransacked:
                self.pirate_token = True #just trying will make them a pirate
                if success:
                    logger.debug(self.player.name+" successfully attacked "+token.player.name+"'s Inn.")
                    inn = token
                    self.silks += inn.silks + self.value_ransack_inn
                    inn.is_ransacked = True
                    inn.silks = 0
        else: raise Exception("Not able to deal with this kind of token.")

        #Keep track of attacks for static visualisation
        attack_history = self.player.attack_history.get(self.game)
        if not attack_history:
            attack_history = self.player.attack_history[self.game] = []
        attack_history.append([self.current_tile, success])
        return success

    def attack(self, token):
        '''Attacks another token, with defensive buffs and card stealing taken into account.
        '''
        #If the target Adventurer has a defensive buff to force multiple rounds of attack then these need to be won first
        if isinstance(token, AdventurerShadyRoutes):
            for defence_round in range(0, token.defence_rounds-1):
                if self.game.rng.random() > self.attack_success_prob:
                    return False
        if self._attack_core(token):
            if isinstance(self.current_tile, CityTile): #If on a city then there's no attacking
                return True
            #Steal Manuscript cards
            if isinstance(token, AdventurerShadyRoutes):
                if len(token.manuscript_cards) > 0:
                    stolen_card = self.player.choose_card(self, token.manuscript_cards)
                    token.lose_card(stolen_card)
                    self.discover_card(stolen_card)
            if self.attacks_abandon: #Adventurers will return to cities, Inns are removed
                if isinstance(token, AdventurerLiteWinds):
                    if not isinstance(token.current_tile, CityTile): #in case they were a Pirate already sent back to a city
                        token.end_expedition()
                elif isinstance(token, InnShadyRoutes):
                    token.dismiss()
            return True
        else:
            return False

    def arrest(self, pirate):
        '''Sends pirates back to their last city and claims a reward.
        '''
        if self.confiscate_silks and pirate.silks > 0:
            self.silks += pirate.silks
            pirate.silks = 0
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
                #Make sure that the Adventurer can't use this Inn this turn
                self.inns_rested.append(inn)
                if self.rest_after_placing:
                    self.inns_rested.remove(self.current_tile.inn)
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
                #Card-modified: the option to send an opponent home even with no silks
                elif (self.attacks_abandon and adventurer.silks == 0
                    and not self == adventurer and adventurer.player != self.player):
                    if self.player.check_attack_adventurer(self, adventurer):
                        self.attack(adventurer)

        #check whether there is an active opponent Inn here to attack
        if self.current_tile.inn:
            inn = self.current_tile.inn
            if not inn.is_ransacked and inn.player != self.player:
                if inn.silks + self.value_ransack_inn > 0:
                    if self.player.check_attack_inn(self, inn):
                        self.attack(inn)
                #Card-modified: Inns that arrest visiting pirates
            if (inn.inns_arrest and not inn.is_ransacked
                and self.pirate_token and not inn.player == self.player):
                if self.game.rng.random() < self.game.attack_success_prob:
                    AdventurerShadyRoutes.arrest(inn, self) #The arrest function should only use common features of the common parent Token class
                    self.end_turn()

    def offer_rest(self):
        '''Extends resting with ransack-awareness, restoration, and card-modified rests.'''
        if self.current_tile.inn:
            inn = self.current_tile.inn
            if not inn.is_ransacked:
                super().offer_rest()
            #Restore the Inn if they are ransacked
            else:
                if (inn.player == self.player
                    and self.silks >= self.cost_inn_restore):
                    if self.player.check_restore_inn(self, inn):
                        self.restore_inn(inn)

        #Card-modified interactions: resting with Adventurers, transfers to Inns
        if self.current_tile.adventurers:
            for adventurer in self.current_tile.adventurers:
                if self.rest_with_adventurers and self.can_rest(adventurer):
                    if self.player.check_rest(self, adventurer):
                        self.rest(adventurer)
        if self.current_tile.inn is not None:
            if (self.transfers_to_inns
                and len(self.game.inns[self.player]) > 0
                and self.silks > 0):
                #Offer the opportunity to move silks around between Inns
                self.transfer_to_inn()

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

    def end_turn(self):
        '''Extends Lite Winds behaviour to keep track of free rests each turn.'''
        self.free_rests = self.num_free_rests
        super().end_turn()

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
        # Need to keep track of whether this Inn has been ransacked
        self.is_ransacked = False
        #Inherit player-specific characteristics that have been buffed
        self.value_inn_trade = game.value_inn_trade[player]
        self.transfer_inn_earnings = game.transfer_inn_earnings[player]
        self.inns_arrest = game.inns_arrest[player]
        self.confiscate_silks = game.confiscate_silks[player]
        self.resting_refurnishes = game.resting_refurnishes[player]
        if self.inns_arrest:
            #Enable arresting
            self.value_arrest = game.value_arrest

    def give_rest(self, adventurer):
        '''Takes into account whether this Inn has been ransacked, and applies card buffs
        '''
        if self.is_ransacked:
            return False
        if super().give_rest(adventurer):
            rest_cost = self.game.cost_inn_rest * adventurer.num_characters
            if self.resting_refurnishes and adventurer.pirate_token:
                logger.debug("Inn is refurnishing Adventurer, getting rid of their Pirate token.")
                adventurer.pirate_token = False
            if self.transfer_inn_earnings and self.silks > 0:
                logger.debug("Inn is moving income from providing rest directly to player's Vault")
                self.game.vault_silks[self.player] += rest_cost
                self.silks -= rest_cost
            if adventurer.rechoose_at_inns and adventurer.silks > self.game.cost_refresh_maps:
                logger.debug("Inn is offering Adventurer the chance to swap all their Chest maps.")
                if adventurer.player.check_buy_maps(adventurer):
                    adventurer.silks -= self.game.cost_refresh_maps
                    adventurer.swap_chest_maps()
            if adventurer.num_free_rests > 0:
                logger.debug("Inn is refunding Adventurer for free rest perk,")
                adventurer.silks += rest_cost
                self.silks -= rest_cost
                adventurer.num_free_rests -= 1  #a free rest has been used up
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

    def __init__(self, players, exploration_rules='continuous', rng=None):
        super().__init__(players, exploration_rules, rng)

        #Some rule values apply per player, so they can be modified by Culture cards
        self.num_manuscript_choices = {}
        self.value_inn_trade = {}
        self.rest_with_adventurers = {}
        self.transfer_inn_earnings = {}
        self.inns_arrest = {}
        self.confiscate_silks = {}
        self.resting_refurnishes = {}
        self.pool_maps = {}
        self.rechoose_at_inns = {}
        #And a placeholder for players to choose a Culture
        self.assigned_cultures = {}
        for player in players:
            self.num_manuscript_choices[player] = self.ruleset.num_manuscript_choices
            self.value_inn_trade[player] = self.ruleset.value_inn_trade
            self.rest_with_adventurers[player] = self.ruleset.rest_with_adventurers
            self.transfer_inn_earnings[player] = self.ruleset.transfer_inn_earnings
            self.inns_arrest[player] = self.ruleset.inns_arrest
            self.confiscate_silks[player] = self.ruleset.confiscate_silks
            self.resting_refurnishes[player] = self.ruleset.resting_refurnishes
            self.pool_maps[player] = self.ruleset.pool_maps
            self.rechoose_at_inns[player] = self.ruleset.rechoose_at_inns
            self.assigned_cultures[player] = None

        #Rebuild the card decks so that Culture and Manuscript cards join the Character deck
        self.card_count = 0
        self.culture_cards = [self.CARD_TYPE(self, card_type) for card_type in self.ruleset.culture_cards]
        self.character_cards = [self.CARD_TYPE(self, card_type) for card_type in self.ruleset.character_cards]
        self.manuscript_cards = [self.CARD_TYPE(self, card_type) for card_type in self.ruleset.manuscript_cards]

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

    def buy_maps(self, adventurer):
        '''Extends the parent with the potential for a free refresh of maps.

        Args:
            adventurer: the visiting Adventurer
        '''
        # If they have the perk, let them have one swap of maps for free
        if adventurer.rechoose_at_inns:
            cost_refresh_maps = self.cost_refresh_maps
            self.cost_refresh_maps = 0
            if adventurer.player.check_buy_maps(adventurer):
                adventurer.swap_chest_maps()
            self.cost_refresh_maps = cost_refresh_maps
        super().buy_maps(adventurer)

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
