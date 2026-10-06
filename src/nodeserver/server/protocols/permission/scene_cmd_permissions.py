from nodeserver.engine.workers.scene.protocols.scene_worker_commands import *
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission


COMMAND_PERMISSIONS: dict[type[IPCSceneWorkerCommand], ScenePermission] = {
    SceneUpdateCommand: ScenePermission.EDIT,
    RuntimeCommand: ScenePermission.EXECUTE,
    
    AddNodesCommand: ScenePermission.EDIT,
    RemoveNodesCommand: ScenePermission.EDIT,
    UpdateNodesCommand: ScenePermission.EDIT,
    AddConnectionsCommand: ScenePermission.EDIT,
    RemoveConnectionsCommand: ScenePermission.EDIT,
    
    UpdateExecutionStateCmd: ScenePermission.EXECUTE,
    UpdateExecutionModeCmd: ScenePermission.EXECUTE,
    GraphStepCommand: ScenePermission.EXECUTE,
    PauseGraphCommand: ScenePermission.EXECUTE,
}

def get_required_permission(command: type[IPCSceneWorkerCommand]) -> ScenePermission:
    permission = COMMAND_PERMISSIONS.get(command, None)
    if not permission:
        super_type = type(command.__class__)
        if issubclass(super_type, IPCSceneWorkerCommand):
            get_required_permission(super_type)

    if not permission:
        raise Exception("Couldn't find permission for command: ", command)
    
    return permission
