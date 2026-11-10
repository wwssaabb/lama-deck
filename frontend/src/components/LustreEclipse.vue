<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch, type CSSProperties } from 'vue'

/* eslint-disable */

// ─────────────────────────────────────────────────────────────────────────────
// 类型定义
// ─────────────────────────────────────────────────────────────────────────────

type RGBA = [number, number, number, number]

export interface Placement {
  x?: number
  y?: number
  angle?: number
  tilt?: number
}

export interface Advanced {
  bandDepth?: number
  cornerDepth?: number
  bulgeAt?: number
  bulgeWidth?: number
  edgeFade?: number
  satin?: number
  crease?: number
  creaseDepth?: number
  glow?: number
  brightness?: number
  whiteColor?: string
  indigoColor?: string
  deepColor?: string
  grain?: number
  vignette?: number
  foldMs?: number
  breathe?: number
  breatheMs?: number
  warp?: number
  warpMs?: number
  hover?: number
  pull?: number
  hoverTwist?: number
  hoverRadius?: number
}

export interface LustreEclipseProps {
  background?: string
  baseColor?: string
  accentColor?: string
  lineColor?: string
  folds?: number
  twist?: number
  speed?: number
  direction?: 'out' | 'in'
  scale?: number
  placement?: Placement
  advanced?: Advanced
  style?: CSSProperties
}

const props = withDefaults(defineProps<LustreEclipseProps>(), {
  background: '#000000',
  baseColor: '#443AD9',
  accentColor: '#41D8FC',
  lineColor: '#33FC41',
  folds: 3,
  twist: 50,
  speed: 74,
  direction: 'in',
  scale: 68,
  placement: () => ({ x: 0, y: 0, angle: 0, tilt: 0 }),
  advanced: () => ({}),
  style: () => ({}),
})

// ─────────────────────────────────────────────────────────────────────────────
// 常量 / 默认值
// ─────────────────────────────────────────────────────────────────────────────

const MOVED_CONTROLS: { into: Record<string, string>; out: Record<string, string> } = {
  into: {},
  out: { hover: 'advanced' },
}
const GROUP_FALLBACKS: Record<string, any> = {}

function withMovedControls(p: LustreEclipseProps): LustreEclipseProps {
  const out: any = { ...p }
  for (const [k, g] of Object.entries(MOVED_CONTROLS.into)) out[k] = (p as any)?.[g]?.[k] ?? GROUP_FALLBACKS[g]?.[k]
  for (const [k, g] of Object.entries(MOVED_CONTROLS.out)) {
    if (out[k] !== undefined) out[g] = { ...(out[g] ?? {}), [k]: out[k] }
  }
  return out
}

const DEFAULTS = {
  background: '#000000',
  baseColor: '#443AD9',
  accentColor: '#41D8FC',
  lineColor: '#33FC41',
  folds: 3,
  twist: 50,
  speed: 74,
  direction: 'in' as const,
  scale: 68,
}

const DEFAULT_ADVANCED: Required<Advanced> = {
  bandDepth: 36,
  cornerDepth: 3,
  bulgeAt: 5,
  bulgeWidth: 75,
  edgeFade: 60,
  satin: 55,
  crease: 3,
  creaseDepth: 60,
  glow: 30,
  brightness: 105,
  whiteColor: '#FBDEFF',
  indigoColor: '#372BBD',
  deepColor: '#281B83',
  grain: 0,
  vignette: 0,
  foldMs: 6000,
  breathe: 3,
  breatheMs: 9000,
  warp: 6,
  warpMs: 7000,
  hover: 50,
  pull: 5,
  hoverTwist: 20,
  hoverRadius: 30,
}

const DEFAULT_PLACEMENT: Required<Placement> = { x: 0, y: 0, angle: 0, tilt: 0 }

const cl = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v))
const num = (v: unknown, d: number) => (typeof v === 'number' && Number.isFinite(v) ? v : d)
const DEG = Math.PI / 180

// ─────────────────────────────────────────────────────────────────────────────
// 颜色解析（原样保留）
// ─────────────────────────────────────────────────────────────────────────────

const COLOR_CACHE = new Map<string, RGBA | null>()

function parseColor(input: string | undefined, fallback: RGBA): RGBA {
  if (typeof input !== 'string') return fallback
  let hit = COLOR_CACHE.get(input)
  if (hit === undefined) {
    hit = parseColorRaw(input)
    COLOR_CACHE.set(input, hit)
  }
  return hit ?? fallback
}

function parseColorRaw(raw: string): RGBA | null {
  let s = raw.trim()
  const v = /^var\(\s*--[^,]+,\s*(.+)\)$/.exec(s)
  if (v) s = v[1].trim()
  if (s[0] === '#') {
    const h = s.slice(1)
    const x = (a: string) => parseInt(a, 16)
    let r: number, g: number, b: number, a = 255
    if (h.length === 3 || h.length === 4) {
      r = x(h[0] + h[0]); g = x(h[1] + h[1]); b = x(h[2] + h[2])
      if (h.length === 4) a = x(h[3] + h[3])
    } else if (h.length === 6 || h.length === 8) {
      r = x(h.slice(0, 2)); g = x(h.slice(2, 4)); b = x(h.slice(4, 6))
      if (h.length === 8) a = x(h.slice(6, 8))
    } else return null
    const out: RGBA = [r / 255, g / 255, b / 255, a / 255]
    return out.every(Number.isFinite) ? out : null
  }
  const m = /^(rgba?|hsla?)\(([^)]*)\)$/i.exec(s)
  if (!m) return null
  const parts = m[2].split(/[\s,/]+/).filter(Boolean)
  if (parts.length < 3) return null
  const numf = (p: string, scale: number) => (p.endsWith('%') ? (parseFloat(p) / 100) * scale : parseFloat(p))
  const alpha = parts.length > 3 ? numf(parts[3], 1) : 1
  let rgb: [number, number, number]
  if (m[1].toLowerCase().startsWith('rgb')) {
    rgb = [numf(parts[0], 255) / 255, numf(parts[1], 255) / 255, numf(parts[2], 255) / 255]
  } else {
    const hh = (((parseFloat(parts[0]) % 360) + 360) % 360) / 360
    const ss = numf(parts[1], 1), ll = numf(parts[2], 1)
    const q = ll < 0.5 ? ll * (1 + ss) : ll + ss - ll * ss
    const p = 2 * ll - q
    const f = (t: number) => {
      t = (t + 1) % 1
      if (t < 1 / 6) return p + (q - p) * 6 * t
      if (t < 1 / 2) return q
      if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6
      return p
    }
    rgb = [f(hh + 1 / 3), f(hh), f(hh - 1 / 3)]
  }
  const out: RGBA = [rgb[0], rgb[1], rgb[2], alpha]
  return out.every(Number.isFinite) ? (out.map((c) => Math.min(1, Math.max(0, c))) as RGBA) : null
}

// ─────────────────────────────────────────────────────────────────────────────
// Uniform 计算
// ─────────────────────────────────────────────────────────────────────────────

function staticUniforms(p: LustreEclipseProps): Record<string, number[]> {
  const adv = { ...DEFAULT_ADVANCED, ...(p.advanced ?? {}) }
  const pl = { ...DEFAULT_PLACEMENT, ...(p.placement ?? {}) }
  const A = DEFAULT_ADVANCED
  const rgb = (v: unknown, fb: string) => parseColor(typeof v === 'string' ? v : fb, parseColor(fb, [0, 0, 0, 1])).slice(0, 3)
  const tilt = cl(num(pl.tilt, 0), -80, 80) * DEG
  const angle = cl(num(pl.angle, 0), -180, 180) * DEG
  return {
    uBg: rgb(p.background, DEFAULTS.background),
    uDeep: rgb(adv.deepColor, A.deepColor),
    uIndigo: rgb(adv.indigoColor, A.indigoColor),
    uBase: rgb(p.baseColor, DEFAULTS.baseColor),
    uLine: rgb(p.lineColor, DEFAULTS.lineColor),
    uAccent: rgb(p.accentColor, DEFAULTS.accentColor),
    uWhite: rgb(adv.whiteColor, A.whiteColor),
    uFolds: [cl(Math.round(num(p.folds, DEFAULTS.folds)), 1, 6) / 3],
    uTwist: [cl(num(p.twist, DEFAULTS.twist), 0, 100) / 50],
    uDepthK: [cl(num(adv.bandDepth, A.bandDepth), 5, 60) / 36],
    uCornerK: [(cl(num(adv.cornerDepth, A.cornerDepth), 0, 30) + 1) / 4],
    uBulge: [(cl(num(adv.bulgeAt, A.bulgeAt), -100, 100) - A.bulgeAt) / 100],
    uBulgeW: [cl(num(adv.bulgeWidth, A.bulgeWidth), 20, 200) / 75],
    uFade: [1 - (cl(num(adv.edgeFade, A.edgeFade), 0, 100) - A.edgeFade) / 200],
    uSatin: [cl(num(adv.satin, A.satin), 0, 100) / 55],
    uCrease: [cl(num(adv.crease, A.crease), 1, 30) / 100, (cl(num(adv.creaseDepth, A.creaseDepth), 0, 100) / 60) * 0.2],
    uGlow: [(cl(num(adv.glow, A.glow), 0, 100) / 30) * 0.05],
    uGain: [(cl(num(adv.brightness, A.brightness), 20, 150) / 105) * 0.985],
    uBreathe: [cl(num(adv.breathe, A.breathe), 0, 15) / 100],
    uWarp: [(cl(num(adv.warp, A.warp), 0, 60) / 1000) * 2],
    uPtr: [
      cl(num(adv.hover, A.hover), 0, 100) / 50,
      (cl(num(adv.pull, A.pull), 0, 20) / 100) * 3,
      (cl(num(adv.hoverTwist, A.hoverTwist), 0, 100) / 100) * 0.6,
      (cl(num(adv.hoverRadius, A.hoverRadius), 5, 100) / 100) * 2,
    ],
    uGrain: [cl(num(adv.grain, A.grain), 0, 100) / 100],
    uVig: [cl(num(adv.vignette, A.vignette), 0, 100) / 100],
    uScale: [cl(num(p.scale, DEFAULTS.scale), 10, 300) / 100],
    uOff: [cl(num(pl.x, 0), -50, 50) / 100, -cl(num(pl.y, 0), -50, 50) / 100],
    uRot: [Math.cos(angle), Math.sin(angle)],
    uTiltSC: [Math.sin(tilt), Math.cos(tilt)],
  }
}

function motionOf(p: LustreEclipseProps) {
  const adv = { ...DEFAULT_ADVANCED, ...(p.advanced ?? {}) }
  const A = DEFAULT_ADVANCED
  return {
    rate: cl(num(p.speed, DEFAULTS.speed), 0, 100) / 50,
    dir: p.direction === 'in' ? -1 : 1,
    foldS: cl(num(adv.foldMs, A.foldMs), 500, 30000) / 1000,
    breatheS: cl(num(adv.breatheMs, A.breatheMs), 1000, 30000) / 1000,
    warpS: cl(num(adv.warpMs, A.warpMs), 1000, 30000) / 1000,
    folds: cl(Math.round(num(p.folds, DEFAULTS.folds)), 1, 6),
    hover: num(adv.hover, A.hover) > 0,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 拟合常数 / 查找表烘焙
// ─────────────────────────────────────────────────────────────────────────────

const TOP_PHASE = [0.3176, 0.2698, 0.2752, -0.2182, -0.6756, 0.0133, 0.2642, 0.076]
const RIGHT_PHASE = [0.2087, -0.1353, 0.3284, -0.2611, -0.8626, -0.0367, 0.268, -0.3745]
const TOP_ENV = [0.48, 0.8911, 0.8886, 1.9023, 0.6989, 3.7343, 0.4005, 1.6022, 0.5564, 0.5922, 1.2456, 1.9118]
const RIGHT_ENV = [0.39, 1.0224, 0.7461, 2.1255, 1.9145, 5.9036, 0.2932, 1.6862, 0.1189, 0.646, 1.2745, 1.9879]
const BREATHE_PHASE = 0.45

const ENV_N = 512
const ENV_AMAX = 2.6

function bakeEnv(out: Float32Array, depthK: number, cornerK: number, bulge: number, bulgeW: number, fade: number) {
  const rows = [TOP_ENV, RIGHT_ENV]
  for (let row = 0; row < 2; row++) {
    const [H, ac, aw, de, ks, sm, , , , , la, lb] = rows[row]
    for (let i = 0; i < ENV_N; i++) {
      const a = ((i + 0.5) / ENV_N) * ENV_AMAX
      const dome = H * depthK * Math.exp(-Math.pow(Math.abs(a - ac + bulge) / (aw * bulgeW), de)) + 1e-4
      const ray = Math.max(ks * cornerK * a, 1e-4)
      const D = Math.pow(Math.pow(dome, -sm) + Math.pow(ray, -sm), -1 / sm)
      const t = cl((a - la * fade) / ((lb - la) * fade), 0, 1)
      const o = (row * ENV_N + i) * 2
      out[o] = D
      out[o + 1] = 1 - t * t * (3 - 2 * t)
    }
  }
}

const f = (x: number) => x.toFixed(4)
const phaseArgs = (P: number[]) => P.map(f).join(', ')
const envArgs = (E: number[], row: number) =>
  [row + 0.5, E[0], E[6], E[7], E[8], E[9]].map((x, i) => (i === 0 ? (x / 2).toFixed(2) : f(x))).join(', ')

// ─────────────────────────────────────────────────────────────────────────────
// Shader 源码（与原实现完全一致）
// ─────────────────────────────────────────────────────────────────────────────

const FRAG = `#version 300 es
precision highp float;
uniform vec2 uRes;
uniform float uS;
uniform float uPx;
uniform vec2 uAx;
uniform vec3 uT;
uniform vec2 uMouse;
uniform float uHover;
uniform float uSeed;
uniform vec3 uBg;
uniform vec3 uDeep;
uniform vec3 uIndigo;
uniform vec3 uBase;
uniform vec3 uLine;
uniform vec3 uAccent;
uniform vec3 uWhite;
uniform float uFolds;
uniform float uTwist;
uniform sampler2D uEnv;
uniform float uSatin;
uniform vec2 uCrease;
uniform float uGlow;
uniform float uGain;
uniform float uBreathe;
uniform float uWarp;
uniform vec4 uPtr;
uniform float uGrain;
uniform float uVig;
uniform float uScale;
uniform vec2 uOff;
uniform vec2 uRot;
uniform vec2 uTiltSC;
out vec4 outColor;
const float PI = 3.14159265;
const float TAU = 6.2831853;
const float FOCAL = 4.4;
const float R1 = 0.218;
const float R2 = 0.317;
const float R3 = 0.371;
const float R4 = 0.484;
const float R5 = 0.735;
const float GLOW_W = 1.3;
const float CORNER_DIM = 0.65;
const float CORNER_R = 0.8;
const float OUTER = 0.45;
const float ENV_AMAX = ${ENV_AMAX.toFixed(2)};

vec3 ramp(float v) {
    v = clamp(v, 0.0, 1.0);
    vec3 c = uBg;
    c += (uDeep - uBg) * clamp(v / R1, 0.0, 1.0);
    c += (uIndigo - uDeep) * clamp((v - R1) / (R2 - R1), 0.0, 1.0);
    c += (uBase - uIndigo) * clamp((v - R2) / (R3 - R2), 0.0, 1.0);
    c += (uLine - uBase) * clamp((v - R3) / (R4 - R3), 0.0, 1.0);
    c += (uAccent - uLine) * clamp((v - R4) / (R5 - R4), 0.0, 1.0);
    c += (uWhite - uAccent) * clamp((v - R5) / (1.0 - R5), 0.0, 1.0);
    return c;
}

vec2 toContent(vec2 s) {
    s -= uOff * 2.0 * uAx;
    s = vec2(uRot.x * s.x - uRot.y * s.y, uRot.y * s.x + uRot.x * s.y);
    float fc = FOCAL / uScale;
    float den = max(fc * uTiltSC.y - s.y * uTiltSC.x, 1e-3);
    float v = s.y * fc / den;
    return vec2(s.x * (fc + v * uTiltSC.x) / fc, v);
}

float phaseOf(vec2 ad, float P0, float P1, float P2, float P3, float P4, float P5, float P6, float off) {
    float a = max(ad.x, 1e-3);
    float r = length(ad);
    float fan = (ad.y / a) * (1.0 + uTwist * (P1 + P2 * a) * a) + uTwist * P3 * ad.y;
    float g = mix(0.5, 1.0, smoothstep(0.0, 0.5, r));
    return (fan / P0 * g + uTwist * ((P4 + (P5 + P6 * r) * r) * r)) * uFolds + off;
}

vec2 envOf(vec2 ad, float br, float row, float H, float e0, float e1, float cl0, float rc) {
    float a = ad.x;
    float d = ad.y;
    if (a <= 0.0 || a >= ENV_AMAX) return vec2(0.0);
    vec2 lut = texture(uEnv, vec2(a / ENV_AMAX, row)).rg;
    float D = max(lut.x, 1e-4) * (1.0 + br / H);
    float q = d / D;
    if (q > e1 * GLOW_W || q < -OUTER || lut.y <= 0.0) return vec2(0.0);
    float r = length(ad);
    float e = 1.0 - smoothstep(e0, e1, q);
    float g = 1.0 - smoothstep(e0, e1 * GLOW_W, q);
    float k = (cl0 + (1.0 - cl0) * smoothstep(0.0, rc, r)) * lut.y;
    k *= mix(CORNER_DIM, 1.0, smoothstep(0.0, CORNER_R, r));
    k *= 1.0 - smoothstep(0.0, 1.0, -q / OUTER);
    return vec2(e, g) * k;
}

float leafOf(float ph, float fw, float r) {
    float u = fract(ph);
    float s = sin(PI * u);
    float cS = clamp(0.25 + 0.5 * r, 0.3, 0.92) * uSatin;
    float rr = 1.1 / max(r, 0.5);
    float p = clamp(min(1.6 * rr * rr, 0.27 / max(fw, 1e-4)), 0.8, 8.0);
    float m = 0.15 * (1.0 - smoothstep(0.6, 1.0, r)) * uSatin;
    float du = min(u, 1.0 - u);
    float w = max(uCrease.x, fw * 1.2);
    float cd = uCrease.y * (uCrease.x / w) * smoothstep(0.3, 0.8, r);
    float s2 = s * s;
    float h = 1.0 - cS * pow(1.0 - s, p) - m * s2 * s2 - cd * exp(-(du * du) / (w * w));
    return mix(clamp(h, 0.0, 1.0), 0.86, smoothstep(0.12, 0.45, fw));
}

float crescent(vec2 ad, float ae, float br, float slide, float pxu,
               float P0, float P1, float P2, float P3, float P4, float P5, float P6, float off,
               float row, float H, float e0, float e1, float cl0, float rc) {
    vec2 e = envOf(ad, br, row, H, e0, e1, cl0, rc);
    if (e.y <= 1e-4) return 0.0;
    if (e.x <= 1e-4) return uGlow * e.y;
    float ph = phaseOf(ad, P0, P1, P2, P3, P4, P5, P6, off) + slide;
    float a = max(ad.x, 1e-3);
    float r = length(ad);
    float k = uFolds * mix(0.5, 1.0, smoothstep(0.0, 0.5, r)) / P0;
    float fw = pxu * k * length(vec2(ad.y / (a * a * ae), 1.0 / a));
    float b = e.x * leafOf(ph, fw, r) * uGain;
    return 1.0 - (1.0 - b) * (1.0 - uGlow * e.y);
}

void main() {
    vec2 res = max(uRes, vec2(1.0));
    vec2 uv = gl_FragCoord.xy / res;
    vec2 q = toContent((gl_FragCoord.xy - 0.5 * res) / max(uS, 1.0));
    vec2 mp = toContent(uMouse);

    vec2 md = q - mp;
    float R = max(uPtr.w, 1e-3) / uScale;
    float bump = uHover * uPtr.x * exp(-dot(md, md) / (R * R));
    q -= md * bump * uPtr.y;

    vec2 A = uAx;
    vec2 adT = vec2((A.x - q.x) / A.x, A.y - q.y);
    vec2 adR = vec2((A.y - q.y) / A.y, A.x - q.x);
    vec2 adL = vec2((q.y + A.y) / A.y, q.x + A.x);
    vec2 adB = vec2((q.x + A.x) / A.x, q.y + A.y);

    float wph = TAU * uT.z;
    adT.y += uWarp * (0.6 * sin(adT.x * 2.3 + wph) + 0.4 * sin(adT.x * 4.1 - wph * 1.3 + 1.7));
    adL.y += uWarp * (0.6 * sin(adL.x * 2.3 + wph) + 0.4 * sin(adL.x * 4.1 - wph * 1.3 + 1.7));
    adR.y += uWarp * (0.6 * sin(adR.x * 2.3 + wph + 2.1) + 0.4 * sin(adR.x * 4.1 - wph * 1.3 + 0.4));
    adB.y += uWarp * (0.6 * sin(adB.x * 2.3 + wph + 2.1) + 0.4 * sin(adB.x * 4.1 - wph * 1.3 + 0.4));

    float slide = uT.x + bump * uPtr.z;
    float br = uBreathe * uT.y;
    float pxu = 1.0 / max(uS, 1e-3);
    float v = crescent(adT, A.x, br, slide, pxu, ${phaseArgs(TOP_PHASE)}, ${envArgs(TOP_ENV, 0)});
    v = max(v, crescent(adL, A.y, br, slide, pxu, ${phaseArgs(TOP_PHASE)}, ${envArgs(TOP_ENV, 0)}));
    v = max(v, crescent(adR, A.y, br, slide, pxu, ${phaseArgs(RIGHT_PHASE)}, ${envArgs(RIGHT_ENV, 1)}));
    v = max(v, crescent(adB, A.x, br, slide, pxu, ${phaseArgs(RIGHT_PHASE)}, ${envArgs(RIGHT_ENV, 1)}));

    vec3 col = ramp(v);
    float vd = length((uv - 0.5) * vec2(A.x / max(A.x, A.y), A.y / max(A.x, A.y))) * 1.6;
    col *= 1.0 - uVig * 0.6 * smoothstep(0.35, 1.05, vd);
    vec2 cell = floor(gl_FragCoord.xy / max(uPx, 1.0));
    float n = fract(sin(dot(cell + uSeed * 17.0, vec2(12.9898, 78.233))) * 43758.5453) - 0.5;
    col += n * (uGrain * 0.12 + 2.0 / 255.0);
    outColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}`

const VERT = `#version 300 es
in vec2 aPos;
void main() { gl_Position = vec4(aPos, 0.0, 1.0); }`

const MAX_PIXELS = 3.2e6
const MIN_QUALITY = 0.6

// ─────────────────────────────────────────────────────────────────────────────
// 组件状态 / 生命周期
// ─────────────────────────────────────────────────────────────────────────────

const rootRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)

const uniRef = ref<Record<string, number[]> | null>(null)
const dirtyRef = ref(true)
const motionRef = ref(motionOf(props))
const wakeRef = ref<() => void>(() => {})

let teardown: (() => void) | null = null

function syncProps() {
  const p = withMovedControls({ ...props } as LustreEclipseProps)
  const next = staticUniforms(p)
  const prev = uniRef.value
  let changed = !prev
  if (prev) {
    for (const k in next) {
      if (next[k].some((v, i) => v !== prev[k][i])) {
        changed = true
        break
      }
    }
  }
  if (changed) {
    uniRef.value = next
    dirtyRef.value = true
  }
  motionRef.value = motionOf(p)
}

// 初始化静态 uniform
syncProps()

// 监听 props 变化
watch(
  () => [
    props.background, props.baseColor, props.accentColor, props.lineColor,
    props.folds, props.twist, props.speed, props.direction, props.scale,
    props.placement, props.advanced,
  ],
  () => {
    syncProps()
    wakeRef.value()
  },
  { deep: true }
)

onMounted(() => {
  const root = rootRef.value
  const canvas = canvasRef.value
  if (!root || !canvas) return

  const reduced = typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  let gl: WebGL2RenderingContext | null = null
  let prog: WebGLProgram | null = null
  let locs = new Map<string, WebGLUniformLocation | null>()
  let sent = new Map<string, Float64Array>()
  let staticSent: Record<string, number[]> | null = null

  const init = (): boolean => {
    gl = canvas.getContext('webgl2', {
      alpha: false,
      antialias: false,
      depth: false,
      stencil: false,
      powerPreference: 'low-power',
      preserveDrawingBuffer: false,
    })
    if (!gl) return false
    const sh = (type: number, src: string) => {
      const s = gl!.createShader(type)!
      gl!.shaderSource(s, src)
      gl!.compileShader(s)
      if (!gl!.getShaderParameter(s, gl!.COMPILE_STATUS) && !gl!.isContextLost())
        console.warn('LustreEclipse shader:', gl!.getShaderInfoLog(s))
      return s
    }
    const p = gl.createProgram()!
    const vs = sh(gl.VERTEX_SHADER, VERT)
    const fs = sh(gl.FRAGMENT_SHADER, FRAG)
    gl.attachShader(p, vs)
    gl.attachShader(p, fs)
    gl.linkProgram(p)
    gl.deleteShader(vs)
    gl.deleteShader(fs)
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
      if (!gl.isContextLost()) console.warn('LustreEclipse link:', gl.getProgramInfoLog(p))
      gl = null
      return false
    }
    prog = p
    gl.useProgram(p)
    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW)
    const loc = gl.getAttribLocation(p, 'aPos')
    gl.enableVertexAttribArray(loc)
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)
    const tex = gl.createTexture()
    gl.activeTexture(gl.TEXTURE0)
    gl.bindTexture(gl.TEXTURE_2D, tex)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
    gl.uniform1i(gl.getUniformLocation(p, 'uEnv'), 0)
    locs = new Map()
    sent = new Map()
    staticSent = null
    envKey = ''
    return true
  }

  const envData = new Float32Array(ENV_N * 2 * 2)
  let envKey = ''
  const syncEnv = (s: Record<string, number[]>) => {
    const g = gl!
    const key = `${s.uDepthK[0]}|${s.uCornerK[0]}|${s.uBulge[0]}|${s.uBulgeW[0]}|${s.uFade[0]}`
    if (key === envKey) return
    envKey = key
    bakeEnv(envData, s.uDepthK[0], s.uCornerK[0], s.uBulge[0], s.uBulgeW[0], s.uFade[0])
    g.texImage2D(g.TEXTURE_2D, 0, g.RG16F, ENV_N, 2, 0, g.RG, g.FLOAT, envData)
  }

  const set = (name: string, v: ArrayLike<number>) => {
    const g = gl!
    let loc = locs.get(name)
    if (loc === undefined) {
      loc = g.getUniformLocation(prog!, name)
      locs.set(name, loc)
    }
    if (!loc) return
    let last = sent.get(name)
    if (last && last.length === v.length) {
      let same = true
      for (let i = 0; i < v.length; i++) if (last[i] !== v[i]) { same = false; break }
      if (same) return
    }
    if (!last || last.length !== v.length) {
      last = new Float64Array(v.length)
      sent.set(name, last)
    }
    for (let i = 0; i < v.length; i++) last[i] = v[i]
    if (v.length === 1) g.uniform1f(loc, v[0])
    else if (v.length === 2) g.uniform2f(loc, v[0], v[1])
    else if (v.length === 3) g.uniform3f(loc, v[0], v[1], v[2])
    else g.uniform4f(loc, v[0], v[1], v[2], v[3])
  }
  const v1 = [0]
  const v2 = [0, 0]
  const v3 = [0, 0, 0]
  const set1 = (name: string, a: number) => { v1[0] = a; set(name, v1) }
  const set2 = (name: string, a: number, b: number) => { v2[0] = a; v2[1] = b; set(name, v2) }
  const set3 = (name: string, a: number, b: number, c: number) => { v3[0] = a; v3[1] = b; v3[2] = c; set(name, v3) }

  let lost = false
  let ready = init()
  let W = 0
  let H = 0
  let shown = 1
  let quality = 1
  const unit = () => Math.max(0.5, Math.min(W, H) / 2)

  const sizeCanvas = () => {
    if (W <= 0 || H <= 0) return
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    let k = dpr * cl(shown, 1, 2) * quality
    const px = W * H * k * k
    if (px > MAX_PIXELS) k *= Math.sqrt(MAX_PIXELS / px)
    const cw = Math.max(1, Math.round(W * k))
    const ch = Math.max(1, Math.round(H * k))
    if (canvas.width !== cw || canvas.height !== ch) {
      canvas.width = cw
      canvas.height = ch
      dirtyRef.value = true
      if (ready && gl && !lost) render()
    }
  }

  const measureShown = (r: DOMRectReadOnly) => {
    if (W <= 0 || r.width <= 0) return
    const s = r.width / W
    if (Math.abs(s - shown) / shown > 0.05) {
      shown = s
      sizeCanvas()
    }
  }

  const ro = new ResizeObserver((entries) => {
    const r = entries[0].contentRect
    W = r.width
    H = r.height
    measureShown(root.getBoundingClientRect())
    sizeCanvas()
    dirtyRef.value = true
    wake()
  })
  ro.observe(root)

  let cx = 0, cy = 0
  let moved = false
  let over = 0
  let tx = 0.5, ty = 0.5
  let mx = 0.5, my = 0.5
  let hov = 0

  const onMove = (e: PointerEvent) => {
    if (e.clientX === cx && e.clientY === cy && over) return
    cx = e.clientX
    cy = e.clientY
    moved = true
    over = 1
    wake()
  }
  const onLeave = () => { over = 0; wake() }
  const onUp = (e: PointerEvent) => { if (e.pointerType === 'touch') onLeave() }
  const onScroll = () => { if (over) { moved = true; wake() } }

  root.addEventListener('pointermove', onMove)
  root.addEventListener('pointerdown', onMove)
  root.addEventListener('pointerleave', onLeave)
  root.addEventListener('pointerup', onUp)
  root.addEventListener('pointercancel', onLeave)
  window.addEventListener('scroll', onScroll, { passive: true, capture: true })

  let onScreen = true
  let pageVisible = document.visibilityState !== 'hidden'
  const io = new IntersectionObserver((entries) => {
    const e = entries[entries.length - 1]
    onScreen = e.isIntersecting
    measureShown(e.boundingClientRect)
    wake()
  })
  io.observe(root)

  const onVis = () => { pageVisible = document.visibilityState !== 'hidden'; wake() }
  document.addEventListener('visibilitychange', onVis)

  let raf = 0
  let drift = 0, breathe = 0, warp = 0
  let lastTick = -1
  let lastDraw = -1
  let due = 0
  let tickEma = 1000 / 60
  let drawEma = 1000 / 60
  let drawn = 0
  let seed = 0

  function wake() {
    if (!raf && !lost && onScreen && pageVisible) {
      lastTick = -1
      raf = requestAnimationFrame(frame)
    }
  }
  wakeRef.value = () => { if (dirtyRef.value) wake() }

  function frame(now: number) {
    raf = 0
    if (lost || !onScreen || !pageVisible || !ready || !gl) return
    if (lastTick >= 0) tickEma += (Math.min(now - lastTick, 100) - tickEma) * 0.1
    lastTick = now
    const mo = motionRef.value
    const rate = mo.rate * (reduced ? 0.25 : 1)
    const leafPx = (rate * unit() * (uniRef.value ? uniRef.value.uScale[0] : 1) * 0.25 * 3) / mo.folds / mo.foldS
    const pointerBusy = moved || Math.abs(tx - mx) + Math.abs(ty - my) > 1e-4 || Math.abs(over - hov) > 1e-3
    const moving = rate > 0
    const fps = pointerBusy || (moving && leafPx > 30) ? 60 : moving ? 30 : 0
    if (fps === 0 && !dirtyRef.value) { lastDraw = -1; return }
    raf = requestAnimationFrame(frame)
    const interval = fps ? 1000 / fps : 0
    if (fps && lastDraw >= 0 && now < due - 3) return
    due = Math.max(due + interval, now - interval)
    const dt = lastDraw < 0 ? 1 / 60 : Math.min((now - lastDraw) / 1000, 0.1)
    if (lastDraw >= 0 && now - lastDraw < 200) drawEma += (now - lastDraw - drawEma) * 0.1
    lastDraw = now
    drawn++

    if (moved || drawn % 30 === 0) {
      const r = root.getBoundingClientRect()
      measureShown(r)
      if (moved && r.width > 0 && r.height > 0) {
        tx = (cx - r.left) / r.width
        ty = 1 - (cy - r.top) / r.height
      }
      moved = false
    }
    const kFollow = 1 - Math.exp(-dt / 0.06)
    const kSoft = 1 - Math.exp(-dt / 0.25)
    mx += (tx - mx) * kFollow
    my += (ty - my) * kFollow
    hov += (over - hov) * kSoft
    if (Math.abs(over - hov) < 1e-3) hov = over

    drift = (((drift + (dt * rate * mo.dir) / mo.foldS) % 1) + 1) % 1
    breathe = (breathe + (dt * rate) / mo.breatheS) % 1
    warp = (warp + (dt * rate) / mo.warpS) % 1
    if (fps) seed = (seed + 1) % 4096

    if (drawn > 30 && fps) {
      const expect = Math.max(interval, tickEma)
      if (drawEma > expect * 1.45 && quality > MIN_QUALITY) {
        quality = Math.max(MIN_QUALITY, quality * 0.88)
        drawEma = expect
        sizeCanvas()
      } else if (drawEma < expect * 1.12 && quality < 1 && drawn % 60 === 0) {
        quality = Math.min(1, quality * 1.06)
        sizeCanvas()
      }
    }
    render()
  }

  function render() {
    const g = gl
    if (!g) return
    const statics = uniRef.value!
    const u = unit() * statics.uScale[0]
    if (staticSent !== statics) {
      for (const k in statics) set(k, statics[k])
      syncEnv(statics)
      staticSent = statics
    }
    dirtyRef.value = false
    const pxPerCss = canvas.height / Math.max(H, 1)
    set2('uRes', canvas.width, canvas.height)
    set1('uPx', pxPerCss)
    set1('uS', u * pxPerCss)
    set2('uAx', W / 2 / u, H / 2 / u)
    set3('uT', drift, Math.sin(2 * Math.PI * (breathe - BREATHE_PHASE)), warp)
    set2('uMouse', ((mx - 0.5) * W) / u, ((my - 0.5) * H) / u)
    set1('uHover', motionRef.value.hover ? hov : 0)
    set1('uSeed', seed)
    g.viewport(0, 0, canvas.width, canvas.height)
    g.drawArrays(g.TRIANGLES, 0, 3)
    if (canvas.style.opacity !== '1') canvas.style.opacity = '1'
  }

  const onLost = (e: Event) => {
    e.preventDefault()
    lost = true
    ready = false
    canvas.style.opacity = '0'
    if (raf) cancelAnimationFrame(raf)
    raf = 0
  }
  const onRestored = () => {
    lost = false
    ready = init()
    dirtyRef.value = true
    wake()
  }
  canvas.addEventListener('webglcontextlost', onLost)
  canvas.addEventListener('webglcontextrestored', onRestored)

  wake()

  teardown = () => {
    if (raf) cancelAnimationFrame(raf)
    raf = 0
    lost = true
    wakeRef.value = () => {}
    ro.disconnect()
    io.disconnect()
    document.removeEventListener('visibilitychange', onVis)
    window.removeEventListener('scroll', onScroll, { capture: true })
    root.removeEventListener('pointermove', onMove)
    root.removeEventListener('pointerdown', onMove)
    root.removeEventListener('pointerleave', onLeave)
    root.removeEventListener('pointerup', onUp)
    root.removeEventListener('pointercancel', onLeave)
    canvas.removeEventListener('webglcontextlost', onLost)
    canvas.removeEventListener('webglcontextrestored', onRestored)
  }
})

onBeforeUnmount(() => {
  teardown?.()
  teardown = null
})
</script>

<template>
  <div
    ref="rootRef"
    :style="{
      position: 'fixed',
      inset: 0,
      zIndex: 0,
      pointerEvents: 'none',
      width: '100%',
      height: '100%',
      aspectRatio: '1200 / 800',
      overflow: 'hidden',
      background: props.background,
      touchAction: 'pan-y',
      ...props.style,
    }"
  >
    <canvas
      ref="canvasRef"
      :style="{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        display: 'block',
        opacity: 0,
      }"
    />
  </div>
</template>