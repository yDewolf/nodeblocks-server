from abc import ABC, abstractmethod
import asyncio
import logging

from nodeblocks.server.web.app import NodeServerWebApp

logger = logging.getLogger("nds.server")
class BaseRouter(ABC):
    app: NodeServerWebApp

    def __init__(self, app: NodeServerWebApp) -> None:
        self.app = app
    
    @abstractmethod
    def _setup_routes(self):
        pass


class BaseDynamicRouter(BaseRouter, ABC):
    _tasks: list[asyncio.Task]

    def __init__(self, app: NodeServerWebApp) -> None:
        super().__init__(app)
        self._tasks = []

    @abstractmethod
    async def start(self):
        pass

    async def stop(self):
        logger.info("Stopping %s...", self.__class__.__name__)
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            logger.info("Finished %s's task: %s", self.__class__.__name__, task.get_name())

    def add_task(self, task: asyncio.Task):
        self._tasks.append(task)
