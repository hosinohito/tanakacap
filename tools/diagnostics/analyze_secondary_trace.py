"""Summarize offline secondary-motion traces; contains no avatar paths or images."""
import argparse
import json
import re
from pathlib import Path
import numpy as np


def summarize(path):
    rows = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('FRAME '):
            continue
        name, quaternion, speed = line.split('|')[:3]
        q = list(map(float, re.findall(r'-?\d+\.\d+', quaternion)))
        rows.setdefault(name, []).append([*q, float(speed)])
    result = []
    for name, values in rows.items():
        a = np.asarray(values)
        q = a[:, :4]
        q /= np.linalg.norm(q, axis=1)[:, None]
        step = np.degrees(2*np.arccos(np.clip(abs((q[1:]*q[:-1]).sum(1)), 0, 1)))
        result.append(dict(path=name, frames=len(a), max_step=float(step.max()),
                           p95_step=float(np.percentile(step, 95)), max_speed=float(a[:,4].max())))
    return sorted(result, key=lambda x:x['p95_step'], reverse=True)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace',type=Path)
    args=parser.parse_args()
    result=summarize(args.trace)
    args.trace.with_suffix('.summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    for row in result[:12]:
        print(f"p95={row['p95_step']:.2f} max={row['max_step']:.2f}: {row['path']}")
