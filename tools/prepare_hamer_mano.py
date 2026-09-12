"""Convert the user's legacy MANO asset once; keep the original unchanged."""
import argparse,hashlib,inspect,json,pickle,sys
from pathlib import Path
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--chumpy',type=Path,required=True);a=p.parse_args()
 if a.source.resolve()==a.output.resolve() or a.output.exists():raise ValueError('A new output path is required')
 # Compatibility is confined to this conversion subprocess, never the tracker.
 if not hasattr(inspect,'getargspec'):inspect.getargspec=inspect.getfullargspec
 for name,value in {'bool':bool,'int':int,'float':float,'complex':complex,'object':object,'str':str,'unicode':str}.items():
  if name not in np.__dict__:setattr(np,name,value)
 sys.path.insert(0,str(a.chumpy.resolve()))
 import chumpy
 original=pickle.loads(a.source.read_bytes(),encoding='latin1')
 converted={k:np.asarray(v.r).copy() if isinstance(v,chumpy.Ch) else v for k,v in original.items()}
 for k in ['v_template','shapedirs','posedirs','weights']:
  assert np.isfinite(np.asarray(converted[k])).all(),k
  assert np.array_equal(np.asarray(original[k].r if isinstance(original[k],chumpy.Ch) else original[k]),converted[k]),k
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('xb') as f:pickle.dump(converted,f,protocol=4)
 receipt={'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'shapes':{k:list(converted[k].shape) for k in ['v_template','shapedirs','posedirs','weights']},'scope':'Numerically identical Chumpy values materialized as NumPy arrays; original untouched.'}
 a.output.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(receipt)
if __name__=='__main__':main()
