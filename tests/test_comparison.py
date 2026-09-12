import numpy as np
import pytest
from capture_lab.comparison_capture import TakeWriter,stage_at,STAGES

def test_face_capture_profile_timeline_and_metadata(tmp_path):
    import json
    from capture_lab.comparison_capture import FACE_STAGES
    elapsed=0
    for key,duration,title,instruction in FACE_STAGES:
        assert stage_at(elapsed,FACE_STAGES)[0]==key
        elapsed+=duration
    assert stage_at(elapsed,FACE_STAGES) is None
    assert elapsed==30 and FACE_STAGES==[('free',30,'録画中','')]
    writer=TakeWriter(tmp_path/'face',[64,48],30,{}, {},'face-head')
    writer.append(np.zeros((48,64,3),np.uint8),0.,1,'free')
    writer.finish()
    meta=json.loads((tmp_path/'face'/'take.json').read_text(encoding='utf-8'))
    assert meta['profile']=='face-head' and meta['stages'][-1][0]=='free'
    assert meta['status']=='complete' and meta['audio'] is False
from capture_lab.comparison import load_take,images,SharedFace,clean,fingerprint
from test_head_pose import projected

def test_lossless_take_and_timestamp_roundtrip(tmp_path):
    path=tmp_path/'take';writer=TakeWriter(path,[64,48],30,{'gaze_enabled':False},{'synthetic':True})
    rng=np.random.default_rng(7);frames=[rng.integers(0,256,(48,64,3),dtype=np.uint8) for _ in range(4)];times=[0.,.04,.09,.13]
    for i,(frame,t) in enumerate(zip(frames,times)):writer.append(frame,t,i*2,'neutral')
    writer.finish();meta,timeline=load_take(path)
    assert [r['time'] for r in timeline]==times
    for (row,image),frame in zip(images(path,timeline),frames):np.testing.assert_array_equal(image,frame)
    (path/'frames.jsonl').write_text('tampered')
    with pytest.raises(ValueError,match='checksum'):load_take(path)

def test_incomplete_capture_and_clock_rejected(tmp_path):
    writer=TakeWriter(tmp_path/'take',[64,48],30,{},{});frame=np.zeros((48,64,3),np.uint8)
    writer.append(frame,0,0,'neutral')
    with pytest.raises(ValueError):writer.append(frame,0,1,'neutral')
    writer.finish('interrupted')
    with pytest.raises(ValueError,match='completed'):load_take(tmp_path/'take')

def test_capture_stage_boundaries():
    assert stage_at(0)[0]=='neutral'
    assert stage_at(10)[0]=='arm_calibration'
    assert stage_at(sum(s[1] for s in STAGES)) is None

def test_shared_face_matches_live_sequence_and_fingerprint(tmp_path):
    settings={'observation_block':3,'observation_stride':1,'head_pose_mode':'pnp','head_pitch_gain':1.8,'mouth_lip_depth_scale':1.5,'face_distance_filter':'stable','gaze_enabled':False}
    from capture_lab.retarget import packet_from_landmarks,FaceFilter
    from capture_lab.head_pose import HeadPose
    from capture_lab.face_distance import FaceDistance
    face=SharedFace(settings,tmp_path);pose=HeadPose();f=FaceFilter(3,1);d=FaceDistance(3,1);image=np.zeros((720,1280,3),np.uint8)
    for i in range(35):
        xy,scores=projected(pitch=0 if i<20 else 15);now=i/30
        p=packet_from_landmarks(xy,scores,i);pose.update(xy,scores,p,(1280,720));f.update(p,now);d.update(xy,scores,p,now)
        assert clean(face.update(image,xy,scores,i,now))==clean(p)
    assert fingerprint(settings)==fingerprint(settings)
    assert fingerprint(settings)['sha256']!=fingerprint({**settings,'face_distance_filter':'legacy'})['sha256']
