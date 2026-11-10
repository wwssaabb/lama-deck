import { computed, ref, shallowRef } from 'vue'
import { defineStore } from 'pinia'
import { fetchHealth } from '../api/client'
import type { HealthInfo, InpaintResult, SourceImage, Tool } from '../types'
import { canvasToBlob, loadImage } from '../utils/canvas'

const MAX_UNDO = 30
const MAX_RESULTS = 20
const PROBE_SIZE = 64

export const useEditorStore = defineStore('editor', () => {
  const image = shallowRef<SourceImage | null>(null)
  const maskCanvas = shallowRef<HTMLCanvasElement | null>(null)
  const maskRevision = ref(0)
  const hasMask = ref(false)
  const undoStack = ref<string[]>([])
  const redoStack = ref<string[]>([])

  const tool = ref<Tool>('brush')
  const brushSize = ref(48)
  const maskVisible = ref(true)
  const maskOpacity = ref(60)
  const maskColor = ref('#f53f3f')
  const showGrid = ref(false)
  const showGuides = ref(true)

  const zoom = ref(1)
  const pan = ref({ x: 0, y: 0 })
  const viewMode = ref<'edit' | 'compare'>('edit')

  const running = ref(false)
  const health = shallowRef<HealthInfo | null>(null)
  const backendUp = ref(true)

  const results = ref<InpaintResult[]>([])
  const activeResultId = ref<number | null>(null)
  const pendingOverwrite = ref(false)

  let objectUrl: string | null = null
  let resultSeq = 0

  const activeResult = computed(
    () => results.value.find((item) => item.id === activeResultId.value) ?? null,
  )
  const canUndo = computed(() => undoStack.value.length > 0)
  const canRedo = computed(() => redoStack.value.length > 0)
  const imageLabel = computed(() =>
    image.value ? `${image.value.name} · ${image.value.width}×${image.value.height}` : '',
  )

  function resetMaskState() {
    undoStack.value = []
    redoStack.value = []
    hasMask.value = false
    maskRevision.value += 1
  }

  function createMask(width: number, height: number) {
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    maskCanvas.value = canvas
    resetMaskState()
  }

  async function adopt(blob: Blob, name: string) {
    const url = URL.createObjectURL(blob)
    let element: HTMLImageElement
    try {
      element = await loadImage(url)
    } catch (err) {
      URL.revokeObjectURL(url)
      throw err
    }
    if (objectUrl) URL.revokeObjectURL(objectUrl)
    objectUrl = url
    image.value = {
      element,
      blob,
      name,
      width: element.naturalWidth,
      height: element.naturalHeight,
    }
    createMask(element.naturalWidth, element.naturalHeight)
    activeResultId.value = null
    pendingOverwrite.value = false
    viewMode.value = 'edit'
    resetView()
  }

  async function loadFile(file: File) {
    if (!file.type.startsWith('image/')) throw new Error('请选择图片文件（PNG / JPEG / WebP）')
    await adopt(file, file.name)
  }

  async function loadSample(url: string, name: string) {
    const res = await fetch(url)
    if (!res.ok) throw new Error(`示例图片加载失败 (${res.status})`)
    await adopt(await res.blob(), name)
  }

  function snapshotMask(): string | null {
    const canvas = maskCanvas.value
    return canvas ? canvas.toDataURL('image/png') : null
  }

  function pushUndo(snapshot: string | null) {
    if (!snapshot) return
    undoStack.value.push(snapshot)
    if (undoStack.value.length > MAX_UNDO) undoStack.value.shift()
    redoStack.value = []
  }

  async function restoreMask(dataUrl: string) {
    const canvas = maskCanvas.value
    if (!canvas) return
    const element = await loadImage(dataUrl)
    const ctx = canvas.getContext('2d')!
    ctx.globalCompositeOperation = 'source-over'
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(element, 0, 0)
    maskRevision.value += 1
    await refreshHasMask()
  }

  async function undo() {
    const snapshot = undoStack.value.pop()
    if (!snapshot) return false
    const current = snapshotMask()
    if (current) redoStack.value.push(current)
    await restoreMask(snapshot)
    return true
  }

  async function redo() {
    const snapshot = redoStack.value.pop()
    if (!snapshot) return false
    const current = snapshotMask()
    if (current) undoStack.value.push(current)
    await restoreMask(snapshot)
    return true
  }

  async function refreshHasMask() {
    const canvas = maskCanvas.value
    if (!canvas) {
      hasMask.value = false
      return
    }
    const probe = document.createElement('canvas')
    probe.width = PROBE_SIZE
    probe.height = PROBE_SIZE
    const ctx = probe.getContext('2d', { willReadFrequently: true })!
    ctx.drawImage(canvas, 0, 0, PROBE_SIZE, PROBE_SIZE)
    const data = ctx.getImageData(0, 0, PROBE_SIZE, PROBE_SIZE).data
    let found = false
    for (let i = 3; i < data.length; i += 4) {
      if (data[i] > 0) {
        found = true
        break
      }
    }
    hasMask.value = found
  }

  function clearMask() {
    const canvas = maskCanvas.value
    if (!canvas) return
    pushUndo(snapshotMask())
    const ctx = canvas.getContext('2d')!
    ctx.globalCompositeOperation = 'source-over'
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    maskRevision.value += 1
    hasMask.value = false
    redoStack.value = []
  }

  async function maskBlob(): Promise<Blob> {
    const canvas = maskCanvas.value
    if (!canvas) throw new Error('请先加载图片')
    const flat = document.createElement('canvas')
    flat.width = canvas.width
    flat.height = canvas.height
    const ctx = flat.getContext('2d')!
    ctx.fillStyle = '#000000'
    ctx.fillRect(0, 0, flat.width, flat.height)
    ctx.drawImage(canvas, 0, 0)
    return canvasToBlob(flat, 'image/png')
  }

  function setZoom(value: number) {
    zoom.value = Math.min(8, Math.max(0.1, value))
  }

  function zoomBy(factor: number) {
    setZoom(zoom.value * factor)
  }

  function resetView() {
    zoom.value = 1
    pan.value = { x: 0, y: 0 }
  }

  async function refreshHealth() {
    try {
      health.value = await fetchHealth()
      backendUp.value = true
    } catch {
      health.value = null
      backendUp.value = false
    }
  }

  function addResult(result: Omit<InpaintResult, 'id' | 'createdAt'>) {
    const createdAt = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    const activeId = activeResultId.value
    const index =
      pendingOverwrite.value && activeId
        ? results.value.findIndex((item) => item.id === activeId)
        : -1

    if (index >= 0) {
      const previous = results.value[index]
      URL.revokeObjectURL(previous.url)
      const item: InpaintResult = { ...previous, ...result, createdAt }
      results.value.splice(index, 1, item)
      activeResultId.value = item.id
      pendingOverwrite.value = false
      viewMode.value = 'compare'
      return item
    }

    const item: InpaintResult = {
      ...result,
      id: ++resultSeq,
      createdAt,
    }
    results.value.unshift(item)
    while (results.value.length > MAX_RESULTS) {
      const dropped = results.value.pop()
      if (dropped) URL.revokeObjectURL(dropped.url)
    }
    activeResultId.value = item.id
    viewMode.value = 'compare'
    return item
  }

  function returnToEdit() {
    viewMode.value = 'edit'
    if (activeResultId.value) pendingOverwrite.value = true
  }

  function selectResult(id: number) {
    activeResultId.value = id
    pendingOverwrite.value = false
    viewMode.value = 'compare'
  }

  function removeResult(id: number) {
    const index = results.value.findIndex((item) => item.id === id)
    if (index < 0) return
    const [removed] = results.value.splice(index, 1)
    URL.revokeObjectURL(removed.url)
    if (activeResultId.value === id) {
      activeResultId.value = results.value[0]?.id ?? null
      if (!activeResultId.value) viewMode.value = 'edit'
    }
  }

  function clearResults() {
    results.value.forEach((item) => URL.revokeObjectURL(item.url))
    results.value = []
    activeResultId.value = null
    pendingOverwrite.value = false
    viewMode.value = 'edit'
  }

  function releaseAll() {
    if (objectUrl) URL.revokeObjectURL(objectUrl)
    results.value.forEach((item) => URL.revokeObjectURL(item.url))
    objectUrl = null
    results.value = []
  }

  return {
    image,
    maskCanvas,
    maskRevision,
    hasMask,
    undoStack,
    redoStack,
    tool,
    brushSize,
    maskVisible,
    maskOpacity,
    maskColor,
    showGrid,
    showGuides,
    zoom,
    pan,
    viewMode,
    running,
    health,
    backendUp,
    results,
    activeResultId,
    activeResult,
    canUndo,
    canRedo,
    imageLabel,
    loadFile,
    loadSample,
    snapshotMask,
    pushUndo,
    undo,
    redo,
    refreshHasMask,
    clearMask,
    maskBlob,
    setZoom,
    zoomBy,
    resetView,
    refreshHealth,
    addResult,
    returnToEdit,
    selectResult,
    removeResult,
    clearResults,
    releaseAll,
  }
})
