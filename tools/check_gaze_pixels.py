"""Compare visible HAOLAN iris pixels with fixed head/face and synthetic gaze only."""
import json,subprocess,sys,time
from pathlib import Path
import cv2
import numpy as np

root=Path(__file__).resolve().parents[1]
output=root/'results/gaze-render'/('pixel-check-'+str(time.time_ns()))
output.mkdir(parents=True,exist_ok=True)
base=dict(version=1,tracked=True,faceTracked=True,body3d=True,torsoTracked=True,
          gazeTracked=True,leftBlink=0,rightBlink=0)
poses={'center':(0,0),'left':(-10,0),'right':(10,0),'up':(0,-6),'down':(0,6)}
report={}
for gain in (1,2):
    rows={}
    for name,(yaw,pitch) in poses.items():
        packet=output/f'{gain}-{name}.json'; image=output/f'{gain}-{name}.png'
        if image.exists(): raise RuntimeError(f'Refusing stale comparison image: {image}')
        packet.write_text(json.dumps(dict(base,gazeYaw=yaw,gazePitch=pitch)),encoding='utf-8')
        subprocess.run([sys.executable,str(root/'tools/smoke_unity.py'),'--gaze-gain',str(gain),
                        '--packet-file',str(packet),'--output',str(image)],cwd=root,check=True,stdout=subprocess.DEVNULL)
        hsv=cv2.cvtColor(cv2.imread(str(image)),cv2.COLOR_BGR2HSV)
        mask=(hsv[:,:,0]>=38)&(hsv[:,:,0]<=95)&(hsv[:,:,1]>100)&(hsv[:,:,2]>70)
        yy,xx=np.indices(mask.shape)
        eyes=[]
        for low,high in ((520,640),(640,760)):
            selected=mask&(xx>=low)&(xx<high)&(yy>=230)&(yy<330)
            if selected.sum()<50: raise AssertionError(f'No visible HAOLAN iris: {gain}/{name}')
            eyes.append([float(xx[selected].mean()),float(yy[selected].mean())])
        rows[name]=eyes
    a=np.array(rows['left']);b=np.array(rows['right'])
    horizontal=(a-b)[:,0]
    vertical=(np.array(rows['down'])-np.array(rows['up']))[:,1]
    assert np.all(horizontal>0) and np.all(vertical>0),rows
    report[str(gain)]=dict(centers=rows,horizontal_span_px=horizontal.tolist(),vertical_span_px=vertical.tolist())
assert np.min(report['2']['horizontal_span_px'])>8,report
assert np.min(report['2']['vertical_span_px'])>5,report
report['scope']='Synthetic gaze +/-10 yaw, +/-6 pitch; fixed head. Visible green iris pixels, not landmark or BakeMesh displacement. Capture accuracy unverified.'
(output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
print(output)
