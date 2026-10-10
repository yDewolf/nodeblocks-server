from abc import ABC

from nodeserver.server.web.app import NodeServerWebApp

class BaseWebPolicy(ABC):
    app: NodeServerWebApp

    def __init__(self, app: NodeServerWebApp) -> None:
        self.app = app
