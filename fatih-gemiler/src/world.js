// Dünya: gökyüzü, ışık, arazi, deniz, yapılar, zincir, kızak kütükleri, meşaleler
import { Water } from 'three/addons/objects/Water.js';
import {
  THREE, mergeGeometries, scene, camera, renderer, bloom, grade, clamp, lerp, smooth, V, rng, fbm, noise2,
  MAT, MAT_DS, prep, M, box, cyl, cone, ico, sph, tor, mesh,
} from './core.js';

// ------------------------------------------------------------- coğrafya
// x: Boğaz (x<-71) -> Galata tepesi (tepe x≈0) -> Haliç (71<x<150) -> Suriçi (x>152). Haliç ağzı güneyde (z≈-110).
export function landHeight(x, z) {
  let h = -7;
  const hx = Math.max(0, 1 - (x / 74) ** 2);
  const hz = smooth(-114, -80, z);
  const n = (fbm(x * 0.03 + 3, z * 0.03) - 0.5) * 4 + (noise2(x * 0.12, z * 0.12) - 0.5) * 0.8;
  h = Math.max(h, (28 * Math.pow(hx, 1.2) + 1.5 + n * hx) * hz - 3);
  h = Math.max(h, smooth(147, 156, x) * (7 + Math.sin(z / 37) * 2 + Math.max(0, (x - 190) * 0.05)) - 3);
  h = Math.max(h, smooth(-182, -202, x) * (18 + Math.sin(z / 30) * 6 + (fbm(x * 0.02, z * 0.02) - 0.5) * 10) - 3);
  return h;
}
export const pz = x => 7 * Math.sin(x / 38);
export const SHORE_W = -71, SHORE_E = 71;
export const shipY = x => Math.max(0.1, landHeight(x, pz(x)) + 1.15);
export function pathPose(x) {
  const yb = shipY(x + 5.5), ys = shipY(x - 5.5), z = pz(x);
  const dz = pz(x + 1) - pz(x - 1);
  return { x, y: Math.max(shipY(x), (yb + ys) / 2), z, yaw: Math.atan2(-dz, 2), pitch: Math.atan2(yb - ys, 11) };
}
export const yawAt = x => Math.atan2(-(pz(x + 1) - pz(x - 1)), 2);

// ------------------------------------------------------------- gökyüzü (özel gradyan + güneş/ay diski)
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: {
    zenith: { value: new THREE.Color() }, horizon: { value: new THREE.Color() }, ground: { value: new THREE.Color() },
    sunColor: { value: new THREE.Color() }, sunDir: { value: V(0, 1, 0) }, sunSize: { value: 0.012 }, glow: { value: 1 }, stars: { value: 0 },
  },
  vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `
    uniform vec3 zenith, horizon, ground, sunColor, sunDir; uniform float sunSize, glow, stars; varying vec3 vP;
    float h21(vec2 p){ return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5); }
    void main(){
      vec3 d = normalize(vP); float h = d.y;
      vec3 col = mix(horizon, zenith, pow(clamp(h, 0.0, 1.0), 0.5));
      col = mix(col, ground, clamp(-h * 5.0, 0.0, 1.0));
      float s = max(dot(d, normalize(sunDir)), 0.0);
      col += sunColor * (pow(s, 6.0) * 0.25 + pow(s, 40.0) * 0.5) * glow;
      col += sunColor * smoothstep(1.0 - sunSize * 1.15, 1.0 - sunSize, s) * 6.0;
      if (stars > 0.0) {
        vec2 g = floor(vec2(atan(d.z, d.x) * 260.0, asin(clamp(d.y, -1.0, 1.0)) * 260.0));
        float r = h21(g);
        col += vec3(1.0, 0.97, 0.9) * step(0.9965, r) * stars * smoothstep(0.05, 0.3, h) * (0.6 + 0.8 * h21(g + 7.0));
      }
      gl_FragColor = vec4(col, 1.0);
    }`,
});
export const sky = new THREE.Mesh(new THREE.SphereGeometry(4000, 48, 24), skyMat);
sky.renderOrder = -10; sky.frustumCulled = false;
scene.add(sky);

// ------------------------------------------------------------- ışıklar
export const hemi = new THREE.HemisphereLight(0xffffff, 0x445533, 0.6);
scene.add(hemi);
export const sun = new THREE.DirectionalLight(0xffffff, 3);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.bias = -0.0003;
sun.shadow.normalBias = 0.05;
sun.shadow.radius = 3;
scene.add(sun, sun.target);
scene.fog = new THREE.FogExp2(0xffffff, 0.0016);

export const TOD = {
  sunset: { zen: 0x2f4e86, hor: 0xffa66b, gnd: 0x3b3a40, sunC: 0xffb070, dir: V(-0.85, 0.16, -0.5), sunI: 3.2, sunL: 0xffb27a, hemiS: 0x8aa0d0, hemiG: 0x5a4a3a, hemiI: 0.55, fog: 0xd9a487, fogD: 0.0019, exp: 1.0, stars: 0, size: 0.016,
            water: 0x1c4d63, grade: { sat: 1.12, con: 1.08, lift: [0.02, 0.0, 0.03], gain: [1.04, 0.98, 0.94] } },
  night:  { zen: 0x050b1d, hor: 0x1d3360, gnd: 0x080a10, sunC: 0xc8d6ff, dir: V(0.45, 0.55, -0.7), sunI: 1.0, sunL: 0x9fb6ff, hemiS: 0x4a6aaa, hemiG: 0x1a1d26, hemiI: 0.45, fog: 0x18284a, fogD: 0.0022, exp: 1.25, stars: 1, size: 0.02,
            water: 0x0a2236, grade: { sat: 0.95, con: 1.1, lift: [0.0, 0.015, 0.05], gain: [1.0, 1.0, 1.06] } },
  dawn:   { zen: 0x3d6cb3, hor: 0xffc48f, gnd: 0x3a3a3e, sunC: 0xffcf96, dir: V(0.9, 0.2, 0.35), sunI: 3.0, sunL: 0xffd2a0, hemiS: 0xb7c7e6, hemiG: 0x5d5446, hemiI: 0.65, fog: 0xf0c3a0, fogD: 0.0017, exp: 1.0, stars: 0, size: 0.014,
            water: 0x235a70, grade: { sat: 1.1, con: 1.05, lift: [0.01, 0.01, 0.03], gain: [1.03, 1.0, 0.96] } },
};
export let currentTOD = null;
const envCache = {};
const pmrem = new THREE.PMREMGenerator(renderer);
function envFor(name) {
  if (envCache[name]) return envCache[name];
  const s = new THREE.Scene();
  const sk = new THREE.Mesh(new THREE.SphereGeometry(100, 32, 16), skyMat.clone());
  sk.material.uniforms = THREE.UniformsUtils.clone(skyMat.uniforms);
  for (const k in skyMat.uniforms) { const v = skyMat.uniforms[k].value; sk.material.uniforms[k].value = v && v.clone ? v.clone() : v; }
  sk.material.uniforms.stars.value = 0;
  s.add(sk);
  envCache[name] = pmrem.fromScene(s, 0.04).texture;
  return envCache[name];
}
export function setTOD(name) {
  if (currentTOD === name) return;
  const p = TOD[name]; currentTOD = name;
  const u = skyMat.uniforms;
  u.zenith.value.set(p.zen); u.horizon.value.set(p.hor); u.ground.value.set(p.gnd);
  u.sunColor.value.set(p.sunC); u.sunDir.value.copy(p.dir).normalize(); u.stars.value = p.stars; u.sunSize.value = p.size;
  sun.color.set(p.sunL); sun.intensity = p.sunI;
  hemi.color.set(p.hemiS); hemi.groundColor.set(p.hemiG); hemi.intensity = p.hemiI;
  scene.fog.color.set(p.fog); scene.fog.density = p.fogD;
  renderer.toneMappingExposure = p.exp;
  scene.environment = envFor(name);
  water.material.uniforms.waterColor.value.set(p.water);
  water.material.uniforms.sunColor.value.set(p.sunL);
  water.material.uniforms.sunDirection.value.copy(p.dir).normalize();
  const g = grade.uniforms;
  g.saturation.value = p.grade.sat; g.contrast.value = p.grade.con;
  g.lift.value.set(...p.grade.lift); g.gain.value.set(...p.grade.gain);
  bloom.strength = name === 'night' ? 0.75 : 0.42;
  bloom.threshold = name === 'night' ? 0.75 : 0.92;
  for (const t of torches) t.visible = false;
}
export function aimSun(target, span = 120) {
  const p = TOD[currentTOD];
  sun.target.position.copy(target);
  sun.position.copy(target).addScaledVector(p.dir.clone().normalize(), 400);
  const c = sun.shadow.camera;
  c.left = -span; c.right = span; c.top = span; c.bottom = -span; c.near = 50; c.far = 900;
  c.updateProjectionMatrix();
}

// ------------------------------------------------------------- arazi
{
  const SIZE = 620, SEG = 230, CX = 20;
  const g = new THREE.PlaneGeometry(SIZE, SIZE, SEG, SEG).toNonIndexed();
  g.rotateX(-Math.PI / 2); g.translate(CX, 0, 0);
  const pos = g.attributes.position;
  for (let i = 0; i < pos.count; i++) pos.setY(i, landHeight(pos.getX(i), pos.getZ(i)));
  const col = new Float32Array(pos.count * 3), c = new THREE.Color(), r = rng(7);
  const SAND = new THREE.Color(0xd9c18c), FOAM = new THREE.Color(0xe9e4d3), G1 = new THREE.Color(0x8fb35a), G2 = new THREE.Color(0x5b8a3c), G3 = new THREE.Color(0x7a8f45),
    DRY = new THREE.Color(0xb2a467), STONE = new THREE.Color(0xc8b596), DEEP = new THREE.Color(0x40625e), DIRT = new THREE.Color(0x9b7d55), ROCK = new THREE.Color(0x8d877a);
  for (let i = 0; i < pos.count; i += 3) {
    const x = (pos.getX(i) + pos.getX(i + 1) + pos.getX(i + 2)) / 3, z = (pos.getZ(i) + pos.getZ(i + 1) + pos.getZ(i + 2)) / 3;
    const y = (pos.getY(i) + pos.getY(i + 1) + pos.getY(i + 2)) / 3;
    const ys = [pos.getY(i), pos.getY(i + 1), pos.getY(i + 2)], slope = Math.max(...ys) - Math.min(...ys);
    const n = fbm(x * 0.05, z * 0.05);
    if (y < -1.0) c.copy(DEEP).lerp(SAND, clamp((y + 4) / 3) * 0.5);
    else if (y < 0.15) c.copy(FOAM);
    else if (y < 1.0) c.copy(SAND);
    else if (x > 146) c.copy(STONE).multiplyScalar(0.92 + r() * 0.1);
    else {
      c.copy(G1).lerp(G2, clamp(y / 28 + (n - 0.5) * 0.8));
      if (n > 0.62) c.lerp(DRY, (n - 0.62) * 2.2);
      if (n < 0.32) c.lerp(G3, 0.4);
      if (slope > 2.2) c.lerp(ROCK, clamp((slope - 2.2) / 2));
      c.multiplyScalar(0.94 + r() * 0.08);
    }
    if (x > -72 && x < 72 && y > 0.2) {
      const dz = Math.abs(z - pz(x));
      if (dz < 4.6) c.copy(DIRT).multiplyScalar(0.88 + r() * 0.1);
      else if (dz < 6.5) c.lerp(DIRT, 0.45);
    }
    for (let k = 0; k < 3; k++) col.set([c.r, c.g, c.b], (i + k) * 3);
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.deleteAttribute('uv');
  g.computeVertexNormals();
  scene.add(mesh(g, MAT, false, true));
}

// ------------------------------------------------------------- deniz
const waterNormals = new THREE.TextureLoader().load('./assets/waternormals.jpg', t => { t.wrapS = t.wrapT = THREE.RepeatWrapping; });
waterNormals.wrapS = waterNormals.wrapT = THREE.RepeatWrapping;
export const water = new Water(new THREE.PlaneGeometry(4000, 4000), {
  textureWidth: 512, textureHeight: 512, waterNormals, sunDirection: V(0, 1, 0), sunColor: 0xffffff, waterColor: 0x1c4d63,
  distortionScale: 2.2, fog: true, alpha: 1.0,
});
water.rotation.x = -Math.PI / 2;
water.position.y = 0.0;
water.material.uniforms.size.value = 3.5;
scene.add(water);
export function updateWater(t) { water.material.uniforms.time.value = t * 0.6; }

// ------------------------------------------------------------- bitki örtüsü (instanced)
// kamera noktalarının çevresi boş bırakılır
const CLEAR = [[-16, pz(-16) - 13, 12], [1, pz(1) + 14.5, 9], [-58, pz(-58) + 8, 9], [-4, -34, 12], [58, -20, 12], [-75, pz(-75) - 3.4, 8], [-30, pz(-30) + 3, 6]];
const clear = (x, z) => CLEAR.some(([cx, cz, r]) => (x - cx) ** 2 + (z - cz) ** 2 < r * r);
{
  const r = rng(41);
  const N = 7000;
  const tuft = new THREE.InstancedMesh(new THREE.ConeGeometry(0.28, 0.9, 3), new THREE.MeshStandardMaterial({ flatShading: true, roughness: 0.9 }), N);
  const rock = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 0), new THREE.MeshStandardMaterial({ flatShading: true, roughness: 0.95 }), 500);
  const bush = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 0), new THREE.MeshStandardMaterial({ flatShading: true, roughness: 0.9 }), 900);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), c = new THREE.Color();
  let n = 0, nr = 0, nb = 0;
  for (let i = 0; i < N * 3 && n < N; i++) {
    const x = -70 + r() * 140, z = -90 + r() * 260, y = landHeight(x, z);
    if (y < 1.0) continue;
    if (x > -72 && x < 72 && Math.abs(z - pz(x)) < 5.2) continue;
    if (clear(x, z)) continue;
    const s = 0.6 + r() * 0.9;
    q.setFromEuler(new THREE.Euler((r() - 0.5) * 0.3, r() * 6, (r() - 0.5) * 0.3));
    m4.compose(V(x, y + 0.3 * s, z), q, V(s, s * (0.8 + r() * 0.6), s));
    tuft.setMatrixAt(n, m4); tuft.setColorAt(n, c.setHSL(0.22 + r() * 0.07, 0.45, 0.28 + r() * 0.12)); n++;
  }
  tuft.count = n;
  for (let i = 0; i < 3000 && nr < 500; i++) {
    const x = -72 + r() * 144, z = -95 + r() * 260, y = landHeight(x, z);
    if (y < -0.5 || y > 26) continue;
    if (x > -72 && x < 72 && Math.abs(z - pz(x)) < 6) continue;
    if (clear(x, z)) continue;
    const s = 0.3 + r() * r() * 1.8;
    q.setFromEuler(new THREE.Euler(r() * 3, r() * 3, r() * 3));
    m4.compose(V(x, y + s * 0.2, z), q, V(s, s * 0.7, s * 1.1));
    rock.setMatrixAt(nr, m4); rock.setColorAt(nr, c.setHSL(0.09, 0.08, 0.45 + r() * 0.15)); nr++;
  }
  rock.count = nr;
  for (let i = 0; i < 5000 && nb < 900; i++) {
    const x = -70 + r() * 140, z = -88 + r() * 250, y = landHeight(x, z);
    if (y < 1.2) continue;
    if (x > -72 && x < 72 && Math.abs(z - pz(x)) < 7.5) continue;
    if (x < -40 && z > pz(x) && z < 45 && Math.abs(z - pz(x)) < 16) continue;
    if (clear(x, z)) continue;
    const s = 0.6 + r() * 1.0;
    q.setFromEuler(new THREE.Euler(0, r() * 6, 0));
    m4.compose(V(x, y + s * 0.4, z), q, V(s * 1.3, s * 0.8, s * 1.2));
    bush.setMatrixAt(nb, m4); bush.setColorAt(nb, c.setHSL(0.25 + r() * 0.06, 0.45, 0.22 + r() * 0.1)); nb++;
  }
  bush.count = nb;
  for (const im of [tuft, rock, bush]) { im.castShadow = true; im.receiveShadow = true; scene.add(im); }
}

// ------------------------------------------------------------- statik yapılar
{
  const r = rng(11), parts = [];
  // --- Suriçi deniz surları
  for (let z = -150; z <= 172; z += 4) {
    const b = landHeight(154, z);
    parts.push(box(3.4, 10, 4.05, 0xcdbb9b, 154, b + 4, z));
    parts.push(box(3.6, 0.4, 4.1, 0xb7a585, 154, b + 9.2, z));
    if (Math.round(z / 4) % 2 === 0) parts.push(box(3.4, 1.4, 2.0, 0xcdbb9b, 154, b + 10, z));
    parts.push(box(0.2, 0.25, 4.05, 0x9e8c6e, 152.2, b + 3, z));
  }
  for (let z = -144; z <= 170; z += 24) {
    const b = landHeight(154, z);
    parts.push(box(8, 16, 8, 0xbca787, 154, b + 7, z));
    parts.push(box(8.6, 0.6, 8.6, 0xa8957a, 154, b + 15.2, z));
    for (const [dx, dz] of [[-3.6, -3.6], [-3.6, 0], [-3.6, 3.6], [3.6, -3.6], [3.6, 3.6], [0, -3.6], [0, 3.6]]) parts.push(box(1.4, 1.4, 1.4, 0xbca787, 154 + dx, b + 16.2, z + dz));
    for (const dy of [5, 10]) parts.push(box(0.3, 1.4, 0.7, 0x2b2420, 149.9, b + dy, z));
    // sancak
    parts.push(cyl(0.08, 0.08, 4, 4, 0x3a2a1a, M(154, b + 18, z)));
    parts.push(box(0.05, 1.4, 2.2, (z / 24) % 2 ? 0x6a2c86 : 0xc8a236, 154, b + 19.2, z + 1.1));
  }
  // --- Suriçi evleri
  for (let i = 0; i < 620; i++) {
    const x = 160 + r() * 115, z = -150 + r() * 320;
    if (Math.hypot(x - 215, z + 80) < 30) continue;
    const b = landHeight(x, z), w = 4 + r() * 4, d = 4 + r() * 4, h = 3.5 + r() * 5;
    const wall = [0xf2e8d5, 0xe9dcc3, 0xf5efe3, 0xdccbb0, 0xe8d2b0][Math.floor(r() * 5)];
    const roof = [0xc0573a, 0xb44a30, 0xcf6a45, 0xa8452e][Math.floor(r() * 4)];
    const ry = Math.floor(r() * 4) * Math.PI / 2;
    parts.push(box(w, h, d, wall, x, b + h / 2 - 0.5, z, 0, ry));
    parts.push(cone(Math.max(w, d) * 0.76, 2.2, 4, roof, M(x, b + h + 0.6, z, 0, Math.PI / 4 + ry, 0, w / Math.max(w, d), 1, d / Math.max(w, d))));
    for (let k = 0; k < 2; k++) parts.push(box(0.7, 1.0, 0.1, 0x3a2e28, x - w / 4 + k * w / 2, b + h * 0.6, z - d / 2 - 0.05));
  }
  // --- Kubbeli bazilika (1453'te minaresiz)
  {
    const x = 215, z = -80, b = landHeight(x, z);
    parts.push(box(44, 18, 50, 0xe2c29c, x, b + 9, z));
    parts.push(box(48, 2, 54, 0xd2b08a, x, b + 18.5, z));
    parts.push(cyl(15, 15, 5, 32, 0xdcb991, M(x, b + 21.5, z)));
    for (let a = 0; a < 40; a++) parts.push(box(0.8, 2.2, 0.3, 0x3a2e28, x + Math.cos(a / 40 * Math.PI * 2) * 15.1, b + 21.5, z + Math.sin(a / 40 * Math.PI * 2) * 15.1, 0, -a / 40 * Math.PI * 2 + Math.PI / 2, 0));
    parts.push(prep(new THREE.SphereGeometry(14, 28, 12, 0, Math.PI * 2, 0, Math.PI / 2), 0x8e9ba4, M(x, b + 24, z, 0, 0, 0, 1, 0.62, 1)));
    for (const s of [-1, 1]) {
      parts.push(prep(new THREE.SphereGeometry(10, 20, 8, 0, Math.PI * 2, 0, Math.PI / 2), 0x8e9ba4, M(x, b + 19, z + s * 18, 0, 0, 0, 1, 0.55, 1)));
      parts.push(box(8, 30, 8, 0xd7b48c, x + 20, b + 12, z + s * 22));
    }
  }
  // --- Galata Kulesi + Ceneviz surları ve evleri
  {
    const x = 26, z = -58, b = landHeight(x, z);
    parts.push(cyl(3.6, 4.1, 24, 16, 0xc2b195, M(x, b + 11, z)));
    parts.push(cyl(4.5, 4.5, 1.4, 16, 0xa8977b, M(x, b + 23, z)));
    for (let a = 0; a < 16; a++) parts.push(box(0.9, 1.1, 0.9, 0xa8977b, x + Math.cos(a / 16 * 6.283) * 4.3, b + 24.2, z + Math.sin(a / 16 * 6.283) * 4.3));
    parts.push(cone(4.4, 8, 16, 0x5f7080, M(x, b + 28, z)));
    for (const dy of [6, 12, 18]) for (let a = 0; a < 4; a++) parts.push(box(0.4, 1.4, 0.8, 0x2a221e, x + Math.cos(a * 1.57) * 3.9, b + dy, z + Math.sin(a * 1.57) * 3.9, 0, -a * 1.57, 0));
    // Ceneviz surları (tepeden kıyıya)
    for (let i = 0; i < 26; i++) {
      const wx = x + (i - 13) * 3.2, wz = z - 8 + Math.sin(i * 0.35) * 3, wb = landHeight(wx, wz);
      if (wb < 0.5) continue;
      parts.push(box(3.3, 5, 1.4, 0xc4b394, wx, wb + 2, wz));
      if (i % 2) parts.push(box(1.2, 1, 1.4, 0xc4b394, wx, wb + 5, wz));
    }
    for (let i = 0; i < 110; i++) {
      const hx = -12 + r() * 80, hz = -96 + r() * 36;
      if (Math.hypot(hx - x, hz - z) < 7) continue;
      const hb = landHeight(hx, hz); if (hb < 1) continue;
      const w = 3 + r() * 3, h = 3 + r() * 3.5, ry = r() * 0.6;
      parts.push(box(w, h, w * (0.8 + r() * 0.4), [0xf0e6d2, 0xe6d5b8, 0xf4ede0][Math.floor(r() * 3)], hx, hb + h / 2 - 0.5, hz, 0, ry));
      parts.push(cone(w * 0.78, 2, 4, [0xbf5a3d, 0xb04c33][Math.floor(r() * 2)], M(hx, hb + h + 0.5, hz, 0, Math.PI / 4 + ry, 0)));
    }
  }
  // --- Ağaçlar
  for (let i = 0; i < 420; i++) {
    const x = -68 + r() * 136, z = -78 + r() * 240;
    const b = landHeight(x, z);
    if (b < 1.6) continue;
    if (Math.abs(z - pz(x)) < 16) continue;
    if (x < -40 && z > pz(x) && z < 48) continue;
    if (z < -48 && x > -20 && x < 72) continue;
    if (clear(x, z)) continue;
    const t = r();
    if (t < 0.4) { // servi
      const h = 8 + r() * 6;
      parts.push(cyl(0.2, 0.3, 1.5, 5, 0x5b3d24, M(x, b + 0.7, z)));
      parts.push(cone(1.15, h * 0.65, 7, 0x2c5a33, M(x, b + 1.2 + h * 0.32, z)));
      parts.push(cone(0.85, h * 0.45, 7, 0x2f6237, M(x, b + 1.2 + h * 0.62, z)));
    } else if (t < 0.65) { // fıstık çamı
      const h = 6 + r() * 3;
      parts.push(cyl(0.25, 0.4, h, 6, 0x6b4a2e, M(x, b + h / 2, z, 0, 0, (r() - 0.5) * 0.2)));
      parts.push(ico(3.2 + r(), 0x3f6e33, M(x, b + h + 0.4, z, 0, r() * 3, 0, 1, 0.42, 1), 1));
    } else { // yuvarlak ağaç
      const h = 2 + r();
      parts.push(cyl(0.25, 0.35, h, 5, 0x6b4a2e, M(x, b + h / 2, z)));
      const gc = [0x4f8a3c, 0x5c9a45, 0x467d35, 0x6a9a3e][Math.floor(r() * 4)];
      parts.push(ico(2.1 + r(), gc, M(x, b + h + 1.6, z), 1));
      parts.push(ico(1.5 + r() * 0.6, gc, M(x + 1.2, b + h + 1.0, z + 0.6), 1));
    }
  }
  // --- Osmanlı ordugâhı (Beşiktaş kıyısı)
  for (let i = 0; i < 34; i++) {
    const x = -67 + r() * 14, z = 18 + r() * 56;
    const b = landHeight(x, z); if (b < 0.6) continue;
    const big = r() < 0.2, s = big ? 1.6 : 1;
    parts.push(cyl(2.2 * s, 2.2 * s, 1.6 * s, 10, 0xf4efe4, M(x, b + 0.8 * s, z)));
    parts.push(cone(2.5 * s, 2.4 * s, 10, i % 3 ? 0xf4efe4 : 0xc0392b, M(x, b + 2.8 * s, z)));
    parts.push(cyl(0.05, 0.05, 1.4, 4, 0x3a2a1a, M(x, b + 4.4 * s, z)));
    parts.push(box(0.05, 0.4, 0.7, 0xc0262d, x, b + 4.9 * s, z + 0.35));
  }
  const g = mergeGeometries(parts);
  scene.add(mesh(g, MAT, true, true));
}

// ------------------------------------------------------------- bulutlar
const clouds = new THREE.Group();
{
  const r = rng(91), cm = new THREE.MeshStandardMaterial({ color: 0xffffff, flatShading: true, roughness: 1, emissive: 0x222222, fog: false });
  for (let i = 0; i < 26; i++) {
    const parts = [];
    const n = 4 + Math.floor(r() * 5);
    for (let k = 0; k < n; k++) parts.push(prep(new THREE.IcosahedronGeometry(8 + r() * 10, 1), 0xffffff, M((k - n / 2) * 10 + r() * 6, r() * 5, r() * 8, 0, 0, 0, 1, 0.55, 0.8)));
    const m = new THREE.Mesh(mergeGeometries(parts), cm);
    const a = r() * Math.PI * 2, d = 500 + r() * 900;
    m.position.set(Math.cos(a) * d, 160 + r() * 140, Math.sin(a) * d);
    m.rotation.y = r() * 3;
    m.userData.v = 1 + r() * 2;
    clouds.add(m);
  }
  scene.add(clouds);
}
export function updateClouds(t) { clouds.children.forEach(c => { c.position.x += 0; c.rotation.y += 0; c.position.z = c.position.z; }); clouds.position.x = t * 2; clouds.visible = currentTOD !== 'night'; }

// ------------------------------------------------------------- zincir
{
  const parts = [], z0 = -110;
  for (let x = 72; x <= 150; x += 5) {
    parts.push(cyl(0.75, 0.75, 3.4, 10, 0x6a4529, M(x, 0.25, z0, 0, 0, Math.PI / 2)));
    parts.push(cyl(0.78, 0.78, 0.25, 10, 0x2e2a26, M(x - 1, 0.25, z0, 0, 0, Math.PI / 2)));
    parts.push(cyl(0.78, 0.78, 0.25, 10, 0x2e2a26, M(x + 1, 0.25, z0, 0, 0, Math.PI / 2)));
  }
  for (let x = 72; x <= 150; x += 0.7) {
    const sag = 0.25 + 0.25 * Math.sin(((x - 72) % 5) / 5 * Math.PI);
    parts.push(tor(0.32, 0.09, 0x26231f, M(x, 0.55 - sag * 0.6, z0, 0, 0, 0, 1, 1, 1).multiply(M(0, 0, 0, Math.round(x / 0.7) % 2 ? Math.PI / 2 : 0, Math.PI / 2, 0)), 4, 8));
  }
  // kıyı bağlantı kuleleri
  parts.push(box(6, 10, 6, 0xbca787, 70, 3, z0));
  parts.push(box(6, 12, 6, 0xbca787, 152, 4, z0));
  const m = mesh(mergeGeometries(parts));
  m.material = new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.5, metalness: 0.35, envMapIntensity: 1 });
  scene.add(m);
}
export const CHAIN_Z = -110;

// ------------------------------------------------------------- kızak kütükleri
export const logs = [];
{
  const g = new THREE.CylinderGeometry(0.24, 0.24, 5.2, 9);
  const m = new THREE.MeshStandardMaterial({ color: 0x7a4e2a, flatShading: true, roughness: 0.28, metalness: 0.05, envMapIntensity: 1.2 });
  for (let x = -74; x <= 74; x += 2.2) {
    const z = pz(x), dz = pz(x + 0.5) - pz(x - 0.5), y = landHeight(x, z);
    if (y < -0.4) continue;
    const lm = new THREE.Mesh(g, m);
    lm.castShadow = true; lm.receiveShadow = true;
    lm.position.set(x, y + 0.2, z);
    lm.rotation.order = 'YXZ'; lm.rotation.y = -Math.atan2(dz, 1); lm.rotation.x = Math.PI / 2;
    lm.userData.x = x;
    logs.push(lm); scene.add(lm);
  }
}
export function setLogs(maxX) { for (const l of logs) l.visible = l.userData.x <= maxX; }

// ------------------------------------------------------------- güzergah çizgisi
const routeCurve = new THREE.CatmullRomCurve3(Array.from({ length: 70 }, (_, i) => {
  const x = -90 + i * (180 / 69);
  return V(x, Math.max(0.8, landHeight(x, pz(x)) + 2.4), pz(x));
}));
const routeGeo = new THREE.TubeGeometry(routeCurve, 300, 1.25, 8, false);
const routeMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xff3b2f).multiplyScalar(2.2), transparent: true, fog: false });
const routeMesh = new THREE.Mesh(routeGeo, routeMat);
const arrowHead = new THREE.Mesh(new THREE.ConeGeometry(3.6, 8, 16), routeMat);
scene.add(routeMesh, arrowHead);
export function setRoute(k, opacity = 1) {
  routeMesh.visible = arrowHead.visible = k > 0.001;
  routeGeo.setDrawRange(0, Math.floor(routeGeo.index.count * k / 6) * 6);
  routeMat.opacity = opacity;
  const u = clamp(k, 0.001, 1), p = routeCurve.getPointAt(u), tg = routeCurve.getTangentAt(u);
  arrowHead.position.copy(p); arrowHead.quaternion.setFromUnitVectors(V(0, 1, 0), tg);
}

// ------------------------------------------------------------- ateş: meşaleler + kamp ateşleri
function glowTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d'), gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(255,240,200,1)'); gr.addColorStop(0.2, 'rgba(255,190,90,0.8)'); gr.addColorStop(0.5, 'rgba(255,110,20,0.25)'); gr.addColorStop(1, 'rgba(255,80,0,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function smokeTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(200,200,210,0.5)'); gr.addColorStop(1, 'rgba(200,200,210,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
export const fireTex = glowTexture();
const smokeTex = smokeTexture();
const flameMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffa030).multiplyScalar(3), fog: false });
const flameMat2 = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffe080).multiplyScalar(4), fog: false });
const flameGeo = new THREE.ConeGeometry(0.22, 0.8, 5);
export function makeFire(scale = 1) {
  const g = new THREE.Group();
  const flames = [];
  for (let i = 0; i < 3; i++) { const f = new THREE.Mesh(flameGeo, i ? flameMat : flameMat2); f.position.set((i - 1) * 0.12 * scale, 0.35 * scale, (i % 2 - 0.5) * 0.1 * scale); f.scale.setScalar(scale * (i ? 0.8 : 1)); g.add(f); flames.push(f); }
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: fireTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
  sp.scale.set(3.5 * scale, 3.5 * scale, 1); sp.position.y = 0.4 * scale; g.add(sp);
  g.userData = { flames, sp, scale, seed: Math.random() * 10 };
  return g;
}
export function animateFire(g, t) {
  const { flames, sp, scale, seed } = g.userData;
  flames.forEach((f, i) => { const k = 1 + Math.sin(t * 17 + seed + i * 2) * 0.18 + Math.sin(t * 9.3 + i) * 0.12; f.scale.set(scale * (i ? 0.8 : 1) * (2 - k) * 0.9, scale * (i ? 0.8 : 1) * k * 1.1, scale * (i ? 0.8 : 1)); });
  const s = 3.5 * scale * (1 + Math.sin(t * 13 + seed) * 0.08);
  sp.scale.set(s, s, 1);
}
export const torches = [];
for (let x = -66; x <= 66; x += 10) for (const s of [-1, 1]) {
  const z = pz(x) + s * 6.6, b = landHeight(x, z);
  if (b < 0.5) continue;
  const g = new THREE.Group();
  g.add(mesh(mergeGeometries([cyl(0.07, 0.1, 3.4, 6, 0x3e2818, M(0, 1.7, 0)), cyl(0.28, 0.14, 0.4, 6, 0x222222, M(0, 3.5, 0))])));
  const f = makeFire(0.8); f.position.y = 3.6; g.add(f);
  g.position.set(x, b, z); g.userData = { x, fire: f }; g.visible = false;
  scene.add(g); torches.push(g);
}
// kamp ateşleri + duman
const campfires = [];
{
  const r = rng(5);
  for (let i = 0; i < 6; i++) {
    const x = -64 + r() * 10, z = 22 + r() * 46, b = landHeight(x, z);
    if (b < 0.6) continue;
    const g = new THREE.Group();
    g.add(mesh(mergeGeometries([0, 1, 2, 3].map(k => cyl(0.12, 0.12, 1.6, 5, 0x3a2614, M(0, 0.15, 0, Math.PI / 2, k * 0.8, 0))))));
    const f = makeFire(1.4); f.position.y = 0.1; g.add(f);
    const smoke = [];
    for (let k = 0; k < 8; k++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: smokeTex, transparent: true, depthWrite: false })); g.add(s); smoke.push(s); }
    g.position.set(x, b, z); g.userData = { fire: f, smoke }; g.visible = false;
    scene.add(g); campfires.push(g);
  }
}
// meşalelerden gerçek ışık (en yakın 6 meşale)
const fireLights = Array.from({ length: 6 }, () => { const l = new THREE.PointLight(0xff9a40, 0, 22, 1.6); scene.add(l); return l; });
export function setFires(on, t, maxX = 999, focus = null) {
  const ref = focus || camera.position;
  const vis = [];
  for (const g of torches) {
    g.visible = on && g.userData.x <= maxX;
    if (g.visible) { animateFire(g.userData.fire, t); vis.push(g); }
  }
  for (const c of campfires) {
    c.visible = on;
    if (on) {
      animateFire(c.userData.fire, t);
      c.userData.smoke.forEach((s, k) => { const a = ((t * 0.25 + k / 8) % 1); s.position.set(Math.sin(k + t * 0.3) * 0.6 * a, 1 + a * 9, Math.cos(k) * 0.5 * a); const sc = 1.5 + a * 6; s.scale.set(sc, sc, 1); s.material.opacity = 0.35 * (1 - a) * Math.min(1, a * 5); });
    }
  }
  vis.sort((a, b) => a.position.distanceToSquared(ref) - b.position.distanceToSquared(ref));
  fireLights.forEach((l, i) => {
    const g = vis[i];
    if (g) { l.position.copy(g.position).add(V(0, 3.8, 0)); l.intensity = 24 * (1 + Math.sin(t * 15 + i) * 0.1); }
    else l.intensity = 0;
  });
}
