from abc import ABC, abstractmethod
import logging
from multiprocessing import Queue
from queue import Empty
from typing import Generic, TypeVar, Union

from nodeserver.engine.protocols.ipc_protocol import IPCCommand, IPCCommandResponse, IPCEvent

logger = logging.getLogger("nds.worker")

class WorkerCommandHandler[T_Command: IPCCommand, T_Event: IPCEvent, T_Response: IPCCommandResponse](ABC):
    event_queue: Queue[Union[T_Event, T_Response]]
    command_queue: Queue[T_Command]

    def __init__(
            self,
            command_queue: Queue[T_Command], 
            event_queue: Queue[Union[T_Event, T_Response]] 
        ) -> None:
            self.command_queue = command_queue
            self.event_queue = event_queue

    @abstractmethod
    def dispatch(self, cmd: T_Command) -> T_Response:
        pass

    @abstractmethod
    def create_failed_response(self, message: str, request_id: str) -> IPCCommandResponse:
       pass

    # Must be called by the worker:

    def process_command(self, timeout: float = 0.05) -> None:
        try:
            command = self.command_queue.get(timeout=0.05)
            self._handle_command(command)
        except Empty:
            pass
    
    def process_pending_commands(self) -> None:
        while not self.command_queue.empty():
            try:
                command = self.command_queue.get_nowait()
                self._handle_command(command)
            except Empty:
                break

    # Internal Utils

    def _handle_command(self, command: T_Command):
        try:
            cmd_response = self.dispatch(command)
            if not cmd_response:
                logger.warning("Command '%s' missing response", command.__class__.__name__)
                cmd_response = self.create_failed_response(
                    message="No response returned by handler",
                    request_id=command.request_id
                )
            else:
                if hasattr(cmd_response, "request_id") and cmd_response.request_id is None:
                    object.__setattr__(cmd_response, "request_id", command.request_id)

                logger.debug("%s -> %s", command.__class__.__name__, cmd_response.status)
        
        except Exception as e:
            logger.error("Error executing command %s", command.__class__.__name__)
            cmd_response = self.create_failed_response(
                message=f"Internal error: {str(e)}",
                request_id=command.request_id
            )
            return

        self.event_queue.put(cmd_response) # type: ignore
