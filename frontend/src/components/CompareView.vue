<script setup lang="ts">
import { computed, ref } from 'vue'
import { downloadBlob } from '../utils/canvas'
import { useEditorStore } from '../stores/editor'

const store = useEditorStore()
const boxRef = ref<HTMLDivElement | null>(null)
const pos = ref(50)
const dragging = ref(false)

const result = computed(() => store.activeResult)
const originalUrl = computed(() => store.image?.element.src ?? '')

function updatePos(event: PointerEvent) {
  const box = boxRef.value
  if (!box) return
  const rect = box.getBoundingClientRect()
  const ratio = ((event.clientX - rect.left) / rect.width) * 100
  pos.value = Math.min(100, Math.max(0, ratio))
}

function onDown(event: PointerEvent) {
  dragging.value = true
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
  updatePos(event)
}

function onMove(event: PointerEvent) {
  if (dragging.value) updatePos(event)
}

function onUp() {
  dragging.value = false
}

function download() {
  if (result.value) downloadBlob(result.value.blob, 'inpainted.png')
}
</script>

<template>
  <div class="compare">
    <div class="head">
      <div class="info">
        <span class="title">修复结果对比</span>
        <span v-if="result" class="meta">
          引擎 {{ result.engine }} · 耗时 {{ result.ms }}ms · {{ result.width }}×{{
            result.height
          }} · {{ result.createdAt }}
        </span>
      </div>
      <div class="actions">
        <el-button size="small" @click="store.returnToEdit()">返回编辑</el-button>
        <el-button size="small" type="primary" @click="download">下载 PNG</el-button>
      </div>
    </div>

    <div
      ref="boxRef"
      class="compare-box"
      @pointerdown="onDown"
      @pointermove="onMove"
      @pointerup="onUp"
      @pointercancel="onUp"
    >
      <img v-if="result" class="layer" :src="result.url" alt="修复结果" />
      <div class="clip" :style="{ clipPath: `inset(0 ${100 - pos}% 0 0)` }">
        <img v-if="originalUrl" class="layer" :src="originalUrl" alt="原图" />
      </div>
      <div class="divider" :style="{ left: `${pos}%` }">
        <span class="handle">⟷</span>
      </div>
      <span class="tag left">原图</span>
      <span class="tag right">修复结果</span>
      <span class="tip">拖动分割线对比 · 滚轮可在画布中放大细节</span>
    </div>
  </div>
</template>

<style scoped>
.compare {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(
    140deg,
    rgba(18, 23, 36, 0.76),
    rgba(14, 18, 30, 0.66) 45%,
    rgba(11, 15, 26, 0.6)
  );
  backdrop-filter: blur(26px) saturate(155%);
  border: 1px solid rgba(255, 255, 255, 0.13);
  border-radius: 20px;
  box-shadow:
    0 14px 38px rgba(2, 6, 16, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.16);
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.info {
  display: flex;
  align-items: baseline;
  gap: 12px;
  min-width: 0;
}

.title {
  font-size: 14px;
  font-weight: 600;
  color: #f2f6fc;
}

.meta {
  font-size: 12px;
  color: #93a1b5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.compare-box {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  border-radius: 12px;
  background: #060a12;
  box-shadow: inset 0 2px 14px rgba(0, 0, 0, 0.55);
  touch-action: none;
  cursor: ew-resize;
  user-select: none;
}

.layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  pointer-events: none;
}

.clip {
  position: absolute;
  inset: 0;
}

.divider {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #ffffff;
  transform: translateX(-1px);
  pointer-events: none;
}

.handle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #ffffff;
  color: #0f2f4a;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.45);
}

.tag {
  position: absolute;
  top: 12px;
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: #e2e8f0;
  font-size: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
  pointer-events: none;
}

.tag.left {
  left: 12px;
}

.tag.right {
  right: 12px;
}

.tip {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  color: #cbd5e1;
  background: rgba(15, 23, 42, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.14);
  padding: 3px 12px;
  border-radius: 999px;
  pointer-events: none;
}
</style>
