"""Replay the saved checkpoint with identical startup, without changing live code."""
from pathlib import Path
import zipfile,sys,runpy
root=Path(__file__).resolve().parents[1]
dest=root/'results/elbow-face-research/baseline_source'
with zipfile.ZipFile(root/'results/checkpoints/before-elbow-face-research-20260912.zip') as z:
    for name in z.namelist():
        if not name.startswith('capture_lab/') or not name.endswith('.py'):continue
        target=(dest/name).resolve()
        if not target.is_relative_to(dest.resolve()):raise ValueError(name)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(z.read(name))
sys.path.insert(0,str(dest))
import capture_lab.body3d, capture_lab.retarget
runpy.run_path(str(root/'tools/replay_body.py'),run_name='__main__')
