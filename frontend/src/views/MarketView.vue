<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>国内 ETF 行情</span>
        <span class="muted">同步时间：{{ syncTime }}</span>
        <el-button :icon="Refresh" @click="loadData">刷新</el-button>
      </div>
    </template>
    <el-table :data="rows" height="620">
      <el-table-column prop="symbol" label="代码" width="100" />
      <el-table-column prop="name" label="名称" min-width="150" />
      <el-table-column prop="trade_date" label="日期" width="120" />
      <el-table-column prop="synced_at" label="同步时间" width="170" />
      <el-table-column prop="close" label="收盘价" width="100" />
      <el-table-column prop="change_pct" label="涨跌幅" width="110">
        <template #default="{ row }">
          <span :class="row.change_pct >= 0 ? 'text-up' : 'text-down'">{{ row.change_pct }}%</span>
        </template>
      </el-table-column>
      <el-table-column prop="ma20" label="MA20" width="100" />
      <el-table-column prop="ma60" label="MA60" width="100" />
      <el-table-column prop="rsi14" label="RSI14" width="100" />
      <el-table-column prop="macd_hist" label="MACD柱" width="110" />
      <el-table-column prop="trend_state" label="趋势状态" width="130">
        <template #default="{ row }">
          <el-tag effect="plain">{{ row.trend_state }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'

import { api } from '../api/modules'
import type { IndicatorSnapshot } from '../types/api'

const rows = ref<IndicatorSnapshot[]>([])
const syncTime = ref('-')

async function loadData() {
  rows.value = await api.indicators()
  syncTime.value = rows.value[0]?.synced_at ?? '-'
}

onMounted(loadData)
</script>
