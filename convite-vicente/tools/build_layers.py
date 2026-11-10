"""Builds the animation layers from the refined masks.
Usage: python3 build_layers.py <seg_dir>
Outputs to ../assets/layers: one RGBA PNG per element (cropped), plate.png (clean forest),
foliage/waterfall ambient layers, mist textures and layers.json with positions."""
import sys, json, cv2, numpy as np
SEG=sys.argv[1]
ROOT='/home/user/image/convite-vicente'
OUT=f'{ROOT}/assets/layers'
import os; os.makedirs(OUT,exist_ok=True)
img=cv2.imread(f'{ROOT}/assets/original.png'); H,W=img.shape[:2]
Z=['ptero','trice','brachio','trex','logo','sign1','sign2','sign3','sign4','picnicL','eggs','stone']
M={k:cv2.imread(f'{SEG}/ref_{k}.png',0) for k in Z}
EXTRA={'sign4':[(356,980,386,1016),(718,980,748,1016)],'sign3':[(372,850,402,880),(692,850,722,880)]}
for k,rs in EXTRA.items():
    for (a,b,c,d) in rs:
        sub=img[b:d,a:c].astype(int); rope=(sub.sum(2)<520)  # darker rope fibres vs bright sky
        M[k][b:d,a:c]=np.maximum(M[k][b:d,a:c],(rope*255).astype(np.uint8))
yy=np.arange(H)[:,None]*np.ones((1,W))
# ownership fixes
own={k:M[k].copy() for k in Z}
for i,k in enumerate(Z):
    for h in Z[i+1:]:
        own[k][M[h]>0]=0          # higher layers own overlapping pixels
own['picnicL'][(M['brachio']>0)&(yy<990)]=0   # brachio body above basket
own['brachio'][(M['picnicL']>0)&(yy>=990)]=0
own['trice'][yy>395]=0              # sign1 corner/rope
# clean tiny islands
for k in Z:
    m=own[k]; n,lab,st,_=cv2.connectedComponentsWithStats(m)
    for i in range(1,n):
        if st[i,4]<400: m[lab==i]=0
union=np.zeros((H,W),np.uint8)
for k in Z: union|=M[k]
meta={'W':W,'H':H,'layers':{}}
def save_rgba(name,rgb,alpha,pad=4):
    ys,xs=np.where(alpha>0)
    x0,y0=max(0,xs.min()-pad),max(0,ys.min()-pad); x1,y1=min(W,xs.max()+pad+1),min(H,ys.max()+pad+1)
    rgba=np.dstack([rgb[y0:y1,x0:x1],alpha[y0:y1,x0:x1]])
    cv2.imwrite(f'{OUT}/{name}.png',rgba,[cv2.IMWRITE_PNG_COMPRESSION,9])
    meta['layers'][name]={'x':int(x0),'y':int(y0),'w':int(x1-x0),'h':int(y1-y0)}
for k in Z:
    a=cv2.GaussianBlur(own[k],(3,3),0.8)   # 1px anti-aliased edge
    save_rgba(k,img,a)
# ---- clean plate: multi-scale normalized convolution (soft hazy jungle) + grain
hole=cv2.dilate(cv2.morphologyEx(union,cv2.MORPH_CLOSE,np.ones((31,31),np.uint8)),np.ones((17,17),np.uint8))
# small leftover islands (rope ends, slivers between objects) are filled too
n,lab,st,_=cv2.connectedComponentsWithStats((hole==0).astype(np.uint8))
for i in range(1,n):
    if st[i,4]<6000: hole[lab==i]=255
f=img.astype(np.float32); valid=(hole==0).astype(np.float32)
def normconv(valid):
    acc=np.zeros_like(f); wacc=np.zeros((H,W),np.float32)
    for sig,wt in [(12,1.0),(30,0.6),(70,0.35),(160,0.2)]:
        num=cv2.GaussianBlur(f*valid[...,None],(0,0),sig); den=cv2.GaussianBlur(valid,(0,0),sig)
        est=num/np.maximum(den,1e-5)[...,None]; c=np.clip(den*4,0,1)*wt
        acc+=est*c[...,None]; wacc+=c
    return acc/np.maximum(wacc,1e-5)[...,None]
# the red tablecloth must not bleed upward into the jungle haze
b,g,r=[f[...,i] for i in range(3)]
cloth=((r>g+40)|((r>200)&(g>200)&(b>190)))&(yy>1270)
mix_hi=normconv(valid*(~cloth))
mix_lo=normconv(valid)
k=np.clip((yy-1285)/30,0,1)[...,None].astype(np.float32)
mix=mix_hi*(1-k)+mix_lo*k
haze=np.array([214,232,226],np.float32)  # BGR soft misty light
dist=cv2.distanceTransform(hole,cv2.DIST_L2,5)
hz=np.clip(dist/120,0,1)[...,None]*0.32
mix=mix*(1-hz)+haze*hz
rng=np.random.default_rng(7); noise=cv2.GaussianBlur(rng.normal(0,1,(H,W)).astype(np.float32),(0,0),1.0)*5
mix+=noise[...,None]
soft=cv2.GaussianBlur(hole.astype(np.float32)/255,(0,0),4)[...,None]
plate=np.clip(f*(1-soft)+mix*soft,0,255).astype(np.uint8)
cv2.imwrite(f'{OUT}/plate.jpg',plate,[cv2.IMWRITE_JPEG_QUALITY,95])
meta['layers']['plate']={'x':0,'y':0,'w':W,'h':H}
# ---- ambient regions (pixels from original, excluding all elements)
def poly_mask(polys,blur=14):
    m=np.zeros((H,W),np.uint8)
    for p in polys: cv2.fillPoly(m,[np.array(p,np.int32)],255)
    m=cv2.GaussianBlur(m,(0,0),blur); return m
excl=cv2.dilate(union,np.ones((7,7),np.uint8))
REG={
 'foliageTL':[[(0,0),(310,0),(300,40),(150,60),(120,330),(150,560),(90,700),(0,720)]],
 'foliageTR':[[(640,0),(1122,0),(1122,610),(1000,640),(990,420),(1040,300),(980,130),(800,90),(700,60)]],
 'foliageBL':[[(0,1150),(70,1170),(140,1280),(330,1350),(300,1402),(0,1402)]],
 'foliageBR':[[(880,1020),(1122,990),(1122,1402),(760,1402),(830,1330),(880,1160)]],
 'waterfall':[[(185,725),(285,725),(290,980),(180,980)]],
}
for name,polys in REG.items():
    a=poly_mask(polys,6 if name=='waterfall' else 14)
    a[excl>0]=0
    a=cv2.GaussianBlur(a,(3,3),0.8)
    save_rgba(name,img,a)
# ---- mist textures (procedural, white with alpha)
def fbm(h,w,seed,oct=6):
    r=np.random.default_rng(seed);acc=np.zeros((h,w),np.float32);amp=1;tot=0
    for o in range(oct):
        s=2**(o+2);n=r.random((max(2,h//(h//s if h//s else 1)),s)).astype(np.float32)
        n=r.random((s*h//w+2,s+2)).astype(np.float32)
        acc+=amp*cv2.resize(n,(w,h),interpolation=cv2.INTER_CUBIC);tot+=amp;amp*=0.5
    acc/=tot;acc=(acc-acc.min())/(acc.max()-acc.min());return acc
for i,seed in enumerate([3,11]):
    mw,mh=2244,1402
    n=fbm(mh,mw,seed)
    n=np.clip((n-0.38)/0.45,0,1)**1.6
    v=np.linspace(0,1,mh)[:,None]
    band=np.exp(-((v-(0.55 if i==0 else 0.35))/0.32)**2)
    al=(n*band*255).astype(np.uint8)
    # make horizontally tileable
    al=np.hstack([al[:,:mw//2],al[:,:mw//2][:,::-1]])
    al=cv2.GaussianBlur(al,(0,0),6)
    rgba=np.dstack([np.full((mh,mw,3),(238,244,246),np.uint8),al])
    cv2.imwrite(f'{OUT}/mist{i+1}.png',rgba)
# water streak texture for waterfall flow
r=np.random.default_rng(5); st=r.random((64,40)).astype(np.float32)
st=cv2.resize(st,(120,600),interpolation=cv2.INTER_CUBIC); st=np.clip((st-0.55)/0.4,0,1)
st=np.vstack([st,st]); st=cv2.GaussianBlur(st,(0,0),1.5)
cv2.imwrite(f'{OUT}/streaks.png',np.dstack([np.full(st.shape+(3,),255,np.uint8),(st*255).astype(np.uint8)]))
json.dump(meta,open(f'{OUT}/layers.json','w'),indent=1)
print(json.dumps(meta['layers']))
