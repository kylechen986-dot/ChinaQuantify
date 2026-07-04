<template>
  <el-card shadow="never">
    <template #header>AI 日报</template>
    <h2 class="report-title">{{ report?.title }}</h2>
    <div class="report-meta">
      <el-tag effect="plain">{{ report?.report_type }}</el-tag>
      <el-tag type="info" effect="plain">{{ report?.model_provider }} / {{ report?.model_name }}</el-tag>
    </div>
    <p class="muted">{{ report?.summary }}</p>
    <el-divider />
    <p class="report-content">{{ report?.content }}</p>
    <el-alert
      title="当前内容仅用于个人研究辅助，不构成投资建议，系统不会自动下单。"
      type="warning"
      show-icon
      :closable="false"
    />
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api } from '../api/modules'
import type { AiReport } from '../types/api'

const report = ref<AiReport>()

onMounted(async () => {
  report.value = await api.latestReport()
})
</script>
