"""Check actual Player snapshots against its RGBA output, without visual inspection.

Create screen.png, hidden.png and square.png with smoke_unity.py --obs,
using --no-preview for hidden and --output-width 960 --output-height 960
for square. This is a rendering check, not tracking-quality evaluation.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    result = {}
    background = np.array([.09, .07, .06]) * 255  # BuildPlayer camera, BGR/gamma
    for name in ("screen", "hidden", "square"):
        path = args.folder / (name + ".png")
        screen = cv2.imread(str(path))
        rgba = cv2.imread(str(path) + ".alpha.png", cv2.IMREAD_UNCHANGED)
        assert screen is not None and rgba is not None, path
        h, w = screen.shape[:2]
        assert rgba.shape[2] == 4 and (rgba[:, :, 3] == 255).sum() > 10000
        expected = np.broadcast_to(background, (h, w, 3)).copy()
        if name != "hidden":
            scale = min(w / rgba.shape[1], h / rgba.shape[0])
            rw, rh = round(rgba.shape[1] * scale), round(rgba.shape[0] * scale)
            image = cv2.resize(rgba.astype(float), (rw, rh))
            x, y = (w - rw) // 2, (h - rh) // 2
            expected[y:y+rh, x:x+rw] = np.clip(
                image[:, :, :3] + background * (1 - image[:, :, 3:4] / 255), 0, 255)
        error = np.abs(screen.astype(float) - expected)
        result[name] = dict(mean=float(error.mean()), p95=float(np.percentile(error, 95)))
        # Separate diagnostic renders can differ slightly in hair motion/AA.
        assert result[name]["mean"] < 3 and result[name]["p95"] < 5, result[name]
        if name == "hidden":
            assert np.max(np.ptp(screen.astype(int), axis=(0, 1))) == 0
    (args.folder / "pixel-check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
