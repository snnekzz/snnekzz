import math, subprocess, wave, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
U='/root/.claude/uploads/06bd034c-1587-5fe1-b293-c50935c211ce/'
F='/tmp/is/calis/'
W,H,FPS=1080,1920,30
IMG={1:Image.open(U+'2f4bad28-image.png').convert('RGB'),2:Image.open(U+'cd0ffca7-image.jpg').convert('RGB'),
     3:Image.open('/tmp/ek/sahne3.jpg').convert('RGB'),4:Image.open(U+'49585ed3-image.jpg').convert('RGB'),
     5:Image.open(U+'08e521f3-image.jpg').convert('RGB')}
COL={'NAİL':(255,190,40),'HAYRİ':(230,120,50),'BAYRAM':(229,36,59),'SELİM':(150,90,230),'RIZA':(40,150,240)}
# (start, file, speaker, text)  *kelime* = sarı vurgu
LINES=[(0.35,'1_nail','NAİL','Beyler! *Dolar* yine fırladı!'),
       (3.25,'2_hayri','HAYRİ','Ne? *Dolmuş* mu kalktı?'),
       (6.45,'3_bayram','BAYRAM','*DOLAR* Hayri Amca, *DOLAR!*'),
       (9.25,'4_hayri','HAYRİ','Bağırma. Bizim zamanımızda dolar yoktu… *dolma* vardı.'),
       (14.95,'5_selim','SELİM','Nail Abi, sen kuyumcusun. Ne yapalım, *altın* mı alalım?'),
       (19.4,'6_nail','NAİL','Bekleyin. Ben önce kendi altınlarımı *satayım*, sonra söylerim.'),
       (24.55,'7_riza','RIZA','Çaylar da dolar oldu. Tanesi *beş dolar.*')]
DUR={}
for s,f,_,_ in LINES:
    with wave.open(f'/tmp/ek/ses/{f}.wav') as w: DUR[f]=w.getnframes()/w.getframerate()
TOTAL=31.0
SHOTS=[(0,3.05,1),(3.05,6.3,2),(6.3,14.75,3),(14.75,24.1,4),(24.1,TOTAL,5)]
def ease(x): x=max(0,min(1,x)); return x*x*(3-2*x)
def lerp(a,b,x): return a+(b-a)*x
def cam(t):
    """(shot, cx, cy, zoom, shake)"""
    for a,b,s in SHOTS:
        if a<=t<b: break
    u=t-a; sh=0
    if s==1:
        z=lerp(1.0,1.12,ease(u/3)); cx,cy=lerp(.5,.3,ease(u/2)),.6
        if 0.35<t<0.75: sh=14*(1-(t-.35)/.4)
    elif s==2: z=lerp(1.05,1.2,ease(u/3.2)); cx,cy=.56,.64
    elif s==3:
        k=ease((t-8.9)/0.6)
        z=lerp(1.25,1.3,ease(u/2.6)) if t<8.9 else lerp(1.3,1.45,ease((t-8.9)/5))
        cx=lerp(.45,.76,k); cy=lerp(.62,.64,k)
        if 6.5<t<8.8: sh=6
    elif s==4:
        k=ease((t-19.2)/0.7)
        z=lerp(1.2,1.3,ease(u/9)); cx=lerp(.3,.45,k); cy=.66
    else:
        z0=lerp(1.25,1.0,ease(u/0.5))
        if t<26.6: z,cx,cy=z0,.5,.55
        else:
            k=ease((t-26.6)/0.5); z=lerp(1.0,1.6,k); cx=lerp(.5,.78,k); cy=lerp(.55,.47,k)
        if t>=28.9: z=1.6+0.05*ease((t-28.9)/2)
    return s,cx,cy,z,sh
def view(t):
    s,cx,cy,z,sh=cam(t); im=IMG[s]; iw,ih=im.size
    cw=iw/z; ch=cw*16/9
    if ch>ih: ch=ih; cw=ch*9/16
    x0=min(max(cx*iw-cw/2,0),iw-cw); y0=min(max(cy*ih-ch/2,0),ih-ch)
    if sh:
        x0+=sh*math.sin(t*90)*cw/W; y0+=sh*math.cos(t*77)*ch/H
        x0=min(max(x0,0),iw-cw); y0=min(max(y0,0),ih-ch)
    return im.resize((W,H),Image.BICUBIC,box=(x0,y0,x0+cw,y0+ch))
FN=ImageFont.truetype(F+'mont900.ttf',62); FS=ImageFont.truetype(F+'mont900.ttf',38)
def wrap(text,maxw):
    toks=text.split(' '); lines=[[]]; 
    for tk in toks:
        trial=' '.join(x for x in lines[-1]+[tk]).replace('*','')
        if lines[-1] and FN.getlength(trial)>maxw: lines.append([tk])
        else: lines[-1].append(tk)
    return lines
def subtitle(img,t):
    cur=None
    for s,f,spk,txt in LINES:
        if s-0.05<=t<=s+DUR[f]+0.25: cur=(s,f,spk,txt)
    if not cur: return
    s,f,spk,txt=cur; a=min(1,(t-s+0.05)/0.12)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    y=250; c=COL[spk]
    tw=FS.getlength(spk); d.rounded_rectangle((W/2-tw/2-26,y,W/2+tw/2+26,y+62),radius=31,fill=c+(255,),outline=(0,0,0,255),width=4)
    d.text((W/2,y+31),spk,font=FS,fill=(255,255,255),anchor='mm',stroke_width=3,stroke_fill=(0,0,0))
    y+=90
    for ln in wrap(txt,940):
        words=[(w.replace('*',''),'*' in w) for w in ln]
        total=FN.getlength(' '.join(w for w,_ in words))+14*sum(h for _,h in words); x=W/2-total/2
        for w,hl in words:
            wl=FN.getlength(w)
            if hl: d.rounded_rectangle((x-10,y-6,x+wl+10,y+76),radius=12,fill=(255,214,0,255),outline=(0,0,0,255),width=4)
            d.text((x,y),w,font=FN,fill=(20,20,20) if hl else (255,255,255),stroke_width=0 if hl else 7,stroke_fill=(0,0,0))
            x+=wl+FN.getlength(' ')+(14 if hl else 0)
        y+=86
    if a<1: lay.putalpha(lay.getchannel('A').point(lambda v:int(v*a)))
    img.alpha_composite(lay)
def card(img,t):
    if t>3.0: return
    a=min(1,t/.2)*(1-max(0,(t-2.6)/.4))
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    s='ESNAF KAHVESİ  ·  #1 DOLAR'; tw=FS.getlength(s)
    d.rounded_rectangle((W/2-tw/2-30,120,W/2+tw/2+30,190),radius=14,fill=(229,36,59,255),outline=(255,255,255,255),width=4)
    d.text((W/2,155),s,font=FS,fill=(255,255,255),anchor='mm')
    lay.putalpha(lay.getchannel('A').point(lambda v:int(v*a))); img.alpha_composite(lay)
def endcard(img,t):
    if t<29.2: return
    a=min(1,(t-29.2)/.3)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    s='SENCE ALTIN MI, DOLAR MI?'; tw=FN.getlength(s)
    d.rounded_rectangle((W/2-tw/2-30,1560,W/2+tw/2+30,1660),radius=18,fill=(255,214,0,255),outline=(0,0,0,255),width=5)
    d.text((W/2,1610),s,font=FN,fill=(20,20,20),anchor='mm')
    s2='Yorumlara yaz 👇'.replace(' 👇',''); d.text((W/2,1720),s2,font=FS,fill=(255,255,255),anchor='mm',stroke_width=5,stroke_fill=(0,0,0))
    lay.putalpha(lay.getchannel('A').point(lambda v:int(v*a))); img.alpha_composite(lay)
def frame(t):
    img=view(t).convert('RGBA')
    v=Image.new('RGBA',(W,H),(0,0,0,0)); dv=ImageDraw.Draw(v)
    for y in range(0,560): dv.line([(0,y),(W,y)],fill=(0,0,0,int(120*(1-y/560)**1.5)))
    img.alpha_composite(v); card(img,t); subtitle(img,t); endcard(img,t)
    return img.convert('RGB')
if __name__=='__main__':
    import sys
    if sys.argv[1]=='still':
        for tt in sys.argv[2:]: frame(float(tt)).save(f'/tmp/ek/st_{tt}.png')
    else:
        a,b,out=int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
        p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
        for i in range(a,b): p.stdin.write(frame(i/FPS).tobytes())
        p.stdin.close(); p.wait()
