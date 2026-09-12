"""Reusable CUDA buffers and optional graph replay; unchanged model/precision.

Synchronous readback is intentional: CPU geometry consumes this observation.
Never allow the next eye/frame to overwrite an output while it is in use.
"""
import numpy as np
import onnxruntime as ort


class GpuRunner:
    def __init__(self, session, mode='run', dynamic_output=False):
        if mode not in ('run','binding','graph'): raise ValueError('Unknown inference mode')
        self.session = session
        self.mode = 'binding' if dynamic_output and mode == 'graph' else mode
        self.dynamic = dynamic_output
        self.input = None
        self.binding = None
        self.outputs = []

    def run(self, tensor, input_name, output_names=None, return_device=False):
        if self.mode == 'run':
            return self.session.run(output_names, {input_name:tensor})
        tensor = np.ascontiguousarray(tensor, dtype=np.float32)
        names = output_names or [out.name for out in self.session.get_outputs()]
        if self.input is None:
            self.names = list(names)
            self.shape = tensor.shape
            self.input_name = input_name
            self.input = ort.OrtValue.ortvalue_from_numpy(tensor, 'cuda', 0)
            self.binding = self.session.io_binding()
            self.binding.bind_ortvalue_input(input_name,self.input)
            if self.dynamic:
                for name in names: self.binding.bind_output(name,'cuda',0)
            else:
                # Run once without capture to resolve any symbolic output dimensions.
                options = ort.RunOptions()
                options.add_run_config_entry('gpu_graph_id','-1')
                samples = self.session.run(names,{input_name:tensor},options)
                for name,value in zip(names,samples):
                    output = ort.OrtValue.ortvalue_from_shape_and_type(value.shape,value.dtype,'cuda',0)
                    self.outputs.append(output)
                    self.binding.bind_ortvalue_output(name,output)
        else:
            if tensor.shape != self.shape or names != self.names or input_name != self.input_name:
                raise ValueError('Bound CUDA tensor shape/names changed; rebuild runner explicitly')
            self.input.update_inplace(tensor)
        if self.dynamic:
            # ORT retains the allocation after execution. Clear it before the
            # next NMS result, whose detection count may grow or shrink.
            self.binding.clear_binding_outputs()
            for name in names:
                self.binding.bind_output(name, 'cuda', 0)
        self.session.run_with_iobinding(self.binding)
        return self.binding.get_outputs() if return_device else self.binding.copy_outputs_to_cpu()


class SplitDetectorRunner:
    """Graph the fixed prefix and pass CUDA buffers directly to unchanged NMS."""
    def __init__(self, core, tail):
        self.core=GpuRunner(core,'graph')
        self.tail=tail
        self.mode='split_graph'
        self.binding=tail.io_binding()

    def run(self,tensor,input_name,output_names=None):
        values=self.core.run(tensor,input_name,return_device=True)
        for name,value in zip(self.core.names,values):
            self.binding.bind_ortvalue_input(name,value)
        self.binding.clear_binding_outputs()
        for output in self.tail.get_outputs():self.binding.bind_output(output.name,'cuda',0)
        self.tail.run_with_iobinding(self.binding)
        return self.binding.copy_outputs_to_cpu()


def provider_options(mode, dynamic_output=False):
    return [('CUDAExecutionProvider', {'device_id':0,
        'enable_cuda_graph': '1' if mode=='graph' and not dynamic_output else '0'})]
