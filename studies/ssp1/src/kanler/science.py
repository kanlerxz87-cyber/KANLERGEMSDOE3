"""SSP1: residualized scarp profiles, independent of all catalogue coordinates.

The new transform is a hypothesis, not a physical fault probability calibration.
All input channels come from the pinned shared feature cache or documented peer
preprocessing of official USGS data. No peer prediction raster is a feature.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi

OFFSETS = np.arange(-4,5,dtype=np.float64)
WIDTHS = (0.7,1.4)
FEATURE_NAMES = [
    'step_r2_w0p7','step_amplitude_w0p7','step_r2_w1p4','step_amplitude_w1p4',
    'residual_odd_fraction','profile_residual_rms','tangent_step_persistence',
    'gravity_topography_gradient_cosine','gravity_gradient_magnitude',
    'K_encoded_cross_normal_contrast','Th_encoded_cross_normal_contrast',
    'lidar_step_clipped_m_per_m','lidar_upface_clipped_m_per_m',
    'lidar_step_asymmetry_clipped_m_per_m','lidar_coherence','lidar_relief_clipped_m',
    'cached_detrended_slope'
]


def residual_projection(t: np.ndarray = OFFSETS) -> np.ndarray:
    x = np.stack([np.ones_like(t),t,t*t],axis=1)
    return np.eye(len(t))-x@np.linalg.pinv(x)


def profile_statistics(profiles: np.ndarray) -> np.ndarray:
    """Input (...,9) heights; return two nested-model R²/amplitudes and parity.

    Each tanh template and observation is residualized against the SAME quadratic
    null. No absolute height, fault labels or spatial coordinates enter this fit.
    Amplitudes use original elevation units; R² is a dimensionless fit improvement.
    """
    z=np.asarray(profiles,dtype=np.float64)
    if z.shape[-1]!=9 or not np.isfinite(z).all():
        raise ValueError('Expected finite nine-point profiles')
    r=z@residual_projection()
    energy=np.sum(r*r,axis=-1)
    good=energy>1e-6
    out=[]
    for width in WIDTHS:
        s=residual_projection()@np.tanh(OFFSETS/width)
        ss=float(s@s)
        dot=r@s
        amp=dot/ss
        r2=np.divide(dot*dot,ss*energy,out=np.zeros_like(energy),where=good)
        out.extend([np.clip(r2,0,1),np.where(good,np.abs(amp),0)])
    odd=(r-r[...,::-1])*0.5
    odd_fraction=np.divide(np.sum(odd*odd,axis=-1),energy,out=np.zeros_like(energy),where=good)
    out.extend([np.clip(odd_fraction,0,1),np.sqrt(np.maximum(energy,0)/9)])
    return np.stack(out,axis=-1).astype(np.float32)


def fill_foot(a: np.ndarray, foot: np.ndarray) -> np.ndarray:
    if not foot.any():
        raise ValueError('Empty footprint')
    a=np.asarray(a,dtype=np.float32).copy()
    # Prevent artificial footprint-edge cliffs. Coordinates depend on data validity,
    # not catalogue presence, and therefore do not change between holdout folds.
    idx=ndi.distance_transform_edt(~foot,return_distances=False,return_indices=True)
    bad=~foot
    a[bad]=a[tuple(idx[:,bad])]
    return a


def encoded_lidar(q: np.ndarray, scale: float, sqrt: bool=True) -> np.ndarray:
    """Invert the documented clipped monotone encoding; zero stays missing/zero.

    This does not recover information lost by clipping or quantization.
    """
    x=np.maximum(np.asarray(q,dtype=np.float32)-1,0)/254
    return (x*x if sqrt else x)*scale


def build_profile_features(shared_stack: Path, data_dir: Path, out_path: Path, receipt_path: Path) -> dict:
    import hashlib,time
    t0=time.monotonic()
    stack=np.load(shared_stack,mmap_mode='r')
    with rasterio.open(data_dir/'sample_submission.tif') as ds:
        foot=np.isfinite(ds.read(1))
        geometry={'shape':list(ds.shape),'crs':str(ds.crs),'transform':list(ds.transform)[:6]}
    if stack.shape[:2]!=foot.shape or stack.shape[2]!=35:
        raise ValueError('SSP1 requires the pinned 35-channel shared cache')
    h,w=foot.shape
    out_path.parent.mkdir(parents=True,exist_ok=True)
    x=np.lib.format.open_memmap(out_path,mode='w+',dtype=np.float32,shape=(h,w,len(FEATURE_NAMES)))
    z=ndi.gaussian_filter(fill_foot(stack[:,:,11],foot),0.8,mode='nearest')
    gy=ndi.gaussian_filter(z,1.0,order=(1,0),mode='nearest')
    gx=ndi.gaussian_filter(z,1.0,order=(0,1),mode='nearest')
    mag=np.hypot(gx,gy)
    ux=gx/np.maximum(mag,1e-6);uy=gy/np.maximum(mag,1e-6)
    for y0 in range(0,h,192):
        y1=min(h,y0+192)
        yy,xx=np.mgrid[y0:y1,0:w].astype(np.float32)
        profiles=np.empty((y1-y0,w,9),dtype=np.float32)
        for j,off in enumerate(OFFSETS):
            profiles[:,:,j]=ndi.map_coordinates(z,[yy+off*uy[y0:y1],xx+off*ux[y0:y1]],order=1,mode='nearest',prefilter=False)
        x[y0:y1,:,:6]=profile_statistics(profiles)
    del profiles,z
    # Tangent persistence uses the local contour direction, not a catalogue strike.
    strength=np.maximum(x[:,:,0],x[:,:,2]).copy()
    for y0 in range(0,h,256):
        y1=min(h,y0+256);yy,xx=np.mgrid[y0:y1,0:w].astype(np.float32)
        total=np.zeros((y1-y0,w),np.float32)
        for off in (-3,-1,0,1,3):
            total+=ndi.map_coordinates(strength,[yy+off*ux[y0:y1],xx-off*uy[y0:y1]],order=1,mode='nearest',prefilter=False)
        x[y0:y1,:,6]=total/5
    del strength
    gravity=fill_foot(stack[:,:,12],foot)
    ggy=ndi.gaussian_filter(gravity,2.0,order=(1,0),mode='nearest')
    ggx=ndi.gaussian_filter(gravity,2.0,order=(0,1),mode='nearest')
    gmag=np.hypot(ggx,ggy)
    x[:,:,7]=(gx*ggx+gy*ggy)/np.maximum(mag*gmag,1e-6)
    x[:,:,8]=gmag
    del gravity,ggy,ggx,gmag,gx,gy,mag
    with rasterio.open(data_dir/'external/geodawn_rad_u8.tif') as ds:
        rad=ds.read([1,2])
    # Encoded percentiles are NOT physical K/Th concentrations or their ratio.
    for y0 in range(0,h,256):
        y1=min(h,y0+256); yy,xx=np.mgrid[y0:y1,0:w].astype(np.float32)
        for j in range(2):
            a=ndi.map_coordinates(rad[j],[yy+3*uy[y0:y1],xx+3*ux[y0:y1]],order=1,mode='nearest',prefilter=False).astype(np.float32)
            b=ndi.map_coordinates(rad[j],[yy-3*uy[y0:y1],xx-3*ux[y0:y1]],order=1,mode='nearest',prefilter=False).astype(np.float32)
            x[y0:y1,:,9+j]=np.where((a>0)&(b>0),np.abs(a-b)/254,0)
    del rad,ux,uy
    with rasterio.open(data_dir/'external/lidar_scarp_features_u8.tif') as ds:
        q=ds.read([3,6,7,9,10])
    x[:,:,11]=encoded_lidar(q[0],1)
    x[:,:,12]=encoded_lidar(q[2],1)
    x[:,:,13]=encoded_lidar(q[1],1)-encoded_lidar(q[2],1)
    x[:,:,14]=encoded_lidar(q[4],1,sqrt=False)
    x[:,:,15]=encoded_lidar(q[3],300)
    x[:,:,16]=stack[:,:,18]
    lidar_valid=int(((q[0]>0)&foot).sum());del q
    for y0 in range(0,h,256):
        tile=x[y0:y0+256]
        tile[~foot[y0:y0+256]]=0
        if not np.isfinite(tile).all():
            raise ValueError('Nonfinite SSP1 feature')
    x.flush()
    receipt={'method':'SSP1','features':FEATURE_NAMES,'shape':list(x.shape),'geometry':geometry,'catalogue_based_features':[], 'peer_prediction_features':[], 'shared_cache':str(shared_stack),'shared_cache_sha256':hashlib.file_digest(shared_stack.open('rb'),'sha256').hexdigest(),'footprint_pixels':int(foot.sum()),'lidar_available_pixels':lidar_valid,'seconds':round(time.monotonic()-t0,2),'feature_file':str(out_path),'feature_file_sha256':hashlib.file_digest(out_path.open('rb'),'sha256').hexdigest()}
    receipt_path.parent.mkdir(parents=True,exist_ok=True)
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def priority_dots(surface: np.ndarray, eligible: np.ndarray, budget: int, spacing: float=2.8) -> np.ndarray:
    """Deterministic score-first disk exclusion; never randomize to evade uniqueness.

    This is not claimed to be a globally DTI-optimal placement. Equal-score ties
    resolve by ascending raster index, and every output dot has finite support.
    """
    surface=np.asarray(surface,dtype=np.float32)
    eligible=np.asarray(eligible,bool)
    if surface.shape!=eligible.shape or surface.ndim!=2 or budget<0 or spacing<=0:
        raise ValueError('Invalid surface, budget, eligibility or spacing')
    idx=np.flatnonzero(eligible & np.isfinite(surface) & (surface>0))
    vals=surface.ravel()[idx]
    order=np.lexsort((idx,-vals))
    idx=idx[order]
    out=np.zeros(surface.shape,bool);blocked=np.zeros(surface.shape,bool)
    r=int(np.ceil(spacing));offsets=[(dy,dx)for dy in range(-r,r+1)for dx in range(-r,r+1)if dy*dy+dx*dx<spacing*spacing]
    h,w=surface.shape;count=0
    for i in idx:
        if count>=budget:
            break
        y,x=divmod(int(i),w)
        if blocked[y,x]:
            continue
        out[y,x]=True;count+=1
        for dy,dx in offsets:
            yy,xx=y+dy,x+dx
            if 0<=yy<h and 0<=xx<w:
                blocked[yy,xx]=True
    return out
