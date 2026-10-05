import time, torch
from pathlib import Path
from ultralytics import SAM
t=time.time()
m=SAM("sam_b.pt")
print("loaded sam_b in",round(time.time()-t,1),"s; cuda",torch.cuda.is_available())
R=Path(r"C:\Users\mrjos\Downloads\wildlife-yolo")
f=sorted((R/"images"/"train").glob("elephant_*.png"))[3]
from PIL import Image
W,H=Image.open(f).size
bx=[]
for l in (R/"labels"/"train"/(f.stem+".txt")).read_text().splitlines():
    c,x,y,w,h=map(float,l.split()); bx.append([(x-w/2)*W,(y-h/2)*H,(x+w/2)*W,(y+h/2)*H])
t=time.time(); r=m(str(f),bboxes=bx); print("segmented",len(bx),"boxes in",round(time.time()-t,2),"s; masks",r[0].masks.data.shape)
