"""Compare fixed lip-depth hypotheses. Correlation is not expression ground truth."""
from pathlib import Path
import sys,json
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from capture_lab.head_pose import fit_pose,frontal_landmarks
source=Path(sys.argv[1]);out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
rows=[json.loads(l) for l in source.read_text().splitlines()]
values={k:[] for k in (1.,1.5,2.,2.5,3.)}
for row in rows:
    p=row['sent_packet'];pose=fit_pose(row['points_xy'],row['scores'],row['image_size'])
    if pose is None or abs(p['headYaw'])>15 or p['mouth']>.3:continue
    r,t,angles,error=pose
    for scale,items in values.items():
        xy=frontal_landmarks(row['points_xy'],r,t,row['image_size'],scale)[23:91]
        axis=(xy[42]+xy[45]-xy[36]-xy[39])/2;span=np.linalg.norm(axis);down=np.array([-axis[1],axis[0]])/span
        center=(xy[51]+xy[57])/2
        corner=np.array([(center-xy[i])@down/span for i in (54,48)])
        items.append([float(angles[0]),*corner])
report={}
for scale,items in values.items():
    a=np.array(items);x=np.sin(np.radians(a[:,0]));design=np.column_stack([x,np.ones(len(x))]);coef=np.linalg.lstsq(design,a[:,1:],rcond=None)[0]
    report[str(scale)]=dict(frames=len(a),corner_pitch_slope=coef[0].tolist(),correlations=[float(np.corrcoef(x,a[:,j])[0,1]) for j in (1,2)])
report['scope']='Closed-mouth/front-yaw subset; expression/head-shape confounding remains. Fixed hypothesis comparison, not automatic live learning.'
out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
