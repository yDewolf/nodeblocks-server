import logging

from nodeserver.engine.runtime.graph_engine import StatelessGraphEngine
from nodeserver.engine.runtime.protocols.engine_context import NodeExecutionStatus
from nodeserver.engine.runtime.job_runtime_context import JobStatus
from nodeserver.engine.runtime.job_runtime_context import JobExecutionContext

logger = logging.getLogger("nds.engine")

class JobStlGraphEngine(StatelessGraphEngine):
    def execute_subgraph(
        self,
        context: JobExecutionContext,
        reraise_exception: bool = False
    ) -> JobExecutionContext:
        return self.execute_graph(context, reraise_exception)

    def execute_graph(
        self, 
        job_context: JobExecutionContext,
        reraise_exception: bool = False
    ) -> JobExecutionContext:
        
        job_context.set_job_status(JobStatus.RUNNING)
        try:
            execution_order = self._execute_nodes(job_context, job_context.target_nodes)
            
            evaluated_statuses = [
                job_context.node_status.get(node_uid) for node_uid in execution_order 
                if node_uid in job_context.node_status
            ]
            if any(status == NodeExecutionStatus.FAILED for status in evaluated_statuses):
                job_context.set_job_status(JobStatus.PARTIAL_SUCCESS)
            else:
                job_context.set_job_status(JobStatus.COMPLETED)
        
        except Exception as e:
            logger.error(f"Failed to execute job: {e}")
            job_context.set_job_status(JobStatus.FAILED)
            if reraise_exception: raise e
        
        return job_context

