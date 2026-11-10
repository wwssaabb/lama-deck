<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useEditorStore } from '../stores/editor'

interface Point {
  x: number
  y: number
}

const ZOOM_MIN = 0.1
const ZOOM_MAX = 8

const store = useEditorStore()
const wrapRef = ref<HTMLDivElement | null>(null)
const viewRef = ref<HTMLCanvasElement | null>(null)
const cursorVisible = ref(false)
const cursorStyle = ref<Record<string, string>>({})

let tintCanvas: HTMLCanvasElement | null = null
let frame = 0
let resizeObserver: ResizeObserver | null = null
let drawing = false
let panning = false
let lastPoint: Point | null = null
let axisStart: Point | null = null
let panOrigin = { x: 0, y: 0, panX: 0, panY: 0 }
let hoverPoint: Point | null = null
let axisLock: 'h' | 'v' | null = null
const axisBadge = ref('')

function clampZoom(value: number): number {
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, value))
}

function ensureTint(width: number, height: number): HTMLCanvasElement {
  if (!tintCanvas || tintCanvas.width !== width || tintCanvas.height !== height) {
    tintCanvas = document.createElement('canvas')
    tintCanvas.width = width
    tintCanvas.height = height
  }
  return tintCanvas
}

function niceStep(raw: number): number {
  const magnitude = Math.pow(10, Math.floor(Math.log10(Math.max(raw, 1))))
  const norm = raw / magnitude
  const factor = norm < 1.5 ? 1 : norm < 3.5 ? 2 : norm < 7.5 ? 5 : 10
  return factor * magnitude
}

function drawGrid(ctx: CanvasRenderingContext2D, view: HTMLCanvasElement, image: HTMLImageElement) {
  const scaleX = view.width / image.naturalWidth
  const scaleY = view.height / image.naturalHeight
  const step = niceStep(48 / Math.max(scaleX, 0.0001))

  ctx.save()
  ctx.lineWidth = 1
  for (const pass of [
    { color: 'rgba(0,0,0,0.45)', offset: 0 },
    { color: 'rgba(255,255,255,0.35)', offset: 1 },
  ]) {
    ctx.strokeStyle = pass.color
    for (let x = step; x < image.naturalWidth; x += step) {
      const sx = Math.round(x * scaleX) + pass.offset
      ctx.beginPath()
      ctx.moveTo(sx, 0)
      ctx.lineTo(sx, view.height)
      ctx.stroke()
    }
    for (let y = step; y < image.naturalHeight; y += step) {
      const sy = Math.round(y * scaleY) + pass.offset
      ctx.beginPath()
      ctx.moveTo(0, sy)
      ctx.lineTo(view.width, sy)
      ctx.stroke()
    }
  }
  ctx.restore()
}

function drawGuides(ctx: CanvasRenderingContext2D, view: HTMLCanvasElement, image: HTMLImageElement) {
  if (!hoverPoint) return
  const scaleX = view.width / image.naturalWidth
  const scaleY = view.height / image.naturalHeight
  const sx = Math.round(hoverPoint.x * scaleX) + 0.5
  const sy = Math.round(hoverPoint.y * scaleY) + 0.5

  ctx.save()
  ctx.lineWidth = 1
  for (const pass of [
    { color: 'rgba(0,0,0,0.5)', offset: 0 },
    { color: 'rgba(56,189,248,0.95)', offset: 1 },
  ]) {
    ctx.strokeStyle = pass.color
    ctx.beginPath()
    ctx.moveTo(sx + pass.offset, 0)
    ctx.lineTo(sx + pass.offset, view.height)
    ctx.moveTo(0, sy + pass.offset)
    ctx.lineTo(view.width, sy + pass.offset)
    ctx.stroke()
  }
  ctx.restore()
}

function render() {
  const view = viewRef.value
  const image = store.image?.element
  const mask = store.maskCanvas
  if (!view || !image) return
  const ctx = view.getContext('2d')
  if (!ctx) return

  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.clearRect(0, 0, view.width, view.height)
  ctx.drawImage(image, 0, 0, view.width, view.height)

  if (mask && store.maskVisible && store.maskOpacity > 0) {
    const tint = ensureTint(view.width, view.height)
    const tctx = tint.getContext('2d')
    if (tctx) {
      tctx.globalCompositeOperation = 'source-over'
      tctx.clearRect(0, 0, tint.width, tint.height)
      tctx.drawImage(mask, 0, 0, tint.width, tint.height)
      tctx.globalCompositeOperation = 'source-in'
      tctx.fillStyle = store.maskColor
      tctx.fillRect(0, 0, tint.width, tint.height)
      tctx.globalCompositeOperation = 'source-over'
      ctx.globalAlpha = store.maskOpacity / 100
      ctx.drawImage(tint, 0, 0)
      ctx.globalAlpha = 1
    }
  }

  if (store.showGrid) drawGrid(ctx, view, image)
  if (store.showGuides) drawGuides(ctx, view, image)
  drawAxisGuide(ctx, view)
}

function scheduleRender() {
  if (frame) return
  frame = requestAnimationFrame(() => {
    frame = 0
    render()
  })
}

function layout() {
  const wrap = wrapRef.value
  const view = viewRef.value
  const image = store.image?.element
  if (!wrap || !view || !image) return
  const cw = wrap.clientWidth
  const ch = wrap.clientHeight
  if (!cw || !ch) return

  const fit = Math.min(cw / image.naturalWidth, ch / image.naturalHeight)
  const scale = fit * store.zoom
  const dw = Math.max(1, Math.round(image.naturalWidth * scale))
  const dh = Math.max(1, Math.round(image.naturalHeight * scale))
  const dpr = Math.min(window.devicePixelRatio || 1, 2)

  view.style.width = `${dw}px`
  view.style.height = `${dh}px`
  view.style.transform = `translate(-50%, -50%) translate(${store.pan.x}px, ${store.pan.y}px)`
  view.width = Math.round(dw * dpr)
  view.height = Math.round(dh * dpr)
  render()
}

function toImage(event: PointerEvent | MouseEvent): Point {
  const view = viewRef.value!
  const image = store.image!.element
  const rect = view.getBoundingClientRect()
  return {
    x: ((event.clientX - rect.left) / rect.width) * image.naturalWidth,
    y: ((event.clientY - rect.top) / rect.height) * image.naturalHeight,
  }
}

function updateCursor(event: PointerEvent) {
  const wrap = wrapRef.value
  const view = viewRef.value
  const image = store.image?.element
  if (!wrap || !view || !image) {
    cursorVisible.value = false
    return
  }
  const wrapRect = wrap.getBoundingClientRect()
  const viewRect = view.getBoundingClientRect()
  const ratio = viewRect.width / image.naturalWidth
  const size = Math.max(4, store.brushSize * ratio)
  cursorStyle.value = {
    left: `${event.clientX - wrapRect.left}px`,
    top: `${event.clientY - wrapRect.top}px`,
    width: `${size}px`,
    height: `${size}px`,
    borderColor: store.tool === 'eraser' ? 'rgba(255,255,255,0.9)' : store.maskColor,
  }
  cursorVisible.value = store.tool !== 'pan'
}

function updateAxisLock(raw: Point, shiftKey: boolean) {
  if (!drawing || !axisStart) {
    axisLock = null
  } else if (!shiftKey) {
    axisLock = null
  } else if (!axisLock) {
    const dx = Math.abs(raw.x - axisStart.x)
    const dy = Math.abs(raw.y - axisStart.y)
    axisLock = dx >= dy ? 'h' : 'v'
  }
  axisBadge.value = axisLock === 'h' ? 'Shift 约束 · 水平' : axisLock === 'v' ? 'Shift 约束 · 垂直' : ''
}

function applyLock(point: Point): Point {
  if (!axisLock || !axisStart) return point
  return axisLock === 'h' ? { x: point.x, y: axisStart.y } : { x: axisStart.x, y: point.y }
}

function drawAxisGuide(ctx: CanvasRenderingContext2D, view: HTMLCanvasElement) {
  if (!drawing || !axisLock || !axisStart) return
  const scaleX = view.width / (store.image?.element.naturalWidth || 1)
  const scaleY = view.height / (store.image?.element.naturalHeight || 1)
  ctx.save()
  ctx.lineWidth = 1.5
  ctx.setLineDash([10, 7])
  ctx.strokeStyle = 'rgba(0,0,0,0.6)'
  ctx.beginPath()
  if (axisLock === 'h') {
    const y = Math.round(axisStart.y * scaleY) + 0.5
    ctx.moveTo(0, y)
    ctx.lineTo(view.width, y)
  } else {
    const x = Math.round(axisStart.x * scaleX) + 0.5
    ctx.moveTo(x, 0)
    ctx.lineTo(x, view.height)
  }
  ctx.stroke()
  ctx.setLineDash([])
  ctx.strokeStyle = '#38bdf8'
  ctx.stroke()
  ctx.restore()
}

function stroke(from: Point, to: Point) {
  const mask = store.maskCanvas
  if (!mask) return
  const ctx = mask.getContext('2d')
  if (!ctx) return
  ctx.globalCompositeOperation = store.tool === 'eraser' ? 'destination-out' : 'source-over'
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.lineWidth = store.brushSize
  ctx.strokeStyle = '#ffffff'
  ctx.beginPath()
  ctx.moveTo(from.x, from.y)
  ctx.lineTo(to.x, to.y)
  ctx.stroke()
  ctx.globalCompositeOperation = 'source-over'
}

function startPan(event: PointerEvent) {
  panning = true
  panOrigin = { x: event.clientX, y: event.clientY, panX: store.pan.x, panY: store.pan.y }
}

function onPointerDown(event: PointerEvent) {
  if (!store.image) return
  event.preventDefault()
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)

  if (event.button === 1 || store.tool === 'pan') {
    startPan(event)
    return
  }
  if (event.button !== 0 || !store.maskCanvas) return

  drawing = true
  axisLock = null
  axisBadge.value = ''
  store.pushUndo(store.snapshotMask())
  const point = toImage(event)
  axisStart = point
  lastPoint = point
  stroke(point, point)
  scheduleRender()
}

function onPointerMove(event: PointerEvent) {
  const image = store.image?.element
  if (image && viewRef.value) {
    const rect = viewRef.value.getBoundingClientRect()
    if (
      event.clientX >= rect.left &&
      event.clientX <= rect.right &&
      event.clientY >= rect.top &&
      event.clientY <= rect.bottom
    ) {
      hoverPoint = toImage(event)
    } else {
      hoverPoint = null
    }
  }
  updateCursor(event)

  if (panning) {
    store.pan = {
      x: panOrigin.panX + (event.clientX - panOrigin.x),
      y: panOrigin.panY + (event.clientY - panOrigin.y),
    }
    return
  }
  if (!drawing || !lastPoint) {
    scheduleRender()
    return
  }
  const raw = toImage(event)
  updateAxisLock(raw, event.shiftKey)
  const point = applyLock(raw)
  stroke(lastPoint, point)
  lastPoint = point
  scheduleRender()
}

async function endPointer() {
  if (panning) {
    panning = false
    return
  }
  if (!drawing) return
  drawing = false
  lastPoint = null
  axisStart = null
  axisLock = null
  axisBadge.value = ''
  await store.refreshHasMask()
}

function onPointerLeave() {
  cursorVisible.value = false
  hoverPoint = null
  scheduleRender()
  void endPointer()
}

function zoomAt(clientX: number, clientY: number, factor: number) {
  const wrap = wrapRef.value
  if (!wrap || !store.image) return
  const next = clampZoom(store.zoom * factor)
  if (Math.abs(next - store.zoom) < 1e-6) return
  const rect = wrap.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2
  const offsetX = clientX - (centerX + store.pan.x)
  const offsetY = clientY - (centerY + store.pan.y)
  const ratio = next / store.zoom
  store.pan = {
    x: store.pan.x + offsetX * (1 - ratio),
    y: store.pan.y + offsetY * (1 - ratio),
  }
  store.setZoom(next)
}

function onWheel(event: WheelEvent) {
  if (!store.image) return
  event.preventDefault()
  zoomAt(event.clientX, event.clientY, Math.pow(1.0016, -event.deltaY))
}

function onKeyDown(event: KeyboardEvent) {
  const target = event.target as HTMLElement | null
  if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) return

  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') {
    event.preventDefault()
    if (event.shiftKey) void store.redo()
    else void store.undo()
    return
  }
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') {
    event.preventDefault()
    void store.redo()
    return
  }

  switch (event.key.toLowerCase()) {
    case 'b':
      store.tool = 'brush'
      break
    case 'e':
      store.tool = 'eraser'
      break
    case 'v':
      store.tool = 'pan'
      break
    case 'g':
      store.showGrid = !store.showGrid
      break
    case 'h':
      store.showGuides = !store.showGuides
      break
    case '0':
      store.resetView()
      break
    case '=':
    case '+':
      store.zoomBy(1.25)
      break
    case '-':
      store.zoomBy(0.8)
      break
    default:
      break
  }
}

watch(
  () => store.image,
  async () => {
    hoverPoint = null
    await nextTick()
    layout()
  },
)
watch(
  () => [store.zoom, store.pan.x, store.pan.y] as const,
  () => layout(),
)
watch(
  () => [store.maskRevision, store.maskVisible, store.maskOpacity, store.maskColor] as const,
  scheduleRender,
)
watch(
  () => [store.showGrid, store.showGuides] as const,
  scheduleRender,
)

onMounted(() => {
  layout()
  resizeObserver = new ResizeObserver(() => layout())
  if (wrapRef.value) {
    resizeObserver.observe(wrapRef.value)
    wrapRef.value.addEventListener('wheel', onWheel, { passive: false })
  }
  window.addEventListener('keydown', onKeyDown)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  if (wrapRef.value) wrapRef.value.removeEventListener('wheel', onWheel)
  window.removeEventListener('keydown', onKeyDown)
  if (frame) cancelAnimationFrame(frame)
})
</script>

<template>
  <div ref="wrapRef" class="canvas-stage">
    <canvas
      v-show="store.image"
      ref="viewRef"
      class="view-canvas"
      :class="{ panning: store.tool === 'pan' }"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="endPointer"
      @pointercancel="endPointer"
      @pointerleave="onPointerLeave"
    />
    <div
      v-if="cursorVisible && store.image && store.tool !== 'pan'"
      class="brush-cursor"
      :style="cursorStyle"
    />
    <div v-if="axisBadge" class="axis-badge">{{ axisBadge }}</div>
    <div v-if="!store.image" class="empty-state">
      <div class="title">先上传一张图片</div>
      <div>在画布上涂抹要移除的区域，再点击右侧「开始修复」</div>
      <div class="keys">滚轮缩放 · 拖动平移 · 按住 Shift 画水平/垂直直线 · B/E 画笔橡皮 · G 网格</div>
    </div>
  </div>
</template>

<style scoped>
.canvas-stage {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.view-canvas {
  position: absolute;
  left: 50%;
  top: 50%;
  display: block;
  touch-action: none;
  cursor: crosshair;
  box-shadow: 0 10px 34px rgba(0, 0, 0, 0.5);
}

.view-canvas.panning {
  cursor: grab;
}

.brush-cursor {
  position: absolute;
  transform: translate(-50%, -50%);
  border: 2px solid;
  outline: 1px solid rgba(0, 0, 0, 0.55);
  border-radius: 50%;
  pointer-events: none;
  mix-blend-mode: normal;
}

.axis-badge {
  position: absolute;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: #bae6fd;
  background: rgba(13, 18, 30, 0.86);
  border: 1px solid rgba(56, 189, 248, 0.5);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(8px);
  pointer-events: none;
}

.empty-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #9fadc2;
  font-size: 13px;
  pointer-events: none;
  text-align: center;
  padding: 0 20px;
}

.empty-state .title {
  font-size: 16px;
  color: #eef3fa;
  font-weight: 600;
}

.empty-state .keys {
  font-size: 12px;
  color: #7d8ba1;
}
</style>
