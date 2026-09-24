# TODO: mudar isso aqui de lugar, já to com muito sono

from nodeserver.engine.protocols.logic_nodes import NodeIO
from nodeserver.engine.runtime.runtime_context import GraphRunContext


class ContextAwareInput(NodeIO):
    # FIXME: isolar alguns atributos do contexto
    context: GraphRunContext
