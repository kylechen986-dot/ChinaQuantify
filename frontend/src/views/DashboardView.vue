<template>
  <div class="page-grid">
    <MetricCard label="跟踪标的" :value="overview?.symbol_count ?? '-'" hint="国内 ETF MVP 标的池" />
    <MetricCard label="上涨数量" :value="overview?.up_count ?? '-'" hint="今日涨幅为正" />
    <MetricCard label="下跌数量" :value="overview?.down_count ?? '-'" hint="今日涨幅为负" />
    <MetricCard label="最新日报" :value="report?.report_date ?? '-'" hint="收盘后生成" />
  </div>

  <div class="section-grid">
    <el-card shadow="never">
      <template #header>市场概览</template>
      <el-table :data="overview?.snapshots ?? []" height="360">
        <el-table-column prop="symbol" label="代码" width="100" />
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="close" label="收盘" width="100" />
        <el-table-column prop="change_pct" label="涨跌幅" width="110">
          <template #default="{ row }">
            <span :class="row.change_pct >= 0 ? 'text-up' : 'text-down'">{{ row.change_pct }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="trend_state" label="趋势" width="120" />
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header>AI 日报摘要</template>
      <h3 class="report-title">{{ report?.title }}</h3>
      <p class="muted">{{ report?.summary }}</p>
      <el-divider />
      <p class="report-content">{{ report?.content }}</p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api } from '../api/modules'
import MetricCard from '../components/MetricCard.vue'
import type { AiReport, MarketOverview } from '../types/api'

const overview = ref<MarketOverview>()
const report = ref<AiReport>()

onMounted(async () => {
  const [marketData, reportData] = await Promise.all([api.marketOverview(), api.latestReport()])
  overview.value = marketData
  report.value = reportData
})
</script>
