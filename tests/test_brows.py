import numpy as np
from capture_lab.brows import measure,observe,BrowFilter,KEYS


def face():
    p=np.zeros((133,2));s=np.ones(133);f=p[23:91]
    f[36]=[100,100];f[39]=[120,100];f[42]=[160,100];f[45]=[180,100]
    f[17:22]=[[96,84],[103,82],[110,80],[117,82],[124,84]]
    f[22:27]=[[156,84],[163,82],[170,80],[177,82],[184,84]]
    return p,s


def test_brows_anatomical_left_and_eye_lids_do_not_drive_brows():
    p,s=face();initial=measure(p,s)
    p[23+22:23+27,1]-=6
    changed=measure(p,s)
    assert np.all(changed[:2]>initial[:2]) and np.allclose(changed[2:],initial[2:])
    p[23+37]=[100,40];p[23+43]=[100,10]
    assert np.allclose(measure(p,s),changed)


def test_brow_measure_translation_scale_roll_invariant():
    p,s=face();baseline=measure(p,s)
    angle=.3;rotation=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    assert np.allclose(measure((p@rotation.T)*2+[40,90],s),baseline)


def test_brow_neutral_does_not_relearn_expression_and_loss_has_no_output():
    p,s=face();tracker=BrowFilter(3,1)
    for i in range(16):
        packet=dict(faceTracked=True);observe(p,s,packet);tracker.update(packet,i/30)
    assert packet['browTracked'] and np.allclose([packet[k] for k in KEYS],0)
    reference=tracker.reference.copy();p[23+22:23+27,1]-=6
    for i in range(16,32):
        packet=dict(faceTracked=True);observe(p,s,packet);tracker.update(packet,i/30)
    assert packet['browLeftInner']>.8 and packet['browRightInner']==0
    assert np.array_equal(tracker.reference,reference)
    s[23+22]=0;observe(p,s,packet);tracker.update(packet,2)
    assert not packet['browTracked']
