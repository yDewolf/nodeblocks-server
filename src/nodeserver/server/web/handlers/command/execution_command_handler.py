from functools import singledispatchmethod

from nodeserver.engine.workers.scene.protocols.scene_worker_protocol import SceneWorkerExecutionState
from nodeserver.engine.workers.scene.protocols.scene_worker_commands import RuntimeCommand, UpdateExecutionModeCmd, UpdateExecutionStateCmd, PauseGraphCommand, GraphStepCommand
from nodeserver.server.protocols.web.messages.client.scene.scene_runtime_commands import ExecutionShortcutCommand, SceneExecutionCommand, SetExecutionModeCommand, SetExecutionStateCommand
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.providers.scene_worker_manager_protocol import ISceneWorkerManager
from nodeserver.server.protocols.session_protocols import SceneConnectionSession
from nodeserver.server.protocols.web.messages.client.base_client_command import BaseClientCommand
from nodeserver.server.protocols.web.messages.client.client_message_enums import ExecutionShortcuts
from nodeserver.server.web.handlers.base_command_handler import BaseSceneCmdHandler


class ExecutionCommandHandler(BaseSceneCmdHandler):
    @property
    def required_permission(self) -> ScenePermission:
        return ScenePermission.EXECUTE

    async def handle(
        self, 
        message: BaseClientCommand, 
        session: SceneConnectionSession, 
        worker_manager: ISceneWorkerManager
    ):
        if isinstance(message, ExecutionShortcutCommand):
            engine_cmd = self.handle_shortcut(
                message, 
                session,
                worker_manager
            )
            return
        
        engine_cmd = self.generate_engine_cmd(message)
        worker_manager.send_command_to_scene(session.scene_id, engine_cmd)


    @singledispatchmethod
    def generate_engine_cmd(self, cmd: SceneExecutionCommand) -> RuntimeCommand:
        # FIXME: better exception
        raise Exception(f"Command '{cmd.__class__.__name__}' is not implemented")

    @generate_engine_cmd.register
    def _(self, cmd: SetExecutionStateCommand):
        return UpdateExecutionStateCmd(
            request_id=cmd.cmd_uid,
            state=cmd.state, target_iterations=cmd.target_iterations
        )

    @generate_engine_cmd.register
    def _(self, cmd: SetExecutionModeCommand):
        return UpdateExecutionModeCmd(
            request_id=cmd.cmd_uid,
            mode=cmd.mode
        )


    def handle_shortcut(
        self, 
        cmd: ExecutionShortcutCommand,
        session: SceneConnectionSession,
        worker_manager: ISceneWorkerManager
    ) -> None:
        match cmd.shortcut:
            case ExecutionShortcuts.EXECUTION_STEP:
                worker_manager.send_command_to_scene(
                    session.scene_id,
                    GraphStepCommand(request_id=cmd.cmd_uid)
                )
            case ExecutionShortcuts.EXECUTION_PAUSE:
                worker_manager.send_command_to_scene(
                    session.scene_id,
                    PauseGraphCommand(request_id=cmd.cmd_uid)
                )

            case ExecutionShortcuts.EXECUTION_CONTINUE:
                state = worker_manager.get_scene_state(session.scene_id)
                if state != SceneWorkerExecutionState.STOPPED:
                    return
                worker_manager.send_command_to_scene(
                    session.scene_id,
                    UpdateExecutionStateCmd(
                        request_id=cmd.cmd_uid,
                        state=SceneWorkerExecutionState.RUNNING
                    )
                )

            case _:
                raise Exception("Execution shortcut not implemented")
