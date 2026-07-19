'''Web game server entry point: thin wrapper over cartolan.server.websocket_server.'''

from cartolan.server.websocket_server import *  # noqa: F401,F403
from cartolan.server.websocket_server import main

if __name__ == "__main__":
    main()
