// Ana döngü: zaman çizelgesi, overlay (altyazı, etiketler, başlık), render
import { THREE, W, H, RENDER_MODE, stage, renderer, composer, camera, grade, clamp, smooth, easeOut, V } from './core.js';
import { setTOD, sky, updateWater, updateClouds } from './world.js';
import { hideActors } from './actors.js';
import { SHOT_FN, buildTimeline } from './shots.js';

export const AUDIO_OFFSET = 0.25;     // anlatım bu kadar gecikmeli başlar
const TAIL = 2.6;                     // son kelimeden sonra kalan süre

const raw = (await (await fetch('./audio/words.json')).json()).words;
// ElevenLabs v4 yönlendirme etiketini ([energetic, ...]) atla
let skip = 0; if (raw[0].text.startsWith('[')) { while (!raw[skip].text.endsWith(']')) skip++; skip++; }
const words = raw.slice(skip).filter(w => w.type === 'word');
const TL = buildTimeline(words, AUDIO_OFFSET, TAIL);
const WT = TL.wt;
export const DURATION = TL.end;

// ------------------------------------------------------------- altyazı grupları (en fazla 3 kelime)
const chunks = [];
{
  let cur = [];
  words.forEach((w, i) => {
    cur.push(i);
    const punct = /[.,:!?]$/.test(w.text);
    if (cur.length >= 3 || punct || i === words.length - 1) { chunks.push(cur); cur = []; }
  });
}
const capEl = document.getElementById('cap');
const titleEl = document.getElementById('title'), punchEl = document.getElementById('punch'), endEl = document.getElementById('endcard');
let lastChunk = -1;
function updateCaptions(t, hide) {
  let ci = -1;
  for (let c = 0; c < chunks.length; c++) {
    const s = WT(chunks[c][0]) - 0.05;
    const e = c < chunks.length - 1 ? WT(chunks[c + 1][0]) - 0.05 : words[words.length - 1].end + AUDIO_OFFSET + 0.4;
    if (t >= s && t < e) { ci = c; break; }
  }
  if (hide) ci = -1;
  if (ci !== lastChunk) {
    capEl.innerHTML = ci < 0 ? '' : chunks[ci].map(i => `<span data-i="${i}">${words[i].text.replace(/[,:]$/, '')}</span>`).join(' ');
    lastChunk = ci;
  }
  if (ci >= 0) {
    const s = WT(chunks[ci][0]) - 0.05;
    const pop = easeOut(clamp((t - s) / 0.12));
    capEl.style.transform = `translateY(${(1 - pop) * 18}px) scale(${0.9 + 0.1 * pop})`;
    capEl.style.opacity = pop;
    for (const sp of capEl.children) { const i = +sp.dataset.i; sp.className = t >= WT(i) - 0.03 && (i === words.length - 1 || t < WT(i + 1) - 0.03) ? 'on' : (t >= WT(i) ? 'done' : ''); }
  }
}

// ------------------------------------------------------------- etiketler
const labelsEl = document.getElementById('labels');
const labelEls = {};
const _v = new THREE.Vector3();
function showLabels(list) {
  const used = new Set();
  for (const L of list) {
    if (!labelEls[L.text]) {
      const d = document.createElement('div'); d.className = 'label';
      d.innerHTML = `<div class="line"></div><div class="dot"></div><div class="box">${L.text}</div>`;
      labelsEl.appendChild(d); labelEls[L.text] = d;
    }
    const el = labelEls[L.text]; used.add(L.text);
    _v.copy(L.p).project(camera);
    const sx = (_v.x * 0.5 + 0.5) * W, sy = (-_v.y * 0.5 + 0.5) * H;
    const a = _v.z < 1 ? L.a : 0;
    el.style.transform = `translate(${sx}px, ${sy}px)`;
    el.style.opacity = a;
    el.style.setProperty('--len', ((L.len || 150) * (0.6 + 0.4 * a)) + 'px');
    const bx = el.querySelector('.box'), bw = bx.offsetWidth;
    bx.style.left = (clamp(sx - bw / 2, 40, W - 40 - bw) - sx) + 'px';
    bx.style.transform = `scale(${0.85 + 0.15 * a})`;
  }
  for (const k in labelEls) if (!used.has(k)) labelEls[k].style.opacity = 0;
}

// ------------------------------------------------------------- render
function renderFrame(t) {
  const idx = TL.shots.findIndex(s => t >= s.t0 && t < s.t1);
  const shot = TL.shots[idx < 0 ? TL.shots.length - 1 : idx];
  setTOD(shot.tod);
  hideActors();
  const k = clamp((t - shot.t0) / (shot.t1 - shot.t0));
  const labels = SHOT_FN[shot.id].call(shot, t, k, t - shot.t0, WT) || [];
  sky.position.copy(camera.position);
  updateWater(t); updateClouds(t);
  // geçişler: beyaz flaş / siyaha geçiş
  let flash = 0, fade = 0;
  for (const s of TL.shots) {
    if (s.flash) flash = Math.max(flash, 0.85 * (1 - smooth(s.t0, s.t0 + 0.22, t)) * (t >= s.t0 ? 1 : 0));
    if (s.fade) fade = Math.max(fade, 1 - smooth(0, 0.22, Math.abs(t - s.t0)));
  }
  if (t < 0.25) fade = Math.max(fade, 1 - t / 0.25);
  if (t > DURATION - 0.5) fade = Math.max(fade, (t - (DURATION - 0.5)) / 0.5);
  grade.uniforms.flash.value = flash; grade.uniforms.fade.value = fade; grade.uniforms.time.value = t;
  composer.render();
  showLabels(labels);
  // overlay
  const N = TL.shots.find(s => s.id === 'N');
  const punchOn = t >= N.t0 && t < N.t1;
  updateCaptions(t, punchOn);
  titleEl.style.opacity = 1 - smooth(TL.shots[1].t0 - 0.3, TL.shots[1].t0 + 0.1, t);
  titleEl.style.transform = `scale(${1.15 - 0.15 * easeOut(clamp(t / 0.5))})`;
  const pk = clamp((t - N.t0) / 0.2);
  punchEl.style.opacity = punchOn ? Math.min(1, pk * 1.5) * (1 - smooth(N.t1 - 0.15, N.t1, t)) : 0;
  punchEl.style.transform = `scale(${1.4 - 0.4 * easeOut(pk)})`;
  const O = TL.shots[TL.shots.length - 1];
  endEl.style.opacity = smooth(O.t0 + 1.2, O.t0 + 1.7, t);
}
window.renderFrame = renderFrame;
window.DURATION = DURATION;
window.TIMELINE = TL.shots.map(s => ({ id: s.id, t0: +s.t0.toFixed(3), t1: +s.t1.toFixed(3) }));
renderFrame(0);
window.ready = true;

if (!RENDER_MODE) {
  const fit = () => { const s = Math.min(innerWidth / W, innerHeight / H); stage.style.transform = `scale(${s})`; stage.style.left = (innerWidth - W * s) / 2 + 'px'; };
  addEventListener('resize', fit); fit();
  const audio = new Audio('./audio/mix.m4a');
  const btn = document.createElement('button'); btn.id = 'play'; btn.textContent = '▶ Oynat'; document.body.appendChild(btn);
  let playing = false, start = 0;
  btn.onclick = () => { audio.currentTime = 0; audio.play().catch(() => {}); start = performance.now(); playing = true; btn.textContent = '↻ Baştan'; };
  const tick = () => { if (playing) { const t = (performance.now() - start) / 1000; if (t < DURATION) renderFrame(t); else playing = false; } requestAnimationFrame(tick); };
  tick();
}
