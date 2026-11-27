import wave, numpy as np, subprocess, sys
sys.path.insert(0,'/tmp/ek')
SR=48000; TOTAL=31.0; N=int(TOTAL*SR); t=np.arange(N)/SR
LINES=[(0.35,'1_nail'),(3.25,'2_hayri'),(6.45,'3_bayram'),(9.25,'4_hayri'),(14.95,'5_selim'),(19.4,'6_nail'),(24.55,'7_riza')]
voice=np.zeros(N,np.float32)
for s,f in LINES:
    with wave.open(f'/tmp/ek/ses/{f}.wav') as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
    i=int(s*SR); voice[i:i+len(a)]+=a[:N-i]
rng=np.random.default_rng(3)
def add(buf,a,at,g):
    i=int(at*SR); n=min(len(a),N-i); buf[i:i+n]+=g*a[:n]
sfx=np.zeros(N,np.float32)
def thud():
    tt=np.arange(int(.5*SR))/SR; return (np.sin(2*np.pi*(55+70*np.exp(-tt*25))*tt)*np.exp(-tt*9)+0.3*rng.standard_normal(len(tt))*np.exp(-tt*60)).astype(np.float32)
def clink(f0=2400):
    tt=np.arange(int(.9*SR))/SR; return sum(np.sin(2*np.pi*f0*m*tt)*np.exp(-tt*(7+3*k))/(k+1) for k,m in enumerate([1,2.76,5.4])).astype(np.float32)
def splash():
    n=int(.6*SR); x=rng.standard_normal(n); env=np.exp(-np.arange(n)/SR*8)*np.minimum(1,np.arange(n)/(.02*SR))
    from scipy.signal import butter,sosfilt
    return sosfilt(butter(2,[800,5000],'band',fs=SR,output='sos'),x*env).astype(np.float32)
def whoosh(d=.35):
    n=int(d*SR); x=rng.standard_normal(n); env=np.sin(np.linspace(0,np.pi,n))**2
    from scipy.signal import butter,sosfilt
    return sosfilt(butter(2,[300,1800],'band',fs=SR,output='sos'),x*env).astype(np.float32)
def sting():
    out=np.zeros(int(1.6*SR),np.float32)
    for k,(f,at) in enumerate([(146.8,0),(138.6,.45)]):
        tt=np.arange(int(1.1*SR))/SR; tone=sum(np.sin(2*np.pi*f*h*tt)/h for h in (1,2,3,4))*np.exp(-tt*(2.5 if k else 5))
        i=int(at*SR); out[i:i+len(tt)]+=tone[:len(out)-i]
    return out*.5
add(sfx,thud(),.33,.9)                       # telefon masaya
add(sfx,clink(2600),2.0,.10)                 # bardak
for at in (3.05,6.3,14.75): add(sfx,whoosh(),at-.12,.12)
add(sfx,thud()*.6,6.42,.35)                  # Bayram yumruk
add(sfx,clink(2300),11.5,.08)                # Hayri çay yudumu
add(sfx,clink(2500),24.15,.35); add(sfx,clink(3100),24.22,.25)   # tepsi
add(sfx,splash(),26.75,.35)                  # çay dökülüyor
add(sfx,sting(),28.95,.8)                    # dum-dum
# ortam: kahve uğultusu
from scipy.signal import butter,sosfilt
amb=sosfilt(butter(2,[150,900],'band',fs=SR,output='sos'),rng.standard_normal(N)).astype(np.float32)*.02
# müzik: hafif pizzicato döngüsü (Hicaz esintili), konuşmada kısılır
notes=[293.7,311.1,370.0,392.0,440.0,466.2,523.3,587.3]
pat=[0,2,3,2,4,3,2,1, 0,2,3,4,5,4,3,2]
music=np.zeros(N,np.float32); beat=0.25
def pluck(f,d=.5):
    n=int(d*SR); p=int(SR/f); buf=rng.uniform(-1,1,p); out=np.zeros(n)
    for i in range(n):
        out[i]=buf[i%p]; buf[i%p]=0.5*(buf[i%p]+buf[(i+1)%p])*0.996
    return out.astype(np.float32)
cache={}
k=0; tt0=0.0
while tt0<28.8:
    f=notes[pat[k%len(pat)]]
    if f not in cache: cache[f]=pluck(f)
    add(music,cache[f],tt0,.5 if k%4==0 else .35)
    if k%8==0:
        if 73.4 not in cache: cache[73.4]=pluck(73.4,1.0)
        add(music,cache[73.4],tt0,.6)
    tt0+=beat; k+=1
music*=np.minimum(1,t/0.4)*np.clip((28.9-t)/0.3,0,1)
e=np.convolve(np.abs(voice),np.ones(int(.1*SR))/int(.1*SR),mode='same')
duck=np.convolve(np.where(e>.01,.35,1.0),np.ones(int(.25*SR))/int(.25*SR),mode='same').astype(np.float32)
mix=voice*1.0+sfx+amb+music*.22*duck
mix=mix/np.max(np.abs(mix))*.9
with wave.open('/tmp/ek/mix_raw.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
import json,re
r=subprocess.run(['ffmpeg','-i','/tmp/ek/mix_raw.wav','-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
m=json.loads(r[r.rfind('{'):r.rfind('}')+1])
af=f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
subprocess.run(['ffmpeg','-y','-loglevel','error','-i','/tmp/ek/mix_raw.wav','-af',af,'-ar','48000','-ac','2','/tmp/ek/mix.wav'],check=True)
print('ok')
