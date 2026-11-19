from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Union

from aiohttp import web

from nodeblocks.server.web.app import NodeServerWebApp

logger = logging.getLogger("nds.server")
class BaseRouter(ABC):
    app: NodeServerWebApp

    def __init__(self, app: NodeServerWebApp) -> None:
        self.app = app
    
    @abstractmethod
    def _setup_routes(self):
        pass

    def public_routes(self, routes: Union[web.AbstractRoute, list[web.AbstractRoute]]) -> Union[web.AbstractRoute, list[web.AbstractRoute]]:
        for route in routes if isinstance(routes, list) else [routes]:
            info = route.get_info()
            path = info.get("path") or info.get("formatter")
            
            if path: self.app.public_routes.add(path)
            else: logger.warning("Failed to add route '%s' to public routes", info)
        
        return routes

    def bypass_ready(self, routes: Union[web.AbstractRoute, list[web.AbstractRoute]]) -> Union[web.AbstractRoute, list[web.AbstractRoute]]:
        for route in routes if isinstance(routes, list) else [routes]:
            info = route.get_info()
            path = info.get("path") or info.get("formatter")
            
            if path: self.app.ready_bypass.add(path)
            else: logger.warning("Failed to add route '%s' to bypass ready routes", info)
        
        return routes


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
