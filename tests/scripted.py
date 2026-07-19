'''A fully deterministic Player for rule tests.

Declines every optional action and banks everything by default; individual
responses can be queued per method with script(), consumed in order.
'''

from collections import deque

from cartolan.players.base import Player


class ScriptedPlayer(Player):
    def __init__(self, name="blue"):
        super().__init__(name)
        self._scripts = {}

    def script(self, method, *values):
        '''Queues return values for the named check_*/choose_* method.'''
        self._scripts.setdefault(method, deque()).extend(values)
        return self

    def _answer(self, method, default):
        queue = self._scripts.get(method)
        if queue:
            return queue.popleft()
        return default

    # movement is driven directly by tests, not via continue_turn
    def continue_turn(self, adventurer):
        raise AssertionError("ScriptedPlayer turns are driven explicitly in tests")

    def continue_move(self, adventurer):
        raise AssertionError("ScriptedPlayer moves are driven explicitly in tests")

    # -- decisions --
    def check_trade(self, adventurer, tile):
        return self._answer("check_trade", True)

    def check_rest(self, adventurer, token):
        return self._answer("check_rest", False)

    def check_collect_silks(self, inn):
        return self._answer("check_collect_silks", False)

    def check_hire_inn(self, adventurer):
        return self._answer("check_hire_inn", False)

    def check_move_inn(self, adventurer):
        return self._answer("check_move_inn", None)

    def check_buy_adventurer(self, adventurer):
        return self._answer("check_buy_adventurer", False)

    def check_buy_inn(self, adventurer, report=""):
        return self._answer("check_buy_inn", None)

    def check_hire_companion(self, adventurer):
        return self._answer("check_hire_companion", False)

    def check_buy_maps(self, adventurer):
        return self._answer("check_buy_maps", False)

    def check_buy_manuscript(self, adventurer):
        return self._answer("check_buy_manuscript", False)

    def check_bank_amount(self, adventurer, chest_silks, vault_silks):
        return self._answer("check_bank_amount", chest_silks)

    def check_travel_silks(self, adventurer, vault_silks, default):
        return self._answer("check_travel_silks", 0)

    def check_attack_adventurer(self, adventurer, other_adventurer):
        return self._answer("check_attack_adventurer", False)

    def check_attack_inn(self, adventurer, inn):
        return self._answer("check_attack_inn", False)

    def check_steal_amount(self, adventurer, maximum, default):
        return self._answer("check_steal_amount", default)

    def check_restore_inn(self, adventurer, inn):
        return self._answer("check_restore_inn", False)

    def check_transfer_inn(self, adventurer):
        return self._answer("check_transfer_inn", None)

    def check_steal_map(self, adventurer, victim):
        return self._answer("check_steal_map", False)

    def check_steal_manuscript(self, adventurer, victim):
        return self._answer("check_steal_manuscript", False)

    def choose_map_pile(self, adventurer, options):
        return self._answer("choose_map_pile", options[0])

    def choose_card(self, adventurer, cards):
        return self._answer("choose_card", cards[0])

    def choose_tile(self, adventurer, tiles):
        return self._answer("choose_tile", tiles[0])
