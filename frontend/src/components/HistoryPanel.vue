<script setup lang="ts">
import { useEditorStore } from '../stores/editor'

const store = useEditorStore()
</script>

<template>
  <div class="panel history liquid-glass">
    <div class="head">
      <h3>历史记录 <span class="count">{{ store.results.length }}</span></h3>
      <el-button
        size="small"
        text
        type="danger"
        :disabled="!store.results.length"
        @click="store.clearResults()"
      >
        清空全部
      </el-button>
    </div>

    <div v-if="store.results.length" class="list">
      <div
        v-for="item in store.results"
        :key="item.id"
        class="row"
        :class="{ active: item.id === store.activeResultId }"
        @click="store.selectResult(item.id)"
      >
        <img :src="item.url" alt="修复结果缩略图" />
        <div class="meta">
          <div class="line1">#{{ item.id }} · {{ item.createdAt }}</div>
          <div class="line2">{{ item.engine }} · {{ item.ms }}ms · {{ item.width }}×{{ item.height }}</div>
        </div>
        <button class="del" title="删除这条记录" @click.stop="store.removeResult(item.id)">×</button>
      </div>
    </div>
    <p v-else class="empty">暂无记录，修复结果会保留在这里</p>
  </div>
</template>

<style scoped>
.history {
  display: flex;
  flex-direction: column;
  min-height: 160px;
  max-height: 42vh;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.head h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #0f2f4a;
}

.count {
  display: inline-block;
  min-width: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(2, 132, 199, 0.14);
  color: #0369a1;
  font-size: 11px;
  text-align: center;
  margin-left: 4px;
}

.list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 2px;
}

.row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(15, 76, 129, 0.07);
  transition: border-color 0.15s ease, background 0.15s ease;
}

.row:hover {
  background: rgba(255, 255, 255, 0.92);
}

.row.active {
  border-color: rgba(2, 132, 199, 0.55);
  background: rgba(2, 132, 199, 0.1);
}

.row img {
  width: 56px;
  height: 42px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
  background: #e2e8f0;
}

.meta {
  flex: 1;
  min-width: 0;
}

.line1 {
  font-size: 12px;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.line2 {
  font-size: 11px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.del {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}

.del:hover {
  background: rgba(244, 63, 94, 0.14);
  color: #e11d48;
}

.empty {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}
</style>
