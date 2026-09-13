"""Conditional image-width coverage; never label landmark visibility as truth."""
import json
import sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tanakacap.arm_width import width_eligibility

def audit(path):
    rows=[json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]
    report={'source':str(path),'frames':len(rows),'sides':{}}
    for side in ('left','right'):
        exclusions=Counter();statuses=Counter();measured=normalized=0
        for row in rows:
            state=width_eligibility(row.get('body_xy'),row.get('body_scores'),row['image_size'],side)
            exclusions[state]+=1
            if state!='eligible':continue
            value=row.get('arm_image_width',{}).get(side,{})
            statuses[value.get('status','not_recorded')]+=1
            if value.get('status')=='measured':
                measured+=1
                normalized+=value.get('distance_normalized_width') is not None
        eligible=exclusions['eligible']
        report['sides'][side]={'eligibility_counts':dict(exclusions),'eligible_statuses':dict(statuses),
            'eligible_frames':eligible,'measured_eligible':measured,'normalized_eligible':normalized,
            'measurement_rate_when_eligible':measured/eligible if eligible else None,
            'normalized_rate_when_eligible':normalized/eligible if eligible else None}
    report['limitation']='Eligibility inferred from elbow/wrist landmarks, not manual visibility labels. Ambiguous/inconsistent contours remain failures; offscreen/low-confidence/short projections are separate exclusions. Old RGB absent: new extraction cannot be replayed.'
    return report

if __name__=='__main__':
    reports=[audit(Path(p)) for p in sys.argv[1:]]
    output=ROOT/'results/width-eligibility';output.mkdir(exist_ok=True)
    (output/'audit.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print(json.dumps(reports,indent=2))
