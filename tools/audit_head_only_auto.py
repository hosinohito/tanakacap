"""Real-recording head-only CUDA check plus controlled loss/translation probes.

No camera required. Generated images and numeric results remain under ignored results/.
"""
import json
import sys
import time
from pathlib import Path
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tanakacap.head_region import HeadRegionDetector, HeadRegionTracker, crop_for
from tanakacap.head_only import HeadOnlyModel


def main():
    output=ROOT/'results'/('head-auto-audit-'+str(time.time_ns()))
    output.mkdir()
    cap=cv2.VideoCapture(str(ROOT/'results/comparison-takes/20260911T235327-031115Z/camera.avi'))
    ok,image=cap.read()
    cap.release()
    assert ok
    detector=HeadRegionDetector(output)
    pose=HeadOnlyModel(output)
    tracker=HeadRegionTracker()
    rows=[]
    now=0.
    for label,frame in [('visible',image)]*6 + [('black',np.zeros_like(image))]*6 + [('visible',image)]*6:
        detections,elapsed=detector.detect(frame)
        roi=tracker.update(detections,now,frame.shape)
        angles=None if roi is None else pose.predict(frame,roi)[0]
        rows.append(dict(label=label,roi=roi,state=tracker.state,angles=None if angles is None else angles.tolist()))
        now+=1/30
    assert all(r['roi'] is None for r in rows[6:12])
    assert rows[5]['roi'] is not None and rows[-1]['roi'] is not None
    original=detector.detect(image)[0]
    assert len(original)==1
    base=original[0][0]
    translated=[]
    for shift in (-220,220):
        moved=cv2.warpAffine(image,np.float32([[1,0,shift],[0,1,0]]),(image.shape[1],image.shape[0]))
        found=detector.detect(moved)[0]
        assert len(found)==1
        actual=found[0][0][0]-base[0]
        assert abs(actual-shift)<20,(shift,actual)
        translated.append(dict(expected_px=shift,measured_px=float(actual)))
    occluded=image.copy()
    x,y,w,h=crop_for(base,image.shape)
    occluded[max(0,y-30):min(image.shape[0],y+h+30),max(0,x-30):min(image.shape[1],x+w+30)]=0
    assert not detector.detect(occluded)[0], 'Covered face must not remain a detection'
    angles=[]
    crops=[]
    for angle in (-20,0,20):
        mat=cv2.getRotationMatrix2D((base[0]+base[2]/2,base[1]+base[3]/2),angle,1)
        frame=cv2.warpAffine(image,mat,(image.shape[1],image.shape[0]))
        found=detector.detect(frame)[0]
        assert found
        roi=crop_for(found[0][0],frame.shape)
        value,_=pose.predict(frame,roi)
        angles.append(value.tolist())
        x,y,w,h=roi
        crops.append(cv2.resize(frame[y:y+h,x:x+w],(240,240)))
    assert angles[0][2] > angles[1][2] > angles[2][2],angles
    cv2.imwrite(str(output/'angle-crops.jpg'),np.hstack(crops))
    head_execution=pose.finish()
    region_execution=detector.finish()
    fixture=dict(version=1,sequence=1,tracked=True,headTracked=True,faceTracked=False,
                 headPitch=angles[1][0],headYaw=angles[1][1],headRoll=angles[1][2])
    (output/'packet.json').write_text(json.dumps(fixture),encoding='utf-8')
    result=dict(status='passed',input='existing recording first frame',
                limitation='Artificial black/occlusion/translation probes are not real-person quality validation',
                rows=rows,translations=translated,rotation_degrees=[-20,0,20],head_angles=angles,
                head_execution=head_execution,region_execution=region_execution)
    (output/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(output)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows',)}))


if __name__=='__main__': main()
