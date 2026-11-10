# Refines rembg masks with GrabCut and morphology; writes refined masks (full-canvas) for review.
import sys, cv2, numpy as np
SEG=sys.argv[1]
img=cv2.imread('/home/user/image/convite-vicente/assets/original.png')
H,W=img.shape[:2]
sys.path.insert(0,'/home/user/image/convite-vicente/tools')
from segment_boxes import BOX, RECT
def full(k):
    x0,y0,x1,y1=BOX[k]; m=cv2.imread(f'{SEG}/mask_{k}.png',0)
    f=np.zeros((H,W),np.uint8); f[y0:y1,x0:x1]=m; return f
out={}
for k,(x0,y0,x1,y1) in BOX.items():
    rb=full(k)
    gc=np.full((H,W),cv2.GC_BGD,np.uint8)
    gc[y0:y1,x0:x1]=cv2.GC_PR_BGD
    if k in RECT:
        for (a,b,c,d) in RECT[k]: gc[b:d,a:c]=cv2.GC_PR_FGD
    gc[rb>128]=cv2.GC_PR_FGD
    gc[rb>235]=cv2.GC_FGD if k not in RECT else cv2.GC_PR_FGD
    bg=np.zeros((1,65)); fg=np.zeros((1,65))
    pad=20; X0,Y0,X1,Y1=max(0,x0-pad),max(0,y0-pad),min(W,x1+pad),min(H,y1+pad)
    sub=gc[Y0:Y1,X0:X1].copy()
    cv2.grabCut(img[Y0:Y1,X0:X1],sub,None,bg,fg,6,cv2.GC_INIT_WITH_MASK)
    m=np.where((sub==1)|(sub==3),255,0).astype(np.uint8)
    # keep large components, fill holes
    n,lab,st,_=cv2.connectedComponentsWithStats(m)
    keep=np.zeros_like(m)
    for i in range(1,n):
        if st[i,4]>1500: keep[lab==i]=255
    cnts,_=cv2.findContours(keep,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    filled=np.zeros_like(keep); cv2.drawContours(filled,cnts,-1,255,-1)
    filled=cv2.morphologyEx(filled,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    f=np.zeros((H,W),np.uint8); f[Y0:Y1,X0:X1]=filled
    cv2.imwrite(f'{SEG}/ref_{k}.png',f)
    pv=img.copy(); pv[f==0]=(255,0,255)
    cv2.imwrite(f'{SEG}/rprev_{k}.png',pv[y0:y1,x0:x1])
    print(k,flush=True)
