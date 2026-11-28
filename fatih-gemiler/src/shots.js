// Çekimler: anlatımın kelime zamanlarına bağlı kurgu
import { THREE, camera, grade, clamp, lerp, smooth, ease, easeOut, V, lerpV, rng, wobble } from './core.js';
import {
  landHeight, pz, pathPose, yawAt, SHORE_E, CHAIN_Z, setTOD, aimSun, setLogs, setRoute, setFires, logs,
} from './world.js';
import {
  placeSimple, placeDetailed, placeOnPath, workers, byzSoldiers, putPerson, P, oxen, putOx, putFatih, placeTeam,
  drums, buckets, carriedLogs, setSplashes, rope, SHIP_L,
} from './actors.js';

// ------------------------------------------------------------- kamera yardımcısı
function cam(pos, tgt, fov = 42, shake = 0, t = 0) {
  camera.position.copy(pos);
  if (shake) camera.position.add(V(wobble(t, 1) * shake, wobble(t, 2) * shake * 0.7, wobble(t, 3) * shake));
  const tg = tgt.clone();
  if (shake) tg.add(V(wobble(t * 0.8, 4) * shake * 0.6, wobble(t * 0.8, 5) * shake * 0.6, 0));
  camera.lookAt(tg);
  if (camera.fov !== fov) { camera.fov = fov; camera.updateProjectionMatrix(); }
}
const gy = (x, z) => landHeight(x, z);
const py = x => landHeight(x, pz(x));

// ------------------------------------------------------------- filo yerleşimleri
function bosphorusFleet(n = 26) {
  const r = rng(21);
  for (let i = 0; i < n; i++) { const c = i % 4, row = Math.floor(i / 4); placeSimple('ottFurled', -100 - c * 16 - r() * 4, 0.05, -58 + row * 18 + r() * 5, Math.PI / 2 + (r() - 0.5) * 0.5); }
}
const CHAIN_OTT_X = [78, 89, 99, 125, 135, 146];
function ottomanAtChain(skip = -1) { CHAIN_OTT_X.forEach((x, i) => { if (i !== skip) placeSimple('ottSail', x, 0.05, -152 - (i % 2) * 9, -Math.PI / 2 + (i - 3) * 0.05); }); }
function byzBehindChain() { for (let i = 0; i < 6; i++) placeSimple(i % 2 ? 'byzFurled' : 'byzSail', 84 + i * 12, 0.05, -95 + (i % 2) * 7, Math.PI / 2 + (i - 2.5) * 0.05); }
function goldenHornFleet(n = 70) {
  const r = rng(77);
  for (let i = 0; i < n; i++) {
    const c = i % 5, row = Math.floor(i / 5);
    placeSimple('ottFurled', 82 + c * 14 + (r() - 0.5) * 4, 0.05, -76 + row * 15.5 + (r() - 0.5) * 4, (r() < 0.5 ? 0.15 : -0.15) + Math.PI * (r() < 0.75 ? 0 : 1) + (r() - 0.5) * 0.6);
  }
}

// ------------------------------------------------------------- çekim tanımları
// w: çekimin başladığı kelimenin indeksi (etiket yönergesinden sonraki ilk kelime = 0)
export const SHOT_DEFS = [
  { w: 0, id: 'A', tod: 'sunset' },
  { w: 2, id: 'B', tod: 'sunset' },
  { w: 8, id: 'C', tod: 'sunset' },
  { w: 12, id: 'D', tod: 'sunset' },
  { w: 18, id: 'E', tod: 'sunset', flash: true },
  { w: 21, id: 'F', tod: 'night', fade: true },
  { w: 27, id: 'G', tod: 'night' },
  { w: 32, id: 'H1', tod: 'night' },
  { w: 35, id: 'H2', tod: 'night' },
  { w: 37, id: 'I', tod: 'night' },
  { w: 41, id: 'J', tod: 'night', flash: true },
  { w: 44, id: 'K', tod: 'night' },
  { w: 48, id: 'L', tod: 'dawn', fade: true },
  { w: 53, id: 'M', tod: 'dawn' },
  { w: 58, id: 'N', tod: 'dawn', flash: true },
  { w: 62, id: 'O', tod: 'dawn' },
];

export function buildTimeline(words, offset, tail) {
  const shots = SHOT_DEFS.map((d, i) => ({ ...d, t0: i === 0 ? 0 : words[d.w].start + offset - 0.12 }));
  const end = words[words.length - 1].end + offset + tail;
  shots.forEach((s, i) => { s.t1 = i < shots.length - 1 ? shots[i + 1].t0 : end; });
  return { shots, end, wt: i => words[i].start + offset };
}

// Etiket: {text, p, a, len}
const fadeIn = (t, t0, d = 0.25) => smooth(t0, t0 + d, t);

export const SHOT_FN = {
  A(t, k, lt, W) { // Haliç ağzına alçak uçuş
    byzBehindChain(); ottomanAtChain(); bosphorusFleet(14);
    setLogs(-999); setRoute(0); setFires(false, t);
    const e = easeOut(k);
    cam(lerpV(V(113, 3.2, -215), V(112, 8.5, -150), e), lerpV(V(110, 4, -110), V(108, 2, -100), e), 40, 0.15, t);
    aimSun(V(110, 0, -130), 110);
    return [];
  },
  B(t, k, lt, W) { // zincir yakın plan
    byzBehindChain(); ottomanAtChain();
    setLogs(-999); setRoute(0); setFires(false, t);
    const e = ease(k);
    const x = lerp(78, 96, e);
    cam(V(x, 2.4, CHAIN_Z - 5.5), V(x + 14, 0.6, CHAIN_Z + 1), 38, 0.08, t);
    aimSun(V(x + 10, 0, CHAIN_Z), 50);
    return [{ text: 'ZİNCİR', p: V(x + 9, 0.8, CHAIN_Z), a: fadeIn(t, W(6) - 0.1), len: 260 }];
  },
  C(t, k, lt, W) { // Osmanlı kadırgaları zincirin önünde
    byzBehindChain(); ottomanAtChain(3);
    setLogs(-999); setRoute(0); setFires(false, t);
    const zz = lerp(-150, -138, easeOut(k));
    placeDetailed(112, 0.05, zz, -Math.PI / 2, 0, { sail: 0.0, oars: k < 0.7 ? 'row' : 'hold', t, bob: true });
    placeDetailed(127, 0.05, zz - 14, -Math.PI / 2 - 0.08, 0, { sail: 1, oars: 'row', t, phase: 1.3, bob: true });
    const e = ease(k);
    cam(lerpV(V(104, 1.7, -121), V(103, 2.3, -124), e), lerpV(V(114, 3.5, -140), V(115, 3.5, -142), e), 40, 0.12, t);
    aimSun(V(112, 0, -140), 60);
    return [{ text: 'OSMANLI DONANMASI', p: V(112, 5, zz), a: fadeIn(t, W(8) + 0.1), len: 170 }];
  },
  D(t, k, lt, W) { // Fatih tepede, gün batımı
    goldenHornFleet(0); byzBehindChain(); bosphorusFleet(10);
    setLogs(-999); setRoute(0); setFires(false, t);
    const fx = -4, fz = -34;
    putFatih(fx, fz, -0.35, t, 0);
    let wi = 0;
    for (let i = 0; i < 4; i++) { const p = workers[wi++]; const x = fx - 2.5 - (i % 2) * 1.5, z = fz + (i < 2 ? 2.5 : -2.5); putPerson(p, x, z, -0.35, P.stand(t, i)); }
    const a = lerp(2.6, 2.15, ease(k)), R = 10.5;
    const c = V(fx + Math.cos(a) * R, gy(fx, fz) + 2.4, fz + Math.sin(a) * R);
    cam(c, V(fx, gy(fx, fz) + 1.9, fz), 38, 0.05, t);
    aimSun(V(fx, gy(fx, fz), fz), 25);
    return [{ text: 'FATİH SULTAN MEHMED', p: V(fx, gy(fx, fz) + 3.9, fz), a: fadeIn(t, W(12)), len: 120 }];
  },
  E(t, k, lt, W) { // harita
    bosphorusFleet(26); byzBehindChain(); ottomanAtChain();
    setLogs(-999); setFires(false, t);
    setRoute(ease(clamp((t - W(18)) / (W(20) + 0.6 - W(18)))));
    const e = ease(k);
    cam(lerpV(V(-180, 225, 70), V(-160, 200, 52), e), V(12, 0, -12), 42, 0, t);
    aimSun(V(10, 0, -20), 210);
    return [
      { text: 'BEŞİKTAŞ', p: V(-73, 2, pz(-73)), a: fadeIn(t, W(18) - 0.1), len: 110 },
      { text: 'KASIMPAŞA', p: V(76, 1, pz(76)), a: fadeIn(t, W(20)), len: 110 },
    ];
  },
  F(t, k, lt, W) { // kütükler döşeniyor, yağlanıyor
    const xF = -70 + 21 * k;
    setLogs(xF); setRoute(0); setFires(true, t, xF + 3);
    placeDetailed(-88, 0.05, pz(-88) + 1, -0.05, 0, { sail: 0, oars: 'up', t, bob: true, lantern: true });
    let wi = 0;
    for (let i = 0; i < 3; i++) {
      const p = workers[wi++], x = xF - 3.5 - i * 3.6, z = pz(x) + (i % 2 ? 3.1 : -3.1);
      putPerson(p, x, z, 0, P.carry(t, i));
      const l = carriedLogs[i]; l.visible = true; l.position.set(x + 0.1, gy(x, z) + 1.95, z); l.rotation.set(Math.PI / 2, 0, 0);
    }
    for (let i = 0; i < 2; i++) {
      const p = workers[wi++], x = xF - 7 - i * 5, z = pz(x) + (i ? -1.8 : 1.8);
      putPerson(p, x, z, i ? Math.PI / 2 : -Math.PI / 2, P.grease(t, i * 2));
      const b = buckets[i]; b.visible = true; b.position.set(x + 0.6, gy(x + 0.6, z) + 0.21, z + (i ? -0.7 : 0.7));
    }
    for (let i = 0; i < 2; i++) { const p = workers[wi++], x = xF + 0.4, z = pz(x) + (i ? -2.4 : 2.4); putPerson(p, x, z, i ? Math.PI / 2 : -Math.PI / 2, P.place(t, i)); }
    for (let i = 0; i < 6; i++) { const p = workers[wi++], x = xF - 14 - i * 4, z = pz(x) + (i % 2 ? 5 : -5); putPerson(p, x, z, 0, P.walk(t, i)); }
    const e = ease(k);
    const cx = lerp(-86, -80, e), cz = pz(cx) - 13;
    cam(V(cx, Math.max(gy(cx, cz), 0) + 7.5, cz), V(xF - 6, py(xF - 6) + 0.4, pz(xF - 6)), 40, 0.1, t);
    aimSun(V(xF - 6, 0, 0), 40);
    return [{ text: 'YAĞLANMIŞ KÜTÜKLER', p: V(xF - 8, py(xF - 8) + 0.5, pz(xF - 8)), a: fadeIn(t, W(24)), len: 230 }];
  },
  G(t, k, lt, W) { // gemi kızağa çekiliyor
    setLogs(999); setRoute(0); setFires(true, t);
    const sx = lerp(-86, -72, ease(k));
    placeOnPath(sx, { sail: 0, oars: 'up', cradle: sx > -82, t, lantern: true });
    placeDetailed(-92, 0.05, pz(-92) - 13, 0.25, 0, { sail: 0, oars: 'row', t, phase: 2, bob: true, lantern: true });
    placeTeam(sx, 0, t, 0, 0);
    const e = ease(k);
    const c = lerpV(V(-58, 0, pz(-58) + 8), V(-57, 0, pz(-57) + 7), e); c.y = gy(c.x, c.z) + 2.6;
    cam(c, V(lerp(-74, -68, e), 2.2, pz(-70)), 40, 0.12, t);
    aimSun(V(-68, 0, 0), 45);
    return [{ text: 'KIZAK', p: V(sx + 2, py(sx + 2) + 0.2, pz(sx + 2)), a: fadeIn(t, W(29)), len: 200 }];
  },
  H1(t, k, lt, W) { // öküzler yakın
    setLogs(999); setRoute(0); setFires(true, t);
    const sx = lerp(-52, -49.5, k);
    placeOnPath(sx, { sail: 0, oars: 'up', cradle: true, t, lantern: true });
    placeTeam(sx, 0, t, 0, 0);
    const x = sx + lerp(31, 29, k), z = pz(x) + 6.5;
    cam(V(x, gy(x, z) + 2.4, z), V(sx + 18, py(sx + 18) + 1.0, pz(sx + 18)), 36, 0.1, t);
    aimSun(V(sx + 18, 0, 0), 25);
    return [];
  },
  H2(t, k, lt, W) { // askerler halatta
    setLogs(999); setRoute(0); setFires(true, t);
    const sx = lerp(-49.5, -47, k);
    placeOnPath(sx, { sail: 0, oars: 'up', cradle: true, t, lantern: true });
    placeTeam(sx, 0, t, 0, 0);
    const x = sx + 15, z = pz(x) + 7.5;
    cam(V(x, gy(x, z) + 3.2, z), V(sx + 9, py(sx + 9) + 1.2, pz(sx + 9)), 38, 0.1, t);
    aimSun(V(sx + 12, 0, 0), 25);
    return [];
  },
  I(t, k, lt, W) { // yelken açılıyor, davullar
    setLogs(999); setRoute(0); setFires(true, t);
    const lead = lerp(-15, -9, k);
    let wi = 0, oi = 0;
    for (let i = 0; i < 3; i++) {
      const x = lead - i * 26; if (x < -70) break;
      placeOnPath(x, { sail: i === 0 ? easeOut(clamp(k * 1.3)) : 1, oars: 'air', cradle: true, t, phase: i, lantern: true });
      [wi, oi] = placeTeam(x, i, t, wi, oi);
    }
    for (let i = 0; i < 3; i++) {
      const x = -1 + i * 1.6, z = pz(x) + 10.5, p = workers[wi++];
      putPerson(p, x, z, Math.PI / 2, P.drum(t, i));
      drums[i].visible = true; drums[i].position.set(x, gy(x, z) + 0.9, z - 0.65); drums[i].rotation.set(0.25, 0, 0);
    }
    const e = ease(k);
    const cx = lerp(2.5, 1.0, e), cz = pz(cx) + 15.5;
    cam(V(cx, gy(cx, cz) + 2.6, cz), V(lead + 1, py(lead) + 3.5, pz(lead)), 42, 0.1, t);
    aimSun(V(lead, 0, 0), 45);
    return [];
  },
  J(t, k, lt, W) { // tepeyi aşan gemi, ay önünde
    setLogs(999); setRoute(0); setFires(true, t);
    const lead = lerp(-3, 7, k);
    let wi = 0, oi = 0;
    for (let i = 0; i < 3; i++) {
      const x = lead - i * 26; if (x < -70) break;
      placeOnPath(x, { sail: 1, oars: 'air', cradle: true, t, phase: i, lantern: true });
      [wi, oi] = placeTeam(x, i, t, wi, oi);
    }
    const c = V(-16, 0, pz(-16) - 13); c.y = gy(c.x, c.z) + 2.2;
    cam(lerpV(c, c.clone().add(V(1.5, 0.8, 0)), ease(k)), V(lead + 4, py(lead) + 6.5, pz(lead)), 44, 0.1, t);
    aimSun(V(lead, 0, 0), 50);
    return [];
  },
  K(t, k, lt, W) { // Haliç'e iniş + sıçrama
    setLogs(999); setRoute(0); setFires(true, t);
    const x0 = 56, x1 = 86, lead = lerp(x0, x1, k), dur = (this.t1 - this.t0);
    const spl = [];
    for (let i = 0; i < 3; i++) {
      const x = lead - i * 24; if (x < 25) break;
      const pp = pathPose(x);
      const wet = x > SHORE_E + 4;
      if (wet) placeDetailed(x, 0.05, pz(x), yawAt(x), 0, { sail: 1, oars: 'row', t, phase: i, bob: true, lantern: true });
      else placeDetailed(pp.x, pp.y, pp.z, pp.yaw, pp.pitch, { sail: 1, oars: 'air', cradle: true, t, phase: i, lantern: true });
      const enterX = SHORE_E + 2, vx = (x1 - x0) / dur;
      spl.push({ x: SHORE_E + 6.5, z: pz(SHORE_E + 6.5), age: (t - this.t0) - (enterX - (x0 - i * 24)) / vx });
    }
    setSplashes(spl);
    let wi = 0;
    for (let i = 0; i < 12; i++) { const x = 46 + i * 2.1, z = pz(x) + (i % 2 ? 6.5 : -6.5); putPerson(workers[wi++], x, z, (i % 2 ? -1 : 1) * Math.PI / 2, P.cheer(t, i)); }
    const e = ease(k);
    cam(lerpV(V(91, 1.3, pz(80) + 16), V(89, 1.6, pz(80) + 13), e), lerpV(V(66, 4, pz(66)), V(76, 2.5, pz(76)), e), 40, 0.15, t);
    aimSun(V(72, 0, 0), 50);
    return [{ text: 'HALİÇ', p: V(98, 0, pz(98) - 6), a: fadeIn(t, W(46)), len: 100 }];
  },
  L(t, k, lt, W) { // şafak: surlardaki Bizans askeri
    goldenHornFleet(70); byzBehindChain();
    setLogs(999); setRoute(0); setFires(false, t);
    for (let i = 0; i < 6; i++) {
      const p = byzSoldiers[i], z = -15 + i * 2.2, b = gy(154, z) + 9.4;
      putPerson(p, 153.4, z, Math.PI, i === 0 ? { ...P.point(t, i), look: lerp(0.6, 0, smooth(0.1, 0.5, k)) } : P.stand(t, i), b);
    }
    const e = ease(k);
    const b0 = gy(154, -17) + 9.4;
    cam(lerpV(V(157.6, b0 + 2.9, -18.8), V(157.0, b0 + 3.0, -17.8), e), lerpV(V(118, b0 - 7, 2), V(110, 3, 12), e), 40, 0.06, t);
    aimSun(V(120, 0, 10), 80);
    return [];
  },
  M(t, k, lt, W) { // zincirin arkasında ~70 gemi
    goldenHornFleet(70); byzBehindChain(); ottomanAtChain();
    setLogs(999); setRoute(0); setFires(false, t);
    const e = ease(k);
    cam(lerpV(V(113, 18, -160), V(113, 62, -196), e), V(112, 0, -40), 42, 0.05, t);
    aimSun(V(112, 0, -20), 160);
    return [
      { text: 'YETMİŞ KADAR GEMİ', p: V(112, 6, 10), a: fadeIn(t, W(53)), len: 150 },
      { text: 'ZİNCİR', p: V(128, 1, CHAIN_Z), a: fadeIn(t, W(56)), len: 100 },
    ];
  },
  N(t, k, lt, W) { // Fatih şafakta filoya bakıyor
    goldenHornFleet(70); byzBehindChain();
    setLogs(999); setRoute(0); setFires(false, t);
    const fx = 58, fz = -20;
    putFatih(fx, fz, 0.1, t, 0);
    let wi = 0;
    for (let i = 0; i < 5; i++) putPerson(workers[wi++], fx + 1 - i * 1.6, fz + (i % 2 ? 4.5 : -4.5) + (i % 2 ? i : -i) * 0.4, 0.1, P.stand(t, i));
    const e = easeOut(k);
    const c = lerpV(V(fx - 9, 0, fz - 1.5), V(fx - 5, 0, fz - 0.8), e); c.y = gy(fx, fz) + lerp(3.4, 3.0, e);
    cam(c, V(fx + 30, 4, fz + 6), 40, 0.04, t);
    aimSun(V(fx + 10, 0, fz), 40);
    return [];
  },
  O(t, k, lt, W) { // kapanış
    goldenHornFleet(70); byzBehindChain(); bosphorusFleet(10);
    setLogs(999); setFires(false, t);
    setRoute(1, 0.9);
    const a = lerp(-2.25, -1.9, k);
    cam(V(30 + Math.cos(a) * 240, lerp(185, 165, k), Math.sin(a) * 240), V(30, 0, -10), 42, 0, t);
    aimSun(V(30, 0, -10), 220);
    return [];
  },
};
