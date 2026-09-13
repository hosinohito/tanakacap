"""Reversible seated/front-workspace reconstruction before avatar normalization.

Keeps filtered image-plane bone vectors and a supported length lower bound.
This is weak-perspective geometry, not a calibrated metric camera or a complete
anatomical shoulder model. No model Z sign is an absolute constraint.
"""
import numpy as np


class FrontProjection:
    def __init__(self):
        self.previous = None
        self.time = None
        self.details = {}

    def reset(self):
        self.previous = None
        self.time = None

    def solve(self, bones, lengths, now):
        bones = np.asarray(bones, float)
        lengths = np.asarray(lengths, float)
        self.details = {}
        if bones.shape != (2, 3) or lengths.shape != (2,) or not np.isfinite(bones).all() or not np.isfinite(lengths).all() or (lengths < .07).any():
            self.details['reason'] = 'lengths_unavailable'
            return None
        if self.time is None or now-self.time > .3:
            self.previous = None
        self.time = now
        planar = np.linalg.norm(bones[:, :2], axis=1)
        # Online maxima are lower bounds. Never shrink a longer valid XY
        # observation to enforce a stale length, nor shorten calibration.
        # A supported maximum projection is a lower bound, not an exact
        # anatomical length. Preserve plausible observed depth when that bound
        # is still too short; otherwise an early genuine reach gets flattened.
        observed_z = np.clip(bones[:, 2], -lengths, lengths)
        effective = np.maximum(lengths, np.hypot(planar, observed_z))
        magnitudes = np.sqrt(np.maximum(0, effective**2-planar**2))
        candidates = []
        for s0, s1 in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            candidate = bones.copy()
            candidate[:, 2] = magnitudes * [s0, s1]
            if candidate[:, 2].sum() < -1e-8:
                continue
            directions = candidate/effective[:, None]
            cosine = float(np.clip(directions[0] @ directions[1], -1, 1))
            if cosine < np.cos(np.radians(155)):
                continue
            # Model depth is a soft observation, bounded against gross outliers.
            model = np.clip(bones[:, 2], -effective, effective)
            cost = .2 * float(np.sum(((candidate[:, 2]-model)/effective)**2))
            if self.previous is not None:
                cost += .6 * float(np.sum(((candidate[:, 2]-self.previous[:, 2])/effective)**2))
            # Resolve near-ties toward an extended reach, not a folded elbow.
            # This does not forbid an actual bent arm or posterior forearm.
            cost += .04*(1-cosine)
            candidates.append((cost, candidate, cosine))
        if not candidates:
            self.details['reason'] = 'no_feasible_front_branch'
            return None
        cost, result, cosine = min(candidates, key=lambda item:item[0])
        self.previous = result.copy()
        self.details = dict(reason='fit', projected=planar.tolist(), supported=lengths.tolist(),
            effective=effective.tolist(), model_z=bones[:, 2].tolist(), solved_z=result[:, 2].tolist(),
            bend_degrees=float(np.degrees(np.arccos(cosine))), cost=cost,
            length_error=float(np.max(np.abs(np.linalg.norm(result,axis=1)-effective))))
        return result
