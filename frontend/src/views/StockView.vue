<template>
  <div class="stock-workspace">
    <section class="stock-list-panel">
      <div class="stock-list-header">
        <div>
          <h2>股票列表</h2>
          <p>点击任一股票，查看它和整体 ETF 市场结合后的研判。</p>
        </div>
        <el-tag type="success" effect="plain">已关注 {{ watchedCount }}</el-tag>
      </div>

      <el-table :data="stocks" height="620" highlight-current-row @row-click="selectStock">
        <el-table-column prop="symbol" label="代码" width="100" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="industry" label="行业" width="110" />
        <el-table-column prop="style" label="风格" width="120" />
        <el-table-column prop="change_pct" label="涨跌幅" width="100">
          <template #default="{ row }">
            <span :class="row.change_pct >= 0 ? 'text-up' : 'text-down'">{{ row.change_pct }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="signal_score" label="评分" width="90" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.watched" type="success" effect="plain">已关注</el-tag>
            <el-tag v-else effect="plain">未关注</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <aside class="stock-detail-panel" v-if="selected">
      <div class="stock-detail-head">
        <div>
          <div class="eyebrow">个股专项研判</div>
          <h2>{{ selected.name }}</h2>
          <p>{{ selected.symbol }} · {{ selected.market }} · {{ selected.industry }} · {{ selected.style }}</p>
        </div>
        <el-button v-if="!selected.watched" type="primary" @click="addToWatch(selected.symbol)">
          加入关注队列
        </el-button>
        <el-tag v-else type="success" effect="plain">已在关注队列</el-tag>
      </div>

      <div class="stock-quick-grid">
        <div>
          <span>收盘价</span>
          <strong>{{ selected.close }}</strong>
        </div>
        <div>
          <span>涨跌幅</span>
          <strong :class="selected.change_pct >= 0 ? 'text-up' : 'text-down'">{{ selected.change_pct }}%</strong>
        </div>
        <div>
          <span>策略评分</span>
          <strong>{{ selected.signal_score }}</strong>
        </div>
        <div>
          <span>RSI14</span>
          <strong>{{ selected.rsi14 }}</strong>
        </div>
      </div>

      <section class="stock-analysis-block">
        <h3>普通话解读</h3>
        <p>{{ selected.plain_analysis }}</p>
      </section>

      <section class="stock-analysis-block">
        <h3>结合整体市场</h3>
        <p>{{ selected.market_context }}</p>
        <p>相对强弱：{{ selected.relative_strength }}；关联观察 ETF：{{ selected.related_etf }}。</p>
      </section>

      <section class="stock-analysis-block">
        <h3>后续测试计划</h3>
        <ul>
          <li v-for="item in selected.test_plan" :key="item">{{ item }}</li>
        </ul>
      </section>

      <section class="stock-analysis-block">
        <h3>风险提醒</h3>
        <ul>
          <li v-for="item in selected.risk_points" :key="item">{{ item }}</li>
        </ul>
      </section>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

import { api } from '../api/modules'
import type { WatchStock } from '../types/api'

const stocks = ref<WatchStock[]>([])
const selected = ref<WatchStock>()

const watchedCount = computed(() => stocks.value.filter((item) => item.watched).length)

async function loadStocks() {
  stocks.value = await api.stocks()
  selected.value = stocks.value[0]
}

async function selectStock(row: WatchStock) {
  selected.value = await api.stockDetail(row.symbol)
}

async function addToWatch(symbol: string) {
  const updated = await api.addWatchStock(symbol)
  stocks.value = stocks.value.map((item) => (item.symbol === updated.symbol ? updated : item))
  selected.value = updated
  ElMessage.success(`${updated.name} 已加入关注队列`)
}

onMounted(loadStocks)
</script>
