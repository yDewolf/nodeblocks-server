from abc import ABC, abstractmethod

from nodeserver.server.web.app import NodeServerWebApp


class BaseRouter(ABC):
    app: NodeServerWebApp

    def __init__(self, app: NodeServerWebApp) -> None:
        self.app = app
    
    @abstractmethod
    def _setup_routes(self):
        pass