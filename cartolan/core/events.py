'''Game event stream: structured notifications from game logic to observers.

Game logic must not write to stdout: narration goes through module loggers
(logging.getLogger("cartolan...")), and state changes that UIs or servers may
want to react to are emitted as GameEvents via Game.emit().
'''

import logging
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GameEvent:
    '''A single notable occurrence in a game.

    kind: short dotted identifier, e.g. "move", "explore.fail", "attack.success"
    actor: the token or player that acted, if any
    data: free-form supporting detail
    '''
    kind: str
    actor: object = None
    data: dict = field(default_factory=dict)


class LoggingSubscriber:
    '''Default subscriber: writes events to the cartolan.game logger.'''

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger("cartolan.game")

    def __call__(self, event):
        self.logger.info("%s %s %s", event.kind,
                         getattr(getattr(event, "actor", None), "name", event.actor) or "",
                         event.data or "")
