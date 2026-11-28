// İskeletli (rigged) insanlar: Mixamo Xbot modeli + bölge boyama (kaftan/ten/şalvar/çizme) + kemiklere takılan aksesuarlar
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';
import { THREE, mergeGeometries, scene, V, rng, prep, M, cyl, sph, tor, cone, box } from './core.js';

const gltf = await new GLTFLoader().loadAsync(new URL('../assets/Xbot.glb', import.meta.url).href);
const CLIPS = Object.fromEntries(gltf.animations.map(a => [a.name, a]));
// eklemeli (additive) pozlar
for (const n of ['sneak_pose', 'sad_pose', 'agree', 'headShake']) if (CLIPS[n]) THREE.AnimationUtils.makeClipAdditive(CLIPS[n]);

// --- bölge özniteliği: baskın kemiğe göre 0 kaftan, 1 ten, 2 şalvar, 3 çizme, 4 iç gömlek
const template = gltf.scene;
template.traverse(o => {
  if (!o.isSkinnedMesh) return;
  const g = o.geometry, si = g.attributes.skinIndex, sw = g.attributes.skinWeight, bones = o.skeleton.bones;
  const reg = new Float32Array(si.count);
  for (let i = 0; i < si.count; i++) {
    let best = 0, bw = -1;
    for (let k = 0; k < 4; k++) { const w = sw.getComponent(i, k); if (w > bw) { bw = w; best = si.getComponent(i, k); } }
    const n = bones[best].name;
    reg[i] = /Head|Neck|Eye/.test(n) ? 1 : /Hand/.test(n) ? 1 : /Foot|Toe/.test(n) ? 3 : /Leg/.test(n) && !/UpLeg/.test(n) ? 2 : 0;
  }
  g.setAttribute('region', new THREE.BufferAttribute(reg, 1));
});

function regionMaterial(cols) {
  const m = new THREE.MeshStandardMaterial({ roughness: 0.85, metalness: 0, envMapIntensity: 0.7 });
  m.userData.cols = cols.map(c => new THREE.Color(c));
  m.onBeforeCompile = sh => {
    sh.uniforms.regCols = { value: m.userData.cols };
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float region; varying float vRegion;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvRegion = region;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform vec3 regCols[5]; varying float vRegion;')
      .replace('vec4 diffuseColor = vec4( diffuse, opacity );', 'int ri = int(vRegion + 0.5); vec3 rc = ri == 0 ? regCols[0] : ri == 1 ? regCols[1] : ri == 2 ? regCols[2] : ri == 3 ? regCols[3] : regCols[4];\nvec4 diffuseColor = vec4( rc, opacity );');
  };
  m.customProgramCacheKey = () => 'region';
  return m;
}

// kemik bulucu
const findBone = (root, name) => { let b = null; root.traverse(o => { if (o.isBone && o.name.replace(':', '') === 'mixamorig' + name.replace(':', '')) b = o; }); return b; };
const ACC_MAT = new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: false, roughness: 0.85, envMapIntensity: 0.7 });

// Xbot kemikleri cm ölçeğinde: aksesuarları metre cinsinden kurup kemiğin dünya ölçeğine böleriz
let BONE_SCALE = 1;
{
  template.updateMatrixWorld(true);
  const hb = findBone(template, ':Head'), s = new THREE.Vector3();
  hb.getWorldScale(s); BONE_SCALE = s.x;
}
function attach(bone, geo, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(geo, ACC_MAT); m.castShadow = true; m.receiveShadow = true;
  m.scale.setScalar(1 / BONE_SCALE); m.position.set(x / BONE_SCALE, y / BONE_SCALE, z / BONE_SCALE);
  bone.add(m); return m;
}
const turbanGeo = (cap) => mergeGeometries([tor(0.105, 0.06, 0xf3efe6, M(0, 0.13, 0.0, Math.PI / 2, 0, 0), 8, 16), sph(0.1, cap, M(0, 0.17, 0, 0, 0, 0, 1, 0.75, 1), 12, 8)]);
const borkGeo = () => mergeGeometries([cyl(0.095, 0.11, 0.26, 12, 0xf3efe6, M(0, 0.23, -0.02, -0.15, 0, 0)), box(0.05, 0.32, 0.16, 0xf3efe6, 0, 0.2, -0.14, -0.6, 0, 0), box(0.05, 0.1, 0.06, 0xd9a63a, 0, 0.16, 0.1)]);
const kavukGeo = () => mergeGeometries([sph(0.17, 0xf7f3ea, M(0, 0.2, 0, 0, 0, 0, 1, 0.82, 1), 16, 10), cyl(0.07, 0.085, 0.12, 10, 0xa3281d, M(0, 0.35, 0))]);
const helmetGeo = () => mergeGeometries([prep(new THREE.SphereGeometry(0.125, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2), 0x9aa3ab, M(0, 0.1, 0)), cone(0.02, 0.16, 6, 0x9aa3ab, M(0, 0.28, 0)), box(0.03, 0.08, 0.22, 0xa8322a, 0, 0.3, -0.03)]);
const beardGeo = (c) => sph(0.062, c, M(0, -0.01, 0.07, 0.35, 0, 0, 1, 1.15, 0.6), 10, 6);
const skirtGeo = (c, trim) => mergeGeometries([prep(new THREE.CylinderGeometry(0.155, 0.215, 0.36, 16, 1, true), c, M(0, -0.15, 0)), cyl(0.157, 0.157, 0.06, 16, trim, M(0, 0.02, 0))]);

const ROBES = [0x9c3b2e, 0x2f5577, 0xb08d45, 0x4a6b3a, 0x7d3b52, 0xcdbb98, 0x6b4a2e, 0x8a2f2a, 0x3b4f6b];
const SKINS = [0xc58f6a, 0xb57d58, 0xd6a37f, 0xa86e4b];
export const people = [];
export function makeHuman(o = {}) {
  const r = rng(o.seed || 1);
  const root = SkeletonUtils.clone(template);
  const robe = o.robe ?? ROBES[Math.floor(r() * ROBES.length)], skin = SKINS[Math.floor(r() * SKINS.length)];
  const pants = o.pants ?? [0x3b3428, 0x4a3a2a, 0x2f3540][Math.floor(r() * 3)], boots = o.boots ?? [0x5a3a22, 0x3a2a1c, 0x8a3a22][Math.floor(r() * 3)];
  const under = o.under ?? [0xe8dcc0, 0xd9c7a0, 0xcfbf9a][Math.floor(r() * 3)];
  const mat = regionMaterial([robe, skin, pants, boots, under]);
  root.traverse(c => { if (c.isSkinnedMesh) { c.material = mat; c.castShadow = true; c.receiveShadow = true; c.frustumCulled = false; } });
  const B = n => findBone(root, ':' + n);
  const bones = { hips: B('Hips'), spine: B('Spine'), spine1: B('Spine1'), spine2: B('Spine2'), neck: B('Neck'), head: B('Head'),
    lArm: B('LeftArm'), rArm: B('RightArm'), lFore: B('LeftForeArm'), rFore: B('RightForeArm'), lUp: B('LeftUpLeg'), rUp: B('RightUpLeg') };
  const hat = o.hat || (r() < 0.72 ? 'turban' : 'bork');
  const capC = [0xa3281d, 0x2f6b3a, 0xc49a3a, 0x7a2e2e][Math.floor(r() * 4)];
  attach(bones.head, hat === 'turban' ? turbanGeo(capC) : hat === 'bork' ? borkGeo() : hat === 'kavuk' ? kavukGeo() : helmetGeo(), 0, 0.02, -0.01);
  attach(bones.head, mergeGeometries([sph(0.016, 0x1a1410, M(0.038, 0.085, 0.092), 6, 4), sph(0.016, 0x1a1410, M(-0.038, 0.085, 0.092), 6, 4), box(0.05, 0.012, 0.012, 0x2a1e16, 0.04, 0.115, 0.095, 0, 0, -0.15), box(0.05, 0.012, 0.012, 0x2a1e16, -0.04, 0.115, 0.095, 0, 0, 0.15), cone(0.018, 0.05, 6, skin, M(0, 0.055, 0.112, Math.PI / 2, 0, 0))]), 0, 0, 0);
  if (o.beard !== false && r() < 0.8) attach(bones.head, beardGeo(o.beardC ?? [0x2b1e16, 0x4a3324, 0x6b6b6b, 0x1e1a18][Math.floor(r() * 4)]), 0, 0.03, 0.02);
  attach(bones.hips, skirtGeo(robe, o.sash ?? [0xd9a63a, 0xc0392b, 0xefe3c8][Math.floor(r() * 3)]), 0, 0.05, 0);
  const mixer = new THREE.AnimationMixer(root);
  const acts = {};
  for (const n of ['idle', 'walk', 'run']) { acts[n] = mixer.clipAction(CLIPS[n]); acts[n].play(); acts[n].setEffectiveWeight(0); }
  root.visible = false; scene.add(root);
  const p = { root, mixer, acts, bones, mat, seed: r() * 10 };
  people.push(p);
  return p;
}

// --- pozlar: temel klip + kemik ofsetleri (radyan)
const _q = new THREE.Quaternion(), _e = new THREE.Euler();
function addRot(bone, x, y, z) { if (!bone) return; _q.setFromEuler(_e.set(x, y, z)); bone.quaternion.multiply(_q); }
export const POSE = {
  idle: (t, k) => ({ clip: 'idle', speed: 1 }),
  walk: (t, k) => ({ clip: 'walk', speed: 1 }),
  run: (t, k) => ({ clip: 'run', speed: 1 }),
  // halat çekme: yavaş adım + öne eğilme + kollar önde
  pull: (t, k) => ({ clip: 'walk', speed: 0.6, spine: [0.32, 0, 0], spine1: [0.14, 0, 0], arms: [0.6, 0, 0.85], fore: [0, 0, 0.5] }),
  carry: (t, k) => ({ clip: 'walk', speed: 0.8, arms: [0, 0, 2.3], fore: [0, 0, 1.4] }),
  cheer: (t, k) => ({ clip: 'idle', speed: 1, arms: [0, 0, 2.85 + Math.sin(t * 7 + k) * 0.2], fore: [0, 0, 0.2] }),
  point: (t, k) => ({ clip: 'idle', speed: 1, rArm: [0, 0, -1.5] }),
  bend: (t, k) => ({ clip: 'idle', speed: 1, spine: [0.6, 0, 0], spine1: [0.35, 0, 0], arms: [0.5, 0, 0.8 + Math.sin(t * 6 + k) * 0.35], fore: [0, 0, 0.4] }),
  drum: (t, k) => ({ clip: 'idle', speed: 1, arms: [0.55, 0, 0.8], lFore: [0, 0, 1.2 + Math.max(0, Math.sin(t * 9 + k)) * 0.7], rFore: [0, 0, -(1.2 + Math.max(0, Math.sin(t * 9 + k + Math.PI)) * 0.7)] }),
  ride: (t, k) => ({ clip: 'idle', speed: 0.4, legs: [-1.45, 0, 0.32], arms: [0.6, 0, 0.6], fore: [0, 0, 0.9] }),
};
export function hideHumans() { for (const p of people) p.root.visible = false; }
export function putHuman(p, x, y, z, yaw, pose, t, k = 0) {
  const P = pose(t, k);
  p.root.visible = true; p.root.position.set(x, y, z); p.root.rotation.set(0, yaw + Math.PI / 2, 0); // model +Z'ye bakar; sahnede ileri = +X
  for (const n in p.acts) p.acts[n].setEffectiveWeight(n === P.clip ? 1 : 0);
  p.mixer.setTime((t + p.seed) * (P.speed || 1));
  const b = p.bones;
  if (P.spine) addRot(b.spine, ...P.spine);
  if (P.spine1) addRot(b.spine1, ...P.spine1);
  if (P.arms) { addRot(b.lArm, P.arms[0], P.arms[1], P.arms[2]); addRot(b.rArm, P.arms[0], -P.arms[1], -P.arms[2]); }
  if (P.fore) { addRot(b.lFore, P.fore[0], P.fore[1], P.fore[2]); addRot(b.rFore, P.fore[0], -P.fore[1], -P.fore[2]); }
  if (P.rArm) addRot(b.rArm, ...P.rArm);
  if (P.rFore) addRot(b.rFore, ...P.rFore);
  if (P.lFore) addRot(b.lFore, ...P.lFore);
  if (P.rFore && P.lFore) {}
  if (P.legs) { addRot(b.lUp, P.legs[0], P.legs[1], P.legs[2]); addRot(b.rUp, P.legs[0], -P.legs[1], -P.legs[2]); }
}
