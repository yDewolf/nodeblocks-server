import re as regex
from types import CoroutineType
from typing import Any, Callable
from websockets.asyncio.server import ServerConnection

class Endpoint:
    raw_url: str
    param_names: dict[str, int]

    # required_fields: list[str]

    def __init__(self, raw_url: str) -> None:
        self.raw_url = raw_url
        self.param_names = {}
        self._setup()

    def _setup(self):
        splitted_url = self.raw_url.split("/")
        for idx, part in enumerate(splitted_url):
            if not part.startswith("{"):
                continue

            group = regex.search(r"(?<={).*?(?=})", part)
            if not group:
                continue
            
            self.param_names[group.group(0)] = idx


class URLRouter:
    routes: dict[Endpoint, Callable[[dict, ServerConnection], CoroutineType[Any, Any, dict | None]]]

    def __init__(self, routes: dict[Endpoint, Callable[[dict, ServerConnection], CoroutineType[Any, Any, dict | None]]]) -> None:
        self.routes = routes


    def route_url(self, url: str) -> tuple[dict, Callable[[dict, ServerConnection], CoroutineType[Any, Any, dict | None]]] | None:
        target_endpoint = None
        for endpoint in self.routes:
            if self.endpoint_matches_url(endpoint, url):
                target_endpoint = endpoint
                break
        
        if target_endpoint:
            parameters = self.get_url_parameters(target_endpoint, url)
            return parameters, self.routes[target_endpoint]

        return None


    @staticmethod
    def get_url_parameters(endpoint: Endpoint, url: str) -> dict:
        exploded_url = url.split("/")
        parameters = {}
        for param, idx in endpoint.param_names.items():
            value = exploded_url[idx]
            parameters[param] = value

        return parameters

    @staticmethod
    def endpoint_matches_url(endpoint: Endpoint, url: str) -> bool:
        exploded_endpoint = endpoint.raw_url.split("/")
        url = url.removesuffix("/")
        exploded_url = url.split("/")
        
        param_indexes = list(endpoint.param_names.values())
        if len(exploded_endpoint) != len(exploded_url):
            if len(exploded_endpoint) < len(exploded_url):
                return False
            
            for idx in range(len(exploded_endpoint)):
                if param_indexes.__contains__(idx):
                    continue

                if idx >= len(exploded_url):
                    return False
                
                if exploded_endpoint[idx] != exploded_url[idx]:
                    return False
                
        for idx in range(len(exploded_endpoint)):
            if param_indexes.__contains__(idx):
                continue
            
            if exploded_url[idx] != exploded_endpoint[idx]:
                return False
        
        return True