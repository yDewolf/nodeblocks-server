from logging import Logger
from threading import Thread, Lock, Event
from nodeserver.api.server_instance import ServerInstance
from nodeserver.networking.nodes.helpers.file.typing_file_reader import TypeFileReader

MANAGER_LOGGER = Logger("InstanceLogger")

class InstanceRunner:
    id: str

    max_instances: int = 4
    instances: dict[str, ServerInstance]
    _instances_cache: list[ServerInstance]

    active: bool = False
    _thread: Thread
    _lock: Lock
    _sleep_event: Event

    def __init__(self, max_instances: int = 4, id: str = "runner"):
        self.instances = {}
        self._instances_cache: list[ServerInstance] = []
        self.active = False
        
        self.id = id
        self.max_instances = max_instances
        self._thread = Thread(target=self._thread_runtime, daemon=True)
        self._lock = Lock()
        self._sleep_event = Event()

    def start_thread(self):
        self.active = True
        self._thread.start()

    def stop_thread(self):
        self.active = False
        self._thread.join()


    def _update_cache(self):
        self._instances_cache = list(self.instances.values())


    def get_instance(self, instance_id: str) -> ServerInstance | None: return self.instances.get(instance_id)

    def add_instance(self, instance: ServerInstance) -> bool:
        if not self.is_available():
             return False

        MANAGER_LOGGER.info("Added instance")
        self.instances[instance._attributed_id] = instance
        self._update_cache()
        return True
    
    def remove_instance(self, instance_id: str):
        with self._lock:
            if instance_id in self.instances:
                del self.instances[instance_id]
                self._update_cache()


    def is_available(self) -> bool:
        return len(self.instances) < self.max_instances and self.active


    def _thread_runtime(self):
        while self.active:
            current_instances = self._instances_cache
            if len(current_instances) == 0:
                self._sleep_event.wait(0.1)
                continue

            for instance in current_instances:
                # try:
                    instance.state_controller.update()
                    instance._handle_command_queue()
                    if instance.is_running():
                        instance.runtime_tick()
                # except Exception as e:
                #     MANAGER_LOGGER.error("Some Instance fumbled", e)
        

        MANAGER_LOGGER.info(f"Runner {self.id} stopped")

class InstanceManager:
    _default_types: TypeFileReader | None = None
    runners: int = 2
    max_runner_instances: int = 4

    instance_runners: dict[str, InstanceRunner] = {}
    instance_mappings: dict[str, str] = {}

    def __init__(self, _default_types: TypeFileReader | None = None):
        self._default_types = _default_types
        self.instance_runners = {}
        self.instance_mappings = {}
        
        self._setup_runners()
        self.activate_runners()


    def set_instance(self, instance_id: str, instance: ServerInstance) -> bool:
        if self.instance_mappings.__contains__(instance_id):
            return False
        
        runner = self._get_available_runner()
        if runner == None:
            return False

        instance._attributed_id = instance_id
        self.instance_mappings[instance_id] = runner.id
        runner.add_instance(instance)
        return True

    def get_instance(self, instance_id: str) -> ServerInstance | None: 
        runner_id = self.instance_mappings.get(instance_id, None)
        if runner_id == None:
            return None
        
        runner = self.instance_runners.get(runner_id, None)
        if runner == None:
            return None

        return runner.get_instance(instance_id)

    def remove_instance(self, instance_id: str):
        runner_id = self.instance_mappings.pop(instance_id, None)
        if runner_id == None:
            return
        
        runner = self.instance_runners.get(runner_id)
        if runner:
            runner.remove_instance(instance_id)


    def get_all_instances(self) -> list[ServerInstance]:
        instances = []
        for runner in self.instance_runners.values():
            runner_instances = runner.instances.values()
            instances += runner_instances

        return instances

    # TODO
    def load_instance(self, instance_data):
        pass

    
    def _setup_runners(self):
        for idx in range(self.runners):
            new_runner = InstanceRunner(self.max_runner_instances, f"Runner{idx}")
            new_runner.active = True
            self.instance_runners[new_runner.id] = new_runner

    def activate_runners(self):
        for id in self.instance_runners:
            runner = self.instance_runners[id]
            runner.start_thread()
        

    def _get_available_runner(self) -> InstanceRunner | None:
        for runner_id in self.instance_runners:
            runner: InstanceRunner = self.instance_runners[runner_id]
            if not runner.is_available():
                continue
        
            return runner
    
        return None