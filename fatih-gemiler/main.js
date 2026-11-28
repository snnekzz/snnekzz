// Fatih'in gemileri karadan yürütmesi (1453) — Three.js sahnesi
// Mod 1 (önizleme): index.html'i tarayıcıda açın, "Oynat" ile sesle birlikte oynar.
// Mod 2 (render): ?render=1 -> window.renderFrame(t) kare kare çizdirilir (render.cjs).
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const W = 1080, H = 1920;
const params = new URLSearchParams(location.search);
const RENDER_MODE = params.has('render');
const PIXEL_RATIO = parseFloat(params.get('pr') || '1');
export const DURATION = 45.6;

// ---------------------------------------------------------------- yardımcılar
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const lerp = (a, b, k) => a + (b - a) * k;
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const ease = k => k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const lerpV = (a, b, k) => a.clone().lerp(b, k);
function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

// Tüm düz renkli parçalar tek malzeme + vertex color kullanır (low-poly görünüm)
const MAT = new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.9, metalness: 0 });
const MAT_DS = new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.9, metalness: 0, side: THREE.DoubleSide });

function prep(geo, color, m4) {
  let g = geo.index ? geo.toNonIndexed() : geo.clone();
  if (g.attributes.uv) g.deleteAttribute('uv');
  if (g.attributes.uv1) g.deleteAttribute('uv1');
  if (!g.attributes.normal) g.computeVertexNormals();
  if (m4) g.applyMatrix4(m4);
  const c = new THREE.Color(color), n = g.attributes.position.count, arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { arr[i * 3] = c.r; arr[i * 3 + 1] = c.g; arr[i * 3 + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(arr, 3));
  return g;
}
function M(x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, sx = 1, sy = 1, sz = 1) {
  return new THREE.Matrix4().compose(V(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), V(sx, sy, sz));
}
const box = (w, h, d, c, x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0) => prep(new THREE.BoxGeometry(w, h, d), c, M(x, y, z, rx, ry, rz));
const cyl = (rt, rb, h, seg, c, m4) => prep(new THREE.CylinderGeometry(rt, rb, h, seg), c, m4);
const cone = (r, h, seg, c, m4) => prep(new THREE.ConeGeometry(r, h, seg), c, m4);
const ico = (r, c, m4) => prep(new THREE.IcosahedronGeometry(r, 0), c, m4);
function triGeo(pts, color) { // pts: dizi [Vector3...] üçlü gruplar
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pts.flatMap(p => [p.x, p.y, p.z]), 3));
  g.computeVertexNormals();
  return prep(g, color);
}
function mesh(geo, mat = MAT, cast = true, recv = false) { const m = new THREE.Mesh(geo, mat); m.castShadow = cast; m.receiveShadow = recv; return m; }

// ---------------------------------------------------------------- coğrafya
// x ekseni: Boğaz (x<-71) -> Galata tepesi (tepe x=0) -> Haliç (71<x<150) -> Suriçi (x>152)
// Haliç'in ağzı güneyde (z≈-110), zincir orada.
function landHeight(x, z) {
  let h = -6;
  // Galata yarımadası
  const hx = Math.max(0, 1 - (x / 74) ** 2);
  const hz = smooth(-112, -80, z);
  const n = Math.sin(x * 0.11 + z * 0.07) * 0.8 + Math.sin(z * 0.13 - x * 0.05) * 0.7;
  const pen = (28 * Math.pow(hx, 1.2) + 1.5 + n * hx) * hz - 3;
  h = Math.max(h, pen);
  // Suriçi (eski şehir)
  const city = smooth(147, 156, x) * (7 + Math.sin(z / 37) * 2 + Math.max(0, (x - 190) * 0.05)) - 3;
  h = Math.max(h, city);
  // Anadolu yakası (uzak arka plan)
  const asia = smooth(-180, -200, x) * (16 + Math.sin(z / 30) * 5) - 3;
  h = Math.max(h, asia);
  return h;
}
const pz = x => 7 * Math.sin(x / 38);                    // güzergahın z'si
const SHORE_W = -71, SHORE_E = 71;
function shipY(x) { return Math.max(0.1, landHeight(x, pz(x)) + 1.15); }

// ---------------------------------------------------------------- renderer / sahne
const stage = document.getElementById('stage');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(PIXEL_RATIO);
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
stage.prepend(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, W / H, 0.5, 2500);
scene.fog = new THREE.Fog(0xcfe8f5, 260, 900);

const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false,
  uniforms: { top: { value: new THREE.Color() }, bottom: { value: new THREE.Color() } },
  vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: 'uniform vec3 top; uniform vec3 bottom; varying vec3 vP; void main(){ float h = clamp(vP.y*1.8+0.12,0.0,1.0); gl_FragColor = vec4(mix(bottom, top, h),1.0);\n#include <colorspace_fragment>\n}',
});
const sky = new THREE.Mesh(new THREE.SphereGeometry(1800, 32, 16), skyMat);
sky.renderOrder = -1;
scene.add(sky);

const hemi = new THREE.HemisphereLight(0xdfefff, 0x6a7a4a, 1.0);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffffff, 2.0);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.06;
scene.add(sun, sun.target);

// glow dokusu (meşale, ay)
function glowTexture(inner, outer) {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d'), gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, inner); gr.addColorStop(0.25, inner); gr.addColorStop(1, outer);
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const fireTex = glowTexture('rgba(255,230,160,1)', 'rgba(255,120,20,0)');
const moonTex = glowTexture('rgba(250,250,255,1)', 'rgba(200,210,255,0)');
const moon = new THREE.Sprite(new THREE.SpriteMaterial({ map: moonTex, transparent: true, depthWrite: false, fog: false }));
moon.scale.set(120, 120, 1);
scene.add(moon);

const TOD = {
  day:   { top: 0x5aa7e0, bottom: 0xd6ecf7, fog: 0xd6ecf7, sun: 0xfff1d6, sunI: 2.4, hemiSky: 0xdfefff, hemiGround: 0x7d8a55, hemiI: 1.05, exp: 1.0, dir: V(-0.5, 0.8, 0.45), moon: false },
  night: { top: 0x0d1c3d, bottom: 0x34508a, fog: 0x2a3f6c, sun: 0xb4c6ff, sunI: 1.5, hemiSky: 0x6f8ccc, hemiGround: 0x27304a, hemiI: 1.1, exp: 1.35, dir: V(0.4, 0.75, -0.5), moon: true },
  dawn:  { top: 0x4f79bd, bottom: 0xf7bf8f, fog: 0xf0c39d, sun: 0xffc78f, sunI: 2.2, hemiSky: 0xffe2c8, hemiGround: 0x6a6650, hemiI: 0.95, exp: 1.0, dir: V(-0.9, 0.35, 0.2), moon: false },
};
let currentTOD = 'day';
function setTOD(name) {
  const p = TOD[name]; currentTOD = name;
  skyMat.uniforms.top.value.set(p.top); skyMat.uniforms.bottom.value.set(p.bottom);
  scene.fog.color.set(p.fog);
  sun.color.set(p.sun); sun.intensity = p.sunI;
  hemi.color.set(p.hemiSky); hemi.groundColor.set(p.hemiGround); hemi.intensity = p.hemiI;
  renderer.toneMappingExposure = p.exp;
  moon.visible = p.moon;
}
function aimSun(target, span = 120) {
  const p = TOD[currentTOD];
  sun.target.position.copy(target);
  sun.position.copy(target).addScaledVector(p.dir.clone().normalize(), 300);
  const c = sun.shadow.camera;
  c.left = -span; c.right = span; c.top = span; c.bottom = -span; c.near = 10; c.far = 700;
  c.updateProjectionMatrix();
}

// ---------------------------------------------------------------- arazi
{
  const SIZE = 560, SEG = 190, CX = 20;
  const g = new THREE.PlaneGeometry(SIZE, SIZE, SEG, SEG).toNonIndexed();
  g.rotateX(-Math.PI / 2);
  g.translate(CX, 0, 0);
  const pos = g.attributes.position;
  for (let i = 0; i < pos.count; i++) pos.setY(i, landHeight(pos.getX(i), pos.getZ(i)));
  const col = new Float32Array(pos.count * 3), c = new THREE.Color(), r = rng(7);
  const SAND = new THREE.Color(0xd8c48f), G1 = new THREE.Color(0x86b25c), G2 = new THREE.Color(0x5e8f42), STONE = new THREE.Color(0xc4b296), DEEP = new THREE.Color(0x6f8c78);
  for (let i = 0; i < pos.count; i += 3) {
    const x = (pos.getX(i) + pos.getX(i + 1) + pos.getX(i + 2)) / 3, z = (pos.getZ(i) + pos.getZ(i + 1) + pos.getZ(i + 2)) / 3;
    const y = (pos.getY(i) + pos.getY(i + 1) + pos.getY(i + 2)) / 3;
    if (y < -1.2) c.copy(DEEP);
    else if (y < 0.9) c.copy(SAND);
    else if (x > 146) c.copy(STONE).multiplyScalar(0.93 + r() * 0.1);
    else c.copy(G1).lerp(G2, clamp(y / 26 + r() * 0.25));
    // güzergah toprak yolu
    if (x > -72 && x < 72 && Math.abs(z - pz(x)) < 4.2 && y > 0.3) c.set(0xa88d63).multiplyScalar(0.92 + r() * 0.08);
    for (let k = 0; k < 3; k++) col.set([c.r, c.g, c.b], (i + k) * 3);
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.deleteAttribute('uv');
  g.computeVertexNormals();
  const terrain = mesh(g, MAT, false, true);
  scene.add(terrain);
}

// su
const water = (() => {
  const g = new THREE.PlaneGeometry(1600, 1600, 140, 140);
  g.rotateX(-Math.PI / 2);
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0x3f93ad, flatShading: true, roughness: 0.3, metalness: 0.05, transparent: true, opacity: 0.9 }));
  m.receiveShadow = true;
  m.position.set(20, 0, 0);
  scene.add(m);
  return m;
})();
const waterBase = water.geometry.attributes.position.array.slice();
function updateWater(t) {
  const p = water.geometry.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = waterBase[i * 3], z = waterBase[i * 3 + 2];
    p.array[i * 3 + 1] = Math.sin(x * 0.35 + t * 1.6) * 0.12 + Math.cos(z * 0.3 + t * 1.2) * 0.12;
  }
  p.needsUpdate = true;
}

// ---------------------------------------------------------------- statik yapılar
const statics = [];
{
  const r = rng(11);
  const parts = [];
  // Suriçi surları ve kuleleri
  for (let z = -150; z <= 170; z += 6) {
    const b = landHeight(154, z);
    parts.push(box(3, 9, 6.05, 0xcbb899, 154, b + 4.5 - 1, z));
    if (Math.round(z / 6) % 2 === 0) parts.push(box(3.2, 1.2, 2.2, 0xcbb899, 154, b + 9, z));
  }
  for (let z = -144; z <= 170; z += 26) {
    const b = landHeight(154, z);
    parts.push(box(7, 14, 7, 0xb9a585, 154, b + 7 - 1, z));
    parts.push(box(7.6, 1.2, 7.6, 0xa8957a, 154, b + 13.4, z));
  }
  // Suriçi evleri
  for (let i = 0; i < 520; i++) {
    const x = 162 + r() * 110, z = -150 + r() * 320;
    if (Math.hypot(x - 215, z + 80) < 26) continue;
    const b = landHeight(x, z), w = 4 + r() * 4, d = 4 + r() * 4, h = 3.5 + r() * 4;
    const wall = [0xf2e8d5, 0xe9dcc3, 0xf5efe3, 0xdccbb0][Math.floor(r() * 4)];
    const roof = [0xc0573a, 0xb44a30, 0xcf6a45][Math.floor(r() * 3)];
    parts.push(box(w, h, d, wall, x, b + h / 2 - 0.5, z));
    parts.push(cone(Math.max(w, d) * 0.75, 2.4, 4, roof, M(x, b + h + 0.7, z, 0, Math.PI / 4, 0, w / Math.max(w, d), 1, d / Math.max(w, d))));
  }
  // Büyük kubbeli bazilika (Ayasofya; 1453'te minaresizdi)
  {
    const x = 215, z = -80, b = landHeight(x, z);
    parts.push(box(40, 16, 46, 0xe7c9a5, x, b + 8, z));
    parts.push(cyl(14, 14, 4, 24, 0xe0bf98, M(x, b + 18, z)));
    parts.push(prep(new THREE.SphereGeometry(13, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2), 0x8c99a3, M(x, b + 20, z)));
    for (const s of [-1, 1]) parts.push(prep(new THREE.SphereGeometry(8, 14, 7, 0, Math.PI * 2, 0, Math.PI / 2), 0x8c99a3, M(x, b + 16, z + s * 20)));
  }
  // Galata Kulesi ve Ceneviz evleri
  {
    const x = 26, z = -58, b = landHeight(x, z);
    parts.push(cyl(3.4, 3.8, 22, 12, 0xbfae92, M(x, b + 10, z)));
    parts.push(cyl(4.2, 4.2, 1.2, 12, 0xa8977b, M(x, b + 21, z)));
    parts.push(cone(4.3, 7, 12, 0x6f7f8c, M(x, b + 25, z)));
    for (let i = 0; i < 70; i++) {
      const hx = -10 + r() * 75, hz = -92 + r() * 34;
      if (Math.hypot(hx - x, hz - z) < 6) continue;
      const hb = landHeight(hx, hz); if (hb < 1) continue;
      const w = 3 + r() * 3, h = 3 + r() * 3;
      parts.push(box(w, h, w, 0xf0e6d2, hx, hb + h / 2 - 0.5, hz));
      parts.push(cone(w * 0.75, 2, 4, 0xbf5a3d, M(hx, hb + h + 0.5, hz, 0, Math.PI / 4, 0)));
    }
  }
  // Ağaçlar (servi + yuvarlak)
  for (let i = 0; i < 260; i++) {
    const x = -68 + r() * 136, z = -75 + r() * 230;
    const b = landHeight(x, z);
    if (b < 1.5) continue;
    if (Math.abs(z - pz(x)) < 15) continue;
    if (x < -40 && z > pz(x) && z < 45) continue;
    if (z < -50 && x > -15 && x < 70) continue;
    if (r() < 0.45) {
      const h = 7 + r() * 5;
      parts.push(cone(1.1, h, 6, 0x2f5e34, M(x, b + h / 2 + 0.5, z)));
    } else {
      parts.push(cyl(0.25, 0.3, 2, 5, 0x6b4a2e, M(x, b + 1, z)));
      parts.push(ico(2 + r() * 1.2, [0x4f8a3c, 0x5c9a45, 0x467d35][Math.floor(r() * 3)], M(x, b + 3.3, z)));
    }
  }
  // Osmanlı ordugâhı çadırları (Beşiktaş kıyısı)
  for (let i = 0; i < 26; i++) {
    const x = -66 + r() * 12, z = 16 + r() * 50;
    const b = landHeight(x, z); if (b < 0.6) continue;
    parts.push(cone(2.2, 3.2, 8, 0xf4efe4, M(x, b + 1.5, z)));
    parts.push(cone(0.6, 1, 8, 0xc0392b, M(x, b + 3.4, z)));
  }
  const g = mergeGeometries(parts);
  const m = mesh(g, MAT, true, true);
  scene.add(m);
}

// ---------------------------------------------------------------- zincir
const chainGroup = new THREE.Group();
{
  const parts = [];
  const z0 = -110;
  for (let x = 70; x <= 152; x += 4) {
    parts.push(cyl(0.7, 0.7, 3.2, 8, 0x6e4a2c, M(x, 0.25, z0, 0, 0, Math.PI / 2)));   // şamandıra kütük
    parts.push(prep(new THREE.TorusGeometry(0.55, 0.16, 5, 8), 0x2b2b2b, M(x + 2, 0.4, z0, 0, Math.PI / 2, 0)));
  }
  parts.push(box(84, 0.18, 0.18, 0x222222, 111, 0.55, z0));
  chainGroup.add(mesh(mergeGeometries(parts)));
  scene.add(chainGroup);
}

// ---------------------------------------------------------------- kızak kütükleri
const logs = [];
const LOG_X = [];
for (let x = -74; x <= 74; x += 2.3) LOG_X.push(x);
{
  const g = new THREE.CylinderGeometry(0.33, 0.33, 5.6, 7);
  const m = new THREE.MeshStandardMaterial({ color: 0x8a5a30, flatShading: true, roughness: 0.35, metalness: 0.1 });
  for (const x of LOG_X) {
    const z = pz(x), dz = (pz(x + 0.5) - pz(x - 0.5));
    const lm = new THREE.Mesh(g, m);
    lm.castShadow = true; lm.receiveShadow = true;
    lm.position.set(x, landHeight(x, z) + 0.25, z);
    lm.rotation.set(Math.PI / 2, -Math.atan2(dz, 1), 0, 'YXZ');
    lm.rotation.order = 'YXZ';
    lm.rotation.y = -Math.atan2(dz, 1);
    lm.rotation.x = Math.PI / 2;
    lm.visible = landHeight(x, z) > -0.4;
    lm.userData.x = x;
    logs.push(lm); scene.add(lm);
  }
}
function setLogs(maxX) { for (const l of logs) l.visible = l.userData.x <= maxX && l.position.y > -0.2; }

// ---------------------------------------------------------------- güzergah çizgisi (harita sahnesi)
const routeCurve = new THREE.CatmullRomCurve3(Array.from({ length: 60 }, (_, i) => {
  const x = -86 + i * (172 / 59);
  return V(x, Math.max(0.6, landHeight(x, pz(x)) + 2.2), pz(x));
}));
const routeGeo = new THREE.TubeGeometry(routeCurve, 240, 1.3, 8, false);
const routeMat = new THREE.MeshBasicMaterial({ color: 0xe8312a, transparent: true, opacity: 1, fog: false });
const routeMesh = new THREE.Mesh(routeGeo, routeMat);
scene.add(routeMesh);
const arrowHead = new THREE.Mesh(new THREE.ConeGeometry(3.6, 8, 12), routeMat);
scene.add(arrowHead);
function setRoute(k, opacity = 1) {
  routeMesh.visible = arrowHead.visible = k > 0.001;
  routeGeo.setDrawRange(0, Math.floor(routeGeo.index.count * k / 6) * 6);
  routeMat.opacity = opacity;
  const u = clamp(k, 0.001, 1), p = routeCurve.getPointAt(u), tg = routeCurve.getTangentAt(u);
  arrowHead.position.copy(p);
  arrowHead.quaternion.setFromUnitVectors(V(0, 1, 0), tg);
}

// ---------------------------------------------------------------- gemiler
function hullGeo(L, B, cHull, cBand, cDeck) {
  const S = 18, prof = [[-1, 1], [-0.97, 0.62], [-0.7, 0.18], [0, 0], [0.7, 0.18], [0.97, 0.62], [1, 1]];
  const st = [];
  for (let i = 0; i <= S; i++) {
    const s = -1 + 2 * i / S, a = Math.abs(s);
    const hw = B / 2 * Math.pow(Math.max(0, 1 - Math.pow(a, 2.4)), 0.55) + 0.04;
    const deck = 1.0 + 0.9 * Math.pow(a, 4);
    const keel = -0.75 * (1 - Math.pow(a, 6)) + 0.5 * Math.pow(a, 6);
    st.push(prof.map(([px, py]) => V(s * L / 2, keel + (deck - keel) * py, px * hw)));
  }
  const P = [], C = [];
  const push = (pts, col) => { const c = new THREE.Color(col); for (const p of pts) { P.push(p.x, p.y, p.z); C.push(c.r, c.g, c.b); } };
  for (let i = 0; i < S; i++) for (let j = 0; j < 6; j++) {
    const a = st[i][j], b = st[i + 1][j], c = st[i + 1][j + 1], d = st[i][j + 1];
    const col = (j === 0 || j === 5) ? cBand : cHull;
    push([a, b, c, a, c, d], col);
  }
  for (let i = 0; i < S; i++) {
    const a = st[i][0].clone(), b = st[i + 1][0].clone(), c = st[i + 1][6].clone(), d = st[i][6].clone();
    for (const p of [a, b, c, d]) p.y -= 0.18;
    push([a, b, c, a, c, d], cDeck);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(C, 3));
  g.computeVertexNormals();
  return g;
}
const SHIP_L = 14, SHIP_B = 3.0;
const PAL = {
  ott: { hull: 0x6e4528, band: 0xa8321f, deck: 0xb58c5c, sail: 0xf3ead6, flag: 0xc0262d },
  byz: { hull: 0x4a3a2e, band: 0x3c3f7a, deck: 0x9c8466, sail: 0x7a3f86, flag: 0xd4a62a },
};
const SAIL_A = V(-3.2, 3.0, 0), SAIL_B = V(5.0, 12.0, 0), SAIL_C = V(5.4, 2.6, 0);
function shipStaticParts(pal, withSail, withOars) {
  const parts = [hullGeo(SHIP_L, SHIP_B, pal.hull, pal.band, pal.deck)];
  parts.push(cone(0.35, 2.4, 6, pal.hull, M(SHIP_L / 2 + 0.8, 0.85, 0, 0, 0, -Math.PI / 2)));          // mahmuz
  parts.push(box(2.6, 1.0, 2.2, pal.band, -SHIP_L / 2 + 2.2, 1.6, 0));                                    // kıç köşkü
  parts.push(cyl(0.05, 0.05, 3, 4, 0x5a3b22, M(-SHIP_L / 2 + 1.2, 3.1, 0)));
  parts.push(box(1.2, 0.7, 0.04, pal.flag, -SHIP_L / 2 + 0.55, 4.2, 0));                                 // sancak
  parts.push(cyl(0.14, 0.18, 10.5, 6, 0x5a3b22, M(1.0, 5.6, 0)));                                         // direk
  if (withSail) {
    const dir = SAIL_B.clone().sub(SAIL_A), mid = SAIL_A.clone().add(SAIL_B).multiplyScalar(0.5);
    parts.push(cyl(0.09, 0.09, dir.length(), 5, 0x5a3b22, M(mid.x, mid.y, 0.15, 0, 0, Math.atan2(-dir.x, dir.y))));
  } else {
    parts.push(cyl(0.09, 0.09, 10, 5, 0x5a3b22, M(0.8, 2.0, 0.6, 0, 0, Math.PI / 2 - 0.12)));             // yatırılmış seren
    parts.push(cyl(0.3, 0.3, 8, 6, pal.sail, M(0.8, 2.25, 0.6, 0, 0, Math.PI / 2 - 0.12)));               // sarılı yelken
  }
  if (withOars) {
    for (let i = 0; i < 9; i++) for (const s of [-1, 1]) {
      const x = -4.5 + i * 1.15;
      parts.push(box(0.1, 0.1, 5.2, 0x7a5634, x, 0.2, s * (SHIP_B / 2 + 1.8), s * 0.42, 0, 0));
    }
  }
  return parts;
}
function sailGeo(color) {
  const off = V(0, 0, 0.35);
  return triGeo([SAIL_A.clone().add(off), SAIL_B.clone().add(off), SAIL_C.clone().add(off)], color);
}
const SHIP_SIMPLE = {
  ottFurled: mergeGeometries(shipStaticParts(PAL.ott, false, true)),
  byzFurled: mergeGeometries(shipStaticParts(PAL.byz, false, true)),
  ottSail: mergeGeometries([...shipStaticParts(PAL.ott, true, true), sailGeo(PAL.ott.sail)]),
  byzSail: mergeGeometries([...shipStaticParts(PAL.byz, true, true), sailGeo(PAL.byz.sail)]),
};
const SIMPLE_POOL = [];
for (let i = 0; i < 130; i++) {
  const m = mesh(SHIP_SIMPLE.ottFurled, MAT_DS, true, false);
  m.rotation.order = 'YZX'; m.visible = false; scene.add(m); SIMPLE_POOL.push(m);
}
// Detaylı gemi: kürekler hareketli, yelken açılıp kapanabilir, kızak (beşik)
const OAR_GEO = mergeGeometries([box(0.1, 0.1, 5.4, 0x7a5634, 0, 0, 2.0), box(0.06, 0.5, 1.1, 0x7a5634, 0, 0, 4.4)]);
const CRADLE_GEO = mergeGeometries([
  box(SHIP_L * 0.8, 0.35, 0.4, 0x5e3d22, 0, -0.95, 0.9), box(SHIP_L * 0.8, 0.35, 0.4, 0x5e3d22, 0, -0.95, -0.9),
  ...[-4, -1.3, 1.3, 4].map(x => box(0.4, 0.6, 2.6, 0x5e3d22, x, -0.6, 0)),
]);
function makeDetailedShip() {
  const g = new THREE.Group(); g.rotation.order = 'YZX';
  const body = mesh(mergeGeometries(shipStaticParts(PAL.ott, true, false)), MAT_DS);
  const sail = mesh(sailGeo(PAL.ott.sail), MAT_DS);
  const cradle = mesh(CRADLE_GEO);
  g.add(body, sail, cradle);
  const oars = [];
  for (let i = 0; i < 9; i++) for (const s of [-1, 1]) {
    const piv = new THREE.Group(); piv.position.set(-4.5 + i * 1.15, 1.0, s * (SHIP_B / 2 - 0.1));
    if (s < 0) piv.rotation.y = Math.PI;
    const o = mesh(OAR_GEO); o.rotation.order = 'YXZ'; piv.add(o); g.add(piv);
    oars.push({ o, s, i });
  }
  // kürekçiler (gemide oturan küçük figürler)
  const crew = mesh(mergeGeometries(Array.from({ length: 8 }, (_, i) => [
    box(0.4, 0.5, 0.35, 0xe8dcc0, -3.8 + i * 1.15, 1.25, 0.5 * (i % 2 ? 1 : -1)),
    ico(0.18, 0xc98e65, M(-3.8 + i * 1.15, 1.7, 0.5 * (i % 2 ? 1 : -1))),
    cyl(0.16, 0.16, 0.18, 6, 0xf4f1ea, M(-3.8 + i * 1.15, 1.88, 0.5 * (i % 2 ? 1 : -1))),
  ]).flat()));
  g.add(crew);
  g.visible = false; scene.add(g);
  return { g, sail, cradle, oars };
}
const DETAILED = Array.from({ length: 10 }, makeDetailedShip);

let simpleIdx = 0, detailedIdx = 0;
function resetShips() { for (const m of SIMPLE_POOL) m.visible = false; for (const d of DETAILED) d.g.visible = false; simpleIdx = 0; detailedIdx = 0; }
function placeSimple(kind, x, y, z, yaw, pitch = 0, roll = 0) {
  const m = SIMPLE_POOL[simpleIdx++]; if (!m) return;
  m.geometry = SHIP_SIMPLE[kind];
  m.position.set(x, y, z); m.rotation.set(roll, yaw, pitch); m.visible = true;
}
// gemiyi güzergah üzerinde konumlandır (x = gemi merkezinin x'i)
function pathPose(x) {
  const yb = shipY(x + 5.5), ys = shipY(x - 5.5), z = pz(x);
  const dz = pz(x + 1) - pz(x - 1);
  const y = Math.max(shipY(x), (yb + ys) / 2);
  return { x, y, z, yaw: Math.atan2(-dz, 2), pitch: Math.atan2(yb - ys, 11) };
}
function placeDetailed(x, y, z, yaw, pitch, opts = {}) {
  const d = DETAILED[detailedIdx++]; if (!d) return null;
  d.g.visible = true; d.g.position.set(x, y, z); d.g.rotation.set(opts.roll || 0, yaw, pitch);
  const sailK = opts.sail ?? 1;
  d.sail.visible = sailK > 0.02;
  d.sail.scale.set(1, sailK, 1);
  d.sail.position.set(0, (1 - sailK) * 8, 0);
  d.cradle.visible = !!opts.cradle;
  const t = opts.t || 0, ph = opts.phase || 0;
  for (const { o, s, i } of d.oars) {
    let sweep = 0, dip = 0.42;
    if (opts.oars === 'row' || opts.oars === 'air') {
      const a = t * 4.2 + ph + i * 0.05;
      sweep = Math.sin(a) * 0.38;
      dip = (opts.oars === 'row' ? 0.4 : 0.05) + Math.cos(a) * 0.14;
    } else if (opts.oars === 'up') { dip = -0.25; }
    o.rotation.y = s > 0 ? sweep : -sweep;
    o.rotation.x = dip;
  }
  return d;
}

// ---------------------------------------------------------------- insanlar ve öküzler
const SKIN = 0xc98e65;
function makePerson(shirt, pants, hat) {
  const root = new THREE.Group(), body = new THREE.Group(); root.add(body);
  const hatG = hat === 'turban' ? [cyl(0.19, 0.17, 0.2, 7, 0xf4f1ea, M(0, 1.9, 0)), ico(0.15, 0xf4f1ea, M(0, 1.98, 0))]
    : hat === 'bork' ? [cyl(0.15, 0.18, 0.45, 7, 0xf4f1ea, M(0, 2.0, 0)), box(0.12, 0.5, 0.25, 0xf4f1ea, -0.18, 1.85, 0, 0, 0, 0.4)]
    : hat === 'helmet' ? [cone(0.22, 0.38, 7, 0x9aa3ab, M(0, 1.97, 0))]
    : [cyl(0.17, 0.17, 0.12, 7, 0x8a2a20, M(0, 1.86, 0))];
  const torso = mesh(mergeGeometries([box(0.42, 0.66, 0.32, shirt, 0, 1.22, 0), box(0.44, 0.1, 0.34, 0x5b3a22, 0, 0.94, 0), ico(0.19, SKIN, M(0, 1.7, 0)), ...hatG]));
  body.add(torso);
  const limb = (geo, x, y, z) => { const p = new THREE.Group(); p.position.set(x, y, z); p.add(mesh(geo)); body.add(p); return p; };
  const legGeo = mergeGeometries([box(0.17, 0.82, 0.18, pants, 0, -0.41, 0), box(0.2, 0.1, 0.28, 0x3b2a1e, 0.04, -0.85, 0)]);
  const armGeo = mergeGeometries([box(0.13, 0.6, 0.14, shirt, 0, -0.3, 0), ico(0.08, SKIN, M(0, -0.64, 0))]);
  const legL = limb(legGeo, 0, 0.9, 0.11), legR = limb(legGeo, 0, 0.9, -0.11);
  const armL = limb(armGeo, 0, 1.5, 0.28), armR = limb(armGeo, 0, 1.5, -0.28);
  root.visible = false; scene.add(root);
  return { root, body, legL, legR, armL, armR };
}
function pose(p, { phase = 0, walk = 0, lean = 0, armF = 0, armSwing = 0, armUp = 0, armAlt = 0 }) {
  p.legL.rotation.z = Math.sin(phase) * walk;
  p.legR.rotation.z = -Math.sin(phase) * walk;
  p.armL.rotation.z = armF + Math.sin(phase + Math.PI) * armSwing + armAlt * Math.sin(phase);
  p.armR.rotation.z = armF + Math.sin(phase) * armSwing - armAlt * Math.sin(phase);
  p.armL.rotation.x = -armUp; p.armR.rotation.x = armUp;
  p.body.rotation.z = -lean;
}
const SHIRTS = [0xc0392b, 0xe6d3a3, 0x3d6b8f, 0x8e5a2b, 0xd9c7a0, 0x7a2e2e, 0x4f6b3a];
const workers = [];
{ const r = rng(3); for (let i = 0; i < 90; i++) workers.push(makePerson(SHIRTS[Math.floor(r() * SHIRTS.length)], [0x3b3b4a, 0x4a3a2a, 0x2f3d4f][Math.floor(r() * 3)], r() < 0.75 ? 'turban' : 'bork')); }
const soldiersByz = [];
for (let i = 0; i < 12; i++) soldiersByz.push(makePerson(i % 2 ? 0x5a3c7a : 0x2e4f8a, 0x3a3030, 'helmet'));

function makeOx(color) {
  const root = new THREE.Group();
  root.add(mesh(mergeGeometries([
    box(2.2, 1.0, 1.0, color, 0, 1.3, 0), box(0.5, 0.35, 0.95, color, 0.6, 1.9, 0),
    box(0.7, 0.62, 0.62, color, 1.35, 1.45, 0), box(0.3, 0.35, 0.5, 0xd9b99a, 1.8, 1.35, 0),
    cone(0.07, 0.55, 5, 0xe9e2cf, M(1.35, 1.9, 0.38, -0.9, 0, 0)), cone(0.07, 0.55, 5, 0xe9e2cf, M(1.35, 1.9, -0.38, 0.9, 0, 0)),
    box(0.08, 0.7, 0.08, color, -1.15, 1.2, 0, 0, 0, 0.2),
  ])));
  const legs = [];
  for (const [x, z] of [[0.8, 0.33], [0.8, -0.33], [-0.8, 0.33], [-0.8, -0.33]]) {
    const p = new THREE.Group(); p.position.set(x, 0.95, z); p.add(mesh(box(0.24, 0.95, 0.24, color, 0, -0.47, 0))); root.add(p); legs.push(p);
  }
  root.visible = false; scene.add(root);
  return { root, legs };
}
const oxen = [];
for (let i = 0; i < 40; i++) oxen.push(makeOx([0x6b4a2e, 0x4a3426, 0x8a6a48, 0x3a2c22][i % 4]));
function poseOx(o, phase, walk) { o.legs.forEach((l, i) => l.rotation.z = Math.sin(phase + (i % 2 === (i < 2 ? 0 : 1) ? 0 : Math.PI)) * walk); }

// halat / boyunduruk çubukları
const STICK_GEO = new THREE.CylinderGeometry(1, 1, 1, 5);
const ropeMat = new THREE.MeshStandardMaterial({ color: 0xc9b07a, roughness: 1, flatShading: true });
const yokeMat = new THREE.MeshStandardMaterial({ color: 0x5e3d22, roughness: 1, flatShading: true });
const sticks = [];
function getStick(i, mat, r) {
  if (!sticks[i]) { const m = new THREE.Mesh(STICK_GEO, mat); m.castShadow = true; scene.add(m); sticks[i] = m; }
  const s = sticks[i]; s.material = mat; s.userData.r = r; s.visible = true; return s;
}
const _up = V(0, 1, 0);
function setStick(s, a, b) {
  const d = b.clone().sub(a), len = d.length();
  s.position.copy(a).addScaledVector(d, 0.5);
  s.quaternion.setFromUnitVectors(_up, d.normalize());
  s.scale.set(s.userData.r, len, s.userData.r);
}

// diğer aksesuarlar
const drums = [0, 1].map(() => { const m = mesh(mergeGeometries([cyl(0.5, 0.5, 0.6, 10, 0xa8321f), cyl(0.51, 0.51, 0.05, 10, 0xf1e6cc, M(0, 0.31, 0))])); m.visible = false; scene.add(m); return m; });
const buckets = [0, 1].map(() => { const m = mesh(cyl(0.25, 0.2, 0.4, 8, 0x5b4632)); m.visible = false; scene.add(m); return m; });
const carriedLogs = [0, 1, 2].map(() => { const m = mesh(prep(new THREE.CylinderGeometry(0.28, 0.28, 4.6, 7), 0x9a6a3a)); m.visible = false; scene.add(m); return m; });

// meşaleler
const torches = [];
for (let x = -64; x <= 64; x += 11) for (const s of [-1, 1]) {
  const z = pz(x) + s * 6.5, b = landHeight(x, z);
  if (b < 0.5) continue;
  const g = new THREE.Group();
  g.add(mesh(cyl(0.08, 0.1, 3.2, 5, 0x4a3020, M(0, 1.6, 0))));
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: fireTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
  sp.scale.set(3.4, 3.4, 1); sp.position.y = 3.5; g.add(sp);
  const core = mesh(ico(0.25, 0xffc040), MAT, false); core.material = new THREE.MeshBasicMaterial({ color: 0xffd060 }); core.position.y = 3.3; g.add(core);
  g.position.set(x, b, z); g.userData = { x, sp }; g.visible = false;
  scene.add(g); torches.push(g);
}
function setTorches(on, maxX = 999, t = 0) {
  for (const g of torches) {
    g.visible = on && g.userData.x <= maxX;
    const f = 1 + Math.sin(t * 13 + g.userData.x) * 0.12 + Math.sin(t * 7.3 + g.userData.x * 2) * 0.08;
    g.userData.sp.scale.set(3.4 * f, 3.4 * f, 1);
  }
}

// su sıçraması
const SPLASH_N = 90;
const splash = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(0.35, 0), new THREE.MeshStandardMaterial({ color: 0xffffff, flatShading: true, roughness: 0.6 }), SPLASH_N);
splash.frustumCulled = false; scene.add(splash);
const splashSeeds = Array.from({ length: SPLASH_N }, (_, i) => { const r = rng(100 + i); return [r() * Math.PI * 2, 4 + r() * 7, 3 + r() * 5, 0.5 + r() * 0.9]; });
const _m4 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _s = V(1, 1, 1);
function setSplashes(list) { // list: [{x,z,age}]
  let n = 0;
  for (const sp of list) {
    if (sp.age < 0 || sp.age > 1.6) continue;
    for (let i = 0; i < SPLASH_N / 3 && n < SPLASH_N; i++) {
      const [ang, vy, vr, sz] = splashSeeds[(i * 3 + Math.floor(sp.x)) % SPLASH_N];
      const a = sp.age, y = vy * a - 9.8 * a * a / 2;
      if (y < -0.5) continue;
      const k = Math.max(0, 1 - a / 1.6) * sz;
      _m4.compose(V(sp.x + Math.cos(ang) * vr * a, Math.max(0, y), sp.z + Math.sin(ang) * vr * a), _q, _s.set(k, k, k));
      splash.setMatrixAt(n++, _m4);
    }
  }
  splash.count = n; splash.instanceMatrix.needsUpdate = true;
}

// ---------------------------------------------------------------- filo yerleşimleri
function layoutBosphorusFleet(count = 26) {
  const r = rng(21);
  for (let i = 0; i < count; i++) {
    const c = i % 4, row = Math.floor(i / 4);
    placeSimple('ottFurled', -98 - c * 15 - r() * 4, 0.05, -55 + row * 17 + r() * 5, Math.PI / 2 + (r() - 0.5) * 0.5, 0, Math.sin(i) * 0.02);
  }
}
function layoutOttomanAtChain() {
  for (let i = 0; i < 7; i++) placeSimple('ottSail', 80 + i * 10.5, 0.05, -150 - (i % 2) * 9, -Math.PI / 2 + (i - 3) * 0.04);
}
function layoutByzBehindChain() {
  for (let i = 0; i < 6; i++) placeSimple(i % 2 ? 'byzFurled' : 'byzSail', 84 + i * 11.5, 0.05, -96 + (i % 2) * 7, Math.PI / 2 + (i - 2.5) * 0.05);
}
function layoutGoldenHornFleet(n = 70) {
  const r = rng(77);
  for (let i = 0; i < n; i++) {
    const c = i % 5, row = Math.floor(i / 5);
    placeSimple('ottFurled', 82 + c * 14 + (r() - 0.5) * 4, 0.05, -78 + row * 15.5 + (r() - 0.5) * 4, (r() < 0.5 ? 0.15 : -0.15) + Math.PI * (r() < 0.75 ? 0 : 1) + (r() - 0.5) * 0.6);
  }
}

// ---------------------------------------------------------------- çekiş ekibi
// her gemi için: 2 halat, 6 asker, 2 çift öküz
function placeTeam(shipX, tIdx, t, wIdx, oIdx, sIdx, opts = {}) {
  const pose_ = pathPose(shipX);
  const bow = V(shipX + 6.6, pose_.y + 1.1, pose_.z);
  let wi = wIdx, oi = oIdx, si = sIdx;
  const phase = t * 5.5 + tIdx * 1.3;
  const frontX = shipX + 22;
  if (frontX > SHORE_E - 2 || shipX + 8 < SHORE_W + 1) return [wi, oi, si];
  for (const side of [-1, 1]) {
    const endX = shipX + 22.5, endZ = pz(endX) + side * 0.7;
    const end = V(endX, landHeight(endX, endZ) + 1.3, endZ);
    const startP = bow.clone().add(V(0, 0, side * 0.4));
    setStick(getStick(si++, ropeMat, 0.07), startP, end);
    // askerler
    for (let k = 0; k < 3; k++) {
      const x = shipX + 9.5 + k * 2.3 + (side > 0 ? 0.8 : 0), z = pz(x) + side * 1.35;
      const p = workers[wi++]; if (!p) continue;
      p.root.visible = true; p.root.position.set(x, landHeight(x, z), z);
      p.root.rotation.y = Math.atan2(-(pz(x + 1) - pz(x - 1)), 2);
      pose(p, { phase: phase + k * 0.9 + side, walk: 0.45, lean: 0.38, armF: 1.25, armSwing: 0.12, armUp: side * -0.25 });
    }
    // öküzler
    for (let k = 0; k < 2; k++) {
      const x = shipX + 17 + k * 3.2, z = pz(x) + side * 0.75;
      const o = oxen[oi++]; if (!o) continue;
      o.root.visible = true; o.root.position.set(x, landHeight(x, z), z);
      o.root.rotation.y = Math.atan2(-(pz(x + 1) - pz(x - 1)), 2);
      o.root.rotation.z = Math.atan2(landHeight(x + 1, z) - landHeight(x - 1, z), 2);
      poseOx(o, phase * 0.8 + k, 0.35);
    }
  }
  // boyunduruklar
  for (let k = 0; k < 2; k++) {
    const x = shipX + 18.1 + k * 3.2, y = landHeight(x, pz(x)) + 2.05;
    setStick(getStick(si++, yokeMat, 0.09), V(x, y, pz(x) - 1.2), V(x, y, pz(x) + 1.2));
  }
  return [wi, oi, si];
}

// ---------------------------------------------------------------- etiketler & altyazı
const labelsEl = document.getElementById('labels');
const labelEls = {};
function getLabel(text) {
  if (!labelEls[text]) {
    const d = document.createElement('div'); d.className = 'label';
    d.innerHTML = `<div class="line"></div><div class="dot"></div><div class="box">${text}</div>`;
    labelsEl.appendChild(d); labelEls[text] = d;
  }
  return labelEls[text];
}
const _v = new THREE.Vector3();
function showLabels(list) { // [{text, p: Vector3, a: opacity, len}]
  const used = new Set();
  for (const L of list) {
    const el = getLabel(L.text); used.add(L.text);
    _v.copy(L.p).project(camera);
    const sx = (_v.x * 0.5 + 0.5) * W, sy = (-_v.y * 0.5 + 0.5) * H;
    el.style.transform = `translate(${sx}px, ${sy}px)`;
    el.style.opacity = _v.z < 1 ? L.a : 0;
    el.style.setProperty('--len', (L.len || 150) + 'px');
    const bx = el.querySelector('.box'), bw = bx.offsetWidth;
    const left = clamp(sx - bw / 2, 40, W - 40 - bw) - sx;
    bx.style.left = left + 'px';
  }
  for (const k in labelEls) if (!used.has(k)) labelEls[k].style.opacity = 0;
}
const fadeIn = (t, t0, d = 0.35) => smooth(t0, t0 + d, t);
const fadeWin = (t, t0, t1, d = 0.3) => smooth(t0, t0 + d, t) * (1 - smooth(t1 - d, t1, t));

const SUBS = [
  [0.0, 2.9, 'Nisan, 1453.'],
  [3.0, 6.45, "Haliç'in ağzı dev bir zincirle kapatılmış."],
  [6.5, 8.8, 'Osmanlı donanması içeri giremiyor.'],
  [8.85, 12.3, "Fatih Sultan Mehmed'in çözümü akıl almaz:"],
  [12.3, 14.2, 'gemileri karadan yürütmek!'],
  [14.25, 18.85, 'Beşiktaş kıyısından tepeye, yağlanmış kütükler döşenir.'],
  [18.85, 21.8, 'Gemiler bu kızakların üstüne çekilir.'],
  [21.85, 24.4, 'Öküzler ve askerler halatlara asılır.'],
  [24.45, 28.95, 'Yelkenler açık, davullar çalarken gemiler tepeyi aşar'],
  [28.95, 31.6, "ve Kasımpaşa'dan Haliç'e kayar."],
  [31.65, 35.2, 'Sabah olduğunda Bizanslılar gözlerine inanamaz:'],
  [35.2, 38.15, 'yetmiş kadar gemi, zincirin arkasında.'],
  [38.15, 39.7, 'Hem de tek gecede.'],
  [39.75, 45.6, 'Ağır bir dolabı merdivenden çıkarmaya çalışan arkadaşına gönder.'],
];
const subEl = document.getElementById('sub'), titleEl = document.getElementById('title'), punchEl = document.getElementById('punch');
let lastSub = null;
function updateOverlay(t) {
  const s = SUBS.find(([a, b]) => t >= a && t < b);
  const txt = s ? s[2] : '';
  if (txt !== lastSub) { subEl.textContent = txt; lastSub = txt; }
  titleEl.style.opacity = fadeWin(t, 0.0, 6.3, 0.4) * (t < 0.05 ? 1 : 1);
  titleEl.style.transform = `scale(${1 + 0.03 * Math.sin(Math.min(t, 6) * 0.8)})`;
  punchEl.style.opacity = fadeWin(t, 38.1, 39.75, 0.15);
  punchEl.style.transform = `scale(${1.25 - 0.25 * ease(clamp((t - 38.1) / 0.25))})`;
}

// ---------------------------------------------------------------- çekimler
function camLook(pos, target) { camera.position.copy(pos); camera.lookAt(target); }
const crestTarget = V(0, 0, 0);

function hideActors() {
  for (const p of workers) p.root.visible = false;
  for (const p of soldiersByz) p.root.visible = false;
  for (const o of oxen) o.root.visible = false;
  for (const s of sticks) if (s) s.visible = false;
  for (const d of drums) d.visible = false;
  for (const b of buckets) b.visible = false;
  for (const l of carriedLogs) l.visible = false;
  setSplashes([]);
}

const SHOTS = [
  { // 1 — Haliç'in ağzı ve zincir
    t0: 0, t1: 6.45, tod: 'day', fn(t, k) {
      layoutByzBehindChain(); layoutOttomanAtChain(); layoutBosphorusFleet(16);
      setLogs(-999); setRoute(0); setTorches(false);
      const e = ease(k);
      camLook(lerpV(V(170, 85, -268), V(132, 28, -176), e), lerpV(V(108, 0, -95), V(110, 3, -104), e));
      aimSun(V(110, 0, -110), 140);
      return [
        { text: 'ZİNCİR', p: V(118, 1, -110), a: fadeIn(t, 3.3), len: 170 },
        { text: 'HALİÇ', p: V(112, 0, -45), a: fadeIn(t, 3.7), len: 110 },
      ];
    } },
  { // 2 — Osmanlı donanması dışarıda
    t0: 6.45, t1: 8.85, tod: 'day', fn(t, k) {
      layoutBosphorusFleet(26); layoutOttomanAtChain();
      setLogs(-999); setRoute(0); setTorches(false);
      const p1 = pathPose(-112);
      placeDetailed(-110, 0.05, -12, Math.PI / 2 - 0.1, 0, { sail: 0, oars: 'row', t, cradle: false });
      placeDetailed(-126, 0.05, 6, Math.PI / 2 + 0.15, 0, { sail: 0, oars: 'row', t, phase: 1.3 });
      const e = ease(k);
      camLook(lerpV(V(-86, 8, -48), V(-82, 11, -36), e), lerpV(V(-118, 3, 2), V(-120, 3, 8), e));
      aimSun(V(-115, 0, 0), 90);
      return [{ text: 'OSMANLI DONANMASI', p: V(-110, 6, -12), a: fadeIn(t, 6.8), len: 190 }];
    } },
  { // 3 — Harita: güzergah
    t0: 8.85, t1: 14.25, tod: 'day', fn(t, k) {
      layoutBosphorusFleet(26); layoutByzBehindChain(); layoutOttomanAtChain();
      setLogs(-999); setTorches(false);
      setRoute(ease(clamp((t - 10.3) / 3.6)));
      const e = ease(k);
      camLook(lerpV(V(-185, 230, 70), V(-165, 205, 52), e), V(12, 0, -14));
      aimSun(V(10, 0, -20), 220);
      return [
        { text: 'BEŞİKTAŞ', p: V(-74, 2, 4), a: fadeIn(t, 9.3), len: 120 },
        { text: 'KASIMPAŞA', p: V(76, 1, 3), a: fadeIn(t, 12.6), len: 120 },
        { text: 'ZİNCİR', p: V(128, 1, -110), a: fadeIn(t, 9.8), len: 90 },
      ];
    } },
  { // 4 — Gece: kütükler döşenip yağlanıyor
    t0: 14.25, t1: 18.85, tod: 'night', fn(t, k) {
      const xF = -69 + 25 * k;
      setLogs(xF); setRoute(0); setTorches(true, xF + 4, t);
      placeDetailed(-86, 0.05, pz(-86) + 2, -0.05, 0, { sail: 0, oars: 'up', t });
      let wi = 0;
      // log taşıyanlar
      for (let i = 0; i < 3; i++) {
        const p = workers[wi++], x = xF - 3 - i * 3.4, z = pz(x) + (i % 2 ? 2.8 : -2.8);
        p.root.visible = true; p.root.position.set(x, landHeight(x, z), z); p.root.rotation.y = 0;
        pose(p, { phase: t * 6 + i, walk: 0.5, lean: 0.12, armF: 0, armUp: 0, armSwing: 0 });
        p.armL.rotation.x = -2.6; p.armR.rotation.x = 2.6;
        const l = carriedLogs[i]; l.visible = true; l.position.set(x, landHeight(x, z) + 2.15, z); l.rotation.set(Math.PI / 2, 0, 0);
      }
      // yağlayanlar
      for (let i = 0; i < 2; i++) {
        const p = workers[wi++], x = xF - 6 - i * 5, z = pz(x) + (i ? -1.6 : 1.6);
        p.root.visible = true; p.root.position.set(x, landHeight(x, z), z); p.root.rotation.y = i ? Math.PI / 2 : -Math.PI / 2;
        pose(p, { phase: t * 7 + i * 2, walk: 0, lean: 0.75, armF: 0.9, armSwing: 0.35 });
        const b = buckets[i]; b.visible = true; b.position.set(x + 0.6, landHeight(x + 0.6, z) + 0.2, z + (i ? -0.8 : 0.8));
      }
      // kütüğü yerleştiren
      for (let i = 0; i < 2; i++) {
        const p = workers[wi++], x = xF + 0.3, z = pz(x) + (i ? -2.6 : 2.6);
        p.root.visible = true; p.root.position.set(x, landHeight(x, z), z); p.root.rotation.y = i ? Math.PI / 2 : -Math.PI / 2;
        pose(p, { lean: 0.6 + Math.sin(t * 3 + i) * 0.1, armF: 1.1 });
      }
      // izleyen/taşıyan diğer işçiler
      for (let i = 0; i < 6; i++) {
        const p = workers[wi++], x = xF - 14 - i * 4, z = pz(x) + (i % 2 ? 4.5 : -4.5);
        p.root.visible = true; p.root.position.set(x, landHeight(x, z), z); p.root.rotation.y = 0;
        pose(p, { phase: t * 6 + i, walk: 0.45, armSwing: 0.4 });
      }
      const e = ease(k);
      const tgt = V(xF - 4, landHeight(xF - 4, pz(xF - 4)) + 1, pz(xF - 4));
      camLook(lerpV(V(-84, 11, 26), V(-74, 12, 27), e), tgt);
      aimSun(tgt, 60);
      return [{ text: 'YAĞLANMIŞ KÜTÜKLER', p: V(-62, landHeight(-62, pz(-62)) + 0.5, pz(-62)), a: fadeIn(t, 16.9), len: 230 }];
    } },
  { // 5 — Gemi kızağa çekiliyor
    t0: 18.85, t1: 21.85, tod: 'night', fn(t, k) {
      setLogs(999); setRoute(0); setTorches(true, 999, t);
      const sx = lerp(-86, -71, ease(k));
      const pp = pathPose(sx);
      placeDetailed(pp.x, pp.y, pp.z, pp.yaw, pp.pitch, { sail: 0, oars: 'up', cradle: sx > -80, t });
      placeDetailed(-90, 0.05, pz(-90) - 12, 0.2, 0, { sail: 0, oars: 'row', t, phase: 2 });
      placeTeam(sx, 0, t, 0, 0, 0);
      const e = ease(k);
      camLook(lerpV(V(-86, 5.5, 19), V(-80, 7, 20), e), lerpV(V(-76, 2.5, 0), V(-66, 3.5, 0), e));
      aimSun(V(-70, 0, 0), 60);
      return [{ text: 'KIZAK', p: V(-73.5, 0.3, pz(-73.5)), a: fadeIn(t, 19.5), len: 150 }];
    } },
  { // 6 — Öküzler ve askerler halatlarda
    t0: 21.85, t1: 24.45, tod: 'night', fn(t, k) {
      setLogs(999); setRoute(0); setTorches(true, 999, t);
      const sx = lerp(-50, -44, k);
      const pp = pathPose(sx);
      placeDetailed(pp.x, pp.y, pp.z, pp.yaw, pp.pitch, { sail: 0, oars: 'up', cradle: true, t });
      placeTeam(sx, 0, t, 0, 0, 0);
      const cx = sx + 26;
      camLook(V(cx, landHeight(cx, pz(cx) + 16) + 6, pz(cx) + 16), V(sx + 9, landHeight(sx + 9, pz(sx + 9)) - 1.5, pz(sx + 9)));
      for (const g of torches) if (g.position.distanceTo(camera.position) < 14) g.visible = false;
      aimSun(V(sx + 10, 10, 0), 50);
      return [];
    } },
  { // 7 — Yelkenler açık, davullar, tepe aşılıyor
    t0: 24.45, t1: 28.95, tod: 'night', fn(t, k) {
      setLogs(999); setRoute(0); setTorches(true, 999, t);
      const lead = lerp(-10, 20, k);
      let wi = 0, oi = 0, si = 0;
      for (let i = 0; i < 6; i++) {
        const x = lead - i * 25; if (x < -70) break;
        const pp = pathPose(x);
        placeDetailed(pp.x, pp.y, pp.z, pp.yaw, pp.pitch, { sail: 1, oars: 'air', cradle: true, t, phase: i });
        [wi, oi, si] = placeTeam(x, i, t, wi, oi, si);
      }
      // davulcular
      for (let i = 0; i < 2; i++) {
        const x = 4 + i * 2.2, z = pz(x) + 9.5, p = workers[wi++];
        p.root.visible = true; p.root.position.set(x, landHeight(x, z), z); p.root.rotation.y = Math.PI / 2;
        pose(p, { armF: 1.0, armAlt: 0.6, phase: t * 9 + i });
        drums[i].visible = true; drums[i].position.set(x, landHeight(x, z) + 0.75, z - 0.6);
      }
      // seyreden askerler
      for (let i = 0; i < 8; i++) {
        const x = -30 + i * 8, z = pz(x) + (i % 2 ? 10 : -10), p = workers[wi++]; if (!p) break;
        p.root.visible = true; p.root.position.set(x, landHeight(x, z), z); p.root.rotation.y = (i % 2 ? 1 : -1) * Math.PI / 2;
        pose(p, { armUp: 0, armF: Math.sin(t * 5 + i) * 0.2 });
      }
      const ly = landHeight(lead, pz(lead));
      camLook(V(lead + 6, ly + 24, pz(lead) + 30), V(lead - 18, ly, pz(lead)));
      aimSun(V(lead - 15, 10, 0), 80);
      return [];
    } },
  { // 8 — Kasımpaşa'dan Haliç'e iniş
    t0: 28.95, t1: 31.65, tod: 'night', fn(t, k) {
      setLogs(999); setRoute(0); setTorches(true, 999, t);
      const lead = lerp(54, 86, k);
      const spl = [];
      let wi = 0;
      for (let i = 0; i < 4; i++) {
        const x = lead - i * 22; if (x < 0) break;
        const cx = Math.min(x, 120);
        let pp = pathPose(cx);
        if (cx > SHORE_E + 6) { pp = { x: cx, y: 0.05, z: pz(cx), yaw: 0, pitch: 0 }; }
        placeDetailed(pp.x, pp.y, pp.z, pp.yaw, pp.pitch, { sail: 1, oars: cx > SHORE_E + 4 ? 'row' : 'air', cradle: cx < SHORE_E + 4, t, phase: i });
        // gemi suya girdiği an
        const vx = 32 / (31.65 - 28.95);
        const tEnter = (SHORE_E + 3 - (54 - i * 22)) / vx;
        spl.push({ x: SHORE_E + 5, z: pz(SHORE_E + 5), age: (t - 28.95) - tEnter });
      }
      setSplashes(spl);
      for (let i = 0; i < 10; i++) {
        const x = 48 + i * 2.2, z = pz(x) + (i % 2 ? 6 : -6), p = workers[wi++];
        p.root.visible = true; p.root.position.set(x, landHeight(x, z), z); p.root.rotation.y = (i % 2 ? 1 : -1) * Math.PI / 2;
        pose(p, { armUp: 0, armF: 2.6 + Math.sin(t * 8 + i) * 0.35 });
      }
      const e = ease(k);
      camLook(lerpV(V(104, 6, 30), V(100, 7, 27), e), lerpV(V(62, 4, 1), V(76, 2, 1), e));
      aimSun(V(70, 0, 0), 70);
      return [{ text: 'HALİÇ', p: V(95, 0, -8), a: fadeIn(t, 29.8), len: 120 }];
    } },
  { // 9 — Şafak: Bizans surlarından bakış
    t0: 31.65, t1: 35.2, tod: 'dawn', fn(t, k) {
      layoutGoldenHornFleet(70); layoutByzBehindChain();
      setLogs(999); setRoute(0); setTorches(false);
      for (let i = 0; i < 7; i++) {
        const p = soldiersByz[i], z = -22 + i * 5.3, b = landHeight(154, z) + 8.6;
        p.root.visible = true; p.root.position.set(153.2, b, z); p.root.rotation.y = Math.PI;
        pose(p, { armF: i % 3 === 0 ? 2.4 : 0.1, armUp: 0 });
      }
      const e = ease(k);
      camLook(lerpV(V(160, 15.5, -32), V(158, 14.5, -24), e), lerpV(V(115, 4, 10), V(112, 3, 22), e));
      aimSun(V(120, 0, 0), 110);
      return [];
    } },
  { // 10 — Zincirin arkasında ~70 gemi
    t0: 35.2, t1: 39.75, tod: 'dawn', fn(t, k) {
      layoutGoldenHornFleet(70); layoutByzBehindChain(); layoutOttomanAtChain();
      setLogs(999); setRoute(0); setTorches(false);
      const e = ease(k);
      camLook(lerpV(V(114, 24, -158), V(114, 66, -196), e), V(112, 0, -40));
      aimSun(V(112, 0, -20), 160);
      return [
        { text: 'YETMİŞ KADAR GEMİ', p: V(112, 5, 10), a: fadeWin(t, 35.4, 38.1), len: 150 },
        { text: 'ZİNCİR', p: V(128, 1, -110), a: fadeWin(t, 36.7, 38.1), len: 110 },
      ];
    } },
  { // 11 — Kapanış: tüm sahne
    t0: 39.75, t1: 99, tod: 'dawn', fn(t, k) {
      layoutGoldenHornFleet(70); layoutByzBehindChain(); layoutBosphorusFleet(10);
      setLogs(999); setTorches(false);
      setRoute(1, 0.85);
      const kk = clamp((t - 39.75) / 5.85), a = lerp(-2.3, -1.95, kk);
      camLook(V(30 + Math.cos(a) * 230, 175 - 20 * kk, Math.sin(a) * 230), V(30, 0, -10));
      aimSun(V(30, 0, -10), 220);
      return [];
    } },
];

// ---------------------------------------------------------------- ana çizim
let lastShot = -1;
function renderFrame(t) {
  const si = SHOTS.findIndex(s => t >= s.t0 && t < s.t1);
  const shot = SHOTS[si < 0 ? SHOTS.length - 1 : si];
  if (shot.tod !== currentTOD) setTOD(shot.tod);
  resetShips(); hideActors();
  const k = clamp((t - shot.t0) / (Math.min(shot.t1, DURATION) - shot.t0));
  const labels = shot.fn(t, k) || [];
  sky.position.copy(camera.position);
  moon.position.copy(camera.position).add(V(-400, 520, -900));
  updateWater(t);
  renderer.render(scene, camera);
  showLabels(labels);
  updateOverlay(t);
  lastShot = si;
}
window.renderFrame = renderFrame;
window.DURATION = DURATION;
setTOD('day');
renderFrame(0);
window.ready = true;

// ---------------------------------------------------------------- önizleme modu
if (!RENDER_MODE) {
  const fit = () => { const s = Math.min(innerWidth / W, innerHeight / H); stage.style.transform = `scale(${s})`; stage.style.left = (innerWidth - W * s) / 2 + 'px'; };
  addEventListener('resize', fit); fit();
  const audio = new Audio('./audio/anlatim.mp3');
  const btn = document.createElement('button'); btn.id = 'play'; btn.textContent = '▶ Oynat'; document.body.appendChild(btn);
  let playing = false, start = 0;
  btn.onclick = () => { audio.currentTime = 0; audio.play().catch(() => {}); start = performance.now(); playing = true; btn.textContent = '↻ Baştan'; };
  const tick = () => {
    if (playing) { const t = (performance.now() - start) / 1000; if (t < DURATION) renderFrame(t); else playing = false; }
    requestAnimationFrame(tick);
  };
  tick();
}
