# Segments the original invitation into layers using rembg (isnet) inside per-element boxes.
import sys, numpy as np
from PIL import Image
from rembg import remove, new_session
SRC='/home/user/image/convite-vicente/assets/original.png'
OUT=sys.argv[1]
im=Image.open(SRC).convert('RGB')
BOX={
 'ptero':(0,45,350,270),'trice':(812,60,1122,420),'brachio':(0,525,305,1085),'trex':(765,550,1122,1195),
 'logo':(298,12,818,395),'sign1':(112,325,1000,582),'sign2':(262,525,805,875),'sign3':(276,840,798,1008),
 'sign4':(258,982,880,1192),'stone':(296,1180,840,1342),'picnicL':(0,975,352,1352),'eggs':(838,1135,1105,1345),
}
s=new_session(sys.argv[2] if len(sys.argv)>2 else 'isnet-general-use')
for k,b in BOX.items():
    c=im.crop(b); m=remove(c,session=s,only_mask=True)
    m.save(f'{OUT}/mask_{k}.png')
    bg=Image.new('RGB',c.size,(255,0,255)); bg.paste(c,(0,0),m); bg.save(f'{OUT}/prev_{k}.png')
    print(k,'done',flush=True)
