<script setup lang="ts">
import { useEditorStore } from '../stores/editor'

const store = useEditorStore()
const colors = ['#f53f3f', '#ff7d00', '#f7ba1e', '#00b578', '#165dff', '#b25eff']
</script>

<template>
  <div class="rail liquid-glass">
    <div class="group">
      <div class="group-title">工具</div>
      <button
        class="tool"
        :class="{ active: store.tool === 'brush' }"
        title="画笔 (B)"
        @click="store.tool = 'brush'"
      >
        画笔
      </button>
      <button
        class="tool"
        :class="{ active: store.tool === 'eraser' }"
        title="橡皮 (E)"
        @click="store.tool = 'eraser'"
      >
        橡皮
      </button>
      <button
        class="tool"
        :class="{ active: store.tool === 'pan' }"
        title="抓手 (V)"
        @click="store.tool = 'pan'"
      >
        抓手
      </button>
    </div>

    <div class="group">
      <div class="group-title">遮罩颜色</div>
      <div class="swatches">
        <button
          v-for="color in colors"
          :key="color"
          class="swatch"
          :class="{ active: store.maskColor === color }"
          :style="{ background: color }"
          :title="color"
          @click="store.maskColor = color"
        />
      </div>
    </div>

    <div class="group">
      <div class="group-title">辅助</div>
      <button
        class="tool"
        :class="{ on: store.showGrid }"
        title="网格 (G)"
        @click="store.showGrid = !store.showGrid"
      >
        网格
      </button>
      <button
        class="tool"
        :class="{ on: store.showGuides }"
        title="纵向 / 横向辅助线 (H)"
        @click="store.showGuides = !store.showGuides"
      >
        辅助线
      </button>
      <button
        class="tool"
        :class="{ on: store.maskVisible }"
        title="显示 / 隐藏遮罩"
        @click="store.maskVisible = !store.maskVisible"
      >
        遮罩
      </button>
    </div>

    <div class="group">
      <div class="group-title">缩放</div>
      <button class="tool" title="放大 (+)" @click="store.zoomBy(1.25)">放大</button>
      <button class="tool" title="缩小 (-)" @click="store.zoomBy(0.8)">缩小</button>
      <button class="tool" title="适应窗口 (0)" @click="store.resetView()">适应</button>
    </div>

    <div class="group">
      <div class="group-title">编辑</div>
      <button class="tool" :disabled="!store.canUndo" title="撤销一步 (Ctrl+Z)" @click="store.undo()">
        撤销
      </button>
      <button
        class="tool"
        :disabled="!store.canRedo"
        title="重做 (Ctrl+Shift+Z)"
        @click="store.redo()"
      >
        重做
      </button>
      <button
        class="tool danger"
        :disabled="!store.hasMask"
        title="完全清除遮罩"
        @click="store.clearMask()"
      >
        清空
      </button>
    </div>
  </div>
</template>

<style scoped>
.rail {
  position: relative;
  width: 78px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 8px;
  border-radius: 22px;
  overflow-y: auto;
}

.group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.group-title {
  font-size: 11px;
  color: #64748b;
  text-align: center;
  letter-spacing: 1px;
}

.tool {
  appearance: none;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.66);
  color: #334155;
  font-size: 12px;
  padding: 7px 0;
  border-radius: 10px;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(15, 76, 129, 0.08);
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    color 0.15s ease;
}

.tool:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.95);
  color: #0f172a;
}

.tool:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.tool.active {
  background: rgba(2, 132, 199, 0.16);
  border-color: rgba(2, 132, 199, 0.5);
  color: #075985;
}

.tool.on {
  background: rgba(6, 182, 212, 0.18);
  border-color: rgba(6, 182, 212, 0.5);
  color: #155e75;
}

.tool.danger:not(:disabled) {
  color: #e11d48;
}

.swatches {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  justify-items: center;
}

.swatch {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 1px 5px rgba(15, 23, 42, 0.22);
  cursor: pointer;
  padding: 0;
}

.swatch.active {
  border-color: #0f172a;
  transform: scale(1.12);
}
</style>
