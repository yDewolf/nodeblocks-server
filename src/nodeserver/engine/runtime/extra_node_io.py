# TODO: mudar isso aqui de lugar, já to com muito sono

from nodeserver.engine.protocols.node.logic_nodes import NodeIO
from nodeserver.engine.runtime.protocols.engine_context import EngineRuntimeContext

class ContextAwareInput(NodeIO):
    # FIXME: isolar alguns atributos do contexto
    context: EngineRuntimeContext
