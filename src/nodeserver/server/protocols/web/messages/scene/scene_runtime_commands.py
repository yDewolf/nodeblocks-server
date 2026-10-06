from typing import Annotated, Literal, Optional, Union

from pydantic import Field

from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState
from nodeserver.server.protocols.web.messages.base_client_command import BaseClientCommand, CommandGroups
from nodeserver.server.protocols.web.messages.client_message_enums import ExecutionShortcuts, SceneExecutionCmdTypes


class SceneExecutionCommand(BaseClientCommand):
    cmd_group: Literal[CommandGroups.EXECUTION]
    type: SceneExecutionCmdTypes


class SetExecutionStateCommand(SceneExecutionCommand):
    type: Literal[SceneExecutionCmdTypes.SET_EXECUTION_STATE]

    state: SceneWorkerExecutionState
    target_iterations: Optional[int] = None # TODO: talvez fazer um comando separado para isso

class SetExecutionModeCommand(SceneExecutionCommand):
    type: Literal[SceneExecutionCmdTypes.SET_EXECUTION_MODE]
    mode: SceneWorkerExecutionMode


class ExecutionShortcutCommand(SceneExecutionCommand):
    type: Literal[SceneExecutionCmdTypes.EXECUTION_SHORTCUT]
    shortcut: ExecutionShortcuts

ExecutionCommandAdapter = Annotated[
    Union[SetExecutionModeCommand, SetExecutionStateCommand, ExecutionShortcutCommand],
    Field(discriminator="type")
]