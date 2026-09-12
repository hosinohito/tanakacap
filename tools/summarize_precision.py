"""Numerical comparison, not a visual quality or ground-truth accuracy verdict."""
import json
import sys
from pathlib import Path
import numpy as np


def summarize(folder):
    folder = Path(folder)
    report = json.loads((folder/'report.json').read_text())
    names = list(report['variants'])
    if len(names) != 2 or report['status'] != 'complete': raise ValueError('Two completed variants required')
    paths = [folder/n/'frames.jsonl' for n in names]
    rows = [[json.loads(x) for x in p.read_text().splitlines()] for p in paths]
    assert len(rows[0]) == len(rows[1])
    xy_deltas, z_deltas, visible_deltas = [], [], []
    flags = {n: {} for n in names}
    packet_deltas = {}
    packet_unequal = 0
    flag_mismatch = {}
    for a,b in zip(*rows):
        assert (a['frame'],a['time']) == (b['frame'],b['time'])
        valid = (np.asarray(a['scores'])>.3)&(np.asarray(b['scores'])>.3)
        xa,xb=np.asarray(a['xy'],float),np.asarray(b['xy'],float)
        delta=np.linalg.norm(xa-xb,axis=1)
        xy_deltas.extend(delta[valid].tolist())
        if 'source_size' in report:
            size=np.asarray(report['source_size'])
            inside=(xa>=0).all(1)&(xb>=0).all(1)&(xa<size).all(1)&(xb<size).all(1)
            visible_deltas.extend(delta[valid&inside].tolist())
        if a['depth'] is not None and b['depth'] is not None:
            za,zb=np.asarray(a['depth'],float),np.asarray(b['depth'],float)
            z_deltas.extend(np.abs(za-zb)[valid].tolist())
        pa,pb=a['sent_packet'],b['sent_packet']
        packet_unequal += pa != pb
        for name,p in zip(names,(pa,pb)):
            for k,v in p.items():
                if isinstance(v,bool): flags[name][k]=flags[name].get(k,0)+int(v)
        for k,va in pa.items():
            vb=pb.get(k)
            if isinstance(va,bool) and isinstance(vb,bool):
                flag_mismatch[k]=flag_mismatch.get(k,0)+int(va!=vb)
            elif isinstance(va,(int,float)) and isinstance(vb,(int,float)) and k not in ('frame','time','sequence'):
                if np.isfinite([va,vb]).all(): packet_deltas.setdefault(k,[]).append(abs(va-vb))
    def stats(values):
        values=np.asarray(values,float);values=values[np.isfinite(values)]
        return dict(count=len(values),mean=float(np.mean(values)),p50=float(np.median(values)),p95=float(np.percentile(values,95)),max=float(np.max(values))) if len(values) else {}
    result=dict(scope='Differences between estimates, not error against a known pose. Independent ROI can amplify precision changes.',
        observations=len(rows[0]),unequal_packets=packet_unequal,
        high_confidence_xy_delta_pixels=stats(xy_deltas),high_confidence_z_delta=stats(z_deltas),
        both_in_frame_high_confidence_xy_delta_pixels=stats(visible_deltas),
        active_observations=flags,flag_mismatch=flag_mismatch,packet_absolute_delta={k:stats(v) for k,v in packet_deltas.items()})
    (folder/'difference.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('packet_absolute_delta','active_observations')},indent=2))


if __name__=='__main__': summarize(sys.argv[1])
