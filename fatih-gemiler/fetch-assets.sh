#!/bin/bash
# Üçüncü taraf varlıkları indirir (repoya eklenmez).
# Xbot.glb: Mixamo karakteri/animasyonları (Adobe Mixamo lisansı; projelerde ticari kullanım serbest, ham dosya dağıtılmaz)
set -e
cd "$(dirname "$0")/assets"
B=https://raw.githubusercontent.com/mrdoob/three.js/r170/examples
[ -f Xbot.glb ] || curl -sfo Xbot.glb $B/models/gltf/Xbot.glb
[ -f grasslight-big.jpg ] || curl -sfo grasslight-big.jpg $B/textures/terrain/grasslight-big.jpg
[ -f waternormals.jpg ] || curl -sfo waternormals.jpg $B/textures/waternormals.jpg
echo "varlıklar hazır"
