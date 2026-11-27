import json, subprocess, sys
src, dst = sys.argv[1], sys.argv[2]
f = "loudnorm=I=-14:TP=" + (sys.argv[3] if len(sys.argv) > 3 else "-1.5") + ":LRA=11"
o = subprocess.run(["ffmpeg","-hide_banner","-i",src,"-af",f+":print_format=json","-f","null","-"],capture_output=True,text=True).stderr
m = json.loads(o[o.rindex("{"):o.rindex("}")+1])
f2 = f+f":measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",src,"-af",f2,"-ar","48000",dst],check=True)
o = subprocess.run(["ffmpeg","-hide_banner","-i",dst,"-af","loudnorm=print_format=json","-f","null","-"],capture_output=True,text=True).stderr
m = json.loads(o[o.rindex("{"):o.rindex("}")+1]); print(dst, m["input_i"], "LUFS", m["input_tp"], "dBTP")
