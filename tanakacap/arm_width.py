"""Image cross-section width diagnostic, not an arm segmentation/depth detector."""
import cv2
import numpy as np


def width_eligibility(xy,scores,image_size,side):
    """Observable forearm proxy, decided before attempting contour extraction.

    This is landmark-based eligibility, not ground-truth visual annotation.
    Contour ambiguity must remain in the denominator.
    """
    if xy is None or scores is None:return 'missing'
    ids=[7,9] if side=='left' else [8,10]
    p=np.asarray(xy,float)[ids];s=np.asarray(scores,float)[ids]
    if not np.isfinite(p).all():return 'missing'
    size=np.asarray(image_size,float);margin=max(8.,min(size)*.025)
    if (p<margin).any() or (p>size-1-margin).any():return 'out_of_frame'
    if not np.isfinite(s).all() or (s<.5).any():return 'low_confidence'
    if np.linalg.norm(p[1]-p[0])<50:return 'foreshortened_or_small'
    return 'eligible'


def consistent_section_width(sections):
    """Fit a mild forearm taper with >=4 supporting image cross sections.

    Return middle-section width. One isolated edge error must not invalidate
    four consistent boundaries; steep/nonlinear variations stay ambiguous.
    """
    if len(sections)<4:return None
    samples=np.asarray(sections,float);x=samples[:,0]-2;y=samples[:,1]
    candidates=[]
    for i in range(len(x)):
        for j in range(i+1,len(x)):
            slope=(y[j]-y[i])/(x[j]-x[i]);middle=y[i]-slope*x[i]
            if middle<=0 or abs(slope)*4>.8*middle:continue
            residual=abs(y-(middle+slope*x))
            good=residual<=max(2.,middle*.1)
            if good.sum()<4:continue
            fit=np.linalg.lstsq(np.column_stack([np.ones(good.sum()),x[good]]),y[good],rcond=None)[0]
            if fit[0]<=0 or abs(fit[1])*4>.8*fit[0]:continue
            candidates.append((-int(good.sum()),float(np.mean(residual[good])),float(fit[0])))
    return min(candidates)[2] if candidates else None


def measure_arm_widths(image,xy,scores,face_scale=None):
    result={}
    h,w=image.shape[:2]
    for side,ids in [('left',[7,9]),('right',[8,10])]:
        eligibility=width_eligibility(xy,scores,(w,h),side)
        if eligibility!='eligible':
            result[side]={'status':eligibility,'eligibility':eligibility};continue
        p=np.asarray(xy,float)[ids]
        direction=p[1]-p[0];length=np.linalg.norm(direction)
        normal=np.array([-direction[1],direction[0]])/length
        radius=int(np.clip(length*.35,16,90))
        offsets=np.arange(-radius,radius+1)
        centers=p[0]+np.linspace(.3,.7,5)[:,None]*direction
        samples=centers[:,None,:]+offsets[None,:,None]*normal
        inside=(samples[...,0]>=1)&(samples[...,0]<w-1)&(samples[...,1]>=1)&(samples[...,1]<h-1)
        strip=cv2.remap(image,samples[...,0].astype(np.float32),samples[...,1].astype(np.float32),cv2.INTER_LINEAR).astype(float)
        # Compare color to the center, requiring a stable contrast boundary on
        # both sides at several cross sections. Same-colored shirt/background
        # yields no measurement. Pattern edges can still produce false widths.
        center=np.median(strip[:,radius-2:radius+3],axis=1)
        distance=np.linalg.norm(strip-center[:,None,:],axis=2)
        # Search rays may leave the image even when the real arm boundary is
        # visible. Ignore unavailable samples, not the entire visible forearm.
        distance[~inside]=np.nan
        widths=[]
        for section,row in enumerate(distance):
            ends=[]
            for outward in (row[radius::-1],row[radius:]):
                hit=np.flatnonzero((outward[3:-2]>45)&(outward[4:-1]>45)&(outward[5:]>45))
                if not len(hit):break
                ends.append(int(hit[0]+3))
            if len(ends)==2 and min(ends)>=5 and max(ends)/min(ends)<2.5:
                widths.append([section,sum(ends)])
        if len(widths)<4:
            result[side]={'status':'ambiguous_contour','eligibility':'eligible','supported_sections':len(widths)};continue
        width=consistent_section_width(widths)
        if width is None:
            result[side]={'status':'inconsistent_contour','eligibility':'eligible','supported_sections':len(widths),'section_widths':widths};continue
        result[side]={'status':'measured','eligibility':'eligible','width_pixels':width,'supported_sections':len(widths),
                      'section_widths':widths,
                      'distance_normalized_width':width*face_scale if face_scale is not None else None,
                      'drives_pose':False}
    return result
