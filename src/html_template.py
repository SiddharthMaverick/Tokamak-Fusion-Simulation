"""
src/html_template.py
====================
Generates the self-contained HTML/JS/WebGL page that is embedded in
the Gradio iframe.  All Three.js code lives here so it can be version-
controlled, linted, and tested independently of the Gradio layer.
"""

from __future__ import annotations


# ── Inline CSS ────────────────────────────────────────────────────────
_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#020409; overflow:hidden; font-family:'Courier New',monospace; }
#cv  { position:absolute; inset:0; }

#ui {
  position:absolute; top:12px; right:5px; width:240px;
  background:#05101fee; border:1px solid #0a2233;
  border-radius:8px; padding:14px;
  display:flex; flex-direction:column; gap:11px;
  font-size:11px; color:#7a9ab0;
}
#ui h2 {
  color:#00d4ff; font-size:10px; letter-spacing:.14em;
  border-bottom:1px solid #0a2233; padding-bottom:6px; margin:0;
}
.ctrl { display:flex; flex-direction:column; gap:3px; }
.ctrl-row { display:flex; justify-content:space-between; align-items:baseline; }
.ctrl-name { color:#aaccdd; }
.ctrl-val  { color:#fff; font-size:12px; }
.ctrl-unit { color:#445566; font-size:10px; margin-left:2px; }
input[type=range] { width:100%; accent-color:#00d4ff; cursor:pointer; height:18px; }
.hint { color:#334455; font-size:10px; }

.derived {
  background:#020d1a; border:1px solid #0a2233; border-radius:4px;
  padding:9px; font-size:10px; line-height:2.0; color:#5a7a90;
}
.derived strong { color:#00d4ff; display:block; margin-bottom:2px; }
.dval { color:#88ccee; }

.legend {
  background:#020d1a; border:1px solid #0a2233; border-radius:4px;
  padding:9px; font-size:10px; line-height:1.9; color:#5a7a90;
}
.legend strong { color:#00d4ff; display:block; margin-bottom:2px; }

.stats { font-size:10px; color:#334455; }
.stats span { color:#88aacc; }

.warn {
  background:#1a0a00; border:1px solid #ff440033; border-radius:4px;
  padding:7px 9px; font-size:10px; color:#ff8844; display:none;
}
"""

# ── JavaScript (Three.js r128 WebGL scene) ────────────────────────────
_JS = """
// ════════════════════════════════════════════════════════════════════
//  Three.js r128 TorusGeometry vertex formula (verified from source):
//    x = (R + r·cosφ)·cosθ
//    y = (R + r·cosφ)·sinθ   ← XY equatorial plane
//    z =  r·sinφ              ← Z = poloidal axis
//  toCart() matches this exactly.  No rotation applied to any mesh.
// ════════════════════════════════════════════════════════════════════

const R0 = 10, a = 3;

// ── Reactor control inputs (initial values) ───────────────────────────
let Ip   = 2.0;   // MA
let Bt   = 3.5;   // T
let Pnbi = 20;    // MW
let ne   = 4.0;   // 1e19 m^-3
let N    = 700;
const TLEN = 25;

// ── Physics derivation ────────────────────────────────────────────────
// Safety factor  q ≈ k_q · Bt / Ip
//   k_q calibrated: q=2.5 @ Ip=2MA, Bt=3.5T  →  k_q ≈ 1.4286
// β_N proxy      ∝ P_NBI / (ne · Bt²)
// v_tor proxy    ∝ P_NBI / ne        (NBI momentum, collisional damping)
// Turbulence     ∝ β_N / q²          (ideal ballooning drive)
const K_Q = (2.5 * 2.0) / 3.5;

function derivedParams(ip, bt, pnbi, ne_) {
  const q     = Math.max(0.5, K_Q * bt / ip);
  const betaN = (pnbi * 2.8) / (ne_ * bt * bt + 0.1);
  const v_tor = (pnbi * 18.0) / (ne_ * 1.2 + 0.5);
  const turb  = Math.min(0.90, Math.max(0.0, betaN / (q * q * 3.2 + 0.1)));
  const vel   = Math.min(0.18, Math.max(0.003, v_tor * 0.0032));
  return { q, betaN, v_tor, turb, vel };
}

let derived = derivedParams(Ip, Bt, Pnbi, ne);

// ── Renderer ──────────────────────────────────────────────────────────
const scene    = new THREE.Scene();
scene.fog      = new THREE.FogExp2(0x020409, 0.015);
const camera   = new THREE.PerspectiveCamera(52, innerWidth / innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
document.getElementById('cv').appendChild(renderer.domElement);
addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

// ── Orbit controls ────────────────────────────────────────────────────
let drag = false, ox = 0, oy = 0;
const sph = { th: 0.6, ph: 1.1, r: 30 };
function syncCam() {
  camera.position.set(
    sph.r * Math.sin(sph.ph) * Math.sin(sph.th),
    sph.r * Math.cos(sph.ph),
    sph.r * Math.sin(sph.ph) * Math.cos(sph.th)
  );
  camera.lookAt(0, 0, 0);
}
syncCam();
const cvEl = renderer.domElement;
cvEl.addEventListener('mousedown',  e => { drag = true; ox = e.clientX; oy = e.clientY; });
addEventListener('mouseup',         ()  => drag = false);
addEventListener('mousemove', e => {
  if (!drag) return;
  sph.th -= (e.clientX - ox) * 0.005;
  sph.ph  = Math.max(0.05, Math.min(Math.PI - 0.05, sph.ph + (e.clientY - oy) * 0.005));
  ox = e.clientX; oy = e.clientY; syncCam();
});
cvEl.addEventListener('wheel', e => {
  sph.r = Math.max(12, Math.min(80, sph.r + e.deltaY * 0.04));
  syncCam(); e.preventDefault();
}, { passive: false });
cvEl.addEventListener('touchstart', e => {
  if (e.touches.length === 1) { drag = true; ox = e.touches[0].clientX; oy = e.touches[0].clientY; }
}, { passive: true });
addEventListener('touchend',  () => drag = false);
addEventListener('touchmove', e => {
  if (!drag || e.touches.length !== 1) return;
  sph.th -= (e.touches[0].clientX - ox) * 0.005;
  sph.ph  = Math.max(0.05, Math.min(Math.PI - 0.05, sph.ph + (e.touches[0].clientY - oy) * 0.005));
  ox = e.touches[0].clientX; oy = e.touches[0].clientY; syncCam();
}, { passive: true });

// ── Coordinate mapping — matches Three.js r128 TorusGeometry exactly ─
function toCart(rho, theta, phi) {
  const Reff = R0 + rho * Math.cos(phi);
  return new THREE.Vector3(
    Reff * Math.cos(theta),   // x
    Reff * Math.sin(theta),   // y  (equatorial XY plane)
    rho  * Math.sin(phi)      // z  (poloidal axis)
  );
}

// ── Static geometry: vessel wireframe ─────────────────────────────────
scene.add(new THREE.Mesh(
  new THREE.TorusGeometry(R0, a, 32, 120),
  new THREE.MeshBasicMaterial({
    color: 0x00aaff, wireframe: true, transparent: true, opacity: 0.08
  })
));

// Flux surface guide tori
[1.0, 2.0].forEach(r => scene.add(new THREE.Mesh(
  new THREE.TorusGeometry(R0, r, 12, 80),
  new THREE.MeshBasicMaterial({
    color: 0x001833, wireframe: true, transparent: true, opacity: 0.20
  })
)));

// Magnetic axis ring (XY plane, z = 0)
{
  const pts = [];
  for (let i = 0; i <= 128; i++) {
    const t = i / 128 * Math.PI * 2;
    pts.push(new THREE.Vector3(R0 * Math.cos(t), R0 * Math.sin(t), 0));
  }
  scene.add(new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(pts),
    new THREE.LineBasicMaterial({ color: 0x004466, transparent: true, opacity: 0.5 })
  ));
}

// Verification rings — lie exactly on the vessel mesh surface
[0, Math.PI / 2, Math.PI].forEach((ph, i) => {
  const pts = [];
  for (let j = 0; j <= 128; j++) pts.push(toCart(a * 0.6, j / 128 * Math.PI * 2, ph));
  scene.add(new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(pts),
    new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.13 - i * 0.04 })
  ));
});

// ── Jet colourmap ─────────────────────────────────────────────────────
function jet(v) {
  v = Math.max(0, Math.min(1, v));
  return [
    Math.max(0, Math.min(1, 1.5 - Math.abs(4 * v - 3))),
    Math.max(0, Math.min(1, 1.5 - Math.abs(4 * v - 2))),
    Math.max(0, Math.min(1, 1.5 - Math.abs(4 * v - 1)))
  ];
}

// ── Multi-octave smooth noise ─────────────────────────────────────────
function noise3(x, y, z) {
  return Math.sin(x * 1.31 + y * 0.73) * Math.cos(z * 0.91) * 0.571
       + Math.sin(y * 2.17 + z * 1.43) * Math.cos(x * 0.67) * 0.286
       + Math.sin(z * 3.07 + x * 1.81) * Math.cos(y * 2.13) * 0.143;
}

// ── Particle line material ────────────────────────────────────────────
const pMat = new THREE.LineBasicMaterial({
  vertexColors: true, blending: THREE.AdditiveBlending,
  transparent: true, opacity: 0.88, depthWrite: false
});
let particles = [];

function buildSystem(n, tlen) {
  particles.forEach(p => scene.remove(p.line));
  particles = [];
  const TP = Math.PI * 2;
  for (let i = 0; i < n; i++) {
    const rho = Math.max(a * 0.03, Math.sqrt(Math.random()) * a * 0.97);
    const th0 = Math.random() * TP;
    const ph0 = Math.random() * TP;
    const spd = 0.5 + Math.random() * 1.0;
    const pos = new Float32Array(tlen * 3);
    const col = new Float32Array(tlen * 3);
    const p0  = toCart(rho, th0, ph0);
    const [r0, g0, b0] = jet(1 - rho / a);
    for (let j = 0; j < tlen; j++) {
      pos[j * 3] = p0.x; pos[j * 3 + 1] = p0.y; pos[j * 3 + 2] = p0.z;
      col[j * 3] = r0;   col[j * 3 + 1] = g0;   col[j * 3 + 2] = b0;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('color',    new THREE.BufferAttribute(col, 3));
    const line = new THREE.Line(geo, pMat);
    scene.add(line);
    particles.push({ rho, th: th0, ph: ph0, spd, line, pos, col });
  }
  document.getElementById('pct').textContent = n;
}
buildSystem(N, TLEN);

// ── Derived parameter display ─────────────────────────────────────────
function updateDisplay() {
  const d = derived;
  document.getElementById('dq').textContent    = d.q.toFixed(2);
  document.getElementById('dbeta').textContent = d.betaN.toFixed(2);
  document.getElementById('dvel').textContent  = d.v_tor.toFixed(1);
  document.getElementById('dturb').textContent = d.turb.toFixed(3);
  document.getElementById('warn').style.display = d.q < 2.0 ? 'block' : 'none';
}
updateDisplay();

// ── Slider bindings ───────────────────────────────────────────────────
function bind(id, lblId, fmt, setFn) {
  const sl = document.getElementById(id);
  const lb = document.getElementById(lblId);
  sl.addEventListener('input', () => {
    const v = parseFloat(sl.value);
    lb.textContent = fmt(v);
    setFn(v);
    derived = derivedParams(Ip, Bt, Pnbi, ne);
    updateDisplay();
  });
}
bind('sIp',  'lIp',  v => v.toFixed(1),    v => Ip   = v);
bind('sBt',  'lBt',  v => v.toFixed(1),    v => Bt   = v);
bind('sNBI', 'lNBI', v => Math.round(v),   v => Pnbi = v);
bind('sne',  'lne',  v => v.toFixed(1),    v => ne   = v);
bind('sN',   'lN',   v => Math.round(v),   v => { N = Math.round(v); buildSystem(N, TLEN); });

// ── Animation loop ────────────────────────────────────────────────────
let prev = performance.now(), fc = 0, ft = 0;
const TP = Math.PI * 2;

function animate() {
  requestAnimationFrame(animate);
  const now = performance.now();
  const dt  = (now - prev) * 0.001;
  prev = now; ft += dt; fc++;
  if (ft > 0.6) {
    document.getElementById('fps').textContent = Math.round(fc / ft);
    ft = 0; fc = 0;
  }

  const gt  = now * 0.00022;
  const q_  = derived.q;
  const vel = derived.vel;
  const trb = derived.turb;

  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];

    // Field-line advance: rotational transform  ι = 1/q
    const dth = vel * p.spd;
    const dph = dth / Math.max(0.1, q_);
    p.th = (p.th + dth) % TP;
    p.ph = (p.ph + dph) % TP;

    // Ballooning turbulence: radial perturbation, field-aligned noise
    const n3   = noise3(p.th + gt, p.ph * q_ + gt * 0.6, gt * 0.4);
    const rhoD = Math.min(a * 0.99, Math.max(a * 0.01, p.rho + n3 * trb * a * 0.40));
    const v3   = toCart(rhoD, p.th, p.ph);

    // Scroll the tail
    const pos = p.pos, col = p.col;
    for (let j = TLEN - 1; j > 0; j--) {
      const jj = j * 3, k = (j - 1) * 3;
      pos[jj] = pos[k]; pos[jj + 1] = pos[k + 1]; pos[jj + 2] = pos[k + 2];
      col[jj] = col[k]; col[jj + 1] = col[k + 1]; col[jj + 2] = col[k + 2];
    }
    pos[0] = v3.x; pos[1] = v3.y; pos[2] = v3.z;

    // Colour: radial temperature proxy + turbulent burst
    const intensity = (1 - p.rho / a) * 0.68 + Math.abs(n3) * 0.32;
    const [cr, cg, cb] = jet(intensity);
    col[0] = cr; col[1] = cg; col[2] = cb;

    p.line.geometry.attributes.position.needsUpdate = true;
    p.line.geometry.attributes.color.needsUpdate    = true;
  }

  renderer.render(scene, camera);
}
animate();
"""

# ── HTML body ─────────────────────────────────────────────────────────
_HTML_BODY = """
<div id="cv"></div>

<div id="ui">
  <h2>&#9889; TOKAMAK REACTOR CONTROLS</h2>

  <div class="ctrl">
    <div class="ctrl-row">
      <span class="ctrl-name">Plasma current I<sub>p</sub></span>
      <span><span class="ctrl-val" id="lIp">2.0</span><span class="ctrl-unit">MA</span></span>
    </div>
    <input type="range" id="sIp" min="0.5" max="5.0" step="0.1" value="2.0">
    <div class="hint">Drives poloidal B field &rarr; sets q profile</div>
  </div>

  <div class="ctrl">
    <div class="ctrl-row">
      <span class="ctrl-name">Toroidal field B<sub>t</sub></span>
      <span><span class="ctrl-val" id="lBt">3.5</span><span class="ctrl-unit">T</span></span>
    </div>
    <input type="range" id="sBt" min="1.0" max="8.0" step="0.1" value="3.5">
    <div class="hint">Main confining field &rarr; raises q</div>
  </div>

  <div class="ctrl">
    <div class="ctrl-row">
      <span class="ctrl-name">NBI power P<sub>NBI</sub></span>
      <span><span class="ctrl-val" id="lNBI">20</span><span class="ctrl-unit">MW</span></span>
    </div>
    <input type="range" id="sNBI" min="0" max="100" step="1" value="20">
    <div class="hint">Neutral beam &rarr; drives rotation &amp; &beta;</div>
  </div>

  <div class="ctrl">
    <div class="ctrl-row">
      <span class="ctrl-name">Density n<sub>e</sub></span>
      <span><span class="ctrl-val" id="lne">4.0</span><span class="ctrl-unit">&times;10&sup1;&sup9; m&sup3;</span></span>
    </div>
    <input type="range" id="sne" min="1.0" max="12.0" step="0.2" value="4.0">
    <div class="hint">Collisionality &rarr; damps rotation</div>
  </div>

  <div class="ctrl">
    <div class="ctrl-row">
      <span class="ctrl-name">Tracers (visual)</span>
      <span><span class="ctrl-val" id="lN">700</span></span>
    </div>
    <input type="range" id="sN" min="100" max="1200" step="50" value="700">
  </div>

  <div class="warn" id="warn">&#9888; Disruption risk: q &lt; 2 (Kruskal-Shafranov)</div>

  <div class="derived">
    <strong>Derived parameters</strong>
    q (edge) &nbsp;&nbsp;&nbsp;= <span class="dval" id="dq">—</span><br>
    &beta;<sub>N</sub> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= <span class="dval" id="dbeta">—</span> %<br>
    v<sub>tor</sub> (proxy) = <span class="dval" id="dvel">—</span> km/s<br>
    &delta;B/B &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= <span class="dval" id="dturb">—</span>
  </div>

  <div class="legend">
    <strong>Temperature proxy (jet)</strong>
    <span style="color:#0055ff">&#9608;</span> Cold edge (&rho;&rarr;a)<br>
    <span style="color:#00ffaa">&#9608;</span> Stable helical orbit<br>
    <span style="color:#ffcc00">&#9608;</span> High-&beta; turbulent<br>
    <span style="color:#ff2200">&#9608;</span> Hot core (&rho;&rarr;0)
  </div>

  <div class="stats">
    FPS <span id="fps">—</span> &nbsp;|&nbsp; N <span id="pct">700</span>
  </div>
</div>
"""

_THREEJS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"


def build_html() -> str:
    """Return the complete self-contained HTML document as a string."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
{_CSS}
</style>
</head>
<body>
{_HTML_BODY}
<script src="{_THREEJS_CDN}"></script>
<script>
{_JS}
</script>
</body>
</html>
"""
