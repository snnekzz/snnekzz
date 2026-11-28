#!/bin/bash
# Ses miksi: anlatım (EQ + kompresör) + müzik (anlatım altında kısılır) + efektler -> -14 LUFS
set -e
cd "$(dirname "$0")/audio"
DUR=${1:-39.25}
OFF=250   # anlatım gecikmesi (ms) — src/main.js AUDIO_OFFSET ile aynı
# müzik 34. saniyede bitiyor: 0-30 + (24-34) çapraz geçişle uzatılır
ffmpeg -y -loglevel error -i music.wav -filter_complex "[0]atrim=0:30,asetpts=N/SR/TB[a];[0]atrim=24:34,asetpts=N/SR/TB[b];[a][b]acrossfade=d=2:c1=tri:c2=tri,apad=pad_dur=3,afade=t=out:st=$(echo "$DUR-2.5" | bc):d=2.5" -t $DUR music_ext.wav
ffmpeg -y -loglevel error \
  -i emrullah_a.mp3 -i music_ext.wav \
  -stream_loop -1 -i sfx/sea.mp3 -stream_loop -1 -i sfx/night.mp3 -stream_loop -1 -i sfx/drums.mp3 \
  -i sfx/haul.mp3 -i sfx/chain.mp3 -i sfx/splash.mp3 \
  -i sfx/whoosh.mp3 -i sfx/whoosh.mp3 -i sfx/whoosh.mp3 -i sfx/whoosh.mp3 -i sfx/whoosh.mp3 -i sfx/sea.mp3 \
  -filter_complex "
  [0]adelay=${OFF}|${OFF},highpass=f=70,equalizer=f=250:t=q:w=1.2:g=-4,equalizer=f=450:t=q:w=1.5:g=-2,equalizer=f=3500:t=q:w=1.2:g=2.5,highshelf=f=8000:g=3,acompressor=threshold=-20dB:ratio=3:attack=5:release=100:makeup=2,apad,atrim=0:$DUR,asplit=2[vo][key];
  [1]volume=0.55[mus];
  [mus][key]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=350:makeup=1[musd];
  [2]atrim=0:11.9,afade=t=out:st=11.3:d=0.6,volume=0.35[sea];
  [3]atrim=0:14.1,afade=t=in:d=0.4,afade=t=out:st=13.5:d=0.6,volume=0.4,adelay=11850|11850[night];
  [4]atrim=0:6.2,afade=t=in:d=0.8,afade=t=out:st=5.4:d=0.8,volume=0.75,adelay=19900|19900[drums];
  [5]atrim=0:8,afade=t=in:d=0.4,afade=t=out:st=7.2:d=0.8,volume=0.6,adelay=15330|15330[haul];
  [6]volume=0.7,adelay=2500|2500[chain];
  [7]volume=0.95,adelay=24900|24900[splash];
  [8]volume=0.55[w0];
  [9]volume=0.5,adelay=9650|9650[w1];
  [10]volume=0.5,adelay=22050|22050[w2];
  [11]volume=0.4,adelay=25650|25650[w3];
  [12]volume=0.55,adelay=31200|31200[w4];
  [13]afade=t=in:d=0.6,volume=0.25,adelay=25900|25900[dawn];
  [vo][musd][sea][night][drums][haul][chain][splash][w0][w1][w2][w3][w4][dawn]amix=inputs=14:duration=first:normalize=0,atrim=0:$DUR[mix]" \
  -map "[mix]" -ar 48000 -ac 2 premix.wav
# iki geçişli loudnorm
J=$(ffmpeg -hide_banner -i premix.wav -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
mi=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
read II TP LRA TH OFFS <<< "$mi"
ffmpeg -y -loglevel error -i premix.wav -af "loudnorm=I=-14:TP=-1:LRA=11:measured_I=$II:measured_TP=$TP:measured_LRA=$LRA:measured_thresh=$TH:offset=$OFFS:linear=true" -ar 48000 mix.wav
ffmpeg -y -loglevel error -i mix.wav -c:a aac -b:a 192k mix.m4a
ffmpeg -hide_banner -i mix.wav -af ebur128=peak=true -f null - 2>&1 | grep -A8 Summary | grep -E "I:|Peak:"
