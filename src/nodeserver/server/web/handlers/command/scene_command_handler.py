from functools import singledispatchmethod

from nodeserver.engine.workers.scene.protocols.scene_worker_commands import GetSceneDataCommand, IPCSceneWorkerCommand, LoadSceneDataCommand, SaveSceneCommand, SetSceneAutosaveCommand
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.providers.scene_worker_manager_protocol import ISceneWorkerManager
from nodeserver.server.protocols.session_protocols import SceneConnectionSession
from nodeserver.server.protocols.web.messages.client.base_client_command import BaseClientCommand
from nodeserver.server.protocols.web.messages.client.scene.client_scene_commands import ClientGetSceneDataCmd, ClientLoadSceneCmd, ClientSaveSceneCmd, ClientSceneCommand, ClientSetSceneAutosaveCmd, SceneCommandAdapter
from nodeserver.server.web.handlers.base_command_handler import BaseSceneCmdHandler


class SceneCommandHandler(BaseSceneCmdHandler):
    @property
    def required_permission(self) -> ScenePermission:
        return ScenePermission.ADMIN # TODO: talvez mudar essa permissão aqui

    async def handle(
        self, 
        message: BaseClientCommand, 
        session: SceneConnectionSession, 
        worker_manager: ISceneWorkerManager
    ):
        cmd = self.generate_cmd(message)
        worker_manager.send_command_to_scene(session.scene_id, cmd)

    @singledispatchmethod
    def generate_cmd(self, cmd: ClientSceneCommand) -> IPCSceneWorkerCommand:
        # FIXME: exception
        raise Exception(f"Command not implemented for payload: {cmd.__class__.__name__}")

    @generate_cmd.register
    def _(self, cmd: ClientLoadSceneCmd):
        return LoadSceneDataCommand(request_id=cmd.cmd_uid, scene_data=cmd.payload)

    @generate_cmd.register
    def _(self, cmd: ClientSaveSceneCmd):
        return SaveSceneCommand(request_id=cmd.cmd_uid)

    @generate_cmd.register
    def _(self, cmd: ClientSetSceneAutosaveCmd):
        return SetSceneAutosaveCommand(request_id=cmd.cmd_uid, autosave=cmd.autosave)

    @generate_cmd.register
    def _(self, cmd: ClientGetSceneDataCmd):
        return GetSceneDataCommand(request_id=cmd.cmd_uid)

    