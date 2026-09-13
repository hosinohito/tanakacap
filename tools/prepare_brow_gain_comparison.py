"""Only eyebrow gain differs; use the same demo asset and current Player."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tanakacap.brows import BrowFilter,KEYS
from tanakacap.head_pose import HeadPose
from tanakacap.retarget import packet_from_landmarks
from tanakacap.comparison import dump,line

def main():
    source=ROOT/'results/comparisons/head-follow-input/source/frames.jsonl'
    base=ROOT/'results/brow-demo/replay.jsonl'
    output=ROOT/'results/comparisons/brow-gain';output.mkdir(parents=True,exist_ok=False)
    source_rows=[json.loads(x) for x in source.read_text().splitlines()]
    baseline=[json.loads(x) for x in base.read_text().splitlines()]
    assert len(source_rows)==len(baseline)
    variants={}
    for name,gain in [('brow-1x',1),('brow-2x',2)]:
        folder=output/name;folder.mkdir();pose=HeadPose();brows=BrowFilter(3,1,gain)
        with (folder/'replay.jsonl').open('w') as stream:
            for row,original in zip(source_rows,baseline):
                p=packet_from_landmarks(row['xy'],row['scores'],row['frame'])
                pose.update(row['xy'],row['scores'],p,(1280,720));brows.update(p,row['time'])
                packet=original['packet'].copy()
                packet['browTracked']=p.get('browTracked',False)
                for key in KEYS:packet[key]=p.get(key,0.)
                if gain==2:
                    assert all(packet[k]==original['packet'].get(k,0.) for k in KEYS)
                    assert packet['browTracked']==original['packet']['browTracked']
                line(stream,dict(packet=packet,dt=original['dt']))
        variants[name]=dict(frames=len(baseline),player_args=['--avatar',str(ROOT/'builds/demos/haolan-custom-brows/avatars/haolan.tcap'),'--use-demo-shape-keys'])
    a=[json.loads(x) for x in (output/'brow-1x/replay.jsonl').read_text().splitlines()]
    b=[json.loads(x) for x in (output/'brow-2x/replay.jsonl').read_text().splitlines()]
    for x,y in zip(a,b):
        assert x['dt']==y['dt']
        assert {k:v for k,v in x['packet'].items() if k not in KEYS}=={k:v for k,v in y['packet'].items() if k not in KEYS}
    dump(output/'report.json',dict(status='complete',variants=variants,
        scope='Same 30-second recording and PnP controls, frozen demo avatar and current Player. Only brow gain changes from 1 to 2 after the same four-frame gate. All non-brow controls and times identical; blink unchanged.'))
    print('Verified:',len(a),'packets; only brow channels differ')

if __name__=='__main__':main()
