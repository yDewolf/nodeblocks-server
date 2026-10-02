import logging

from nodeserver.engine.runtime.graph_engine import StatelessGraphEngine
from nodeserver.engine.runtime.protocols.engine_context import NodeExecutionStatus
from nodeserver.engine.runtime.job_runtime_context import JobStatus
from nodeserver.engine.runtime.job_runtime_context import JobExecutionContext, StepJobExecutionContext

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

    def execute_step(
        self, 
        job_context: StepJobExecutionContext,
        reraise_exception: bool = False
    ) -> StepJobExecutionContext:
        
        if job_context.status == JobStatus.PENDING:
            job_context.set_job_status(JobStatus.RUNNING)
            
        try:
            if job_context.execution_order is None:
                order = job_context.scene.graph.get_topological_order()
                if job_context.target_nodes:
                    order = self._filter_execution_order(order, job_context.target_nodes, job_context)
                
                job_context.execution_order = order
                job_context.current_index = 0

            if job_context.is_finished:
                return job_context

            node_uid = job_context.execution_order[job_context.current_index]
            node_instance = job_context.scene.graph.ensure_node(node_uid)
            
            self._execute_node(node_instance, job_context)
            job_context.current_index += 1

            if job_context.is_finished:
                evaluated_statuses = [
                    job_context.node_status.get(uid) for uid in job_context.execution_order
                    if uid in job_context.node_status
                ]
                if any(status == NodeExecutionStatus.FAILED for status in evaluated_statuses):
                    job_context.set_job_status(JobStatus.PARTIAL_SUCCESS)
                else:
                    job_context.set_job_status(JobStatus.COMPLETED)
        
        except Exception as e:
            logger.error(f"Failed to execute job step: {e}")
            job_context.set_job_status(JobStatus.FAILED)
            if reraise_exception: raise e
        
        return job_context
