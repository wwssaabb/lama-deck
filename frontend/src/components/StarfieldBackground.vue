<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

interface Star {
  x: number
  y: number
  r: number
  phase: number
  speed: number
  depth: number
}

const canvasRef = ref<HTMLCanvasElement | null>(null)

let raf = 0
let resizeObserver: ResizeObserver | null = null
let stars: Star[] = []
let width = 0
let height = 0
let dpr = 1
let start = 0
let reduceMotion = false

function buildStars() {
  const count = Math.min(320, Math.round((width * height) / 5200))
  stars = Array.from({ length: count }, () => {
    const depth = 0.35 + Math.random() * 0.65
    return {
      x: Math.random() * width,
      y: Math.random() * height,
      r: 0.4 + Math.random() * 1.5 * depth,
      phase: Math.random() * Math.PI * 2,
      speed: 0.6 + Math.random() * 1.6,
      depth,
    }
  })
}

function paintBackground(ctx: CanvasRenderingContext2D, time: number) {
  const base = ctx.createLinearGradient(0, 0, width * 0.3, height)
  base.addColorStop(0, '#cbe7ff')
  base.addColorStop(0.45, '#e6f4ff')
  base.addColorStop(1, '#e7fbf6')
  ctx.fillStyle = base
  ctx.fillRect(0, 0, width, height)

  const sunX = width * 0.84
  const sunY = height * 0.1
  const sunR = Math.max(width, height) * 0.55
  const sun = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, sunR)
  sun.addColorStop(0, 'rgba(255, 255, 255, 0.95)')
  sun.addColorStop(0.35, 'rgba(255, 246, 194, 0.5)')
  sun.addColorStop(1, 'rgba(255, 255, 255, 0)')
  ctx.fillStyle = sun
  ctx.fillRect(0, 0, width, height)

  const drift = time * 0.000018
  const clouds = [
    { x: 0.14, y: 0.2, r: 0.3, a: 0.9, sx: 0.06, p: 0 },
    { x: 0.46, y: 0.12, r: 0.26, a: 0.75, sx: 0.05, p: 1.4 },
    { x: 0.72, y: 0.36, r: 0.32, a: 0.6, sx: 0.07, p: 2.6 },
    { x: 0.24, y: 0.58, r: 0.34, a: 0.5, sx: 0.05, p: 3.9 },
    { x: 0.88, y: 0.66, r: 0.3, a: 0.55, sx: 0.06, p: 5.2 },
    { x: 0.55, y: 0.44, r: 0.24, a: 0.45, sx: 0.04, p: 6.4 },
  ]
  for (const cloud of clouds) {
    const cx = (cloud.x + Math.sin(drift * 6 + cloud.p) * cloud.sx) * width
    const cy = (cloud.y + Math.cos(drift * 5 + cloud.p) * cloud.sx * 0.5) * height
    const radius = cloud.r * Math.max(width, height) * 0.6
    const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius)
    glow.addColorStop(0, `rgba(255, 255, 255, ${cloud.a})`)
    glow.addColorStop(0.55, `rgba(255, 255, 255, ${cloud.a * 0.45})`)
    glow.addColorStop(1, 'rgba(255, 255, 255, 0)')
    ctx.fillStyle = glow
    ctx.fillRect(0, 0, width, height)
  }

  const horizon = height * 0.8
  const sea = ctx.createLinearGradient(0, horizon, 0, height)
  sea.addColorStop(0, 'rgba(125, 211, 252, 0)')
  sea.addColorStop(0.45, 'rgba(103, 232, 249, 0.28)')
  sea.addColorStop(1, 'rgba(45, 212, 191, 0.42)')
  ctx.fillStyle = sea
  ctx.fillRect(0, horizon, width, height - horizon)

  ctx.save()
  for (let i = 0; i < 6; i += 1) {
    const y = horizon + ((i + 1) / 7) * (height - horizon)
    const offset = Math.sin(time * 0.00035 + i * 1.1) * 60
    const streak = ctx.createLinearGradient(0, 0, width, 0)
    streak.addColorStop(0, 'rgba(255,255,255,0)')
    streak.addColorStop(0.5, `rgba(255,255,255,${0.5 - i * 0.05})`)
    streak.addColorStop(1, 'rgba(255,255,255,0)')
    ctx.globalAlpha = 0.5
    ctx.fillStyle = streak
    ctx.fillRect(offset, y, width, 1.6)
  }
  ctx.restore()
}

function paintStars(ctx: CanvasRenderingContext2D, time: number) {
  for (const star of stars) {
    const twinkle = 0.25 + 0.75 * Math.abs(Math.sin(time * 0.001 * star.speed + star.phase))
    const driftY = ((time * 0.004 * star.depth) % (height + 40)) - 20
    const y = (star.y - driftY + height) % height
    ctx.globalAlpha = twinkle * (0.35 + star.depth * 0.5)
    ctx.fillStyle = star.depth > 0.8 ? '#ffffff' : '#7dd3fc'
    ctx.beginPath()
    ctx.arc(star.x, y, star.r * 1.15, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1
}

function frame(time: number) {
  const canvas = canvasRef.value
  const ctx = canvas?.getContext('2d')
  if (!canvas || !ctx) return
  if (!start) start = time
  const elapsed = reduceMotion ? 0 : time - start

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  paintBackground(ctx, elapsed)
  paintStars(ctx, elapsed)

  raf = requestAnimationFrame(frame)
}

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  dpr = Math.min(window.devicePixelRatio || 1, 1.5)
  width = window.innerWidth
  height = window.innerHeight
  canvas.width = Math.round(width * dpr)
  canvas.height = Math.round(height * dpr)
  canvas.style.width = `${width}px`
  canvas.style.height = `${height}px`
  buildStars()
}

onMounted(() => {
  reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  resize()
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(document.documentElement)
  raf = requestAnimationFrame(frame)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  if (raf) cancelAnimationFrame(raf)
})
</script>

<template>
  <canvas ref="canvasRef" class="starfield" aria-hidden="true" />
</template>

<style scoped>
.starfield {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  display: block;
}
</style>
