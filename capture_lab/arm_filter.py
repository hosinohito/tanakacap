"""Responsive image-plane motion with an independent, conservative depth filter."""
import numpy as np


def filter_arm(previous, target, dt):
    delta=target-previous
    planar=delta[:,:2]
    distance=np.linalg.norm(planar,axis=1,keepdims=True)
    # Keep the old small-motion gain; open up for deliberate image-plane motion.
    # A bad Z jump must never throttle an otherwise clear arm raise in XY.
    gain=18+np.minimum(42,distance*100)
    xy=previous[:,:2]+planar*np.minimum(1,8*dt/np.maximum(distance,1e-6))*(1-np.exp(-gain*dt))
    z=previous[:,2]+np.clip(delta[:,2],-8*dt,8*dt)*(1-np.exp(-18*dt))
    return np.column_stack((xy,z))
