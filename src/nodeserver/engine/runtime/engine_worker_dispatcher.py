import asyncio
from concurrent.futures import ThreadPoolExecutor

from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.runtime.graph_engine import StatelessGraphEngine
from nodeserver.engine.runtime.runtime_context import GraphRunContext, JobStatus

# FIXME: Experimental, testar bastante
class LocalJobDispatcher:
    queue: asyncio.Queue
    active_jobs: dict[str, GraphRunContext]

    thread_pool: ThreadPoolExecutor
    engine: StatelessGraphEngine

    def __init__(self, max_workers: int = 4):
        self.queue = asyncio.Queue()
        self.active_jobs: dict[str, GraphRunContext] = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.engine = StatelessGraphEngine()

    async def submit_scene(self, scene: NodeScene) -> str:
        context = GraphRunContext(scene)
        self.active_jobs[context.job_id] = context
        
        await self.queue.put(context)
        return context.job_id

    def get_job_status(self, job_id: str) -> JobStatus:
        if job_id in self.active_jobs:
            return self.active_jobs[job_id].status
        return JobStatus.FAILED

    async def worker_loop(self):
        while True:
            context: GraphRunContext = await self.queue.get()
            
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                self.thread_pool, 
                self.engine.execute_job, 
                context
            )
            
            self.queue.task_done()
            # TODO: send websocket feedback
