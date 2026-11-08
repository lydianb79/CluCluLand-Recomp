# Renders the app icon procedurally (original artwork). Usage: python3 Tools/make_icon.py A|B -> /tmp/icon/icon_<variant>.png
# Requires numpy, pillow, scipy.
import numpy as np, sys, math
from PIL import Image, ImageDraw, ImageFilter
SS=4; S=1024*SS
Y,X=np.mgrid[0:S,0:S].astype(np.float32)/S
from scipy.ndimage import gaussian_filter
def blur(a,r):
    f=4
    small=np.asarray(Image.fromarray(a.astype(np.float32)).resize((S//f,S//f),Image.BILINEAR))
    small=gaussian_filter(small,r*SS/f)
    return np.asarray(Image.fromarray(small.astype(np.float32)).resize((S,S),Image.BILINEAR))
def polymask(pts):
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).polygon([(x*S,y*S) for x,y in pts],fill=255); return np.asarray(m,np.float32)/255
def ellmask(cx,cy,rx,ry=None):
    ry=ry or rx; return (((X-cx)/rx)**2+((Y-cy)/ry)**2<=1).astype(np.float32)
def over(img,col,a):
    a=np.clip(a,0,1)[...,None]; return img*(1-a)+np.asarray(col,np.float32)*a
def lin(p0,p1,c0,c1):
    # gradient along p0->p1
    d=np.array(p1)-np.array(p0); t=((X-p0[0])*d[0]+(Y-p0[1])*d[1])/(d@d); t=np.clip(t,0,1)[...,None]
    return np.asarray(c0,np.float32)*(1-t)+np.asarray(c1,np.float32)*t
variant=sys.argv[1]
# --- background ---
if variant=='A':
    top,bot=(0.05,0.55,0.75),(0.01,0.06,0.20)
else:
    top,bot=(0.35,0.10,0.55),(0.03,0.02,0.12)
img=lin((0.5,0.1),(0.5,0.95),top,bot)
# god rays
ang=np.arctan2(X-0.35,Y+0.25)
rays=(np.sin(ang*38)*0.5+0.5)**8*(np.sin(ang*13+1)*0.5+0.5)*np.clip(1-Y*1.3,0,1)
img+=rays[...,None]*np.array([0.25,0.55,0.6] if variant=='A' else [0.5,0.3,0.6])*0.35
# caustics
c=np.clip(np.sin(X*44+np.sin(Y*23)*2.2)*np.sin(Y*38+np.sin(X*19)*2.6),0,1)**3
c2=np.clip(np.sin(X*71-np.sin(Y*29)*1.7)*np.sin(Y*57+np.sin(X*33)*1.9),0,1)**4
img+=(c*0.10+c2*0.06)[...,None]*np.array([0.4,0.85,1.0])
# grid of glowing posts (playfield)
posts=np.zeros((S,S),np.float32)
for i in range(5):
    for j in range(5):
        cx,cy=0.18+i*0.16,0.30+j*0.13
        if abs(cx-0.5)<0.32 and 0.38<cy<0.72: continue
        posts=np.maximum(posts,ellmask(cx,cy,0.012))
pc=np.array([0.3,1.0,0.9]) if variant=='A' else np.array([1.0,0.4,0.85])
img+=blur(posts,14)[...,None]*pc*0.9
img=over(img,pc*0.7+0.3,posts*0.85)
# sea urchin silhouette bottom-left (generic, spiky)
cx,cy,r=0.24,0.80,0.085
rr=np.hypot(X-cx,Y-cy); th=np.arctan2(Y-cy,X-cx)
spikes=r*(0.62+0.38*np.abs(np.cos(th*11))**6)
urch=np.clip((spikes-rr)*S/3,0,1)
img=over(img,(0.10,0.03,0.18) if variant=='A' else (0.02,0.10,0.18),urch*0.95)
rim=np.clip(urch-blur(urch,3),0,1)*(np.cos(th+2.3)*0.5+0.5)
img+=rim[...,None]*np.array([1.0,0.4,0.6])*1.5
# bubbles
rng=np.random.default_rng(7)
for k in range(14):
    bx,by,br=rng.uniform(0.12,0.9),rng.uniform(0.12,0.75),rng.uniform(0.008,0.035)
    if abs(bx-0.5)<0.25 and 0.4<by<0.72: continue
    ring=np.clip(1-np.abs(np.hypot(X-bx,Y-by)-br)*S/(br*S*0.18+2),0,1)
    img+=ring[...,None]*np.array([0.6,0.9,1.0])*0.55
    img+=ellmask(bx-br*0.35,by-br*0.35,br*0.28)[...,None]*0.6
# --- the gold ingot: 3D frustum, oblique projection ---
def proj(x,d,h):
    # x: right, d: depth (+ = away), h: up
    a=math.radians(-14)
    xr=x*math.cos(a)-d*math.sin(a); dr=x*math.sin(a)+d*math.cos(a)
    return (0.5+xr*1.0, 0.60-h*1.0-dr*0.42)
W0,D0,W1,D1,H=0.50,0.26,0.36,0.14,0.15
b=[proj(-W0/2,-D0/2,0),proj(W0/2,-D0/2,0),proj(W0/2,D0/2,0),proj(-W0/2,D0/2,0)]
t=[proj(-W1/2,-D1/2,H),proj(W1/2,-D1/2,H),proj(W1/2,D1/2,H),proj(-W1/2,D1/2,H)]
sil=[b[0],b[1],b[2],t[2],t[3],b[3]] if False else [b[0],b[1],b[2],t[2],t[3],t[0]]
allm=polymask([b[0],b[1],b[2],t[2],t[3],b[3]])
gcol=np.array([1.0,0.70,0.18])
img+=blur(allm,80)[...,None]*gcol*1.0
img+=blur(allm,28)[...,None]*gcol*0.6
# contact shadow
shm=polymask([proj(-W0/2-0.02,-D0/2-0.01,0),proj(W0/2+0.02,-D0/2-0.01,0),proj(W0/2+0.04,D0/2+0.02,0),proj(-W0/2,D0/2+0.02,0)])
img*=1-0.6*blur(shm,10)[...,None]
def face(pts,c0,c1,p0,p1):
    global img
    m=blur(polymask(pts),0.5)
    col=lin(p0,p1,c0,c1)
    img=img*(1-m[...,None])+col*m[...,None]
def mid(p,q): return ((p[0]+q[0])/2,(p[1]+q[1])/2)
# visible faces after rotation: left side, front, right side (back hidden), top
face([b[3],b[0],t[0],t[3]],(0.62,0.36,0.05),(0.80,0.52,0.12),mid(b[3],b[0]),mid(t[3],t[0]))   # left
face([b[1],b[2],t[2],t[1]],(0.50,0.27,0.03),(0.72,0.44,0.08),mid(b[1],b[2]),mid(t[1],t[2]))   # right
face([b[0],b[1],t[1],t[0]],(0.70,0.40,0.04),(1.00,0.80,0.30),mid(b[0],b[1]),mid(t[0],t[1]))   # front
face([t[0],t[1],t[2],t[3]],(1.00,0.97,0.70),(1.00,0.82,0.36),mid(t[0],t[1]),mid(t[3],t[2]))   # top
def line(p,q,w,col,a):
    global img
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).line([(p[0]*S,p[1]*S),(q[0]*S,q[1]*S)],fill=255,width=int(w*SS))
    mm=np.asarray(m,np.float32)/255; img=over(img,col,blur(mm,0.8)*a)
line(t[0],t[1],7,(1,1,0.92),0.95); line(t[1],t[2],4,(1,0.95,0.75),0.7); line(t[3],t[0],5,(1,0.97,0.8),0.8)
line(b[0],t[0],4,(1,0.9,0.6),0.55); line(b[1],t[1],4,(1,0.9,0.6),0.45)
# engraved stamp on top face
cx,cy=mid(mid(t[0],t[2]),mid(t[1],t[3]))
ins=[((p[0]-cx)*0.62+cx,(p[1]-cy)*0.55+cy) for p in t]
m=polymask(ins)-blur(polymask(ins),2.5)
img=over(img,(0.72,0.48,0.10),np.clip(-(m)*1.0,0,1)*0.8)
img=over(img,(1,1,0.9),np.clip(m,0,1)*0.6)
# specular sweep across front face
fm=polymask([b[0],b[1],t[1],t[0]])
sweep=np.exp(-((X-Y*0.55-0.20)/0.035)**2)
img+=(fm*sweep)[...,None]*np.array([1,0.95,0.8])*0.55
tm=polymask(t); img+=(tm*np.exp(-((X+Y*0.9-0.95)/0.03)**2))[...,None]*0.45
# sparkles
for (sx,sy,sz,k) in [(t[1][0]-0.01,t[1][1]+0.005,0.07,1.0),(b[0][0]+0.06,b[0][1]-0.03,0.035,0.7)]:
    star=np.exp(-np.abs(X-sx)*S/(1.6*SS))*np.exp(-np.abs(Y-sy)*S/(sz*S))+np.exp(-np.abs(Y-sy)*S/(1.6*SS))*np.exp(-np.abs(X-sx)*S/(sz*S))
    img+=np.clip(star,0,1)[...,None]*np.array([1,0.95,0.8])*k
    img+=blur(ellmask(sx,sy,0.007),2)[...,None]*k
# bloom of brights + vignette + tonemap
br=np.clip(img-0.85,0,None); img+=np.stack([blur(br[...,k],20) for k in range(3)],-1)*0.8
img*=(1-0.45*((X-0.5)**2+(Y-0.5)**2)*2)[...,None]
img=1-np.exp(-img*1.35)
img=np.clip(img,0,1)**(1/1.1)
# --- squircle mask + inner stroke + shadow (macOS grid: 824px body) ---
u=(X-0.5)/(824/1024/2); v=(Y-0.5)/(824/1024/2)
sq=np.abs(u)**4.2+np.abs(v)**4.2
body=np.clip((1-sq)*S/60,0,1)
inner=np.clip(1-np.abs(sq-0.985)*90,0,1)*np.clip(-v*0.5+0.6,0,1)
img=img+inner[...,None]*0.25
rgba=np.dstack([np.clip(img,0,1),body])
dshadow=blur(np.clip((1-((np.abs(u)**4.2+np.abs((Y-0.515)/(824/1024/2))**4.2)))*10,0,1),18)*0.45
out=np.zeros((S,S,4),np.float32); out[...,3]=dshadow
a=rgba[...,3:4]; out[...,:3]=rgba[...,:3]*a; out[...,3:4]=a+out[...,3:4]*(1-a)
out[...,:3]=np.where(out[...,3:4]>0,out[...,:3]/np.maximum(out[...,3:4],1e-6),0)
im=Image.fromarray((out*255).astype(np.uint8),'RGBA').resize((1024,1024),Image.LANCZOS)
im.save(f'/tmp/icon/icon_{variant}.png')
