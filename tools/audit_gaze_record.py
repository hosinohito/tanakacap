"""Audit numeric gaze recordings; these statistics are not gaze accuracy labels."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np


def quantiles(values):
    return np.percentile(values, [5, 50, 95], axis=0).tolist() if len(values) else None


def correlation(a, b):
    if len(a) < 3 or np.std(a) < 1e-9 or np.std(b) < 1e-9:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def audit(rows):
    valid = [r for r in rows if r['sent_packet'].get('gazeTracked')]
    both = [r for r in rows if all(
        r['gaze']['eyes'].get(s, {}).get('offset') is not None for s in ('left', 'right'))]
    report = dict(
        scope='Numeric detections and sent packets only; no ground-truth gaze or live Player receipt.',
        frames=len(rows), tracked=len(valid),
        rejected_reasons=dict(Counter(x for r in rows for x in r['gaze']['rejections'])),
        valid_eye_counts=dict(Counter(r['gaze']['valid_eyes'] for r in rows)),
        quantile_order=[5, 50, 95],
        result_interval_ms=quantiles([r['result_interval_ms'] for r in rows if r.get('result_interval_ms')]),
        gaze_ms=quantiles([r['gaze_ms'] for r in valid]),
        warmup_frames=sum(r['gaze']['valid_eyes'] > 0 and not r['gaze']['output_tracked'] for r in rows),
        packet_angle_mismatch=sum(r['gaze']['output_angles'] !=
                                 [r['sent_packet']['gazeYaw'], r['sent_packet']['gazePitch']] for r in rows),
    )
    for label, subset in [('both_eyes', both), ('near_frontal', [r for r in both if
            abs(r['sent_packet']['headYaw']) < 10 and abs(r['sent_packet']['headPitch']) < 10])]:
        offsets = np.array([[r['gaze']['eyes'][s]['offset'] for s in ('left', 'right')] for r in subset])
        report[label] = dict(frames=len(subset))
        if len(subset):
            report[label].update(
                offset_quantiles_left_right_xy=quantiles(offsets),
                correlation_xy=[correlation(offsets[:, 0, i], offsets[:, 1, i]) for i in range(2)],
                eye_width_px_left_right=quantiles([[r['gaze']['eyes'][s]['eye_width'] for s in ('left', 'right')] for r in subset]),
            )
    if valid:
        raw = np.array([np.clip(np.mean([v['offset'] for v in r['gaze']['eyes'].values()
                         if v['offset'] is not None], axis=0)*[-80, 60], [-20, -12], [20, 12]) for r in valid])
        out = np.array([r['gaze']['output_angles'] for r in valid])
        report.update(raw_angle_quantiles=quantiles(raw), sent_angle_quantiles=quantiles(out),
                      raw_std=raw.std(0).tolist(), sent_std=out.std(0).tolist(),
                      head_output_correlations=[correlation([r['sent_packet'][k] for r in valid], out[:, i])
                                                for i, k in enumerate(('headYaw', 'headPitch'))])
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.record.read_text(encoding='utf-8').splitlines()]
    report = audit(rows)
    report['source'] = str(args.record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps(report, indent=2, allow_nan=False))
