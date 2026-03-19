from logging import Logger
from threading import Thread
from nodeserver.api.server_instance import ServerInstance

MANAGER_LOGGER = Logger("InstanceLogger")

class InstanceRunner:
    id: str

    max_instances: int = 4
    instances: dict[str, ServerInstance] = {}

    active: bool = False
    _thread: Thread

    def __init__(self, max_instances: int = 4, id: str = "runner"):
        self.id = id
        self.max_instances = max_instances
        self._thread = Thread(target=self._thread_runtime, daemon=True)

    def start_thread(self):
        self.active = True
        self._thread.start()

    def stop_thread(self):
        self.active = False
        self._thread.join()


    def get_instance(self, instance_id: str) -> ServerInstance: return self.instances.get(instance_id)

    def add_instance(self, instance: ServerInstance) -> bool:
        if not self.is_available():
            return False

        self.instances[instance._attributed_id] = instance

    def is_available(self) -> bool:
        return len(self.instances) >= self.max_instances


    # TODO: maybe use asyncio idk
    def _thread_runtime(self):
        while True:
            if not self.active:
                break

            for id in self.instances:
                instance: ServerInstance = self.instances[id]
                
                if instance.running:
                    instance.running_loop()

        MANAGER_LOGGER.debug("Instance Runner thread stopped")

class InstanceManager:
    runners: int = 2
    max_runner_instances: int = 4

    instance_runners: dict[str, InstanceRunner] = {}
    instance_mappings: dict[str, str] = {}

    def __init__(self):
        self._setup_runners()


    def set_instance(self, instance_id: str, instance: ServerInstance) -> bool:
        runner = self._get_available_runner()
        if runner == None:
            return False

        instance._attributed_id = instance_id
        self.instance_mappings[instance_id] = runner.id
        runner.add_instance(instance)
        return True

    def get_instance(self, instance_id: str) -> ServerInstance: 
        runner_id = self.instance_mappings.get(instance_id, None)
        if runner_id == None:
            return None
        
        runner = self.instance_runners.get(runner_id, None)
        if runner == None:
            return None

        return runner.get_instance(instance_id)


    # TODO
    def load_instance(self, instance_data):
        pass

    
    def _setup_runners(self):
        for idx in range(self.runners):
            new_runner = InstanceRunner(self.max_runner_instances, f"Runner{idx}")
            self.instance_runners[new_runner.id] = new_runner

    def _get_available_runner(self) -> InstanceRunner:
        for runner_id in self.instance_runners:
            runner: InstanceRunner = self.instance_runners[runner_id]
            if runner.is_available():
                continue
        
            return runner
    
        return None