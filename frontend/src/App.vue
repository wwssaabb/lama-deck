<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import CompareView from './components/CompareView.vue'
import ControlPanel from './components/ControlPanel.vue'
import EditorCanvas from './components/EditorCanvas.vue'
import HistoryPanel from './components/HistoryPanel.vue'
import LeftToolbar from './components/LeftToolbar.vue'
import StarfieldBackground from './components/StarfieldBackground.vue'
import UploadArea from './components/UploadArea.vue'
import { useEditorStore } from './stores/editor'

const store = useEditorStore()
let timer = 0

const chips = computed(() => {
  if (!store.backendUp || !store.health) {
    return [{ key: 'down', text: '后端未连接', cls: 'off' }]
  }
  const h = store.health
  const items = [
    { key: 'engine', text: `引擎 ${h.engine}`, cls: h.engine === 'lama' ? '' : 'warn' },
    { key: 'device', text: `设备 ${h.device}`, cls: '' },
    {
      key: 'model',
      text: h.model_ready ? 'LaMa 就绪' : 'LaMa 未就绪',
      cls: h.model_ready ? '' : 'warn',
    },
  ]
  if (h.fallback_reason) items.push({ key: 'reason', text: h.fallback_reason, cls: 'warn' })
  return items
})

const zoomLabel = computed(() => `${Math.round(store.zoom * 100)}%`)
const showEditor = computed(
  () => store.viewMode !== 'compare' || !store.activeResult,
)

onMounted(() => {
  store.refreshHealth()
  timer = window.setInterval(() => store.refreshHealth(), 15000)
})

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
  store.releaseAll()
})
</script>

<template>
  <StarfieldBackground />
  <div class="app">
    <header class="app-header liquid-glass">
      <div class="brand">
        <h1>LaMa Studio</h1>
        <span class="sub">基于 advimman/lama 的图像修复 · 物体移除</span>
      </div>
      <div class="health-chips">
        <span v-for="chip in chips" :key="chip.key" class="chip" :class="chip.cls">
          <i class="dot" />
          {{ chip.text }}
        </span>
      </div>
    </header>

    <main class="workspace">
      <LeftToolbar />

      <section class="center-col">
        <UploadArea />

        <div class="stage">
          <div v-if="showEditor" class="editor-stack">
            <div class="canvas-box">
              <EditorCanvas />
            </div>

            <div class="settings-bar liquid-glass">
              <div class="setting">
                <span class="label">笔刷 {{ store.brushSize }}px</span>
                <el-slider
                  v-model="store.brushSize"
                  :min="4"
                  :max="300"
                  :show-tooltip="false"
                />
              </div>
              <div class="setting">
                <span class="label">遮罩 {{ store.maskOpacity }}%</span>
                <el-slider
                  v-model="store.maskOpacity"
                  :min="10"
                  :max="90"
                  :show-tooltip="false"
                />
              </div>
              <div class="meta">
                <span class="label">缩放 {{ zoomLabel }}</span>
                <span class="hint">Shift 约束水平/垂直 · 滚轮缩放 · 拖动平移</span>
              </div>
            </div>
          </div>

          <CompareView v-else />
        </div>
      </section>

      <aside class="side-col">
        <ControlPanel />
        <HistoryPanel />
      </aside>
    </main>
  </div>
</template>
