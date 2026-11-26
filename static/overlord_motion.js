// Project Overlord motion layer.
// - Landing page that dissolves into wind-blown dust (three.js) and doubles as the loading screen.
// - Dashboard motion on state changes (GSAP timelines + ScrollTrigger), timed with Arc's motion tokens.
// All libraries are vendored in ./vendor so the intro works without venue Wi-Fi.
// three.js (~570 KB) is imported only when the intro plays, so ?intro=0 and reduced motion never download it.
// GSAP core + ScrollTrigger, bundled and minified from GSAP's ES module files (the UMD build assigns to window).
import { gsap, ScrollTrigger } from "./vendor/gsap.min.js";

gsap.registerPlugin(ScrollTrigger);

// Arc motion tokens (arc-library registry/motion-tokens.ts), in seconds, with GSAP's closest built-in eases:
// enter cubic-bezier(0.16,1,0.3,1) ~ expo.out, exit (0.7,0,0.84,0) ~ expo.in, standard (0.22,1,0.36,1) ~ power4.out.
const T = {
  dur: { instant: 0.12, fast: 0.16, exit: 0.18, standard: 0.24, considered: 0.48 },
  ease: { enter: "expo.out", exit: "expo.in", standard: "power4.out" },
  stagger: { word: 0.04, line: 0.08, item: 0.035 },
  blur: { soft: 4, text: 8 },
};
const MAX_STAGGER = T.dur.considered; // Arc: total stagger stays under ~0.48s however long the text is.
gsap.defaults({ duration: T.dur.standard, ease: T.ease.enter });
// Wall-clock timing: with lag smoothing, throttled frames (a busy projector laptop, a background tab)
// stretch the dust transition and the landing page can hang. Nothing here needs frame-by-frame physics.
gsap.ticker.lagSmoothing(0);
// Read live, so turning reduced motion on in the OS takes effect without a reload.
const reducedQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
const reduced = () => reducedQuery.matches;

const THEME_KEY = "ov-theme";
const isDark = () => document.documentElement.dataset.ovTheme === "dark";
// Apply the saved choice before anything renders, so the intro matches the dashboard behind it.
// Light stays the default: it is the projector-safe look, and dark is opt-in.
try {
  if (localStorage.getItem(THEME_KEY) === "dark") document.documentElement.dataset.ovTheme = "dark";
} catch {}

// Astryx Neutral surfaces and text roles, matching the dashboard palette in app.py.
const PAD = isDark()
  ? { paper: "#1B1B1B", ink: "#FFFFFF", ink2: "#9E9E9E", accent: "#F1F1F1", onAccent: "#111111" }
  : { paper: "#F1F1F1", ink: "#111111", ink2: "#474747", accent: "#1B1B1B", onAccent: "#FFFFFF" };

/* ------------------------------------------------------------------ */
/* Landing page                                                        */
/* ------------------------------------------------------------------ */

const INTRO_CSS = `
#ov-intro { position: fixed; inset: 0; z-index: 10000; cursor: pointer; color: ${PAD.ink};
  font-family: 'Figtree', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: ${PAD.paper};
  display: grid; align-items: center; }
#ov-intro .ov-intro-inner { margin-left: 8vw; max-width: min(70ch, 84vw); padding: 48px 0; }
#ov-intro h1 { margin: 0; font-size: clamp(48px, 7vw, 88px); line-height: 1.02; font-weight: 700; letter-spacing: -0.035em; text-wrap: balance; }
#ov-intro .ov-intro-lede { margin: 20px 0 0; font-size: clamp(18px, 1.6vw, 22px); line-height: 1.5; color: ${PAD.ink2}; max-width: 46ch; text-wrap: pretty; }
#ov-intro .ov-intro-meta { margin: 14px 0 0; font-size: 16px; color: ${PAD.ink2}; }
#ov-intro .ov-intro-cta { display: inline-block; line-height: 44px; margin: 40px 0 0; height: 44px; padding: 0 18px; border-radius: 10px;
  background: ${PAD.accent}; color: ${PAD.onAccent}; font-size: 16px; font-weight: 600; }
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
  if (reduced()) return null;
  // One timeline: the headline clears out of a blur, each later line starts as the one above is half in.
  // Blur is limited to the headline's few words; filters repaint, transforms and opacity do not.
  const tl = gsap.timeline({ defaults: { duration: T.dur.considered, ease: T.ease.enter } });
  groups.forEach((words, i) => {
    const each = Math.min(T.stagger.word, MAX_STAGGER / Math.max(words.length, 1));
    const from = { autoAlpha: 0, y: "0.3em", ...(i === 0 && { filter: `blur(${T.blur.text}px)` }) };
    const to = { autoAlpha: 1, y: 0, stagger: each, ...(i === 0 && { filter: "blur(0px)", clearProps: "filter" }) };
    tl.fromTo(words, from, to, i === 0 ? 0 : `<${T.stagger.line * 2}`);
  });
  return tl;
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
  // The call-to-action is a filled button, so its fill turns to dust with the words.
  const cta = intro.querySelector(".ov-intro-cta");
  if (cta) {
    const r = cta.getBoundingClientRect();
    ctx.fillStyle = PAD.accent;
    ctx.beginPath();
    ctx.roundRect(r.left, r.top, r.width, r.height, 10);
    ctx.fill();
  }
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

function runDust(intro, THREE) {
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
  // The shader owns the easing per mote, so the clock itself runs linear on GSAP's ticker.
  return gsap
    .to(uniforms.uTime, { value: total, duration: total, ease: "none", onUpdate: () => renderer.render(scene, camera) })
    .then(() => {
      geo.dispose();
      mat.dispose();
      renderer.dispose();
    });
}

function fadeIntro(intro) {
  if (reduced()) return Promise.resolve();
  return gsap.to(intro, { autoAlpha: 0, filter: `blur(${T.blur.soft}px)`, duration: T.dur.considered, ease: T.ease.exit }).then(() => {});
}

function startIntro() {
  if (new URLSearchParams(location.search).get("intro") === "0") return;
  const intro = buildIntro();
  const reveal = revealIntro(intro);
  // Fetch three.js while the landing page is read; the dust needs it only after the first click.
  const three = reduced() ? Promise.reject(new Error("reduced motion")) : import("./vendor/three.min.js");
  three.catch(() => {});
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
    // Words are sampled from their on-screen boxes, so finish the reveal before rasterizing.
    reveal?.progress(1);
    try {
      if (reduced()) throw new Error("reduced motion");
      await runDust(intro, await three);
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
let verdictTl = null;
let verdictTrigger = null;
const seen = { recovered: 0, verdict: "", flags: "", footing: [], dispatch: "", vision: "" };
const money = (n) => "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function rise(targets, vars = {}) {
  if (reduced() || !targets || targets.length === 0) return null;
  return gsap.fromTo(
    targets,
    { autoAlpha: 0, y: "0.3em" },
    { autoAlpha: 1, y: 0, overwrite: "auto", clearProps: "opacity,visibility,transform", ...vars },
  );
}

/* The one authored moment: the Pay and Hold figures count up, the status badge pops in,
   then the reason rises. It plays when the verdict is on screen. */
function playVerdict(verdict) {
  verdictTl?.kill();
  verdictTrigger?.kill();
  if (reduced()) return;
  const stamp = verdict.querySelector(".ov-stamp");
  const figures = verdict.querySelectorAll(".ov-fig");
  const lines = verdict.querySelectorAll(".alert-title, .alert-body");
  verdictTl = gsap
    .timeline({ paused: true })
    .fromTo(figures, { autoAlpha: 0, y: "0.3em" }, { autoAlpha: 1, y: 0, duration: T.dur.considered, stagger: T.stagger.line, clearProps: "opacity,visibility,transform" });
  verdict.querySelectorAll(".ov-fig-value").forEach((el, i) => {
    const target = parseFloat(el.textContent.replace(/[^0-9.]/g, "")) || 0;
    const n = { v: 0 };
    verdictTl.to(n, { v: target, duration: T.dur.considered * 1.5, ease: T.ease.standard, onUpdate: () => { el.textContent = money(n.v); } }, i * T.stagger.line);
  });
  verdictTl
    .fromTo(stamp, { autoAlpha: 0, scale: 0.6 }, { autoAlpha: 1, scale: 1, duration: 0.32, ease: "back.out(2.2)", clearProps: "transform" }, 0.35)
    .addLabel("impact")
        .fromTo(
      lines,
      { autoAlpha: 0, y: "0.3em" },
      { autoAlpha: 1, y: 0, duration: T.dur.considered, stagger: T.stagger.line, clearProps: "opacity,visibility,transform" },
      "impact+=0.04",
    );
  const r = verdict.getBoundingClientRect();
  if (r.top < innerHeight * 0.85 && r.bottom > 0) verdictTl.play();
  else verdictTrigger = ScrollTrigger.create({ trigger: verdict, start: "top 85%", once: true, onEnter: () => verdictTl.play() });
}

/* Run progress: the summary row fills in agent order (PO, goods receipt, invoice, difference),
   so the count of filled cells is real progress, shown above the run button. */
const RUN_STEPS = ["Reading the purchase order", "Checking the goods receipt", "Reading the invoice", "Comparing the totals", "Verifying the math"];
const run = { active: false, started: 0, clicked: 0, step: -1 };
let barTo = null;

function runButton() {
  const el = document.querySelector(".ov-run-hint");
  return el && (el.matches("button") ? el : el.querySelector("button"));
}

function trackRun(cells) {
  const btn = runButton();
  const help = document.querySelector(".ov-run-help");
  const track = document.querySelector(".ov-run-progress");
  const bar = track?.querySelector("i");
  if (!btn || !help || !bar) return;
  barTo ??= gsap.quickTo(bar, "scaleX", { duration: 0.4, ease: T.ease.standard });
  const busy = btn.disabled;

  // Only a click on Execute starts a run; the button is also disabled while an uploaded document is read.
  if (busy && !run.active && run.clicked) {
    run.active = true;
    run.started = run.clicked || performance.now(); // time from the click, not from when the button disabled
    run.step = -1;
    gsap.killTweensOf(track);
    gsap.set(track, { autoAlpha: 1 });
    gsap.set(bar, { scaleX: 0 });
  }
  if (busy) {
    const filled = cells.filter((t) => t.trim() && t.trim() !== "—").length;
    const step = Math.min(filled, RUN_STEPS.length - 1);
    if (step > run.step) {
      run.step = step;
      help.innerHTML = `Step ${step + 1} of ${RUN_STEPS.length} <span>· ${RUN_STEPS[step]}</span>`;
      barTo((step + 1) / (RUN_STEPS.length + 1));
    }
  } else if (run.active) {
    run.active = false;
    run.clicked = 0;
    const secs = ((performance.now() - run.started) / 1000).toFixed(1);
    help.innerHTML = `Checked in ${secs} seconds`;
    barTo(1);
    gsap.to(track, { autoAlpha: 0, duration: T.dur.considered, delay: 0.9 });
  }
}

function onDashboardChange() {
  // Gradio may patch this text in place or swap the element, so compare values, not nodes.
  const value = document.querySelector(".ov-impact-value");
  if (value && !counting) {
    const shown = parseFloat(value.textContent.replace(/[^0-9.]/g, "")) || 0;
    if (shown !== seen.recovered && !reduced()) {
      const write = (n) => document.querySelectorAll(".ov-impact-value").forEach((el) => { el.textContent = money(n); });
      const counter = { v: seen.recovered };
      counting = true;
      write(counter.v);
      gsap.to(counter, {
        v: shown,
        duration: T.dur.considered * 1.5,
        ease: T.ease.standard,
        overwrite: true,
        onUpdate: () => write(counter.v),
        onComplete: () => { write(shown); counting = false; },
      });
    }
    seen.recovered = shown;
  }

  const verdict = document.querySelector(".ov-verdict--alert, .ov-verdict--ok");
  // Key on the reason, not the figures: the count-up rewrites the figures, which must not read as a new verdict.
  const verdictSig = verdict ? verdict.className + (verdict.querySelector(".ov-verdict-why")?.textContent ?? "").trim() : "";
  if (verdict && verdictSig !== seen.verdict) playVerdict(verdict);
  seen.verdict = verdictSig;

  const rows = document.querySelectorAll(".ov-line-row--flagged td");
  const flagSig = [...rows].map((td) => td.textContent).join("|");
  if (rows.length && flagSig !== seen.flags && !reduced()) {
    // Animate to the current theme's tint, then hand the colour back to CSS so a later theme switch applies.
    const tint = getComputedStyle(rows[0]).backgroundColor;
    gsap.fromTo(rows, { backgroundColor: "rgba(0,0,0,0)" }, {
      backgroundColor: tint,
      duration: T.dur.considered,
      stagger: T.stagger.item,
      ease: T.ease.standard,
      clearProps: "backgroundColor",
    });
  }
  seen.flags = flagSig;

  const cells = [...document.querySelectorAll(".ov-footing tr:nth-child(2) td")];
  const texts = cells.map((td) => td.textContent);
  const changed = cells.filter((td, i) => texts[i] !== seen.footing[i]);
  if (changed.length && seen.footing.length) rise(changed, { stagger: T.stagger.item });
  seen.footing = texts;
  trackRun(texts);
  // The switch lives in the header, which Gradio re-renders on every run, so re-sync its state.
  syncThemeToggle();

  const dispatch = document.querySelector(".ov-dispatch-success");
  const dispatchSig = dispatch ? dispatch.textContent : "";
  if (dispatch && dispatchSig !== seen.dispatch) rise([dispatch], { duration: T.dur.considered });
  seen.dispatch = dispatchSig;

  const vision = document.querySelector(".ov-vision-badge");
  const visionSig = vision ? vision.textContent : "";
  if (vision && visionSig !== seen.vision && seen.vision) rise([vision]);
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
  }).observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["disabled"] });
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
  // GSAP cannot reach the ::view-transition pseudo-elements, so this one wipe stays on the Web Animations API.
  if (reduced() || !document.startViewTransition) return apply();
  const r = origin.getBoundingClientRect();
  const x = r.left + r.width / 2, y = r.top + r.height / 2;
  const radius = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
  document.startViewTransition(apply).ready.then(() => {
    document.documentElement.animate(
      { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
      { duration: T.dur.considered * 1250, easing: "cubic-bezier(0.16, 1, 0.3, 1)", pseudoElement: "::view-transition-new(root)" },
    );
  });
}

document.addEventListener("click", (e) => {
  const toggle = e.target.closest?.("#ov-theme-toggle");
  if (toggle) setTheme(!isDark(), toggle);
  // The run button's attention ring has done its job once the user finds it.
  if (e.target.closest?.(".ov-run-hint")) {
    document.documentElement.classList.add("ov-has-run");
    run.clicked = performance.now();
  }
});

startIntro();
watchDashboard();
