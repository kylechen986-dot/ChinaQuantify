<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>AI 日报</span>
        <el-button :icon="Refresh" :loading="loading" @click="loadReport">重新生成</el-button>
      </div>
    </template>

    <el-skeleton v-if="loading" :rows="8" animated />

    <el-alert
      v-else-if="error"
      :title="error"
      type="error"
      show-icon
      :closable="false"
    />

    <div v-else-if="report">
      <h2 class="report-title">{{ report.title }}</h2>
      <div class="report-meta">
        <el-tag effect="plain">{{ report.report_type }}</el-tag>
        <el-tag type="info" effect="plain">{{ report.model_provider }} / {{ report.model_name }}</el-tag>
        <el-tag type="success" effect="plain">{{ report.report_date }}</el-tag>
      </div>
      <p class="muted">{{ report.summary }}</p>
      <el-divider />
      <div class="report-content">{{ report.content }}</div>
    </div>

    <el-alert
      class="report-warning"
      title="当前内容仅用于个人研究辅助，不构成投资建议，系统不会自动下单。"
      type="warning"
      show-icon
      :closable="false"
    />
  </el-card>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'

import { api } from '../api/modules'
import type { AiReport } from '../types/api'

const report = ref<AiReport>()
const loading = ref(false)
const error = ref('')

async function loadReport() {
  loading.value = true
  error.value = ''
  try {
    report.value = await api.latestReport()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'AI 日报加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(loadReport)
</script>
