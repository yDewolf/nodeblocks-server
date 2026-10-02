import pytest

from nodeserver.engine.helpers.node_spec_builder import NodeSpecBuilder
from nodeserver.engine.protocols.node.logic_nodes import BaseNode, NodeInputs, NodeOutputs
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.protocols.node_provider import BaseNodeProvider
from nodeserver.engine.protocols.parameters.node_parameter import NodeParameters
from nodeserver.engine.runtime.job_graph_engine import JobStlGraphEngine
from nodeserver.engine.runtime.protocols.engine_context import NodeExecutionStatus
from nodeserver.engine.runtime.job_runtime_context import GraphRunContext
from nodeserver.engine.helpers.engine_runtime_helper import EngineRuntimeHelper
from nodeserver.engine.runtime.job_runtime_context import JobStatus
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData


class ValueInput(NodeInputs):
    val: int = 0

class ValueOutput(NodeOutputs):
    out: int

class IncrementNode(BaseNode[ValueInput, ValueOutput]):
    InputModel = ValueInput
    OutputModel = ValueOutput

    def forward(self, inputs: ValueInput) -> ValueOutput:
        return ValueOutput(out=inputs.val + 1)


class FailingNode(BaseNode):
    InputModel = ValueInput
    OutputModel = ValueOutput

    def forward(self, inputs: ValueInput) -> ValueOutput:
        raise ValueError("Simulated failure")


class MultiInput(NodeInputs):
    items: list[int] = []

class SumListOutput(NodeOutputs):
    total: int

class SumListNode(BaseNode[MultiInput, SumListOutput]):
    InputModel = MultiInput
    OutputModel = SumListOutput

    def forward(self, inputs: MultiInput) -> SumListOutput:
        return SumListOutput(total=sum(inputs.items))


class StringOutput(NodeOutputs):
    out_str: str = "invalid_number"

class StringNode(BaseNode[ValueInput, StringOutput]):
    InputModel = ValueInput
    OutputModel = StringOutput
    def forward(self, inputs: ValueInput) -> StringOutput:
        return StringOutput()

class ConfigurableInput(NodeInputs):
    required_val: int
    default_val: int = 100
    optional_text: str | None = None

class OutputModel(NodeOutputs):
    result: int

class InputTestNode(BaseNode[ConfigurableInput, OutputModel]):
    InputModel = ConfigurableInput
    OutputModel = OutputModel

    def __init__(self, scene_data: NodeSceneData) -> None:
        super().__init__(scene_data)
        self.execution_count = 0

    def forward(self, inputs: ConfigurableInput) -> OutputModel:
        self.execution_count += 1
        computed = (inputs.required_val + inputs.default_val)
        return OutputModel(
            result=computed,
        )


class ParamTestOut(NodeOutputs):
    result: int
    text: str

class ParamTestNode(BaseNode[NodeInputs, ParamTestOut]):
    OutputModel = ParamTestOut

    class Parameters(NodeParameters):
        multiplier: int = 2
        mode: str = "standard"

    params: Parameters
    execution_count: int

    def __init__(self, scene_data: NodeSceneData) -> None:
        super().__init__(scene_data)
        self.execution_count = 0

    def forward(self, inputs: NodeInputs) -> ParamTestOut:
        self.execution_count += 1
        computed = 5 * self.params.multiplier
        return ParamTestOut(
            result=computed,
            text=f"mode_{self.params.mode}_run_{self.execution_count}"
        )

@pytest.fixture
def engine():
    return JobStlGraphEngine()

@pytest.fixture
def scene(default_registry):
    spec_builder = NodeSpecBuilder(default_registry)
    
    default_registry.register_node_type(spec_builder.build_node_spec("test", "increment", IncrementNode), IncrementNode)
    default_registry.register_node_type(spec_builder.build_node_spec("test", "failing", FailingNode), FailingNode)
    default_registry.register_node_type(spec_builder.build_node_spec("test", "sum_list", SumListNode), SumListNode)
    default_registry.register_node_type(spec_builder.build_node_spec("test", "string_node", StringNode), StringNode)
    default_registry.register_node_type(spec_builder.build_node_spec("test", "input_test", InputTestNode), InputTestNode)
    default_registry.register_node_type(spec_builder.build_node_spec("test", "param_test", ParamTestNode), ParamTestNode)

    scene = NodeScene(registry=default_registry, node_provider=BaseNodeProvider(registry=default_registry))
    return scene



class TestStatelessGraphEngineRealNodes:

    def test_execute_job_linear_pipeline_success(self, engine, scene):
        node_a = scene.create_node("test:increment")
        node_b = scene.create_node("test:increment")

        scene.graph.connect(
            from_node_id=node_a.uid, from_slot_id="out",
            to_node_id=node_b.uid, to_slot_id="val"
        )

        context = GraphRunContext(job_id="job_001", scene=scene)
        result_context = engine.execute_job(context)

        assert result_context.status == JobStatus.COMPLETED
        assert result_context.node_status[node_a.uid] == NodeExecutionStatus.SUCCESS
        assert result_context.node_status[node_b.uid] == NodeExecutionStatus.SUCCESS

        key_a = result_context.get_cache_key(node_a.uid, "out")
        key_b = result_context.get_cache_key(node_b.uid, "out")
        assert result_context.output_cache[key_a] == 1
        assert result_context.output_cache[key_b] == 2

    def test_execute_job_skips_dependent_nodes_on_failure(self, engine, scene):
        node_fail = scene.create_node("test:failing")
        node_b = scene.create_node("test:increment")

        scene.graph.connect(
            from_node_id=node_fail.uid, from_slot_id="out",
            to_node_id=node_b.uid, to_slot_id="val"
        )

        context = GraphRunContext(job_id="job_002", scene=scene)
        result_context = engine.execute_job(context)

        assert result_context.status == JobStatus.PARTIAL_SUCCESS
        assert result_context.node_status[node_fail.uid] == NodeExecutionStatus.FAILED
        assert result_context.node_status[node_b.uid] == NodeExecutionStatus.SKIPPED
        assert node_fail.uid in result_context.errors

    def test_process_node_persistent_cache_hit(self, engine, scene):
        node_fail = scene.create_node("test:failing")
        
        context = GraphRunContext(job_id="job_003", scene=scene)
        computed_hash = EngineRuntimeHelper._compute_node_hash(node_fail, context)

        context.persistent_cache[node_fail.uid] = {
            "hash": computed_hash,
            "outputs": {"out": 999}
        }

        # aqui ele tem que acessar o cache ao invés de rodar o node
        success = engine._process_node(node_fail, context)

        assert success is True
        cache_key = context.get_cache_key(node_fail.uid, "out")
        assert context.output_cache[cache_key] == 999

    def test_resolve_unlimited_inputs_multiple_connections(self, engine, scene):
        node_a1 = scene.create_node("test:increment")
        node_a2 = scene.create_node("test:increment")
        node_sum = scene.create_node("test:sum_list")

        scene.graph.connect(
            from_node_id=node_a1.uid, from_slot_id="out",
            to_node_id=node_sum.uid, to_slot_id="items"
        )
        scene.graph.connect(
            from_node_id=node_a2.uid, from_slot_id="out",
            to_node_id=node_sum.uid, to_slot_id="items"
        )

        context = GraphRunContext(job_id="job_004", scene=scene)
        result_context = engine.execute_job(context)

        assert result_context.status == JobStatus.COMPLETED
        sum_key = result_context.get_cache_key(node_sum.uid, "total")
        
        assert result_context.output_cache[sum_key] == 2


class TestNodeParametersAndDefaults:
    def test_default_inputs_and_default_parameters(self, engine, scene):
        node_source = scene.create_node("test:increment") # out = 0 + step(1) = 1
        node_target = scene.create_node("test:input_test")

        scene.graph.connect(
            from_node_id=node_source.uid, from_slot_id="out",
            to_node_id=node_target.uid, to_slot_id="required_val"
        )

        context = GraphRunContext(job_id="job_params_1", scene=scene)
        result_context = engine.execute_job(context)

        assert result_context.status == JobStatus.COMPLETED
        assert result_context.node_status[node_target.uid] == NodeExecutionStatus.SUCCESS

        res_key = result_context.get_cache_key(node_target.uid, "result")

        # Cálculo esperado:
        # required_val = 1 (do node_source)
        # default_val = 100 (default do ConfigurableInput)
        # (1 + 100) = 101
        assert result_context.output_cache[res_key] == 101
    
    def test_missing_required_slot_fails_validation(self, engine, scene):
        node_target = scene.create_node("test:input_test")

        context = GraphRunContext(job_id="job_params_3", scene=scene)
        result_context = engine.execute_job(context)

        assert result_context.status == JobStatus.PARTIAL_SUCCESS
        assert result_context.node_status[node_target.uid] == NodeExecutionStatus.FAILED
        
        assert node_target.uid in result_context.errors
        assert "required_val" in str(result_context.errors[node_target.uid])

    def test_incompatible_input_type_fails_runtime(self, engine, scene):
        str_node = scene.create_node("test:string_node")
        target_node = scene.create_node("test:input_test")

        scene.graph.connect(
            from_node_id=str_node.uid, from_slot_id="str_out",
            to_node_id=target_node.uid, to_slot_id="required_val"
        )

        context = GraphRunContext(job_id="job_params_4", scene=scene)
        result_context = engine.execute_job(context)

        assert result_context.node_status[str_node.uid] == NodeExecutionStatus.SUCCESS
        assert result_context.node_status[target_node.uid] == NodeExecutionStatus.FAILED
        assert target_node.uid in result_context.errors

class TestNodeParameterReprocessing:
    def test_node_data_param_update(self, engine, scene):
        node_source = scene.create_node("test:param_test")

        logic_target: ParamTestNode = scene.get_logic_node(node_source.uid)
        logic_target.params.mode = "custom"
        logic_target.params.multiplier = 5

        node_instance = scene.graph.get_node(logic_target.scene_data.uid)
        assert node_instance.node_data.data["mode"] == "custom"
        assert node_instance.node_data.data["multiplier"] == 5

    def test_node_reprocessed_on_direct_parameter_mutation(self, engine, scene):
        node_target = scene.create_node("test:param_test")
        context = GraphRunContext(job_id="job_reprocess_1", scene=scene)
        
        engine.execute_job(context)

        logic_target: InputTestNode = scene.get_logic_node(node_target.uid)
        assert logic_target.execution_count == 1
        
        res_key = context.get_cache_key(node_target.uid, "result")
        text_key = context.get_cache_key(node_target.uid, "text")
        
        assert context.output_cache[res_key] == 10
        assert context.output_cache[text_key] == "mode_standard_run_1"

        engine.execute_job(context)
        assert logic_target.execution_count == 1

        logic_target.params.mode = "custom"
        logic_target.params.multiplier = 5

        engine.execute_job(context)

        assert logic_target.execution_count == 2
        assert context.output_cache[res_key] == 25 # (5 * 5)
        assert context.output_cache[text_key] == "mode_custom_run_2"

    def test_node_reprocessed_on_update_parameters_method(self, engine, scene):
        node_target = scene.create_node("test:param_test")
        context = GraphRunContext(job_id="job_reprocess_2", scene=scene)

        engine.execute_job(context)
        logic_target: InputTestNode = scene.get_logic_node(node_target.uid)
        assert logic_target.execution_count == 1

        res_key = context.get_cache_key(node_target.uid, "result")
        assert context.output_cache[res_key] == 10

        logic_target.update_parameters({"mode": "custom", "multiplier": 5})
        engine.execute_job(context)

        assert logic_target.execution_count == 2
        assert context.output_cache[res_key] == 25
        assert context.output_cache[context.get_cache_key(node_target.uid, "text")] == "mode_custom_run_2"

    def test_node_hash_changes_when_parameters_change(self, scene):
        node_target = scene.create_node("test:param_test")
        context = GraphRunContext(job_id="job_hash_test", scene=scene)
        logic_target: InputTestNode = scene.get_logic_node(node_target.uid)

        hash_before = EngineRuntimeHelper._compute_node_hash(node_target, context)
        logic_target.params.multiplier = 10

        hash_after = EngineRuntimeHelper._compute_node_hash(node_target, context)
        assert hash_before != hash_after
