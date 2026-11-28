// Ortak: renderer, sahne, kamera, post-processing ve geometri yardımcıları
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';

export { THREE, mergeGeometries };
export const W = 1080, H = 1920;
const params = new URLSearchParams(location.search);
export const RENDER_MODE = params.has('render');
export const PIXEL_RATIO = parseFloat(params.get('pr') || '1');

// ------------------------------------------------------------- matematik
export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a, b, k) => a + (b - a) * k;
export const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const ease = k => k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
export const easeOut = k => 1 - Math.pow(1 - k, 3);
export const easeIn = k => k * k * k;
export const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
export const lerpV = (a, b, k) => a.clone().lerp(b, k);
export function rng(seed) { let s = (Math.imul(seed | 0, 2654435761) ^ 0x9e3779b9) >>> 0; for (let i = 0; i < 3; i++) s = (s * 1664525 + 1013904223) >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function hash(x, y) { const h = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return h - Math.floor(h); }
export function noise2(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  return lerp(lerp(hash(xi, yi), hash(xi + 1, yi), u), lerp(hash(xi, yi + 1), hash(xi + 1, yi + 1), u), v);
}
export const fbm = (x, y) => noise2(x, y) * 0.55 + noise2(x * 2.1, y * 2.1) * 0.3 + noise2(x * 4.3, y * 4.3) * 0.15;
// Kamera sarsıntısı için yumuşak gürültü
export const wobble = (t, s = 0) => Math.sin(t * 1.3 + s) * 0.5 + Math.sin(t * 2.7 + s * 1.7) * 0.3 + Math.sin(t * 5.1 + s * 2.3) * 0.2;

// ------------------------------------------------------------- malzemeler & geometri
export const MAT = new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.82, metalness: 0, envMapIntensity: 0.7 });
export const MAT_DS = new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.82, metalness: 0, envMapIntensity: 0.7, side: THREE.DoubleSide });
export const MAT_SMOOTH = new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: false, roughness: 0.75, metalness: 0, envMapIntensity: 0.7 });

export function prep(geo, color, m4) {
  let g = geo.index ? geo.toNonIndexed() : geo.clone();
  for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
  if (!g.attributes.normal) g.computeVertexNormals();
  if (m4) g.applyMatrix4(m4);
  const c = new THREE.Color(color), n = g.attributes.position.count, arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { arr[i * 3] = c.r; arr[i * 3 + 1] = c.g; arr[i * 3 + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(arr, 3));
  return g;
}
export function M(x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, sx = 1, sy = 1, sz = 1) {
  return new THREE.Matrix4().compose(V(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), V(sx, sy, sz));
}
export const box = (w, h, d, c, x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0) => prep(new THREE.BoxGeometry(w, h, d), c, M(x, y, z, rx, ry, rz));
export const cyl = (rt, rb, h, seg, c, m4) => prep(new THREE.CylinderGeometry(rt, rb, h, seg), c, m4);
export const cone = (r, h, seg, c, m4) => prep(new THREE.ConeGeometry(r, h, seg), c, m4);
export const ico = (r, c, m4, d = 0) => prep(new THREE.IcosahedronGeometry(r, d), c, m4);
export const sph = (r, c, m4, ws = 8, hs = 6) => prep(new THREE.SphereGeometry(r, ws, hs), c, m4);
export const tor = (r, t, c, m4, rs = 6, ts = 10) => prep(new THREE.TorusGeometry(r, t, rs, ts), c, m4);
export function tube(points, r, c, seg = 8, rad = 5) { return prep(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), seg, r, rad, false), c); }
export function triGeo(pts, colors) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pts.flatMap(p => [p.x, p.y, p.z]), 3));
  const cols = [];
  for (let i = 0; i < pts.length; i++) { const c = new THREE.Color(Array.isArray(colors) ? colors[Math.floor(i / 3) % colors.length] : colors); cols.push(c.r, c.g, c.b); }
  g.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
  g.computeVertexNormals();
  return g;
}
export function mesh(geo, mat = MAT, cast = true, recv = true) { const m = new THREE.Mesh(geo, mat); m.castShadow = cast; m.receiveShadow = recv; return m; }

// ------------------------------------------------------------- renderer
export const stage = document.getElementById('stage');
export const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(PIXEL_RATIO);
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
(stage || document.body).prepend(renderer.domElement);

export const scene = new THREE.Scene();
export const camera = new THREE.PerspectiveCamera(42, W / H, 0.3, 6000);

// ------------------------------------------------------------- post-processing
const rt = new THREE.WebGLRenderTarget(W * PIXEL_RATIO, H * PIXEL_RATIO, { type: THREE.HalfFloatType, samples: 4 });
export const composer = new EffectComposer(renderer, rt);
composer.setPixelRatio(PIXEL_RATIO);
composer.setSize(W, H);
composer.addPass(new RenderPass(scene, camera));
export const bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), 0.45, 0.55, 0.92);
composer.addPass(bloom);
composer.addPass(new OutputPass());
export const grade = new ShaderPass({
  uniforms: {
    tDiffuse: { value: null }, time: { value: 0 }, vignette: { value: 0.28 }, grain: { value: 0.014 },
    saturation: { value: 1.08 }, contrast: { value: 1.06 }, lift: { value: new THREE.Vector3(0, 0, 0) },
    gain: { value: new THREE.Vector3(1, 1, 1) }, ca: { value: 0.0015 }, fade: { value: 0 }, flash: { value: 0 },
  },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float time, vignette, grain, saturation, contrast, ca, fade, flash;
    uniform vec3 lift, gain; varying vec2 vUv;
    void main(){
      vec2 d = vUv - 0.5; float r2 = dot(d * vec2(0.75, 1.0), d * vec2(0.75, 1.0));
      vec2 off = d * ca * (0.3 + r2 * 2.0);
      vec3 col = vec3(texture2D(tDiffuse, vUv + off).r, texture2D(tDiffuse, vUv).g, texture2D(tDiffuse, vUv - off).b);
      float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
      col = mix(vec3(l), col, saturation);
      col = (col - 0.5) * contrast + 0.5;
      col = col * gain + lift * (1.0 - col);
      col *= 1.0 - vignette * smoothstep(0.06, 0.42, r2);
      float n = fract(sin(dot(vUv * vec2(1080.0, 1920.0) + fract(time * 7.13) * 91.7, vec2(12.9898, 78.233))) * 43758.5453);
      col += (n - 0.5) * grain;
      col = mix(col, vec3(0.0), fade);
      col = mix(col, vec3(1.0), flash);
      gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
    }`,
});
composer.addPass(grade);
