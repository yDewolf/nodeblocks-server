
from functools import singledispatchmethod
from typing import Optional

from nodeserver.engine.workers.scene.protocols.scene_worker_commands import AddNodeData, AddNodesCommand, RemoveNodesCommand, SceneGraphCommand, UpdateNodeData, UpdateNodesCommand
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.providers.scene_worker_manager_protocol import ISceneWorkerManager
from nodeserver.server.protocols.session_protocols import SceneConnectionSession
from nodeserver.server.protocols.web.messages.client_message_enums import GraphActionTypes
from nodeserver.server.protocols.web.messages.graph.client_graph_commands import ClientGraphCommand, ConnGraphCommand, NodeGraphCommand
from nodeserver.server.protocols.web.messages.graph.graph_action_payloads import NodeActionPayloadAdapter, NodeAddUpdateAction, NodeRemoveAction
from nodeserver.server.web.handlers.base_command_handler import BaseSceneCmdHandler

# TODO:
class GraphCommandHandler(BaseSceneCmdHandler):
    @property
    def required_permission(self) -> ScenePermission:
        return ScenePermission.EDIT

    def handle(
        self, 
        message: ClientGraphCommand, 
        session: SceneConnectionSession, 
        worker_manager: ISceneWorkerManager
    ):
        cmd: Optional[SceneGraphCommand] = None
        if isinstance(message, NodeGraphCommand):
            cmd = self.generate_node_cmd(message.payload, message.cmd_uid)
        
        elif isinstance(message, ConnGraphCommand):
            pass

        if cmd:
            worker_manager.send_command_to_scene(session.scene_id, cmd)

        
    # -- Nodes

    @singledispatchmethod
    def generate_node_cmd(self, payload: NodeActionPayloadAdapter, cmd_uid: str) -> SceneGraphCommand:
        # FIXME: exception
        raise Exception("Command not implemented")
    

    @generate_node_cmd.dispatcher
    def _(self, payload: NodeAddUpdateAction, cmd_uid: str):
        if payload.action == GraphActionTypes.ADD:
            return AddNodesCommand(
                request_id=cmd_uid,
                nodes=[
                    AddNodeData(
                        nodetype_fqn=scene_data.type_id,
                        node_data=scene_data
                    ) for uid, scene_data in payload.action_data.items()
                ]
            )

        if payload.action == GraphActionTypes.UPDATE:
            return UpdateNodesCommand(
                request_id=cmd_uid,
                nodes={
                    uid: UpdateNodeData(
                        data=scene_data.data, # parameter data
                        position=scene_data.position
                    ) for uid, scene_data in payload.action_data.items()
                }
            )

    @generate_node_cmd.dispatcher
    def _(self, payload: NodeRemoveAction, cmd_uid: str):
        return RemoveNodesCommand(
            request_id=cmd_uid,
            uids=payload.uids
        )
