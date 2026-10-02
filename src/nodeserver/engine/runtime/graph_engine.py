from nodeserver.engine.runtime.base_graph_engine import BaseGraphEngine, logger
from nodeserver.engine.runtime.job_runtime_context import EngineRuntimeContext

from typing import Optional


class StatelessGraphEngine(BaseGraphEngine):
    def execute_subgraph(
        self,
        target_nodes: list[str],
        context: EngineRuntimeContext,
        reraise_exception: bool = False
    ) -> EngineRuntimeContext:
        return self.execute_graph(context, reraise_exception, target_nodes=target_nodes)

    def execute_graph(
        self,
        context: EngineRuntimeContext,
        reraise_exception: bool = False,
        target_nodes: Optional[list[str]] = None,
    ) -> EngineRuntimeContext:
        try:
            self._execute_nodes(context, target_nodes)
        except Exception as e:
            logger.error(f"Failed to execute graph: {e}")
            if reraise_exception: raise e

        return context
