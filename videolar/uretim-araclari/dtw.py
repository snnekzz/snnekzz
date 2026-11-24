import json, numpy as np, librosa, re, subprocess
P = json.load(open("timing_piper.json"))["segs"]
sr=16000; hop=320
a,_=librosa.load("voice.wav",sr=sr)       # piper (bilinen zamanlar)
b,_=librosa.load("eleven.mp3",sr=sr)
def feat(x):
    m=librosa.feature.mfcc(y=x,sr=sr,n_mfcc=20,hop_length=hop)[1:]
    m=(m-m.mean(1,keepdims=True))/(m.std(1,keepdims=True)+1e-6); return m
A,B=feat(a),feat(b)
D,wp=librosa.sequence.dtw(X=A,Y=B,metric="cosine")
wp=wp[::-1]; ta=wp[:,0]*hop/sr; tb=wp[:,1]*hop/sr
def mp(t): i=np.searchsorted(ta,t); return float(tb[min(i,len(tb)-1)])
out=subprocess.run(["ffmpeg","-hide_banner","-i","eleven.mp3","-af","silencedetect=noise=-40dB:d=0.15","-f","null","-"],capture_output=True,text=True).stderr
ss=[float(x) for x in re.findall(r"silence_start: ([\d.]+)",out)]; se=[float(x) for x in re.findall(r"silence_end: ([\d.]+)",out)]
pauses=list(zip(ss,se))
res=[]
for s in P:
    res.append((mp(s["start"]),mp(s["end"])))
for i,((s,e),p) in enumerate(zip(res,P)):
    # en yakın duraklamaya oturt
    print(f"{s:6.2f}-{e:6.2f}  {p['cap'][:45]}")
json.dump({"raw":res,"pauses":pauses},open("dtw_out.json","w"))
