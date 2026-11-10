import asyncio
import logging
from typing import Optional

from nodeblocks.engine.runtime.protocols.engine_events import IPCEngineNodeEvent
from nodeblocks.engine.workers.protocols.general_worker_protocol import WorkerEvent
from nodeblocks.engine.workers.scene.protocols.scene_worker_protocol import IPCSceneWorkerEvent, SceneWorkerCommandResponse, WorkerEngineEventWrapper
from nodeblocks.server.protocols.web.messages.server.mappings.worker_event_map import get_worker_event_payload
from nodeblocks.server.protocols.web.messages.server.server_messages import ServerBatchEventWrapper, ServerCmdResponse, BaseServerMessage, ServerEngineEventWrapper, ServerMessageAdapter, ServerWorkerEventWrapper
from nodeblocks.server.protocols.web.messages.server.mappings.cmd_response_map import get_response_payload
from nodeblocks.server.protocols.web.messages.server.mappings.engine_event_map import get_engine_event_payload
from nodeblocks.server.web.app import NodeServerWebApp
from nodeblocks.server.web.exceptions.router_exceptions import CmdReponseMissingRequestId
from nodeblocks.server.web.routing.base_router import BaseDynamicRouter

logger = logging.getLogger("nds.server")

class SceneWebsocketEventRouter(BaseDynamicRouter):
    _event_buffers: dict[str, list[IPCSceneWorkerEvent]]
    batch_interval: float = 1 / 30

    def __init__(self, app: NodeServerWebApp) -> None:
        super().__init__(app)
        self.app.scene_worker_manager.set_event_callback(self._on_worker_event)
        self._event_buffers = {}

    # Router stuff

    def _setup_routes(self):
        pass

    async def start(self):
        self.add_task(
            asyncio.create_task(self._flush_event_buffers(), name="websocket_event_flusher")
        )
    
    async def stop(self):
        await super().stop()
        self._event_buffers.clear()

    # worker event callback

    async def _on_worker_event(self, scene_id: str, event: IPCSceneWorkerEvent):
        logger.debug("Event from scene: '%s': %s", scene_id, event)
        if isinstance(event, (SceneWorkerCommandResponse, WorkerEvent)):
            await self._dispatch_immediate(scene_id, event)
            return

        if isinstance(event, WorkerEngineEventWrapper):
            if scene_id not in self._event_buffers:
                self._event_buffers[scene_id] = []
            
            self._event_buffers[scene_id].append(event)
            return

        await self._dispatch_immediate(scene_id, event)

    async def _dispatch_immediate(self, scene_id: str, event: IPCSceneWorkerEvent):
        message = self._wrap_event(event)
        if message:
            await self.app.session_manager.broadcast_to_scene(
                scene_id=scene_id,
                message=message
            )

    # tasks

    async def _flush_event_buffers(self):
        while True:
            try:
                await asyncio.sleep(self.batch_interval)
                for scene_id, events in list(self._event_buffers.items()):
                    if not events:
                        continue

                    throttled_events = self._apply_throttling(events)
                    
                    batch_messages: list[ServerMessageAdapter] = []
                    for event in throttled_events:
                        message = self._wrap_event(event)
                        if message: batch_messages.append(message)

                    if len(batch_messages) == 1:
                        await self.app.session_manager.broadcast_to_scene(
                            scene_id=scene_id,
                            message=batch_messages[0],
                        )
                    elif batch_messages:
                        batch_packet = ServerBatchEventWrapper(
                            messages=batch_messages
                        )

                        await self.app.session_manager.broadcast_to_scene(
                            scene_id=scene_id,
                            message=batch_packet
                        )
                    
                    events.clear()

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error("Error flushing websocket event buffers: %s", e)

    # utils

    def _apply_throttling(self, events: list[IPCSceneWorkerEvent]) -> list[IPCSceneWorkerEvent]:
        latest_node_events: dict[str, WorkerEngineEventWrapper] = {}
        other_events: list[IPCSceneWorkerEvent] = []

        for event in events:
            if isinstance(event, WorkerEngineEventWrapper) and isinstance(event, IPCEngineNodeEvent):
                latest_node_events[event.node_uid] = event
                continue

            other_events.append(event)

        return other_events + list(latest_node_events.values())


    def _wrap_event(self, event: IPCSceneWorkerEvent) -> Optional[ServerMessageAdapter]:
        if isinstance(event, SceneWorkerCommandResponse):
            if not event.request_id:
                raise CmdReponseMissingRequestId(self.__class__, event.__class__)

            return ServerCmdResponse(
                cmd_uid=event.request_id,
                response_payload=get_response_payload(event)
            )

        elif isinstance(event, WorkerEvent):
            return ServerWorkerEventWrapper(
                event_payload=get_worker_event_payload(event)
            )

        elif isinstance(event, WorkerEngineEventWrapper):
            return ServerEngineEventWrapper(
                event_payload=get_engine_event_payload(event.engine_event),
            )

        logger.error("No wrap implementation for event: %s", event)
        return None
