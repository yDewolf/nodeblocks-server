
import asyncio
import logging
from typing import Optional

from nodeblocks.server.protocols.server_tasks import ServerTask, TaskState
from nodeblocks.server.protocols.web.messages.server.server_events import ServerStatusEvent, ServerStatuses
from nodeblocks.server.web.manager.server_session_manager import ServerSessionManager

logger = logging.getLogger("nds.server")

class ServerStatusManager:
    session_manager: ServerSessionManager
    status: ServerStatuses
    _tasks: dict[str, ServerTask]

    def __init__(self, session_manager: ServerSessionManager) -> None:
        self.session_manager = session_manager
        self.status = ServerStatuses.INITIALIZING
        self._tasks = {}

    # -- methods

    async def send_current_status(self, session_id: str):
        active_message = None
        # FIXME: múltiplas tasks podem estar rodando ao mesmo tempo
        for task in self._tasks.values():
            if task.state == TaskState.RUNNING or task.state == TaskState.FAILED:
                active_message = task.message or f"Executing: {task.name}"
                break

        message = self.session_manager.encode_event(ServerStatusEvent(
            status=self.status,
            message=active_message
        ))
        await self.session_manager.send_to_connection_id(message, session_id)

    def register_task(self, task_id: str, name: str, message: Optional[str] = None) -> str:
        self._tasks[task_id] = ServerTask(id=task_id, name=name, state=TaskState.RUNNING, message=message)
        logger.info("Registered task: %s", task_id)
        asyncio.create_task(self._evaluate_and_broadcast())
        return task_id

    async def update_task(self, task_id: str, state: TaskState, message: Optional[str] = None) -> None:
        if not task_id in self._tasks:
            return
        
        self._tasks[task_id].state = state
        if message is not None:
            self._tasks[task_id].message = message

        logger.info("Updating %s task state to: %s", task_id, state)
        await self._evaluate_and_broadcast()

    # Shouldn't be used unless it is a critical situation
    async def update_server_status(self, status: ServerStatuses, message: Optional[str] = None):
        self.status = status
        await self.session_manager.broadcast(ServerStatusEvent(
            status=status,
            message=message
        ))

    # -- helpers

    async def complete_task(self, task_id: str, message: Optional[str] = None) -> None:
        await self.update_task(task_id, TaskState.COMPLETED, message)
        logger.info("%s task was completed.", task_id)

    async def fail_task(self, task_id: str, message: Optional[str] = None) -> None:
        await self.update_task(task_id, TaskState.FAILED, message)
        logger.info("%s task failed.", task_id)

    # -- utils

    async def _evaluate_and_broadcast(self) -> None:
        if not self._tasks:
            return

        new_status = self._calculate_global_status()
        active_message = None
        for task in self._tasks.values():
            if task.state == TaskState.FAILED:
                active_message = f"Error in task {task.name}: {task.message or 'Unspecified error'}"
                break
            elif task.state == TaskState.RUNNING:
                active_message = task.message or f"Running: {task.name}"

        if new_status != self.status:
            self.status = new_status
            await self.session_manager.broadcast(ServerStatusEvent(
                status=self.status,
                message=active_message
            ))
            logger.debug("Server status updated to: %s", self.status)

    def _calculate_global_status(self) -> ServerStatuses:
        states = [task.state for task in self._tasks.values()]
        if any(state == TaskState.FAILED for state in states):
            return ServerStatuses.FAILED
            
        if states and all(state == TaskState.COMPLETED for state in states):
            return ServerStatuses.READY
            
        if any(state == TaskState.RUNNING for state in states):
            return ServerStatuses.SETTING_UP
        
        return ServerStatuses.INITIALIZING
