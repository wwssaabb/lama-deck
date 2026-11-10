<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { inpaint } from '../api/client'
import type { EngineChoice } from '../types'
import { useEditorStore } from '../stores/editor'

const store = useEditorStore()
const engine = ref<EngineChoice>('auto')
const refine = ref(false)
const radius = ref(3)
const dilate = ref(2)

const canRun = computed(() => Boolean(store.image && store.hasMask && !store.running))
const laMaDown = computed(
  () =>
    store.backendUp &&
    Boolean(store.health) &&
    (store.health?.engine === 'opencv' || !store.health?.model_ready),
)

const engineOptions = [
  { value: 'auto', label: 'auto · 自动选择' },
  { value: 'lama', label: 'lama · LaMa 神经网络' },
  { value: 'opencv', label: 'opencv · 传统算法' },
]

async function run() {
  const image = store.image
  if (!image || !store.hasMask || store.running) return
  store.running = true
  try {
    const mask = await store.maskBlob()
    const res = await inpaint(image.blob, mask, {
      engine: engine.value,
      refine: refine.value,
      radius: radius.value,
      dilate: dilate.value,
    })
    store.addResult({
      url: URL.createObjectURL(res.blob),
      blob: res.blob,
      engine: res.engine,
      ms: res.ms,
      width: image.width,
      height: image.height,
    })
    ElMessage.success(`修复完成 · 引擎 ${res.engine} · 耗时 ${res.ms}ms`)
    store.refreshHealth()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '修复失败')
    store.refreshHealth()
  } finally {
    store.running = false
  }
}
</script>

<template>
  <div class="panel liquid-glass">
    <h3>修复参数</h3>

    <div class="field">
      <div class="field-label"><span>推理引擎</span></div>
      <el-select v-model="engine" size="small" style="width: 100%">
        <el-option
          v-for="item in engineOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
    </div>

    <div class="field">
      <div class="field-label">
        <span>遮罩外扩 dilate</span>
        <span class="value">{{ dilate }}px</span>
      </div>
      <el-slider v-model="dilate" :min="0" :max="10" :show-tooltip="false" />
      <p class="tip">把遮罩向外扩几像素再修复，可消除物体残留的边缘</p>
    </div>

    <div class="field">
      <div class="field-label">
        <span>修复半径 radius</span>
        <span class="value">{{ radius }}</span>
      </div>
      <el-slider v-model="radius" :min="1" :max="30" :show-tooltip="false" />
    </div>

    <div class="field">
      <div class="field-label">
        <span>边界细化 refine</span>
        <el-switch v-model="refine" size="small" />
      </div>
      <p class="tip">对接缝外圈再做一次融合，让过渡更自然</p>
    </div>

    <el-button
      type="primary"
      style="width: 100%"
      :loading="store.running"
      :disabled="!canRun"
      @click="run"
    >
      {{ store.running ? '修复中…' : '开始修复' }}
    </el-button>
    <p class="tip center">
      {{ store.hasMask ? '遮罩已就绪' : '先在画布上涂抹要移除的区域' }}
    </p>
  </div>

  <div class="panel liquid-glass" style="margin-top: 12px">
    <h3>运行状态</h3>
    <el-alert
      v-if="!store.backendUp"
      type="error"
      :closable="false"
      show-icon
      title="后端未连接"
      description="请先启动后端：backend/run.ps1（默认 http://127.0.0.1:8000）"
    />
    <el-alert
      v-else-if="laMaDown"
      type="warning"
      :closable="false"
      show-icon
      title="LaMa 模型未就绪，当前使用 OpenCV 传统算法兜底"
      :description="
        store.health?.fallback_reason ||
        '安装 requirements-lama.txt 并下载权重后即可启用神经网络修复'
      "
    />
    <el-alert
      v-else
      type="success"
      :closable="false"
      show-icon
      title="LaMa 神经网络修复已就绪"
      :description="`设备 ${store.health?.device} · 版本 ${store.health?.version}`"
    />

    <div v-if="store.health" class="kv">
      <div><span>engine</span><b>{{ store.health.engine }}</b></div>
      <div><span>model</span><b>{{ store.health.model || '—' }}</b></div>
      <div><span>device</span><b>{{ store.health.device }}</b></div>
      <div><span>torch</span><b>{{ store.health.torch_available ? '可用' : '未安装' }}</b></div>
    </div>
  </div>
</template>

<style scoped>
.tip {
  margin: 6px 0 0;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.tip.center {
  text-align: center;
}

.kv {
  margin-top: 10px;
  display: grid;
  gap: 6px;
}

.kv div {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #64748b;
}

.kv b {
  font-weight: 500;
  color: #0f2f4a;
  font-variant-numeric: tabular-nums;
}
</style>
