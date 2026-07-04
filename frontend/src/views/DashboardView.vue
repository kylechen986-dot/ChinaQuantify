<template>
  <div class="dashboard-stack">
    <el-alert
      v-if="errors.length"
      class="dashboard-alert"
      :title="errors.join('；')"
      type="warning"
      show-icon
      :closable="false"
    />

    <section class="dashboard-hero">
      <div class="dashboard-market-hero">
        <div class="eyebrow">今日市场</div>
        <h2>{{ marketTone }} · {{ marketHeadline }}</h2>
        <p>{{ marketSummary }}</p>
        <div class="dashboard-chip-row">
          <el-tag effect="plain">最强 {{ overview?.strongest.name ?? '-' }}</el-tag>
          <el-tag type="info" effect="plain">最弱 {{ overview?.weakest.name ?? '-' }}</el-tag>
          <el-tag type="success" effect="plain">{{ overview?.sync_timezone ?? 'Asia/Shanghai' }}</el-tag>
        </div>
      </div>

      <div class="dashboard-sync-panel">
        <span>行情同步</span>
        <strong>{{ overview?.synced_at ?? '正在同步' }}</strong>
        <small>精确到秒，刷新页面会重新拉取当前行情快照。</small>
        <el-progress :percentage="marketBreadth" :color="marketBreadthColor" :show-text="false" />
      </div>
    </section>

    <div class="page-grid">
      <MetricCard label="跟踪 ETF" :value="overview?.symbol_count ?? '-'" hint="国内 ETF MVP 标的池" />
      <MetricCard label="上涨数量" :value="overview?.up_count ?? '-'" hint="今日涨幅为正" />
      <MetricCard label="下跌数量" :value="overview?.down_count ?? '-'" hint="今日涨幅为负" />
      <MetricCard label="市场宽度" :value="`${marketBreadth}%`" hint="上涨标的占比" />
    </div>

    <div class="dashboard-grid">
      <section class="dashboard-panel dashboard-panel-large">
        <div class="dashboard-panel-head">
          <div>
            <h3>ETF 市场概览</h3>
            <p>先看哪些方向更强，再进入行情页看完整指标。</p>
          </div>
          <el-tag effect="plain">{{ overview?.trade_date ?? '今日' }}</el-tag>
        </div>
        <el-table :data="overview?.snapshots ?? []" height="340" v-loading="marketLoading">
          <el-table-column prop="symbol" label="代码" width="100" />
          <el-table-column prop="name" label="名称" min-width="140" />
          <el-table-column prop="synced_at" label="同步时间" width="170" />
          <el-table-column prop="close" label="收盘" width="100" />
          <el-table-column prop="change_pct" label="涨跌幅" width="110">
            <template #default="{ row }">
              <span :class="row.change_pct >= 0 ? 'text-up' : 'text-down'">{{ row.change_pct }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="rsi14" label="RSI14" width="90" />
          <el-table-column label="趋势" width="120">
            <template #default="{ row }">
              <el-tag :type="trendTagType(row.trend_state)" effect="plain">{{ trendText(row.trend_state) }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="dashboard-panel">
        <div class="dashboard-panel-head">
          <div>
            <h3>策略信号</h3>
            <p>只做研究提醒，不自动下单。</p>
          </div>
          <el-tag type="info" effect="plain">{{ signals.length }} 条</el-tag>
        </div>
        <div class="dashboard-signal-list" v-if="signals.length">
          <article v-for="signal in signals" :key="signal.symbol" class="dashboard-signal">
            <div>
              <strong>{{ signal.name }}</strong>
              <p>{{ signal.reason }}</p>
            </div>
            <el-tag :type="signal.signal_type === 'CAUTION' ? 'warning' : 'success'" effect="plain">
              {{ signal.signal_type }} · {{ signal.signal_score }}
            </el-tag>
          </article>
        </div>
        <el-skeleton v-else-if="signalLoading" :rows="5" animated />
        <el-empty v-else description="暂无策略信号" />
      </section>

      <section class="dashboard-panel">
        <div class="dashboard-panel-head">
          <div>
            <h3>关注个股</h3>
            <p>结合整体市场看关注队列。</p>
          </div>
          <el-tag type="success" effect="plain">{{ watchStocks.length }} 只</el-tag>
        </div>
        <div class="dashboard-watch-list" v-if="watchStocks.length">
          <article v-for="stock in watchStocks" :key="stock.symbol" class="dashboard-watch-item">
            <div class="dashboard-watch-head">
              <div>
                <strong>{{ stock.name }}</strong>
                <span>{{ stock.symbol }} · {{ stock.industry }}</span>
              </div>
              <b :class="stock.change_pct >= 0 ? 'text-up' : 'text-down'">{{ stock.change_pct }}%</b>
            </div>
            <div class="dashboard-watch-data">
              <span>现价 {{ stock.close }}</span>
              <span>RSI {{ stock.rsi14 }}</span>
              <span>评分 {{ stock.signal_score }}</span>
            </div>
            <p>{{ stock.plain_analysis }}</p>
          </article>
        </div>
        <el-skeleton v-else-if="stockLoading" :rows="5" animated />
        <el-empty v-else description="暂无关注个股" />
      </section>

      <section class="dashboard-panel">
        <div class="dashboard-panel-head">
          <div>
            <h3>AI 日报摘要</h3>
            <p>{{ report?.model_provider ?? 'AI' }} · {{ report?.report_date ?? '今日' }}</p>
          </div>
          <el-button size="small" :loading="loading" @click="loadDashboard">刷新</el-button>
        </div>
        <template v-if="report">
          <h4 class="dashboard-report-title">{{ report.title }}</h4>
          <p class="dashboard-report-summary">{{ report.summary }}</p>
          <div class="dashboard-report-content">{{ report.content }}</div>
        </template>
        <el-skeleton v-else-if="reportLoading" :rows="8" animated />
        <el-empty v-else description="暂无日报摘要" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { api } from '../api/modules'
import MetricCard from '../components/MetricCard.vue'
import type { AiReport, MarketOverview, StrategySignal, WatchStock } from '../types/api'

const overview = ref<MarketOverview>()
const report = ref<AiReport>()
const signals = ref<StrategySignal[]>([])
const watchStocks = ref<WatchStock[]>([])
const loading = ref(false)
const marketLoading = ref(false)
const signalLoading = ref(false)
const stockLoading = ref(false)
const reportLoading = ref(false)
const errors = ref<string[]>([])

const marketTone = computed(() => {
  if (!overview.value) return '同步中'
  if (overview.value.up_count > overview.value.down_count) return '偏暖'
  if (overview.value.up_count < overview.value.down_count) return '偏弱'
  return '震荡'
})

const marketBreadth = computed(() => {
  if (!overview.value?.symbol_count) return 0
  return Math.round((overview.value.up_count / overview.value.symbol_count) * 100)
})

const marketBreadthColor = computed(() => {
  if (marketBreadth.value >= 60) return '#d92d20'
  if (marketBreadth.value <= 40) return '#039855'
  return '#1f7aec'
})

const marketHeadline = computed(() => {
  const strongest = overview.value?.strongest
  if (!strongest) return '等待行情数据'
  return `${strongest.name} 领涨 ${strongest.change_pct}%`
})

const marketSummary = computed(() => {
  const current = overview.value
  if (!current) return '正在读取 ETF 行情、策略信号和关注个股。'
  return `当前跟踪 ${current.symbol_count} 只 ETF，上涨 ${current.up_count} 只、下跌 ${current.down_count} 只。最强方向是 ${current.strongest.name}，最弱方向是 ${current.weakest.name}。`
})

function trendText(value: string) {
  const map: Record<string, string> = {
    STRONG_UP: '强势上行',
    UP: '上行',
    SIDEWAYS: '震荡',
    DOWN: '转弱',
  }
  return map[value] ?? value
}

function trendTagType(value: string) {
  if (value === 'STRONG_UP' || value === 'UP') return 'success'
  if (value === 'DOWN') return 'warning'
  return 'info'
}

async function loadPart<T>(task: Promise<T>, label: string, loadingRef: typeof loading, apply: (data: T) => void) {
  loadingRef.value = true
  try {
    apply(await task)
  } catch (err) {
    errors.value.push(`${label}加载失败`)
  } finally {
    loadingRef.value = false
  }
}

async function loadDashboard() {
  loading.value = true
  errors.value = []
  try {
    await Promise.allSettled([
      loadPart(api.marketOverview(), '市场概览', marketLoading, (data) => {
        overview.value = data
      }),
      loadPart(api.signals(), '策略信号', signalLoading, (data) => {
        signals.value = data
      }),
      loadPart(api.watchStocks(), '关注个股', stockLoading, (data) => {
        watchStocks.value = data
      }),
      loadPart(api.latestReport(), 'AI 日报', reportLoading, (data) => {
        report.value = data
      }),
    ])
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>
