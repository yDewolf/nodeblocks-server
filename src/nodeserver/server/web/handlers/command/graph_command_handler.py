
from functools import singledispatchmethod
from typing import Optional

from nodeserver.engine.workers.scene.protocols.scene_worker_commands import AddConnData, AddConnectionsCommand, AddNodeData, AddNodesCommand, RemoveConnectionsCommand, RemoveNodesCommand, SceneGraphCommand, UpdateNodeData, UpdateNodesCommand
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.providers.scene_worker_manager_protocol import ISceneWorkerManager
from nodeserver.server.protocols.session_protocols import SceneConnectionSession
from nodeserver.server.protocols.web.messages.client_message_enums import GraphActionTypes
from nodeserver.server.protocols.web.messages.graph.client_graph_commands import ClientGraphCommand, ConnGraphCommand, NodeGraphCommand
from nodeserver.server.protocols.web.messages.graph.graph_action_payloads import ConnActionPayloadAdapter, ConnAddUpdateAction, ConnRemoveAction, NodeActionPayloadAdapter, NodeAddUpdateAction, NodeRemoveAction
from nodeserver.server.web.handlers.base_command_handler import BaseSceneCmdHandler

# TODO: implement command stacks (multiple subcommands that map to a single request id)
# or make the client send multiple requests for multiple scene objects
class GraphCommandHandler(BaseSceneCmdHandler):
    @property
    def required_permission(self) -> ScenePermission:
        return ScenePermission.EDIT

    async def handle(
        self, 
        message: ClientGraphCommand, 
        session: SceneConnectionSession, 
        worker_manager: ISceneWorkerManager
    ):
        cmd: Optional[SceneGraphCommand] = None
        if isinstance(message, NodeGraphCommand):
            cmd = self.generate_node_cmd(message.payload, message.cmd_uid)
        
        elif isinstance(message, ConnGraphCommand):
            cmd = self.generate_conn_cmd(message.payload, message.cmd_uid)

        if cmd:
            worker_manager.send_command_to_scene(session.scene_id, cmd)

        
    # -- Nodes

    @singledispatchmethod
    def generate_node_cmd(self, payload: NodeActionPayloadAdapter, cmd_uid: str) -> SceneGraphCommand:
        # FIXME: exception
        raise Exception(f"Command not implemented for payload: {payload.__class__.__name__}")
    

    @generate_node_cmd.register
    def _(self, payload: NodeAddUpdateAction, cmd_uid: str):
        if payload.action == GraphActionTypes.ADD:
            return AddNodesCommand(
                request_id=cmd_uid,
                nodes=[
                    AddNodeData(
                        uid=uid,
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

        raise Exception(f"Command not implemented for payload: {payload.__class__.__name__}")

    @generate_node_cmd.register
    def _(self, payload: NodeRemoveAction, cmd_uid: str):
        return RemoveNodesCommand(
            request_id=cmd_uid,
            uids=payload.uids
        )

    # -- Connections

    @singledispatchmethod
    def generate_conn_cmd(self, payload: ConnActionPayloadAdapter, cmd_uid: str) -> SceneGraphCommand:
        # FIXME: exception
        raise Exception(f"Command not implemented for payload: {payload.__class__.__name__}")

    @generate_conn_cmd.register
    def _(self, payload: ConnAddUpdateAction, cmd_uid: str):
        if payload.action == GraphActionTypes.ADD:
            return AddConnectionsCommand(
                request_id=cmd_uid,
                connections=[
                    AddConnData(
                        uid=uid,
                        from_node_id=conn_data.from_slot.node_id,
                        from_slot_id=conn_data.from_slot.slot_id,
                        to_node_id=conn_data.to_slot.node_id,
                        to_slot_id=conn_data.to_slot.slot_id,
                    ) for uid, conn_data in payload.action_data.items()
                ]
            )

        if payload.action == GraphActionTypes.UPDATE:
            raise Exception("Can't update a connection (for now). You should remove it then add another")
        
        raise Exception(f"Command not implemented for payload: {payload.__class__.__name__}")

    @generate_conn_cmd.register
    def _(self, payload: ConnRemoveAction, cmd_uid: str):
        return RemoveConnectionsCommand(
            request_id=cmd_uid,
            uids=payload.uids
        )

