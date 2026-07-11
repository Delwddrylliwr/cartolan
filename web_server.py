'''Deprecated entry-point shim: use python -m cartolan.server.websocket_server instead.'''

from cartolan.server.websocket_server import *  # noqa: F401,F403
from cartolan.server.websocket_server import main

if __name__ == "__main__":
    main()
