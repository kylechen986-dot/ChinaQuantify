<template>
  <el-card shadow="never">
    <template #header>策略与信号</template>
    <el-table :data="signals" height="620">
      <el-table-column prop="trade_date" label="日期" width="120" />
      <el-table-column prop="symbol" label="代码" width="100" />
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="strategy_name" label="策略" min-width="180" />
      <el-table-column prop="signal_type" label="信号" width="120">
        <template #default="{ row }">
          <el-tag :type="tagType(row.signal_type)" effect="plain">{{ row.signal_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="signal_score" label="分值" width="100" />
      <el-table-column prop="reason" label="触发原因" min-width="360" />
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api } from '../api/modules'
import type { StrategySignal } from '../types/api'

const signals = ref<StrategySignal[]>([])

function tagType(signalType: string) {
  if (signalType === 'WATCH') return 'success'
  if (signalType === 'CAUTION') return 'warning'
  if (signalType === 'RISK') return 'danger'
  return 'info'
}

onMounted(async () => {
  signals.value = await api.signals()
})
</script>
