"""Bilateral K/Th displacement at coherent LiDAR scarps (one fixed research lane).

No catalogue, prior predictions, fitted statistics or registry inputs are used.
Angles follow the cached-product generator: degrees clockwise from north.
"""
from __future__ import annotations
import numpy as np
from scipy.ndimage import map_coordinates

FEATURE_NAMES=('K','Th','step','coherence','sin2strike','cos2strike','K_gain','Th_gain','joint_gain')


def _check_u8(a, shape):
    a=np.asarray(a)
    if a.shape!=shape or a.dtype!=np.uint8:
        raise ValueError('Each cache channel must be a shape-aligned uint8 array')
    return a


def texture_features(footprint, k, th, step, coherence, strike, lidar_valid, *, chunk_size=150000):
    """Return (feature matrix at row-major footprint pixels, support).

    Five samples on either side of each local strike are compared at three
    tangential lags. Invalid source samples invalidate the derived features;
    no wrap-around, rescaling from labels, or imputation using the catalogue.
    """
    fp=np.asarray(footprint,dtype=bool)
    if fp.ndim!=2 or not fp.any() or chunk_size < 1: raise ValueError('Nonempty 2D footprint and positive chunk size required')
    k,th,step,coherence,strike,lidar_valid=(_check_u8(v,fp.shape) for v in (k,th,step,coherence,strike,lidar_valid))
    ids=np.flatnonzero(fp)
    matrix=np.zeros((len(ids),len(FEATURE_NAMES)),np.float32)
    qa=[a.ravel()[ids] for a in (k,th,step,coherence,strike,lidar_valid)]
    for col,q in enumerate(qa[:2]):
        matrix[:,col]=np.where(q>0,(q.astype(np.float32)-1)/254,0)
    matrix[:,2]=np.where(qa[2]>0,((qa[2].astype(np.float32)-1)/254)**2,0)
    matrix[:,3]=np.where(qa[3]>0,(qa[3].astype(np.float32)-1)/254,0)
    valid_angle=qa[4]>0
    theta=np.maximum(qa[4].astype(np.float32)-1,0)*(np.pi/254)
    matrix[:,4]=np.where(valid_angle,np.sin(2*theta),0)
    matrix[:,5]=np.where(valid_angle,np.cos(2*theta),0)
    center=np.logical_and.reduce([q>0 for q in qa])
    support=np.zeros(len(ids),bool)
    candidates=np.flatnonzero(center)
    h,w=fp.shape
    for start in range(0,len(candidates),chunk_size):
        ix=candidates[start:start+chunk_size]
        pos=ids[ix]
        yy=(pos//w).astype(np.float32); xx=(pos%w).astype(np.float32)
        angle=theta[ix]
        ty=-np.cos(angle); tx=np.sin(angle)
        ny=np.sin(angle); nx=np.cos(angle)
        n=len(ix)
        # stats[channel, lag, point]; samples are scaled only by a fixed 255.
        sum_a=np.zeros((2,3,n),np.float32); sum_b=np.zeros_like(sum_a)
        sum_aa=np.zeros_like(sum_a); sum_bb=np.zeros_like(sum_a); sum_ab=np.zeros_like(sum_a)
        ok=np.ones(n,bool)
        for along in (-4,-2,0,2,4):
            acoord=np.array([yy-3*ny+along*ty, xx-3*nx+along*tx])
            aval=[]
            for band in (k,th):
                v=map_coordinates(band,acoord,order=0,mode='constant',cval=0,prefilter=False).astype(np.float32)
                ok &= v>0; aval.append(v/255.)
            for lag_i,lag in enumerate((-2,0,2)):
                bcoord=np.array([yy+3*ny+(along+lag)*ty,xx+3*nx+(along+lag)*tx])
                for chan,band in enumerate((k,th)):
                    bv=map_coordinates(band,bcoord,order=0,mode='constant',cval=0,prefilter=False).astype(np.float32)
                    ok &= bv>0; b=bv/255.; a=aval[chan]
                    sum_a[chan,lag_i]+=a; sum_b[chan,lag_i]+=b
                    sum_aa[chan,lag_i]+=a*a; sum_bb[chan,lag_i]+=b*b; sum_ab[chan,lag_i]+=a*b
        covariance=sum_ab-sum_a*sum_b/5
        va=np.maximum(sum_aa-sum_a*sum_a/5,0)
        vb=np.maximum(sum_bb-sum_b*sum_b/5,0)
        denom=np.sqrt(va*vb)
        # A near-constant profile has no interpretable correlation.
        correlation=np.zeros_like(covariance)
        np.divide(covariance,denom,out=correlation,where=denom>1e-6)
        np.clip(correlation,-1,1,out=correlation)
        for chan in (0,1):
            best=np.maximum(correlation[chan,0],correlation[chan,2])
            gain=np.maximum(best-correlation[chan,1],0)
            matrix[ix,6+chan]=np.where(ok & (best>0),gain,0)
        same=(correlation[0,2]>=correlation[0,0])==(correlation[1,2]>=correlation[1,0])
        matrix[ix,8]=np.where(same & ok,np.sqrt(matrix[ix,6]*matrix[ix,7]),0)
        support[ix]=ok
    if not np.isfinite(matrix).all(): raise ValueError('Nonfinite derived features')
    return matrix,support
