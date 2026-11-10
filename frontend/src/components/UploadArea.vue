<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useEditorStore } from '../stores/editor'

const store = useEditorStore()
const inputRef = ref<HTMLInputElement | null>(null)
const dragging = ref(false)

const samples = [
  { url: '/samples/sample-1.jpg', name: '官方示例 1.jpg' },
  { url: '/samples/sample-2.png', name: '官方示例 2.png' },
]

async function handleFile(file: File | undefined | null) {
  if (!file) return
  try {
    await store.loadFile(file)
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '图片加载失败')
  }
}

function onPick(event: Event) {
  const input = event.target as HTMLInputElement
  handleFile(input.files?.[0])
  input.value = ''
}

async function onSample(command: (typeof samples)[number]) {
  try {
    await store.loadSample(command.url, command.name)
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '示例图片加载失败')
  }
}

function onDrop(event: DragEvent) {
  dragging.value = false
  handleFile(event.dataTransfer?.files?.[0])
}
</script>

<template>
  <div
    class="upload-bar panel liquid-glass"
    :class="{ dragging }"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="onDrop"
  >
    <input
      ref="inputRef"
      type="file"
      accept="image/png,image/jpeg,image/webp"
      hidden
      @change="onPick"
    />
    <el-button type="primary" @click="inputRef?.click()">上传图片</el-button>

    <el-dropdown trigger="click" @command="onSample">
      <el-button>官方示例</el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item
            v-for="(sample, index) in samples"
            :key="sample.url"
            :command="sample"
          >
            官方案例图片 {{ index + 1 }}
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <span class="hint">
      {{ store.imageLabel || '支持点击上传或拖拽图片（PNG / JPEG / WebP）' }}
    </span>
    <span v-if="dragging" class="drop-tip">松开即可载入</span>
  </div>
</template>

<style scoped>
.upload-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  position: relative;
}

.upload-bar.dragging {
  border-color: rgba(56, 189, 248, 0.65);
  background: rgba(56, 189, 248, 0.14);
}

.hint {
  font-size: 12px;
  color: #9fadc2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drop-tip {
  position: absolute;
  right: 14px;
  font-size: 12px;
  color: #38bdf8;
}
</style>
