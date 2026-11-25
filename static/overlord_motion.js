// Project Overlord motion layer.
// - Landing page that dissolves into wind-blown dust (three.js) and doubles as the loading screen.
// - Dashboard motion on state changes (anime.js), timed with Arc's motion tokens.
// Both libraries are vendored in ./vendor so the intro works without venue Wi-Fi.
import * as THREE from "./vendor/three.module.min.js";
import { animate, stagger, cubicBezier } from "./vendor/anime.esm.min.js";

// Arc motion tokens (arc-library registry/motion-tokens.ts), in milliseconds.
const T = {
  dur: { instant: 120, fast: 160, exit: 180, standard: 240, considered: 480 },
  ease: {
    enter: cubicBezier(0.16, 1, 0.3, 1),
    exit: cubicBezier(0.7, 0, 0.84, 0),
    standard: cubicBezier(0.22, 1, 0.36, 1),
    inOut: cubicBezier(0.65, 0, 0.35, 1),
  },
  stagger: { word: 40, line: 80, item: 35 },
  blur: { subtle: 2, soft: 4, text: 8 },
};
const MAX_STAGGER = T.dur.considered; // Arc: total stagger stays under ~0.48s however long the text is.
const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const THEME_KEY = "ov-theme";
const isDark = () => document.documentElement.dataset.ovTheme === "dark";
// Apply the saved choice before anything renders, so the intro matches the dashboard behind it.
// Light stays the default: it is the projector-safe look, and dark is opt-in.
try {
  if (localStorage.getItem(THEME_KEY) === "dark") document.documentElement.dataset.ovTheme = "dark";
} catch {}

const PAD = isDark()
  ? { paper: "#121A16", rule: "#24322A", margin: "#6E3A34", ink: "#E6EDE7", ink2: "#A9B8AE", green: "#5BC995" }
  : { paper: "#F4F7EF", rule: "#CFDBC6", margin: "#D9A39C", ink: "#1D2721", ink2: "#46554B", green: "#1C6B43" };

/* ------------------------------------------------------------------ */
/* Landing page                                                        */
/* ------------------------------------------------------------------ */

const INTRO_CSS = `
#ov-intro { position: fixed; inset: 0; z-index: 10000; cursor: pointer; color: ${PAD.ink};
  font-family: 'IBM Plex Sans', system-ui, sans-serif; background-color: ${PAD.paper};
  background-image: linear-gradient(to right, transparent 0 calc(8vw - 3px), ${PAD.margin} calc(8vw - 3px) calc(8vw - 2px), transparent calc(8vw - 2px) 8vw, ${PAD.margin} 8vw calc(8vw + 1px), transparent calc(8vw + 1px)),
    repeating-linear-gradient(to bottom, transparent 0 31px, ${PAD.rule} 31px 32px);
  display: grid; align-items: center; }
#ov-intro .ov-intro-inner { margin-left: calc(8vw + 48px); max-width: min(70ch, 80vw); padding: 48px 0; }
#ov-intro h1 { margin: 0; font-size: clamp(48px, 7vw, 88px); line-height: 1.02; font-weight: 700; letter-spacing: -0.035em; text-wrap: balance; }
#ov-intro .ov-intro-lede { margin: 20px 0 0; font-size: clamp(18px, 1.6vw, 22px); line-height: 1.5; color: ${PAD.ink2}; max-width: 46ch; text-wrap: pretty; }
#ov-intro .ov-intro-meta { margin: 14px 0 0; font-size: 16px; color: ${PAD.ink2}; }
#ov-intro .ov-intro-cta { margin: 40px 0 0; font-size: 18px; font-weight: 600; color: ${PAD.green}; }
#ov-intro .ov-intro-status { margin: 8px 0 0; min-height: 1.5em; font-size: 16px; color: ${PAD.ink2}; }
#ov-intro .ov-w { display: inline-block; }
#ov-intro canvas { position: fixed; inset: 0; width: 100vw; height: 100vh; pointer-events: none; }
#ov-intro.is-dust { background: transparent; cursor: default; }
#ov-intro.is-dust .ov-intro-inner { visibility: hidden; }
`;

function splitWords(el) {
  const words = el.textContent.trim().split(/\s+/);
  el.setAttribute("aria-label", el.textContent.trim());
  el.innerHTML = words.map((w) => `<span class="ov-w" aria-hidden="true">${w}</span>`).join(" ");
  return [...el.querySelectorAll(".ov-w")];
}

function buildIntro() {
  const style = document.createElement("style");
  style.textContent = INTRO_CSS;
  document.head.appendChild(style);

  const intro = document.createElement("div");
  intro.id = "ov-intro";
  intro.setAttribute("role", "button");
  intro.setAttribute("tabindex", "0");
  intro.setAttribute("aria-label", "Open the Project Overlord audit workspace");
  intro.innerHTML = `
    <div class="ov-intro-inner">
      <h1 data-dust>Project Overlord</h1>
      <p class="ov-intro-lede" data-dust>Every invoice is checked against its purchase order and its goods receipt before a single dollar is paid.</p>
      <p class="ov-intro-meta" data-dust>Track PS-BA1. Five agents, one verdict, a dispute ready to send.</p>
      <p class="ov-intro-cta" data-dust>Click anywhere to open the audit workspace</p>
      <p class="ov-intro-status" aria-live="polite"></p>
    </div>`;
  document.body.appendChild(intro);
  return intro;
}

function revealIntro(intro) {
  const groups = [...intro.querySelectorAll("[data-dust]")].map(splitWords);
  if (REDUCED) return;
  let offset = 0;
  for (const words of groups) {
    const step = Math.min(T.stagger.word, MAX_STAGGER / Math.max(words.length, 1));
    animate(words, {
      opacity: [0, 1],
      translateY: ["0.3em", "0em"],
      filter: [`blur(${T.blur.text}px)`, "blur(0px)"],
      duration: T.dur.considered,
      delay: stagger(step, { start: offset }),
      ease: T.ease.enter,
    });
    offset += T.stagger.line * 2;
  }
}

/* The dashboard has to be mounted and styled before the dust can reveal it. */
function dashboardReady() {
  const mounted = () => document.querySelector(".ov-topbar") && document.querySelector(".ov-footing");
  return new Promise((resolve) => {
    const check = () => (mounted() ? resolve() : setTimeout(check, 100));
    check();
  }).then(() => document.fonts.ready);
}

/* ------------------------------------------------------------------ */
/* Dust transition                                                     */
/* ------------------------------------------------------------------ */

function rasterizeIntro(intro, W, H) {
  const c = document.createElement("canvas");
  c.width = W;
  c.height = H;
  const ctx = c.getContext("2d", { willReadFrequently: true });
  ctx.fillStyle = PAD.paper;
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = PAD.rule;
  for (let y = 31; y < H; y += 32) ctx.fillRect(0, y, W, 1);
  const m = Math.round(W * 0.08);
  ctx.fillStyle = PAD.margin;
  ctx.fillRect(m - 3, 0, 1, H);
  ctx.fillRect(m, 0, 1, H);
  ctx.textBaseline = "alphabetic";
  for (const word of intro.querySelectorAll(".ov-w")) {
    const r = word.getBoundingClientRect();
    const cs = getComputedStyle(word);
    ctx.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    ctx.fillStyle = cs.color;
    const metrics = ctx.measureText(word.textContent);
    const baseline = r.top + (r.height + metrics.actualBoundingBoxAscent - metrics.actualBoundingBoxDescent) / 2;
    ctx.fillText(word.textContent, r.left, baseline);
  }
  return ctx.getImageData(0, 0, W, H).data;
}

function buildParticles(pixels, W, H) {
  // Ink is sampled densely so letters keep their shape; paper sparsely, sized to tile the screen.
  const paperRGB = [1, 3, 5].map((i) => parseInt(PAD.paper.slice(i, i + 2), 16));
  const pos = [], col = [], size = [], delay = [], rnd = [];
  const push = (x, y, i, s, rgb = null) => {
    pos.push(x, y, 0);
    if (rgb) col.push(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255);
    else col.push(pixels[i] / 255, pixels[i + 1] / 255, pixels[i + 2] / 255);
    size.push(s);
    // The wind erodes the sheet from left to right, ragged rather than as a straight front.
    delay.push((x / W) * 0.9 + (y / H) * 0.12 + Math.random() * 0.35);
    rnd.push(Math.random(), Math.random(), Math.random());
  };
  const INK = 2, PAPER = 4;
  const isInk = (i) => Math.abs(pixels[i] - paperRGB[0]) + Math.abs(pixels[i + 1] - paperRGB[1]) + Math.abs(pixels[i + 2] - paperRGB[2]) > 40;
  for (let y = 0; y < H; y += PAPER) {
    for (let x = 0; x < W; x += PAPER) {
      const i = (y * W + x) * 4;
      push(x + PAPER / 2, y + PAPER / 2, i, PAPER * 1.15, isInk(i) ? paperRGB : null);
    }
  }
  for (let y = 0; y < H; y += INK) {
    for (let x = 0; x < W; x += INK) {
      const i = (y * W + x) * 4;
      if (isInk(i)) push(x, y, i, INK * 1.35);
    }
  }
  return { pos, col, size, delay, rnd };
}

const VERT = `
attribute vec3 aColor; attribute float aSize; attribute float aDelay; attribute vec3 aRand;
uniform float uTime; uniform float uPR; uniform vec3 uDust;
varying vec3 vColor; varying float vAlpha;
void main() {
  float life = 1.15 + aRand.z * 0.7;
  float t = clamp((uTime - aDelay) / life, 0.0, 1.0);
  float e = t * t;
  vec3 p = position;
  // Wind pushes right and lifts; each mote drifts on its own swirl.
  p.x += e * (700.0 + aRand.x * 900.0) + sin(t * 7.0 + aRand.y * 12.0) * 26.0 * t;
  p.y -= e * (180.0 + aRand.y * 420.0) + cos(t * 6.0 + aRand.x * 12.0) * 34.0 * t;
  // Motes darken as they lift, so paper-coloured dust stays visible over the paper-coloured dashboard.
  vColor = mix(aColor, uDust, smoothstep(0.0, 0.35, t) * 0.42);
  vAlpha = 1.0 - smoothstep(0.45, 1.0, t);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  gl_PointSize = aSize * uPR * mix(1.0, 0.35, t);
}`;

const FRAG = `
varying vec3 vColor; varying float vAlpha;
void main() {
  if (vAlpha <= 0.0) discard;
  gl_FragColor = vec4(vColor, vAlpha);
}`;

function runDust(intro) {
  const W = window.innerWidth, H = window.innerHeight;
  const pixels = rasterizeIntro(intro, W, H);
  const { pos, col, size, delay, rnd } = buildParticles(pixels, W, H);

  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(W, H, false);
  renderer.setClearColor(0x000000, 0);
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(0, W, 0, H, -1, 1); // pixel space, y down
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute("aColor", new THREE.Float32BufferAttribute(col, 3));
  geo.setAttribute("aSize", new THREE.Float32BufferAttribute(size, 1));
  geo.setAttribute("aDelay", new THREE.Float32BufferAttribute(delay, 1));
  geo.setAttribute("aRand", new THREE.Float32BufferAttribute(rnd, 3));
  // Raw 0-1 values (not THREE.Color) so the dust tint matches the sampled sRGB pixels exactly.
  const dust = isDark() ? new THREE.Vector3(0.66, 0.74, 0.69) : new THREE.Vector3(0.36, 0.42, 0.38);
  const uniforms = { uTime: { value: 0 }, uPR: { value: renderer.getPixelRatio() }, uDust: { value: dust } };
  const mat = new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, uniforms, transparent: true, depthTest: false, depthWrite: false });
  scene.add(new THREE.Points(geo, mat));

  intro.appendChild(renderer.domElement);
  renderer.render(scene, camera);
  intro.classList.add("is-dust"); // swap the DOM page for its particle copy on the same frame

  const total = 0.9 + 0.12 + 0.35 + 1.85; // max delay + max life
  const start = performance.now();
  return new Promise((resolve) => {
    const frame = (now) => {
      uniforms.uTime.value = (now - start) / 1000;
      renderer.render(scene, camera);
      if (uniforms.uTime.value < total) requestAnimationFrame(frame);
      else {
        geo.dispose();
        mat.dispose();
        renderer.dispose();
        resolve();
      }
    };
    requestAnimationFrame(frame);
  });
}

function fadeIntro(intro) {
  if (REDUCED) return Promise.resolve();
  return animate(intro, {
    opacity: [1, 0],
    filter: ["blur(0px)", `blur(${T.blur.soft}px)`],
    duration: T.dur.considered,
    ease: T.ease.exit,
  }).then(() => {});
}

function startIntro() {
  if (new URLSearchParams(location.search).get("intro") === "0") return;
  const intro = buildIntro();
  revealIntro(intro);
  const ready = dashboardReady();
  let leaving = false;

  const leave = async () => {
    if (leaving) return;
    leaving = true;
    const status = intro.querySelector(".ov-intro-status");
    let settled = false;
    ready.then(() => (settled = true));
    await Promise.race([ready, new Promise((r) => setTimeout(r, 150))]);
    if (!settled) {
      status.textContent = "Loading the audit engine…";
      await ready;
    }
    status.textContent = "";
    try {
      if (REDUCED) throw new Error("reduced motion");
      await runDust(intro);
    } catch {
      await fadeIntro(intro);
    }
    intro.remove();
    document.querySelector(".gradio-container")?.focus?.();
  };

  intro.addEventListener("pointerdown", leave);
  intro.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      leave();
    }
  });
  intro.focus();
}

/* ------------------------------------------------------------------ */
/* Dashboard motion: animate only when a state actually changes.       */
/* Gradio re-renders these HTML blocks on every streamed step, so each */
/* effect is keyed by content and fires once per new state.           */
/* ------------------------------------------------------------------ */

let counting = false;
const seen = { recovered: 0, verdict: "", flags: "", footing: [], dispatch: "", vision: "" };
const money = (n) => "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function rise(targets, extra = {}) {
  if (REDUCED) return;
  animate(targets, {
    opacity: [0, 1],
    translateY: ["0.3em", "0em"],
    filter: [`blur(${T.blur.soft}px)`, "blur(0px)"],
    duration: T.dur.standard,
    ease: T.ease.enter,
    ...extra,
  });
}

function onDashboardChange() {
  // Gradio may patch this text in place or swap the element, so compare values, not nodes.
  const value = document.querySelector(".ov-impact-value");
  if (value && !counting) {
    const shown = parseFloat(value.textContent.replace(/[^0-9.]/g, "")) || 0;
    if (shown !== seen.recovered && !REDUCED) {
      const write = (n) => document.querySelectorAll(".ov-impact-value").forEach((el) => { el.textContent = money(n); });
      const counter = { v: seen.recovered };
      counting = true;
      write(counter.v);
      animate(counter, {
        v: shown,
        duration: T.dur.considered * 1.5,
        ease: T.ease.standard,
        onUpdate: () => write(counter.v),
        onComplete: () => { write(shown); counting = false; },
      });
    }
    seen.recovered = shown;
  }

  const verdict = document.querySelector(".ov-verdict--alert, .ov-verdict--ok");
  const verdictSig = verdict ? verdict.textContent.trim() : "";
  if (verdict && verdictSig !== seen.verdict && !REDUCED) {
    // The one authored moment: the stamp lands, then the finding rises out of a soft blur.
    animate(verdict.querySelector(".ov-stamp"), {
      scale: [1.9, 1],
      opacity: [0, 1],
      rotate: ["-9deg", "-2deg"],
      duration: T.dur.considered,
      ease: T.ease.enter,
    });
    rise(verdict.querySelectorAll(".alert-title, .alert-body"), { delay: stagger(T.stagger.line, { start: 120 }) });
  }
  seen.verdict = verdictSig;

  const rows = document.querySelectorAll(".ov-line-row--flagged td");
  const flagSig = [...rows].map((td) => td.textContent).join("|");
  if (rows.length && flagSig !== seen.flags && !REDUCED) {
    // Animate to the current theme's tint, then hand the colour back to CSS so a later theme switch applies.
    const tint = getComputedStyle(rows[0]).backgroundColor;
    animate(rows, {
      backgroundColor: ["rgba(0,0,0,0)", tint],
      duration: T.dur.considered,
      delay: stagger(T.stagger.item),
      ease: T.ease.standard,
      onComplete: () => rows.forEach((td) => td.style.removeProperty("background-color")),
    });
  }
  seen.flags = flagSig;

  const cells = [...document.querySelectorAll(".ov-footing tr:nth-child(2) td")];
  const changed = cells.filter((td, i) => td.textContent !== seen.footing[i]);
  if (changed.length && seen.footing.length) rise(changed, { delay: stagger(T.stagger.item) });
  seen.footing = cells.map((td) => td.textContent);

  const dispatch = document.querySelector(".ov-dispatch-success");
  const dispatchSig = dispatch ? dispatch.textContent : "";
  if (dispatch && dispatchSig !== seen.dispatch) rise(dispatch, { duration: T.dur.considered });
  seen.dispatch = dispatchSig;

  const vision = document.querySelector(".ov-vision-badge");
  const visionSig = vision ? vision.textContent : "";
  if (vision && visionSig !== seen.vision && seen.vision) rise(vision);
  seen.vision = visionSig;
}

function watchDashboard() {
  let queued = false;
  new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      onDashboardChange();
    });
  }).observe(document.body, { childList: true, subtree: true, characterData: true });
}

/* ------------------------------------------------------------------ */
/* Light / dark toggle: the new theme wipes in as a circle from the    */
/* switch (View Transitions API), or swaps instantly where unsupported. */
/* ------------------------------------------------------------------ */

function syncThemeToggle() {
  const toggle = document.getElementById("ov-theme-toggle");
  if (toggle) toggle.setAttribute("aria-checked", String(isDark()));
}

function setTheme(dark, origin) {
  const apply = () => {
    if (dark) document.documentElement.dataset.ovTheme = "dark";
    else delete document.documentElement.dataset.ovTheme;
    try { localStorage.setItem(THEME_KEY, dark ? "dark" : "light"); } catch {}
    syncThemeToggle();
  };
  if (REDUCED || !document.startViewTransition) return apply();
  const r = origin.getBoundingClientRect();
  const x = r.left + r.width / 2, y = r.top + r.height / 2;
  const radius = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
  document.startViewTransition(apply).ready.then(() => {
    document.documentElement.animate(
      { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
      { duration: T.dur.considered * 1.25, easing: "cubic-bezier(0.16, 1, 0.3, 1)", pseudoElement: "::view-transition-new(root)" },
    );
  });
}

document.addEventListener("click", (e) => {
  const toggle = e.target.closest?.("#ov-theme-toggle");
  if (toggle) setTheme(!isDark(), toggle);
  // The run button's attention ring has done its job once the user finds it.
  if (e.target.closest?.(".ov-run-hint")) document.documentElement.classList.add("ov-has-run");
});

startIntro();
watchDashboard();
// The switch is rendered by Gradio after this module runs; sync it once it exists.
new MutationObserver((_, obs) => {
  if (document.getElementById("ov-theme-toggle")) {
    syncThemeToggle();
    obs.disconnect();
  }
}).observe(document.body, { childList: true, subtree: true });
