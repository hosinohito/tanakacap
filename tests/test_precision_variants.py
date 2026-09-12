import onnx
import pytest
from onnx import helper, TensorProto
from capture_lab.onnx_variants import fp16_model
from capture_lab.gpu_runner import provider_options
from capture_lab.tensorrt_backend import require_provider


def test_fp16_preserves_original_io_and_sensitive_ops(tmp_path):
    path = tmp_path/'original.onnx'
    graph = helper.make_graph([
        helper.make_node('MatMul', ['x','w'], ['hidden']),
        helper.make_node('Softmax', ['hidden'], ['y'], axis=-1)], 'test',
        [helper.make_tensor_value_info('x', TensorProto.FLOAT, [1,2])],
        [helper.make_tensor_value_info('y', TensorProto.FLOAT, [1,2])],
        [helper.make_tensor('w', TensorProto.FLOAT, [2,2], [1,0,0,1])])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid('',17)])
    onnx.save(model,path)
    original = path.read_bytes()
    converted = fp16_model(path)
    assert path.read_bytes() == original
    assert converted != path and fp16_model(path) == converted
    result = onnx.load(converted)
    onnx.checker.check_model(result, full_check=True)
    assert result.graph.input[0].type.tensor_type.elem_type == TensorProto.FLOAT
    assert result.graph.output[0].type.tensor_type.elem_type == TensorProto.FLOAT
    assert result.graph.initializer[0].data_type == TensorProto.FLOAT16
    assert any(n.op_type == 'Softmax' for n in result.graph.node)


def test_fp16_graph_not_enabled_for_dynamic_output():
    assert provider_options('graph-fp16')[0][1]['enable_cuda_graph'] == '1'
    assert provider_options('graph-fp16', True)[0][1]['enable_cuda_graph'] == '0'


def test_reject_silent_provider_fallback():
    class Session:
        def disable_fallback(self): self.disabled = True
        def get_providers(self): return ['CPUExecutionProvider']
    session = Session()
    with pytest.raises(RuntimeError, match='refusing silent fallback'):
        require_provider(session,'graph-fp16')
    assert session.disabled


def test_trt_request_rejects_cuda_only_session():
    class Session:
        def disable_fallback(self): pass
        def get_providers(self): return ['CUDAExecutionProvider','CPUExecutionProvider']
    with pytest.raises(RuntimeError, match='TensorrtExecutionProvider'):
        require_provider(Session(),'trt-fp16')
