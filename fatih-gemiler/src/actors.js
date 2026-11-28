// Aktörler: kadırgalar, insanlar (eklemli), öküzler, Fatih ve atı, halatlar, su sıçraması
import {
  THREE, mergeGeometries, scene, clamp, lerp, V, rng, MAT, MAT_DS, prep, M, box, cyl, cone, ico, sph, tor, tube, mesh,
} from './core.js';
import { landHeight, pz, pathPose, yawAt, SHORE_W, SHORE_E, fireTex } from './world.js';

// =============================================================== KADIRGA
export const SHIP_L = 15, SHIP_B = 3.2;
const PAL = {
  ott: { hull: 0x6a4126, top: 0x3a2416, band: 0xa3281d, low: 0x40291a, deck: 0xb58a58, sailA: 0xf3ead6, sailB: 0xc7362b, awning: 0xb0241c, trim: 0xd9a63a, flag: 0xc0262d, flag2: 0x1f6b3a },
  byz: { hull: 0x4b3a2c, top: 0x2c2420, band: 0x3b3f7e, low: 0x2e241c, deck: 0x9c8466, sailA: 0x5b2f6b, sailB: 0x6e3a80, awning: 0x4a2c66, trim: 0xd2a63a, flag: 0xd4a62a, flag2: 0x6a2c86 },
};
const DECK_Y = 1.15;
function hullGeo(pal) {
  const L = SHIP_L, B = SHIP_B, S = 30;
  const prof = [[-1, 1], [-1.03, 0.82], [-0.97, 0.58], [-0.8, 0.32], [-0.46, 0.1], [0, 0], [0.46, 0.1], [0.8, 0.32], [0.97, 0.58], [1.03, 0.82], [1, 1]];
  const segCol = j => (j === 0 || j === 9) ? pal.top : (j === 1 || j === 8) ? pal.band : (j === 4 || j === 5) ? pal.low : pal.hull;
  const st = [];
  for (let i = 0; i <= S; i++) {
    const s = -1 + 2 * i / S, a = Math.abs(s);
    const hw = B / 2 * Math.pow(Math.max(0, 1 - Math.pow(a, 2.6)), 0.5) + 0.05;
    const deck = 1.25 + 1.1 * Math.pow(a, 5) + (s < 0 ? 0.35 * Math.pow(a, 3) : 0);
    const keel = -0.8 * (1 - Math.pow(a, 6)) + 0.6 * Math.pow(a, 6);
    st.push(prof.map(([px, py]) => V(s * L / 2, keel + (deck - keel) * py, px * hw)));
  }
  const P = [], C = [];
  const push = (pts, col) => { const c = new THREE.Color(col); for (const p of pts) { P.push(p.x, p.y, p.z); C.push(c.r, c.g, c.b); } };
  for (let i = 0; i < S; i++) for (let j = 0; j < prof.length - 1; j++) {
    const a = st[i][j], b = st[i + 1][j], c = st[i + 1][j + 1], d = st[i][j + 1];
    push([a, b, c, a, c, d], segCol(j));
  }
  for (let i = 0; i < S; i++) {
    const a = st[i][0].clone(), b = st[i + 1][0].clone(), c = st[i + 1][prof.length - 1].clone(), d = st[i][prof.length - 1].clone();
    for (const p of [a, b, c, d]) p.y -= 0.12;
    push([a, b, c, a, c, d], i % 2 ? pal.deck : 0xa67e50);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(C, 3));
  g.computeVertexNormals();
  return g;
}
// Latin yelkeni: seren A(alt-kıç) -> B(üst-baş), iskota köşesi C
const SAIL_A = V(-4.4, 3.0, 0.45), SAIL_B = V(6.8, 13.8, 0.45), SAIL_C = V(5.6, 2.7, 0.45);
const SN = 8, SM = 6;
function sailGeo(pal) {
  const P = [], Cc = [];
  for (let i = 0; i < SN; i++) for (let j = 0; j < SM; j++) {
    const col = new THREE.Color(i % 2 ? pal.sailB : pal.sailA);
    for (let k = 0; k < 6; k++) Cc.push(col.r, col.g, col.b);
    for (let k = 0; k < 18; k++) P.push(0);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(Cc, 3));
  setSail(g, 1, 0);
  return g;
}
const _Y = V(), _Y2 = V(), _q = [V(), V(), V(), V()];
function sailPoint(out, i, j, k, t) {
  _Y.lerpVectors(SAIL_A, SAIL_B, i / SN);
  const v = (j / SM) * k;
  out.lerpVectors(_Y, SAIL_C, v);
  const bil = Math.sin(Math.PI * i / SN) * Math.sin(Math.PI * Math.min(1, v * 1.05)) * 1.3 * k;
  out.z += bil + Math.sin(t * 3 + i * 0.7 + j) * 0.08 * k * (j / SM);
  return out;
}
function setSail(g, k, t) {
  const p = g.attributes.position.array; let o = 0;
  for (let i = 0; i < SN; i++) for (let j = 0; j < SM; j++) {
    const a = sailPoint(_q[0], i, j, k, t), b = sailPoint(_q[1], i + 1, j, k, t), c = sailPoint(_q[2], i + 1, j + 1, k, t), d = sailPoint(_q[3], i, j + 1, k, t);
    for (const q of [a, b, c, a, c, d]) { p[o++] = q.x; p[o++] = q.y; p[o++] = q.z; }
  }
  g.attributes.position.needsUpdate = true;
  g.computeVertexNormals();
}
function shipStatic(pal, { sail = false, oars = true, crew = true }) {
  const L = SHIP_L, B = SHIP_B, parts = [hullGeo(pal)];
  const AZ = B / 2 + 0.6;
  // apostis (kürek kızakları) ve çapraz kirişler
  for (const s of [-1, 1]) {
    parts.push(box(10.4, 0.16, 0.22, pal.top, 0.2, DECK_Y + 0.12, s * AZ));
    for (let x = -4.8; x <= 5.2; x += 1.25) parts.push(box(0.12, 0.12, 0.8, pal.top, x, DECK_Y + 0.05, s * (B / 2 + 0.22)));
    parts.push(box(10.2, 0.08, 0.06, pal.trim, 0.2, DECK_Y + 0.22, s * AZ));
  }
  parts.push(box(10.5, 0.12, 0.7, 0x8a6a44, 0.2, DECK_Y + 0.05, 0));                             // korsiya
  // pruva: mahmuz + rambade
  parts.push(cone(0.28, 3.4, 6, pal.top, M(L / 2 + 1.4, 1.05, 0, 0, 0, -Math.PI / 2 - 0.08)));
  parts.push(box(1.8, 0.35, 2.4, pal.top, L / 2 - 1.6, DECK_Y + 0.3, 0));
  // kıç: köşk + tente
  parts.push(box(3.2, 0.5, 2.6, pal.top, -L / 2 + 2.2, DECK_Y + 0.55, 0));
  for (const s of [-1, 1]) for (const x of [-L / 2 + 0.9, -L / 2 + 3.5]) parts.push(cyl(0.05, 0.05, 1.5, 5, pal.trim, M(x, DECK_Y + 1.4, s * 1.1)));
  parts.push(prep(new THREE.CylinderGeometry(1.25, 1.25, 3.0, 12, 1, true, 0, Math.PI), pal.awning, M(-L / 2 + 2.2, DECK_Y + 2.05, 0, 0, 0, Math.PI / 2).multiply(M(0, 0, 0, 0, Math.PI / 2, 0))));
  parts.push(box(3.1, 0.12, 2.6, pal.trim, -L / 2 + 2.2, DECK_Y + 2.1, 0));
  parts.push(cyl(0.07, 0.09, 2.6, 5, pal.top, M(-L / 2 + 0.25, DECK_Y + 2.0, 0, 0, 0, 0.35)));      // kıç direği (fener)
  // sancak
  parts.push(cyl(0.04, 0.04, 2.2, 4, 0x3a2a1a, M(-L / 2 + 3.4, DECK_Y + 3.3, 0)));
  parts.push(box(1.5, 0.9, 0.04, pal.flag, -L / 2 + 2.6, DECK_Y + 3.9, 0));
  // direk + seren
  parts.push(cyl(0.13, 0.2, 12.5, 7, 0x5a3b22, M(1.0, DECK_Y + 6.0, 0)));
  parts.push(box(0.5, 0.4, 0.5, 0x4a2f1a, 1.0, DECK_Y + 12.2, 0));
  if (sail) {
    const d = SAIL_B.clone().sub(SAIL_A), mid = SAIL_A.clone().add(SAIL_B).multiplyScalar(0.5);
    parts.push(cyl(0.08, 0.13, d.length() + 1, 6, 0x5a3b22, M(mid.x, mid.y, 0.35, 0, 0, Math.atan2(-d.x, d.y))));
  } else {
    parts.push(cyl(0.09, 0.12, 14, 6, 0x5a3b22, M(0.8, DECK_Y + 1.3, 0.75, 0, 0, Math.PI / 2 - 0.1)));
    parts.push(cyl(0.32, 0.32, 10, 7, pal.sailA, M(0.8, DECK_Y + 1.6, 0.75, 0, 0, Math.PI / 2 - 0.1)));
    for (let k = -4; k <= 4; k += 2) parts.push(cyl(0.34, 0.34, 0.15, 7, pal.sailB, M(0.8 + k * 0.99, DECK_Y + 1.6 + k * 0.1, 0.75, 0, 0, Math.PI / 2 - 0.1)));
  }
  if (oars) {
    for (let i = 0; i < 10; i++) for (const s of [-1, 1]) {
      const x = -4.6 + i * 1.08;
      parts.push(box(0.09, 0.09, 6.2, 0x7a5634, x, DECK_Y - 0.6, s * (AZ + 1.9), s * 0.5, 0, 0));
      parts.push(box(0.05, 0.42, 1.0, 0x7a5634, x, DECK_Y - 2.0, s * (AZ + 4.2), s * 0.5, 0, 0));
    }
  }
  if (crew) parts.push(...crewParts(pal));
  return parts;
}
function crewParts(pal) {
  const parts = [], shirts = [0xe8dcc0, 0xc0392b, 0x3d6b8f, 0xd9c7a0];
  for (let i = 0; i < 10; i++) for (const s of [-1, 1]) {
    const x = -4.4 + i * 1.08, z = s * (SHIP_B / 2 - 0.2), sh = shirts[(i + (s > 0 ? 1 : 0)) % 4];
    parts.push(box(0.36, 0.5, 0.32, sh, x, DECK_Y + 0.45, z, 0, 0, -0.25));
    parts.push(ico(0.15, 0xc98e65, M(x + 0.12, DECK_Y + 0.88, z), 0));
    parts.push(cyl(0.15, 0.15, 0.16, 6, 0xf4f1ea, M(x + 0.12, DECK_Y + 1.02, z)));
  }
  // kaptan ve leventler
  for (let k = 0; k < 4; k++) {
    const x = -SHIP_L / 2 + 1.6 + k * 0.8, z = (k % 2 - 0.5) * 1.2;
    parts.push(cyl(0.18, 0.26, 0.9, 6, k ? 0x7a2e2e : 0x1f6b3a, M(x, DECK_Y + 1.25, z)));
    parts.push(ico(0.16, 0xc98e65, M(x, DECK_Y + 1.85, z)));
    parts.push(sph(0.2, 0xf4f1ea, M(x, DECK_Y + 2.05, z, 0, 0, 0, 1, 0.8, 1)));
  }
  return parts;
}
function riggingGeo(withSail) {
  const top = V(1.0, DECK_Y + 12.2, 0), pts = [];
  const add = (a, b) => pts.push(a.x, a.y, a.z, b.x, b.y, b.z);
  add(top, V(SHIP_L / 2 - 0.5, DECK_Y + 0.5, 0));
  add(top, V(-SHIP_L / 2 + 0.6, DECK_Y + 1.3, 0));
  for (const s of [-1, 1]) for (const x of [-1.2, 0.2, 1.6]) add(top, V(x, DECK_Y + 0.2, s * (SHIP_B / 2 + 0.55)));
  if (withSail) { add(SAIL_A, V(-5.2, DECK_Y + 0.4, 0)); add(SAIL_C, V(5.4, DECK_Y + 0.4, 0.6)); add(SAIL_B, V(SHIP_L / 2, DECK_Y + 0.6, 0)); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3)); return g;
}
const RIG_MAT = new THREE.LineBasicMaterial({ color: 0x2a1d12 });
function pennantGeo(color) {
  const g = new THREE.PlaneGeometry(3.2, 0.5, 8, 1);
  g.translate(1.6, 0, 0);
  g.attributes.position.array.forEach((_, i, a) => { if (i % 3 === 1) { const x = a[i - 1]; a[i] *= 1 - x / 3.6; } });
  return prep(g, color);
}
const SIMPLE = {};
for (const side of ['ott', 'byz']) {
  SIMPLE[side + 'Furled'] = mergeGeometries([...shipStatic(PAL[side], { sail: false }), pennantGeo(PAL[side].flag2).applyMatrix4(M(1.0, DECK_Y + 12.5, 0))]);
  SIMPLE[side + 'Sail'] = mergeGeometries([...shipStatic(PAL[side], { sail: true }), sailGeo(PAL[side]), pennantGeo(PAL[side].flag2).applyMatrix4(M(1.0, DECK_Y + 12.5, 0))]);
}
const RIG_FURLED = riggingGeo(false), RIG_SAIL = riggingGeo(true);
const SIMPLE_POOL = [];
for (let i = 0; i < 140; i++) {
  const g = new THREE.Group(); g.rotation.order = 'YZX';
  const m = mesh(SIMPLE.ottFurled, MAT_DS, true, true);
  const r = new THREE.LineSegments(RIG_FURLED, RIG_MAT);
  g.add(m, r); g.userData = { m, r }; g.visible = false; scene.add(g); SIMPLE_POOL.push(g);
}
// detaylı (animasyonlu) kadırga
const OAR_GEO = mergeGeometries([box(0.09, 0.09, 6.6, 0x7a5634, 0, 0, 1.9), box(0.05, 0.5, 1.1, 0x7a5634, 0, 0, 4.9)]);
const CRADLE_GEO = mergeGeometries([
  box(SHIP_L * 0.82, 0.4, 0.45, 0x5e3d22, 0, -0.9, 1.0), box(SHIP_L * 0.82, 0.4, 0.45, 0x5e3d22, 0, -0.9, -1.0),
  ...[-4.5, -1.5, 1.5, 4.5].map(x => box(0.45, 0.7, 2.9, 0x5e3d22, x, -0.55, 0)),
  box(0.6, 0.3, 2.4, 0x5e3d22, SHIP_L * 0.41 + 0.2, -0.75, 0, 0, 0, 0.5),
]);
const LANTERN_MAT = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffc060).multiplyScalar(3) });
function makeDetailedShip() {
  const g = new THREE.Group(); g.rotation.order = 'YZX';
  const body = mesh(mergeGeometries(shipStatic(PAL.ott, { sail: true, oars: false })), MAT_DS);
  const sgeo = sailGeo(PAL.ott);
  const sail = mesh(sgeo, MAT_DS);
  const rig = new THREE.LineSegments(RIG_SAIL, RIG_MAT);
  const cradle = mesh(CRADLE_GEO);
  const pgeo = pennantGeo(PAL.ott.flag2); const pennant = mesh(pgeo, MAT_DS, false); pennant.position.set(1.0, DECK_Y + 12.5, 0);
  const pbase = pgeo.attributes.position.array.slice();
  const lantern = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.5, 0.35), LANTERN_MAT); lantern.position.set(-SHIP_L / 2 - 0.2, DECK_Y + 3.0, 0);
  const lglow = new THREE.Sprite(new THREE.SpriteMaterial({ map: fireTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })); lglow.scale.set(2.5, 2.5, 1); lantern.add(lglow);
  g.add(body, sail, rig, cradle, pennant, lantern);
  const oars = [];
  for (let i = 0; i < 10; i++) for (const s of [-1, 1]) {
    const piv = new THREE.Group(); piv.position.set(-4.6 + i * 1.08, DECK_Y + 0.15, s * (SHIP_B / 2 + 0.6));
    if (s < 0) piv.rotation.y = Math.PI;
    const o = mesh(OAR_GEO, MAT, true, false); o.rotation.order = "YXZ"; piv.add(o); g.add(piv);
    oars.push({ o, s, i });
  }
  g.visible = false; scene.add(g);
  return { g, sail, sgeo, cradle, oars, pgeo, pbase, lantern, sailK: -1 };
}
const DETAILED = Array.from({ length: 10 }, makeDetailedShip);
let si = 0, di = 0;
export function resetShips() { for (const s of SIMPLE_POOL) s.visible = false; for (const d of DETAILED) d.g.visible = false; si = 0; di = 0; }
export function placeSimple(kind, x, y, z, yaw, pitch = 0, roll = 0) {
  const s = SIMPLE_POOL[si++]; if (!s) return;
  s.userData.m.geometry = SIMPLE[kind];
  s.userData.r.geometry = kind.endsWith('Sail') ? RIG_SAIL : RIG_FURLED;
  s.position.set(x, y, z); s.rotation.set(roll, yaw, pitch); s.visible = true;
}
export function placeDetailed(x, y, z, yaw, pitch, o = {}) {
  const d = DETAILED[di++]; if (!d) return null;
  const t = o.t || 0, ph = o.phase || 0;
  d.g.visible = true; d.g.position.set(x, y + (o.bob ? Math.sin(t * 1.4 + ph) * 0.08 : 0), z);
  d.g.rotation.set((o.roll || 0) + (o.bob ? Math.sin(t * 1.1 + ph) * 0.02 : 0), yaw, pitch);
  const k = o.sail ?? 1;
  d.sail.visible = k > 0.02;
  if (k > 0.02) setSail(d.sgeo, k, t + ph);
  d.cradle.visible = !!o.cradle;
  d.lantern.visible = !!o.lantern;
  // flama dalgası
  const p = d.pgeo.attributes.position.array;
  for (let i = 0; i < p.length; i += 3) { const xx = d.pbase[i]; p[i + 2] = Math.sin(xx * 1.6 - t * 6 + ph) * 0.18 * xx / 3.2; }
  d.pgeo.attributes.position.needsUpdate = true;
  for (const { o: oar, s, i } of d.oars) {
    let sweep = 0, dip = 0.5;
    if (o.oars === 'row' || o.oars === 'air') {
      const a = t * 4.0 + ph + i * 0.04;
      sweep = Math.sin(a) * 0.42;
      dip = (o.oars === 'row' ? 0.46 : 0.02) + Math.cos(a) * 0.16;
    } else if (o.oars === 'up') dip = -0.35;
    oar.rotation.y = s > 0 ? sweep : -sweep;
    oar.rotation.x = dip;
  }
  return d;
}
export function placeOnPath(x, o = {}) { const p = pathPose(x); return placeDetailed(p.x, p.y, p.z, p.yaw, p.pitch, o); }

// =============================================================== İNSAN
const SKIN = [0xc98e65, 0xb97c55, 0xd9a07a];
function limb(parent, x, y, z) { const p = new THREE.Group(); p.position.set(x, y, z); parent.add(p); return p; }
export function makePerson(opt = {}) {
  const r = rng(opt.seed || 1);
  const skin = SKIN[Math.floor(r() * 3)];
  const robe = opt.robe ?? 0xc0392b, under = opt.under ?? 0xe6d8b8, pants = opt.pants ?? 0x3b3428, sash = opt.sash ?? 0xd9a63a;
  const root = new THREE.Group();
  const body = limb(root, 0, 0.95, 0);
  const torsoParts = [
    cyl(0.2, 0.17, 0.62, 8, robe, M(0, 0.31, 0, 0, 0, 0, 1, 1, 0.78)),
    cyl(0.18, 0.3, 0.6, 8, robe, M(0, -0.24, 0, 0, 0, 0, 1, 1, 0.85)),                      // kaftan eteği
    cyl(0.185, 0.185, 0.12, 8, sash, M(0, 0.02, 0, 0, 0, 0, 1, 1, 0.8)),                     // kuşak
    box(0.02, 0.5, 0.12, under, 0.155, 0.32, 0),                                               // iç gömlek
    cyl(0.07, 0.08, 0.1, 6, skin, M(0, 0.66, 0)),
  ];
  if (opt.fur) torsoParts.push(tor(0.17, 0.06, 0x6b4a2e, M(0, 0.6, 0, Math.PI / 2, 0, 0, 1, 0.8, 1)));
  body.add(mesh(mergeGeometries(torsoParts)));
  const head = limb(body, 0, 0.7, 0);
  const hp = [ico(0.15, skin, M(0, 0.14, 0), 1), box(0.06, 0.07, 0.05, skin, 0.15, 0.13, 0)];
  if (opt.beard !== false && r() < 0.75) hp.push(sph(0.12, opt.beardC ?? [0x2b1e16, 0x4a3324, 0x6b6b6b][Math.floor(r() * 3)], M(0.06, 0.04, 0, 0, 0, -0.3, 1, 0.9, 1), 7, 5));
  const hat = opt.hat || (r() < 0.7 ? 'turban' : 'bork');
  if (hat === 'turban') { hp.push(tor(0.12, 0.07, 0xf4f1ea, M(0, 0.25, 0, Math.PI / 2, 0, 0), 5, 9), sph(0.12, opt.cap ?? 0xc0392b, M(0, 0.29, 0, 0, 0, 0, 1, 0.8, 1), 7, 5)); }
  else if (hat === 'bork') { hp.push(cyl(0.13, 0.16, 0.42, 8, 0xf4f1ea, M(-0.02, 0.42, 0, 0, 0, 0.15)), box(0.1, 0.6, 0.24, 0xf4f1ea, -0.2, 0.3, 0, 0, 0, 0.5), box(0.06, 0.12, 0.08, 0xd9a63a, 0.1, 0.27, 0)); }
  else if (hat === 'kavuk') { hp.push(sph(0.22, 0xf7f3ea, M(0, 0.33, 0, 0, 0, 0, 1, 0.8, 1), 12, 8), cyl(0.09, 0.11, 0.14, 8, 0xa3281d, M(0, 0.52, 0))); }
  else if (hat === 'helmet') { hp.push(prep(new THREE.SphereGeometry(0.17, 8, 5, 0, Math.PI * 2, 0, Math.PI / 2), 0x9aa3ab, M(0, 0.18, 0)), cone(0.03, 0.2, 4, 0x9aa3ab, M(0, 0.4, 0)), box(0.25, 0.12, 0.04, 0xa8322a, -0.02, 0.42, 0)); }
  head.add(mesh(mergeGeometries(hp)));
  const mkArm = (s) => {
    const sh = limb(body, 0, 0.56, s * 0.25);
    sh.add(mesh(mergeGeometries([cyl(0.065, 0.06, 0.34, 6, robe, M(0, -0.16, 0))])));
    const el = limb(sh, 0, -0.32, 0);
    el.add(mesh(mergeGeometries([cyl(0.058, 0.05, 0.3, 6, robe, M(0, -0.14, 0)), sph(0.06, skin, M(0, -0.32, 0), 6, 4)])));
    return { sh, el };
  };
  const mkLeg = (s) => {
    const hip = limb(root, 0, 0.95, s * 0.1);
    hip.add(mesh(cyl(0.085, 0.07, 0.46, 6, pants, M(0, -0.23, 0))));
    const kn = limb(hip, 0, -0.46, 0);
    kn.add(mesh(mergeGeometries([cyl(0.068, 0.058, 0.44, 6, pants, M(0, -0.22, 0)), box(0.24, 0.08, 0.12, 0x3b2a1e, 0.05, -0.46, 0)])));
    return { hip, kn };
  };
  const p = { root, body, head, aL: mkArm(1), aR: mkArm(-1), lL: mkLeg(1), lR: mkLeg(-1) };
  root.visible = false; scene.add(root);
  return p;
}
// poz: yürüme fazı, eğilme, kollar
export function pose(p, o = {}) {
  const ph = o.phase || 0, w = o.walk || 0;
  p.lL.hip.rotation.z = Math.sin(ph) * w + (o.hip || 0);
  p.lR.hip.rotation.z = -Math.sin(ph) * w + (o.hip || 0);
  p.lL.kn.rotation.z = -(o.knee || 0) - w * 1.5 * Math.max(0, Math.sin(ph + 1.3));
  p.lR.kn.rotation.z = -(o.knee || 0) - w * 1.5 * Math.max(0, Math.sin(ph + 1.3 + Math.PI));
  p.lL.hip.rotation.x = o.spread || 0; p.lR.hip.rotation.x = -(o.spread || 0);
  p.body.rotation.z = -(o.lean || 0);
  p.body.position.y = 0.95 + Math.abs(Math.sin(ph)) * w * 0.08 - (o.crouch || 0);
  const swing = o.swing ?? w * 0.6;
  p.aL.sh.rotation.z = (o.shL ?? o.sh ?? 0) - Math.sin(ph) * swing + (o.altL || 0);
  p.aR.sh.rotation.z = (o.shR ?? o.sh ?? 0) + Math.sin(ph) * swing + (o.altR || 0);
  p.aL.el.rotation.z = o.elL ?? o.el ?? 0.15;
  p.aR.el.rotation.z = o.elR ?? o.el ?? 0.15;
  p.aL.sh.rotation.x = -(o.out || 0.08); p.aR.sh.rotation.x = (o.out || 0.08);
  p.head.rotation.y = o.look || 0;
  p.head.rotation.z = o.nod || 0;
}
export const P = {
  pull: (t, k = 0) => ({ phase: t * 3.2 + k, walk: 0.38, lean: 0.48, sh: 1.1, el: 1.2, swing: 0.05, knee: 0.15, nod: 0.25 }),
  walk: (t, k = 0) => ({ phase: t * 5 + k, walk: 0.45 }),
  carry: (t, k = 0) => ({ phase: t * 4.4 + k, walk: 0.4, shL: 2.4, shR: 2.4, elL: 1.1, elR: 1.1, swing: 0, lean: 0.08 }),
  grease: (t, k = 0) => ({ lean: 1.05, knee: 0.5, crouch: 0.15, hip: 0.5, shL: 0.5 + Math.sin(t * 6 + k) * 0.4, shR: 0.9 + Math.sin(t * 6 + k + 1) * 0.3, el: 0.4 }),
  drum: (t, k = 0) => ({ shL: 0.7, shR: 0.7, elL: 1.5 + Math.max(0, Math.sin(t * 9 + k)) * 0.8, elR: 1.5 + Math.max(0, Math.sin(t * 9 + k + Math.PI)) * 0.8, lean: 0.1 }),
  cheer: (t, k = 0) => ({ shL: 2.8 + Math.sin(t * 7 + k) * 0.25, shR: 2.6 + Math.sin(t * 7 + k + 1) * 0.25, elL: 0.3, elR: 0.3, out: 0.3, look: Math.sin(k) * 0.3 }),
  stand: (t, k = 0) => ({ sh: 0.05 + Math.sin(t * 1.3 + k) * 0.03, look: Math.sin(t * 0.7 + k) * 0.25 }),
  point: (t, k = 0) => ({ shR: 1.55, elR: 0.05, shL: 0.1, look: 0.1 }),
  ride: () => ({ hip: 1.35, knee: 1.3, spread: 0.35, sh: 0.55, el: 0.9, lean: -0.05 }),
  place: (t, k = 0) => ({ lean: 0.85, knee: 0.6, crouch: 0.2, hip: 0.6, sh: 1.3 + Math.sin(t * 3 + k) * 0.15, el: 0.3 }),
};
export function putPerson(p, x, z, yaw, pp, y = null) {
  p.root.visible = true; p.root.position.set(x, y ?? landHeight(x, z), z); p.root.rotation.set(0, yaw, 0); pose(p, pp);
}
const ROBES = [0xb03a2e, 0x2f5f8a, 0xc49a3a, 0x3f6b3a, 0x8e3b5a, 0xd8c7a0, 0x7a4a2a];
export const workers = [];
{ const r = rng(3); for (let i = 0; i < 110; i++) workers.push(makePerson({ seed: i + 10, robe: ROBES[Math.floor(r() * ROBES.length)], sash: [0xd9a63a, 0xc0392b, 0xf0e6d0][Math.floor(r() * 3)], pants: [0x3b3428, 0x4a3a2a, 0x2f3d4f][Math.floor(r() * 3)], cap: [0xc0392b, 0x2f6b3a, 0xd9a63a][Math.floor(r() * 3)] })); }
export const byzSoldiers = [];
for (let i = 0; i < 12; i++) byzSoldiers.push(makePerson({ seed: 300 + i, robe: i % 2 ? 0x5a3c7a : 0x2e4f8a, sash: 0x8a8f96, pants: 0x3a3030, hat: 'helmet' }));
export const fatih = makePerson({ seed: 999, robe: 0xa3281d, under: 0xd9a63a, sash: 0xd9a63a, hat: 'kavuk', fur: true, beard: true, beardC: 0x3a2618, pants: 0x2a2a2a });

// =============================================================== ÖKÜZ
export function makeOx(color, seed = 1) {
  const r = rng(seed);
  const root = new THREE.Group();
  const dark = new THREE.Color(color).multiplyScalar(0.7).getHex();
  const patch = r() < 0.3 ? 0xe9e0cc : color;
  const bodyParts = [
    sph(1, color, M(0, 1.45, 0, 0, 0, 0, 1.25, 0.6, 0.56), 12, 8),
    sph(0.62, color, M(0.75, 1.62, 0, 0, 0, 0, 1, 1, 0.92), 10, 7),                 // omuz/hörgüç
    sph(0.55, patch, M(-0.85, 1.5, 0, 0, 0, 0, 1, 1, 1), 10, 7),                    // sağrı
    sph(0.4, dark, M(1.05, 1.05, 0, 0, 0, 0, 0.8, 1, 0.6), 8, 5),                   // gerdan
    cyl(0.3, 0.4, 0.8, 8, color, M(1.35, 1.55, 0, 0, 0, -1.0)),                     // boyun
  ];
  root.add(mesh(mergeGeometries(bodyParts)));
  const head = limb(root, 1.62, 1.55, 0);
  head.add(mesh(mergeGeometries([
    box(0.62, 0.42, 0.42, color, 0.25, 0, 0, 0, 0, -0.35), box(0.3, 0.3, 0.36, 0xc9a38a, 0.55, -0.16, 0, 0, 0, -0.35),
    tube([V(0.05, 0.2, 0.16), V(0.0, 0.35, 0.45), V(0.15, 0.6, 0.62)], 0.05, 0xe9e2cf, 6, 4),
    tube([V(0.05, 0.2, -0.16), V(0.0, 0.35, -0.45), V(0.15, 0.6, -0.62)], 0.05, 0xe9e2cf, 6, 4),
    box(0.08, 0.14, 0.26, dark, 0.02, 0.1, 0.3, 0.6, 0, 0), box(0.08, 0.14, 0.26, dark, 0.02, 0.1, -0.3, -0.6, 0, 0),
  ])));
  const legs = [];
  for (const [x, z] of [[0.75, 0.3], [0.75, -0.3], [-0.8, 0.3], [-0.8, -0.3]]) {
    const up = limb(root, x, 1.15, z); up.add(mesh(cyl(0.15, 0.11, 0.55, 6, color, M(0, -0.27, 0))));
    const lo = limb(up, 0, -0.55, 0); lo.add(mesh(mergeGeometries([cyl(0.09, 0.08, 0.5, 6, color, M(0, -0.25, 0)), cyl(0.1, 0.11, 0.1, 6, 0x2a2420, M(0, -0.52, 0))])));
    legs.push({ up, lo });
  }
  const tail = limb(root, -1.25, 1.65, 0);
  tail.add(mesh(mergeGeometries([cyl(0.03, 0.04, 0.9, 4, color, M(0, -0.45, 0)), sph(0.08, dark, M(0, -0.95, 0, 0, 0, 0, 0.8, 1.6, 0.8), 5, 4)])));
  root.visible = false; scene.add(root);
  return { root, legs, head, tail };
}
export function poseOx(o, ph, walk, t = 0) {
  o.legs.forEach((l, i) => {
    const a = ph + (i === 0 || i === 3 ? 0 : Math.PI);
    l.up.rotation.z = Math.sin(a) * walk;
    l.lo.rotation.z = -Math.max(0, Math.sin(a + 1.2)) * walk * 1.4;
  });
  o.head.rotation.z = -0.25 + Math.sin(ph * 2) * 0.05 * (walk > 0 ? 1 : 0);
  o.tail.rotation.x = Math.sin(t * 2.5 + ph) * 0.25;
  o.root.position.y += Math.abs(Math.sin(ph)) * walk * 0.05;
}
export const oxen = [];
for (let i = 0; i < 44; i++) oxen.push(makeOx([0x8a6440, 0xa07a52, 0x7a5a3c, 0xb8956a, 0x6e5038][i % 5], 50 + i));
export function putOx(o, x, z, yaw, ph, walk, t) {
  o.root.visible = true; o.root.position.set(x, landHeight(x, z), z);
  o.root.rotation.set(0, yaw, Math.atan2(landHeight(x + 1, z) - landHeight(x - 1, z), 2) * 0.8);
  poseOx(o, ph, walk, t);
}

// =============================================================== AT (Fatih'in atı)
export const horse = (() => {
  const c = 0xe8e4dc, d = 0xb9b2a6, root = new THREE.Group();
  root.add(mesh(mergeGeometries([
    sph(1, c, M(0, 1.55, 0, 0, 0, 0, 1.15, 0.5, 0.42), 12, 8),
    sph(0.5, c, M(0.7, 1.6, 0, 0, 0, 0, 1, 1, 0.85), 10, 6), sph(0.5, c, M(-0.75, 1.62, 0, 0, 0, 0, 1, 1, 0.9), 10, 6),
    cyl(0.22, 0.36, 1.1, 8, c, M(1.15, 2.1, 0, 0, 0, -0.65)),
    box(1.0, 0.12, 0.08, 0x3a3530, 1.1, 2.35, 0, 0, 0, -0.65),                                       // yele
    box(1.1, 0.12, 1.0, 0xa3281d, 0, 2.06, 0), box(1.15, 0.05, 1.05, 0xd9a63a, 0, 2.0, 0),          // eyer örtüsü
  ])));
  const head = limb(root, 1.5, 2.55, 0);
  head.add(mesh(mergeGeometries([box(0.75, 0.3, 0.3, c, 0.25, -0.1, 0, 0, 0, -0.9), box(0.1, 0.18, 0.06, d, -0.05, 0.18, 0.09), box(0.1, 0.18, 0.06, d, -0.05, 0.18, -0.09)])));
  const legs = [];
  for (const [x, z] of [[0.7, 0.22], [0.7, -0.22], [-0.75, 0.22], [-0.75, -0.22]]) {
    const up = limb(root, x, 1.3, z); up.add(mesh(cyl(0.11, 0.08, 0.6, 6, c, M(0, -0.3, 0))));
    const lo = limb(up, 0, -0.6, 0); lo.add(mesh(mergeGeometries([cyl(0.06, 0.06, 0.6, 6, c, M(0, -0.3, 0)), cyl(0.08, 0.09, 0.12, 6, 0x2a2420, M(0, -0.62, 0))])));
    legs.push({ up, lo });
  }
  const tail = limb(root, -1.15, 1.75, 0); tail.add(mesh(cone(0.14, 1.1, 6, 0x3a3530, M(0, -0.5, 0, Math.PI, 0, 0))));
  root.visible = false; scene.add(root);
  return { root, legs, head, tail };
})();
export function putFatih(x, z, yaw, t, walk = 0, y = null) {
  const gy = y ?? landHeight(x, z);
  horse.root.visible = true; horse.root.position.set(x, gy, z); horse.root.rotation.set(0, yaw, 0);
  horse.legs.forEach((l, i) => { const a = t * 4 + (i === 0 || i === 3 ? 0 : Math.PI); l.up.rotation.z = Math.sin(a) * walk + (walk ? 0 : (i < 2 ? 0.05 : -0.05)); l.lo.rotation.z = -Math.max(0, Math.sin(a + 1.2)) * walk * 1.2; });
  horse.head.rotation.z = Math.sin(t * 1.3) * 0.08; horse.tail.rotation.x = Math.sin(t * 2) * 0.15;
  putPerson(fatih, x - 0.05, z, yaw, P.ride(), gy + 1.18);
  fatih.root.position.x = x + Math.cos(yaw) * 0.05; fatih.root.position.z = z - Math.sin(yaw) * 0.05;
}

// =============================================================== HALAT & ÇUBUK
const STICK = new THREE.CylinderGeometry(1, 1, 1, 6);
const ropeMat = new THREE.MeshStandardMaterial({ color: 0xc9ab72, roughness: 1, flatShading: true });
const woodMat = new THREE.MeshStandardMaterial({ color: 0x5e3d22, roughness: 1, flatShading: true });
const sticks = [];
let sti = 0;
const _u = V(0, 1, 0);
function stick(a, b, r, mat) {
  let s = sticks[sti++];
  if (!s) { s = new THREE.Mesh(STICK, mat); s.castShadow = true; scene.add(s); sticks.push(s); }
  s.material = mat; s.visible = true;
  const d = b.clone().sub(a), len = d.length();
  s.position.copy(a).addScaledVector(d, 0.5); s.quaternion.setFromUnitVectors(_u, d.normalize()); s.scale.set(r, len, r);
}
export function rope(a, b, sag = 0.4, r = 0.055) {
  const N = 5; let prev = a;
  for (let i = 1; i <= N; i++) {
    const k = i / N, p = a.clone().lerp(b, k); p.y -= Math.sin(Math.PI * k) * sag;
    stick(prev, p, r, ropeMat); prev = p;
  }
}
export function beam(a, b, r = 0.09) { stick(a, b, r, woodMat); }

// aksesuarlar
const accessories = [];
function acc(geo) { const m = mesh(geo); m.visible = false; scene.add(m); accessories.push(m); return m; }
export const drums = [0, 1, 2].map(() => acc(mergeGeometries([cyl(0.5, 0.5, 0.65, 12, 0xa3281d), cyl(0.52, 0.52, 0.05, 12, 0xf1e6cc, M(0, 0.34, 0)), cyl(0.52, 0.52, 0.05, 12, 0xf1e6cc, M(0, -0.34, 0)), cyl(0.53, 0.53, 0.06, 12, 0xd9a63a)])));
export const buckets = [0, 1].map(() => acc(mergeGeometries([cyl(0.25, 0.2, 0.42, 8, 0x5b4632), cyl(0.22, 0.22, 0.02, 8, 0x2a1a10, M(0, 0.2, 0))])));
export const carriedLogs = [0, 1, 2].map(() => acc(prep(new THREE.CylinderGeometry(0.3, 0.3, 5.0, 8), 0x8a5a30)));

// =============================================================== SU SIÇRAMASI
const SPN = 160;
const splashMesh = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(0.32, 0), new THREE.MeshStandardMaterial({ color: 0xf2f6f8, flatShading: true, roughness: 0.4, emissive: 0x334455 }), SPN);
splashMesh.frustumCulled = false; scene.add(splashMesh);
const foamMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, depthWrite: false });
const foamRings = [0, 1, 2, 3].map(() => { const m = new THREE.Mesh(new THREE.RingGeometry(0.8, 1.3, 32), foamMat.clone()); m.rotation.x = -Math.PI / 2; m.visible = false; scene.add(m); return m; });
const seeds = Array.from({ length: SPN }, (_, i) => { const r = rng(100 + i); return [r() * Math.PI * 2, 5 + r() * 9, 2 + r() * 6, 0.4 + r() * 1.0]; });
const _m4 = new THREE.Matrix4(), _qq = new THREE.Quaternion(), _s = V();
export function setSplashes(list) {
  let n = 0;
  foamRings.forEach(f => f.visible = false);
  list.forEach((sp, si2) => {
    if (sp.age < 0 || sp.age > 2.5) return;
    const fr = foamRings[si2]; if (fr) { fr.visible = true; fr.position.set(sp.x, 0.08, sp.z); const s = 2 + sp.age * 7; fr.scale.set(s, s, 1); fr.material.opacity = Math.max(0, 0.7 * (1 - sp.age / 2.5)); }
    for (let i = 0; i < SPN / 2 && n < SPN; i++) {
      const [ang, vy, vr, sz] = seeds[(i * 2 + si2) % SPN];
      const a = sp.age, y = vy * a - 9.8 * a * a / 2;
      if (y < -0.3) continue;
      const k = Math.max(0, 1 - a / 1.8) * sz;
      _m4.compose(V(sp.x + Math.cos(ang) * vr * a * 1.4, Math.max(0, y), sp.z + Math.sin(ang) * vr * a), _qq, _s.set(k, k, k));
      splashMesh.setMatrixAt(n++, _m4);
    }
  });
  splashMesh.count = n; splashMesh.instanceMatrix.needsUpdate = true;
}

// =============================================================== SIFIRLAMA
export function hideActors() {
  resetShips();
  for (const p of workers) p.root.visible = false;
  for (const p of byzSoldiers) p.root.visible = false;
  fatih.root.visible = false; horse.root.visible = false;
  for (const o of oxen) o.root.visible = false;
  for (let i = 0; i < sticks.length; i++) sticks[i].visible = false;
  sti = 0;
  for (const a of accessories) a.visible = false;
  setSplashes([]);
}

// =============================================================== ÇEKİŞ EKİBİ
// Geminin önünde: 2 halat, her halatta 4 asker, 2 çift öküz + boyunduruk
export function placeTeam(shipX, idx, t, w0, o0) {
  let wi = w0, oi = o0;
  const pp = pathPose(shipX);
  if (shipX + 24 > SHORE_E - 1 || shipX + 8 < SHORE_W + 1) return [wi, oi];
  const yaw = yawAt(shipX + 12);
  const bow = V(shipX + 7.2 * Math.cos(pp.pitch), pp.y + 1.25 + 7.2 * Math.sin(pp.pitch), pp.z);
  for (const side of [-1, 1]) {
    const endX = shipX + 24.5, endZ = pz(endX) + side * 0.75, end = V(endX, landHeight(endX, endZ) + 1.5, endZ);
    rope(bow.clone().add(V(0, 0, side * 0.35)), end, 0.15);
    for (let k = 0; k < 4; k++) {
      const x = shipX + 9.6 + k * 2.1 + (side > 0 ? 0.7 : 0), z = pz(x) + side * 1.25;
      const p = workers[wi++]; if (!p) continue;
      putPerson(p, x, z, yaw, P.pull(t, k * 0.9 + side + idx));
    }
    for (let k = 0; k < 2; k++) {
      const x = shipX + 18.6 + k * 3.4, z = pz(x) + side * 0.72, o = oxen[oi++]; if (!o) continue;
      putOx(o, x, z, yaw, t * 2.6 + k + idx + (side > 0 ? 0.5 : 0), 0.32, t);
    }
  }
  for (let k = 0; k < 2; k++) {
    const x = shipX + 20.1 + k * 3.4, y = landHeight(x, pz(x)) + 2.25;
    beam(V(x, y, pz(x) - 1.3), V(x, y, pz(x) + 1.3), 0.1);
  }
  // sürücü
  const dv = workers[wi++]; if (dv) { const x = shipX + 21, z = pz(x) - 2.6; putPerson(dv, x, z, yaw + 0.3, { ...P.walk(t, idx), shR: 2.2 + Math.sin(t * 4) * 0.4, elR: 0.3 }); }
  return [wi, oi];
}
