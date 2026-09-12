"""Trial K: CUDA crop/normalization, with explicit interpolation parity audit."""
from pathlib import Path
import cv2
import numpy as np
import onnx
import onnxruntime as ort
from .gpu_runner import provider_options


class GpuPreprocessor:
    def __init__(self, frame_shape, input_wh, color_order, profile_folder=None):
        height,width=frame_shape[:2];iw,ih=input_wh
        self.shape=frame_shape
        folder=Path(__file__).resolve().parents[1]/'models/preprocess-cache'
        folder.mkdir(exist_ok=True)
        path=folder/f'grid-v1-{width}x{height}-{iw}x{ih}-{color_order}.onnx'
        if not path.exists():
            h=onnx.helper;initial=[];nodes=[]
            def const(name,value):
                initial.append(onnx.numpy_helper.from_array(np.asarray(value),name));return name
            yy,xx=np.mgrid[:ih,:iw]
            const('grid',np.stack((xx,yy,np.ones_like(xx)),axis=-1)[None].astype(np.float32))
            const('quant',np.float32(32));const('half',np.float32(.5))
            const('normalizer',np.array([2/(width-1),2/(height-1)],np.float32))
            const('one',np.float32(1));const('zero',np.float32(0));const('max',np.float32(255))
            const('channels',np.array([2,1,0] if color_order=='RGB' else [0,1,2],np.int64))
            const('mean',np.array([123.675,116.28,103.53],np.float32)[None,:,None,None])
            const('std',np.array([58.395,57.12,57.375],np.float32)[None,:,None,None])
            nodes.extend([
                h.make_node('Cast',['frame'],['float_frame'],to=onnx.TensorProto.FLOAT),
                h.make_node('Transpose',['float_frame'],['nchw'],perm=[0,3,1,2]),
                h.make_node('MatMul',['grid','inverse'],['pixels']),
                h.make_node('Mul',['pixels','quant'],['quantized']),
                h.make_node('Round',['quantized'],['rounded']),
                h.make_node('Div',['rounded','quant'],['pixel_grid']),
                h.make_node('Mul',['pixel_grid','normalizer'],['scaled_grid']),
                h.make_node('Sub',['scaled_grid','one'],['sample_grid']),
                h.make_node('GridSample',['nchw','sample_grid'],['crop_float'],mode='bilinear',padding_mode='zeros',align_corners=1),
                h.make_node('Add',['crop_float','half'],['pixel_round']),
                h.make_node('Floor',['pixel_round'],['crop_uint8_values']),
                h.make_node('Clip',['crop_uint8_values','zero','max'],['clipped']),
                h.make_node('Gather',['clipped','channels'],['ordered'],axis=1),
                h.make_node('Sub',['ordered','mean'],['centered']),
                h.make_node('Div',['centered','std'],['tensor'])])
            graph=h.make_graph(nodes,'tcap_preprocess',[
                h.make_tensor_value_info('frame',onnx.TensorProto.UINT8,[1,height,width,3]),
                h.make_tensor_value_info('inverse',onnx.TensorProto.FLOAT,[3,2])],
                [h.make_tensor_value_info('tensor',onnx.TensorProto.FLOAT,[1,3,ih,iw])],initial)
            model=h.make_model(graph,opset_imports=[h.make_opsetid('',17)],ir_version=8)
            onnx.checker.check_model(model)
            temporary=path.with_suffix('.tmp');onnx.save(model,temporary);temporary.replace(path)
        options=ort.SessionOptions();options.intra_op_num_threads=2;options.log_severity_level=3
        options.enable_profiling=profile_folder is not None
        if profile_folder:options.profile_file_prefix=str(Path(profile_folder)/'gpu-preprocess')
        providers=provider_options('graph')
        providers[0][1]['use_tf32']='0'  # Pixel coordinates must not use reduced mantissa matmul.
        self.session=ort.InferenceSession(str(path),sess_options=options,providers=providers)
        self.session.disable_fallback()
        if self.session.get_providers()[0]!='CUDAExecutionProvider':raise RuntimeError('Preprocessing requires CUDA')
        self.frame=ort.OrtValue.ortvalue_from_shape_and_type([1,height,width,3],np.uint8,'cuda',0)
        self.matrix=ort.OrtValue.ortvalue_from_shape_and_type([3,2],np.float32,'cuda',0)
        self.output=ort.OrtValue.ortvalue_from_shape_and_type([1,3,ih,iw],np.float32,'cuda',0)
        self.binding=self.session.io_binding()
        for name,value in [('frame',self.frame),('inverse',self.matrix)]:self.binding.bind_ortvalue_input(name,value)
        self.binding.bind_ortvalue_output('tensor',self.output)

    def run(self,frame,affine):
        if frame.shape!=self.shape:raise ValueError('Frame size changed; recreate GPU preprocessing explicitly')
        matrix=np.ascontiguousarray(cv2.invertAffineTransform(affine).T,dtype=np.float32)
        self.frame.update_inplace(np.ascontiguousarray(frame[None],dtype=np.uint8))
        self.matrix.update_inplace(matrix)
        self.session.run_with_iobinding(self.binding)
        return self.output
