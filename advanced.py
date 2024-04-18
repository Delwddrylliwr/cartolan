'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

import random
from beginner import AgentBeginner
from regular import AdventurerRegular, AgentRegular, CityTileRegular
from base import Player, Token, WindDirection, TileEdges, Card

class CardAdvanced(Card):
    '''Modifies the rules for objects from other Cartolan classes.
    '''
    def __init__(self, game, card_type):
        super().__init__(game, card_type)
        self.buffs = game.card_type_buffs[card_type[3:]]

    #some supporting functions to deal with different attribute types
    def add(self, a, b):
        '''Applies elementwise addition when given lists of lists rather than numbers
        '''
        if isinstance(a, list) and isinstance(b, list):
            if isinstance(a[0], list) and isinstance(b[0], list):
                combs = [[a[i], b[i]] for i in range(min(len(a), len(b)))]
                return [[ comb[0][j] + comb[1][j] for j in range(min(len(comb[0]), len(comb[1])))] for comb in combs]
        else:
            return a + b

    def sub(self, a, b):
        '''Applies elementwise addition when given lists of lists rather than numbers
        '''
        if isinstance(a, list) and isinstance(b, list):
            if isinstance(a[0], list) and isinstance(b[0], list):
                combs = [[a[i], b[i]] for i in range(min(len(a), len(b)))]
                return [[ comb[0][j] - comb[1][j] for j in range(min(len(comb[0]), len(comb[1])))] for comb in combs]
        else:
            return a - b

    def apply_buffs(self, target):
        '''Incorporates rule changes for the Adventurer/Agent that come from this cards
        '''
        if isinstance(target, Token):
            player_name = target.player.name
            print("Adding card buffs for "+player_name+"...")
            for buff_attr in self.buffs:
                #Check that the token has the attribute associated with the buff
                current_attr_val = getattr(target, buff_attr, None) 
                if current_attr_val is not None:
                    print("For "+player_name+" "+target.__class__.__name__+", adding a buff to their "+buff_attr)
                    #Apply the buff
                    if self.buffs[buff_attr]["buff_type"] == "boost":
                        setattr(target, buff_attr, self.add(current_attr_val, self.buffs[buff_attr]["buff_val"]))
                    elif self.buffs[buff_attr]["buff_type"] == "new":
                        setattr(target, buff_attr, self.buffs[buff_attr]["buff_val"])
                    print(player_name+" " +target.__class__.__name__+"'s "+buff_attr+" now has value "+str(getattr(target, buff_attr, None)))
        elif isinstance(target, Player):
            player_name = target.name
            print("Adding card buffs for "+player_name+"...")
            for buff_attr in self.buffs:
                #Check that the token has the attribute associated with the buff
                current_attr_val = getattr(self.game, buff_attr, None)
                #@TODO allow for games sharing all attributes with adventurers and agents...
                if isinstance(current_attr_val, dict):
                    if current_attr_val[target] is not None:
                        print("For "+player_name+", adding a buff to their "+buff_attr)
                        #Apply the buff
                        current_attr_val[target] = self.buffs[buff_attr]["buff_val"]
            #                    setattr(self.game, buff_attr, current_attr_val)
                        print(player_name+"'s "+buff_attr+" now has value "+str(getattr(self.game, buff_attr, None)[target]))
        else:
            player_name = "Anonymous"
        
    
    def remove_buffs(self, target):
        '''Reverts rule changes for the Adventurer/Agent that come from this card
        '''
        if isinstance(target, Token):
            player_name = target.player.name
            print("Removing card buffs for "+player_name+"...")
            for buff_attr in self.buffs:
                #Check that the token has the attribute associated with the buff
                current_attr_val = getattr(target, buff_attr, None) 
                if current_attr_val is not None:
                    #Remove the buff
                    if self.buffs[buff_attr]["buff_type"] == "boost":
                        setattr(target, buff_attr, self.sub(current_attr_val, self.buffs[buff_attr]["buff_val"]))
                    elif self.buffs[buff_attr]["buff_type"] == "new":
                        #@TODO if a buff has been doubled up then it shouldn't be lost
                        setattr(target, buff_attr, getattr(self.game, buff_attr))
                    print(player_name+"'s "+buff_attr+" now has value "+str(getattr(target, buff_attr, None)))
        elif isinstance(target, Player):
            player_name = target.name
        else:
            player_name = "Anonymous"
        
class AdventurerAdvanced(AdventurerRegular):
    '''Extends to allow a set of map tiles to be carried by each Adventurer in their chest and placed instead of a random one
    '''
    def __init__(self, game, player, starting_city):
        super().__init__(game, player, starting_city)
        
        #Bring in game variables that might be altered by company/character stats
        #First those specific to Adventurers
        self.defence_rounds = game.defence_rounds
        self.agent_on_existing = game.agent_on_existing
        self.rest_after_placing = game.rest_after_placing
        self.transfers_to_agents = game.transfers_to_agents
        self.attacks_abandon = game.attacks_abandon
        self.num_free_rests = game.num_free_rests
        self.free_rests = 0
        #Also player-specific characteristics
        self.rest_with_adventurers = game.rest_with_adventurers[player]
        self.confiscate_treasure = game.confiscate_treasure[player]
        self.pool_maps = game.pool_maps[player]
        self.rechoose_at_agents = game.rechoose_at_agents[player]
        #Prepare to hold cards
        self.character_card = None
        self.discovery_cards = []
        #Randomly draw a Character card
        #let the player choose between multiple character cards if the game visual is already started
        if self.game.game_started:
            self.choose_character()
        #Take on any changes to rules based on the Company card
#        game.assigned_cadres[player].apply_buffs(self)
        #If the pool maps buff has been applied then the chest maps will be shared with other Adventurers
        if self.pool_maps:
            peers = game.adventurers[player]
            peers[0].num_chest_tiles += self.num_chest_tiles
            self.chest_tiles = peers[0].chest_tiles 
            self.num_chest_tiles = peers[0].num_chest_tiles
            #@TODO keep this synched as buffs give individual adventurers more maps
    
    def choose_character(self):
        '''Lets the player choose a character card from a random subset
        '''
        character_cards = self.game.character_cards
        card_options = random.sample(character_cards, k=self.game.num_character_choices[self.player])
        self.character_card = self.player.choose_card(self, card_options)
        character_cards.remove(self.character_card)
        #Take on the changes to rules based on the Character card
        self.character_card.apply_buffs(self)
        #Now some ugly fixes where the card buff alone wasn't enough for desired behaviour
        self.replenish_chest_tiles() #in case the buffs increased the chest tile
        # If exploration values have been boosted
        self.value_fill_map_gap = self.game.value_fill_map_gap
        for water_edges in self.value_fill_map_gap:
            for exploration_value in water_edges:
                exploration_value += self.bonus_fill_map_gap

    def discover_card(self, card):
        '''Adds a Discovery card to the Adventurer, modifying rules according to the card's buffs
        '''
        print(self.player.name+"'s Adventurer has received the card of type "+card.card_type)
        self.discovery_cards.append(card)
        card.apply_buffs(self)
        # Now some ugly fixes where the card buff alone wasn't enough for desired behaviour
        self.replenish_chest_tiles()  # in case the buffs increased the chest tile
        #If exploration values have been boosted
        self.value_fill_map_gap = self.game.value_fill_map_gap
        for water_edges in self.value_fill_map_gap:
            for exploration_value in water_edges:
                exploration_value += self.bonus_fill_map_gap
        #If maps are pooled then compare to peers
        if self.pool_maps:
            peers = self.game.adventurers[self.player]
            if not peers[0].num_chest_tiles == self.num_chest_tiles:
                peers[0].num_chest_tiles = self.num_chest_tiles
    
    def lose_card(self, card):
        '''Removes a discovery card from the Adventurer, modifying rules according to what buffs were previously being provided
        '''
        print(self.player.name+"'s Adventurer has lost a card of type "+card.card_type)
        self.discovery_cards.remove(card)
        card.remove_buffs(self)
        # Now some ugly fixes where the card buff alone wasn't enough for desired behaviour
        self.replenish_chest_tiles()  # in case the buffs increased the chest tile
        # If exploration values have been boosted
        self.value_fill_map_gap = self.game.value_fill_map_gap
        for water_edges in self.value_fill_map_gap:
            for exploration_value in water_edges:
                exploration_value += self.bonus_fill_map_gap
        #If maps are pooled then compare to peers
        if self.pool_maps:
            peers = self.game.adventurers[self.player]
            if not peers[0].num_chest_tiles == self.num_chest_tiles:
                peers[0].num_chest_tiles = self.num_chest_tiles
    
    def can_rest(self, token):
        '''checks whether the Adventurer can rest with an Agent on this tile'''
        restable = False
        #Make sure that wealth isn't a barrier when free rests are available
        if self.free_rests > 0:
            self.wealth += self.game.cost_agent_rest
        if super().can_rest(token):
#            print("Deemed that could rest with Agent")
            restable = True
        # can the adventurer rest with an adventurer instead?
        elif (self.rest_with_adventurers
              and isinstance(token, AdventurerAdvanced)
              and token not in self.agents_rested
              and not token == self):
#            print("Checking if can rest with an Adventurer")
            if (token.player == self.player 
                or (self.wealth >= self.game.cost_agent_rest
                and not self.pirate_token)
                or (self.free_rests > 0
                and not self.pirate_token)):
#                print("Deemed that resting with an Adventurer is possible.")
                restable = True
        else:
#            print("Deemed rest was impossible with "+token.__class__.__name__)
            restable = False
        if self.free_rests > 0:
            self.wealth -= self.game.cost_agent_rest
        return restable
        
    def trade(self, tile):
        '''Extends to allow agents to profit from trade
        '''
        if super().trade(tile):
             # check whether there is an Agent on the tile
            if tile.agent is not None:
                tile.agent.manage_trade(self)
            return True
        else: return False        
    
    def rest(self, token):
        '''Extends Regular to allow for resting with Adventurers in some circumstances
        
        Arguments:
            token accepts a Cartolan Token
        '''
        #Ensure that wealth isn't a barrier when free rests are available
        if self.free_rests > 0:
            self.wealth += self.game.cost_agent_rest
        if isinstance(token, AgentAdvanced):
            rested = token.give_rest(self)
#        print("Make sure that the adventurer is equipped with the right method")
        elif self.rest_with_adventurers and not callable(getattr(token, "give_rest", None)):
            token.cost_agent_rest = token.game.cost_agent_rest
#            token.give_rest = AgentAdvanced.give_rest
#            return token.give_rest(self)
            rested = AgentBeginner.give_rest(token, self)
        else: 
            rested = False
        #Remove any wealth compensation for free rest
        if self.free_rests > 0:
            if rested and not token.player == self.player:
                self.free_rests -= 1
                token.wealth -= self.game.cost_agent_rest #If the rest was free then the Inn shouldn't be rewarded
            else:
                self.wealth -= self.game.cost_agent_rest
        return rested
    
    def attack(self, token):
        '''Extends Regular mode to allow stealing of Chest Tiles
        '''
        #If the target Adventurer has a defensive buff to force multiple rounds of attack then these need to be won first
        if isinstance(token, AdventurerAdvanced):
            for defence_round in range(0, token.defence_rounds-1):
                if random.random() > self.attack_success_prob:
                    return False
        if super().attack(token):
            if isinstance(self.current_tile, CityTileRegular): #If on a city then there's no attacking
                return True
            #Steal Discovery cards
            if isinstance(token, AdventurerAdvanced):
                if len(token.discovery_cards) > 0:
#                    stolen_card = token.discovery_cards.pop(random.randint(0, len(token.discovery_cards)-1))
                    stolen_card = self.player.choose_card(self, token.discovery_cards)
                    token.lose_card(stolen_card)
                    self.discover_card(stolen_card)
            if self.attacks_abandon: #Adventurers will return to cities, Agents are removed
                if isinstance(token, AdventurerRegular):
                    if not isinstance(token.current_tile, CityTileRegular): #in case they were a Pirate already sent back to a city
                        token.end_expedition()
                elif isinstance(token, AgentRegular):
                    token.dismiss()
            return True
        else:
            return False
        
    def interact_tile(self):
        '''Extends the Regular, to allow placing Agents on existing tiles for some Adventurer buffs
        '''
        super().interact_tile()
        if self.agent_on_existing and self.check_tile_available(self.current_tile):
            #An agent can still be placed on this existing tile, but at the cost of placing from the city
            cost_exploring = self.game.cost_agent_exploring
            cost_existing = self.game.cost_agent_from_city
            if self.wealth >= cost_existing:
                self.cost_agent_exploring = cost_existing
#                self.place_agent()
                if super().place_agent() and self.rest_after_placing:
                    self.agents_rested.remove(self.current_tile.agent)
                self.cost_agent_exploring = cost_exploring
        # if (self.transfers_to_agents 
        #     and len(self.game.agents[self.player]) > 0 
        #     and self.wealth > 0):
        #     #Offer the opportunity to move wealth around between Agents
        #     self.transfer_to_agent()
    
#    def place_agent(self):
#        '''Extends standard behaviour to allow a buff with same-turn resting
#        '''
#        if super().place_agent() and self.rest_after_placing:
#            self.agents_rested.remove(self.current_tile.agent)
#            return True
#        else: return False
    
    # def discover(self, tile):
    #     '''Extends standard behaviour to allow transfers to Agents even after exploration.
    #     '''
    #     super().discover(tile)
    #     if (self.transfers_to_agents 
    #         and len(self.game.agents[self.player]) > 0 
    #         and self.wealth > 0):
    #         #Offer the opportunity to move wealth around between Agents
    #         self.transfer_to_agent()
    #     return True
    
    def transfer_to_agent(self):
        '''Offers the opporutnity to transfer current wealth to any of the player's Agents
        '''
        transfer_agent = self.player.check_transfer_agent(self)
        while isinstance(transfer_agent, AgentAdvanced):
            #Check the amount to transfer and move it
            transfer_amount = self.player.check_deposit(self, self.wealth, -transfer_agent.wealth)
            self.wealth -= transfer_amount
            transfer_agent.wealth += transfer_amount
            #See if another transfer is desired
            transfer_agent = self.player.check_transfer_agent(self)
    
    def restore_agent(self, agent):
        '''Extends standard behaviour to allow a buff with same-turn resting
        '''
        if super().restore_agent(agent) and self.rest_after_placing:
            self.agents_rested.remove(self.current_tile.agent)
            return True
        else: return False        
    
    def interact_tokens(self):
        '''Extends regular to attack even poor Adventurers if the card is held that will send them home.
        '''
        super().interact_tokens()
        if self.current_tile.adventurers:
            for adventurer in self.current_tile.adventurers:
#                print("Checking whether special interactions are possible with "+adventurer.player.name+" player's Adventurer")
                if (self.attacks_abandon and adventurer.wealth == 0 #give the option to send the opponent to a city even if they have no wealth 
                    and not self == adventurer):
                    if self.player.check_attack_adventurer(self, adventurer):
                        self.attack(adventurer)
                if self.rest_with_adventurers and self.can_rest(adventurer):
#                    print("Checking whether player wants one of the adventurers on the current tile to give rest.")
                    if self.player.check_rest(self, adventurer):
                        self.rest(adventurer)
        if self.current_tile.agent is not None:
#            print("Checking whether special interactions are possible with "+self.current_tile.agent.player.name+"'s Agent")
            agent = self.current_tile.agent
            if (agent.agents_arrest and not agent.is_dispossessed 
                and self.pirate_token and not agent.player == self.player):
                if random.random() < self.game.attack_success_prob:
                    AdventurerAdvanced.arrest(agent, self) #The arrest function should only use common features of the common parent Token class
#                   self.current_tile.agent.arrest(self) #The arrest function should only use common features of the common parent Token class
                    self.end_turn()
            if (self.transfers_to_agents 
                and len(self.game.agents[self.player]) > 0 
                and self.wealth > 0):
                #Offer the opportunity to move wealth around between Agents
                self.transfer_to_agent()
    
    def arrest(self, pirate):
        '''Extends regular behaviour to allow capture of wealth for particular buffs.
        '''
        if self.confiscate_treasure and self.pirate.wealth > 0:
            self.wealth += pirate.wealth
            pirate.wealth = 0
        AdventurerRegular.arrest(self, pirate)

    def end_turn(self):
      '''Extends beginner behaviour to keep track of free rests each turn.'''
        self.free_rests = self.num_free_rests
        super().end_turn()

class AgentAdvanced(AgentRegular):
    '''Extends Regular mode to allow Agents' rules to be changed by cards
    '''
    def __init__(self, game, player, tile):
        super().__init__(game, player, tile)
        #Inherit player-specific characteristics that have been buffed
        self.value_agent_trade = game.value_agent_trade[player]
        self.transfer_agent_earnings = game.transfer_agent_earnings[player] 
        self.agents_arrest = game.agents_arrest[player]
        self.confiscate_treasure = game.confiscate_treasure[player]
        self.resting_refurnishes = game.resting_refurnishes[player]
        if self.agents_arrest:
            #Enable arresting
            self.value_arrest = game.value_arrest
#            self.arrest = AdventurerRegular.arrest
    
    def give_rest(self, adventurer):
        '''Extends Regular mode to allow buffs from cards
        '''
        if AgentRegular.give_rest(self, adventurer):
            if self.resting_refurnishes and adventurer.pirate_token:
                print("Agent is refurnishing Adventurer, getting rid of their Pirate token.")
                adventurer.pirate_token = False
            if self.transfer_agent_earnings and self.wealth > 0:
                print("Agent is moving income from providing rest directly to player's Vault")
                self.game.player_wealths[self.player] += self.game.cost_agent_rest
                self.wealth -= self.game.cost_agent_rest
            if adventurer.rechoose_at_agents and adventurer.wealth > self.game.cost_refresh_maps:
                print("Agent is offering Adventurer the chance to swap all their Chest maps.")
                if adventurer.player.check_buy_maps(adventurer):
                    adventurer.wealth -= self.game.cost_refresh_maps
                    adventurer.rechoose_chest_tiles()
            if adventurer.num_free_rests > 0:
                print("Agent is refunding Adventurer for free rest perk,")
                adventurer.wealth += self.game.cost_agent_rest
                self.wealth -= self.game.cost_agent_rest
                adventurer.num_fre_rests -= 1 #a free rest has been used up
            return True
        else:
            return False
        
    def manage_trade(self, adventurer):
        '''Receives wealth when trade takes place on its tile, either keeping this or giving it to an Adventurer of the same player
        
        Arguments:
        Cartolan.Adventurer the Adventurer making the trade
        '''
        #check whether dispossessed
        if self.is_dispossessed:
            return False
        #check whether Adventurer trading is from the same player
        elif adventurer.player == self.player:
            if self.transfer_agent_earnings:
                print("Agent on tile "+str(self.current_tile.tile_position.longitude)+", "+str(self.current_tile.tile_position.latitude)+
                      " has transferred trade income direct to the bank instead of to the Adventurer")
                adventurer.wealth -= adventurer.value_trade
                self.game.player_wealths[adventurer.player] += adventurer.value_trade
        else:
            # retain wealth if they are a different player
            print("Agent on tile " +str(self.current_tile.tile_position.longitude)+","
                  +str(self.current_tile.tile_position.longitude)+ " has kept monopoly bonus")
            self.wealth += self.value_agent_trade
        return True

class CityTileAdvanced(CityTileRegular):
    '''Extends to replenish Chest Tiles, and offer purchase of refreshed chest tiles
    '''
    def offer_purchases(self, adventurer):
       '''Extends to allow rule changes from cards
       '''
       self.buy_adventurers(adventurer)
       self.buy_agents(adventurer)
       self.buy_manuscripts(adventurer)
       self.buy_maps(adventurer)

    def buy_manuscripts(self, adventurer):
        '''Offers the visiting Adventurer the chance to upgrade themselves.

        Args:
            adventurer: the visiting adventurer
        '''
        print(
            "Offering " + adventurer.player.name + "'s adventurer the chance to upgrade the Adventurer with a Discovery/Manuscript card")
        available_cards = self.game.discovery_cards
        rejected_cards = []
        while (available_cards
               and adventurer.game.player_wealths[adventurer.player] >= self.game.cost_tech
               and adventurer.player.check_buy_tech(adventurer)):

            print(adventurer.player.name + "'s has chosen to buy a Manuscript card")
            card_options = []
            # Offer several cards, but only those which don't duplicate another one time card buff the Adventurer already has
            while (len(card_options) < self.game.num_discovery_choices[adventurer.player]
                   and available_cards):
                new_tech_card = available_cards.pop(random.randint(0, len(available_cards) - 1))
                # Check whether this is a one off perk and then whether its a duplicate, returning it and drawing another if so
                for buff_attr in new_tech_card.buffs:
                    if new_tech_card.buffs[buff_attr]["buff_type"] == "new":
                        if buff_attr in adventurer.character_card.buffs:
                            rejected_cards.append(new_tech_card)
                            break
                        for existing_card in adventurer.discovery_cards:
                            if buff_attr in existing_card.buffs:
                                rejected_cards.append(new_tech_card)
                                break
                card_options.append(new_tech_card)
            if card_options:  # Providing there were some valid discovery cards still available, let the player choose
                chosen_card = adventurer.player.choose_card(adventurer, card_options)
                card_options.remove(chosen_card)
                adventurer.discover_card(chosen_card)
                adventurer.game.player_wealths[adventurer.player] -= self.game.cost_tech
            available_cards += card_options  # Return the remaining options to the deck
            available_cards += rejected_cards  # Return the cards that weren't suitable to the Discovery deck

    def buy_maps(self, adventurer):
        '''Extends the parent with the potential for a free refresh of maps.

        Args:
            adventurer: the visiting Adventurer
        '''
        # If they have the perk, let them have one swap of maps for free
        if adventurer.rechoose_at_agents:
            cost_refresh_maps = self.game.cost_refresh_maps
            self.game.cost_refresh_maps = 0
            if adventurer.player.check_buy_maps(adventurer):
                adventurer.rechoose_chest_tiles()
            self.game.cost_refresh_maps = cost_refresh_maps
        super().buy_maps(adventurer)


class CapitalTileAdvanced(CityTileAdvanced):
    def __init__(self, game, tile_back = "water"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(True,True,True,True)):
        return super().__init__(game, wind_direction, tile_edges, True, True)

class MythicalTileAdvanced(CityTileAdvanced):
    def __init__(self, game, tile_back = "land"
                 , wind_direction = WindDirection(True,True)
                 , tile_edges = TileEdges(False,False,False,False)):
        return super().__init__(game, wind_direction, tile_edges, False, False)