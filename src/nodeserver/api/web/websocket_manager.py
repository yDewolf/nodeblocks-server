
from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.internal.websocket_handler import WebsocketHandler


class WebsocketInstanceManager(InstanceManager):
    websocket_handler: WebsocketHandler

    # TODO: Setup websocket routes etc.
