<template>
  <div class="page-grid">
    <MetricCard label="累计收益" :value="formatPercent(summary?.metrics.total_return)" hint="样例回测结果" />
    <MetricCard label="最大回撤" :value="formatPercent(summary?.metrics.max_drawdown)" hint="风险观察核心指标" />
    <MetricCard label="胜率" :value="formatPercent(summary?.metrics.win_rate)" hint="交易胜率" />
    <MetricCard label="夏普比率" :value="summary?.metrics.sharpe ?? '-'" hint="风险调整收益" />
  </div>

  <el-card shadow="never">
    <template #header>{{ summary?.strategy_name }} - {{ summary?.name }}</template>
    <EquityChart :data="summary?.equity_curve ?? []" />
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api } from '../api/modules'
import EquityChart from '../components/EquityChart.vue'
import MetricCard from '../components/MetricCard.vue'
import type { BacktestSummary } from '../types/api'

const summary = ref<BacktestSummary>()

function formatPercent(value: number | undefined) {
  if (typeof value !== 'number') return '-'
  return `${(value * 100).toFixed(2)}%`
}

onMounted(async () => {
  summary.value = await api.backtestSummary()
})
</script>
