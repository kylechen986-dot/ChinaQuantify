<template>
  <div class="report-workspace">
    <aside class="report-history">
      <div class="history-title">历史日报</div>
      <button
        v-for="item in reports"
        :key="item.id"
        class="history-item"
        :class="{ active: item.id === report?.id }"
        type="button"
        @click="loadReport(item.id)"
      >
        <span class="history-date">{{ item.report_date }}</span>
        <span class="history-summary">{{ item.summary }}</span>
      </button>
    </aside>

    <section class="report-main">
      <div class="daily-card hero-message">
        <div>
          <div class="eyebrow">AI 每日简报</div>
          <h2>{{ report?.title ?? '正在生成日报' }}</h2>
          <p>{{ report?.summary ?? '稍等片刻，系统正在整理今日行情、策略信号和风险提示。' }}</p>
        </div>
        <el-button :icon="Refresh" :loading="loading" type="primary" @click="loadLatest">重新生成</el-button>
      </div>

      <el-skeleton v-if="loading" :rows="10" animated />

      <el-alert
        v-else-if="error"
        :title="error"
        type="error"
        show-icon
        :closable="false"
      />

      <template v-else-if="report">
        <div class="daily-metrics">
          <div class="daily-metric">
            <span>市场状态</span>
            <strong>{{ report.market_tone ?? marketTone }}</strong>
            <small>用一句话看懂今天</small>
          </div>
          <div class="daily-metric">
            <span>上涨/下跌</span>
            <strong>{{ overview?.up_count ?? '-' }} / {{ overview?.down_count ?? '-' }}</strong>
            <small>上涨多，说明整体更暖一些</small>
          </div>
          <div class="daily-metric">
            <span>最强 ETF</span>
            <strong>{{ overview?.strongest.name ?? '-' }}</strong>
            <small>{{ overview?.strongest.change_pct ?? '-' }}%，今天更有动能</small>
          </div>
          <div class="daily-metric">
            <span>最弱 ETF</span>
            <strong>{{ overview?.weakest.name ?? '-' }}</strong>
            <small>{{ overview?.weakest.change_pct ?? '-' }}%，短线更弱</small>
          </div>
        </div>

        <div class="message-grid">
          <article class="daily-card">
            <div class="card-kicker">小白解读</div>
            <h3>今天到底是什么意思？</h3>
            <p>{{ plainLanguageSummary }}</p>
          </article>

          <article class="daily-card">
            <div class="card-kicker">数据时间</div>
            <h3>{{ overview?.synced_at ?? report.report_date }}</h3>
            <p>这是行情同步时间，精确到秒。看日报时先看这个时间，确认自己看的不是旧数据。</p>
          </article>
        </div>

        <section class="daily-card">
          <div class="card-kicker">策略信号</div>
          <h3>系统今天提醒了什么</h3>
          <div class="signal-list">
            <div v-for="signal in signals" :key="signal.symbol" class="signal-message">
              <div>
                <strong>{{ signal.name }}</strong>
                <p>{{ signal.reason }}</p>
              </div>
              <el-tag :type="signal.signal_type === 'CAUTION' ? 'warning' : 'success'" effect="plain">
                {{ signal.signal_type }} · {{ signal.signal_score }}
              </el-tag>
            </div>
          </div>
        </section>

        <section class="daily-card">
          <div class="card-kicker">关注个股</div>
          <h3>结合整体市场，看这两只测试股票</h3>
          <div class="stock-card-grid">
            <article v-for="stock in watchStocks" :key="stock.symbol" class="stock-card">
              <div class="stock-card-head">
                <div>
                  <strong>{{ stock.name }}</strong>
                  <span>{{ stock.symbol }} · {{ stock.industry }} · {{ stock.style }}</span>
                </div>
                <el-tag :type="stock.change_pct >= 0 ? 'danger' : 'success'" effect="plain">
                  {{ stock.change_pct }}%
                </el-tag>
              </div>
              <div class="stock-data-row">
                <span>收盘 {{ stock.close }}</span>
                <span>RSI {{ stock.rsi14 }}</span>
                <span>{{ stock.signal_type }} · {{ stock.signal_score }}</span>
              </div>
              <p>{{ stock.plain_analysis }}</p>
              <small>{{ stock.market_context }}</small>
            </article>
          </div>
        </section>

        <section class="daily-card">
          <div class="card-kicker">完整日报</div>
          <h3>AI 生成正文</h3>
          <div class="report-meta">
            <el-tag effect="plain">{{ report.report_type }}</el-tag>
            <el-tag type="info" effect="plain">{{ report.model_provider }} / {{ report.model_name }}</el-tag>
            <el-tag type="success" effect="plain">{{ report.report_date }}</el-tag>
          </div>
          <div class="report-content">{{ report.content }}</div>
        </section>

        <el-alert
          class="report-warning"
          title="当前内容仅用于个人研究辅助，不构成投资建议，系统不会自动下单。"
          type="warning"
          show-icon
          :closable="false"
        />
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'

import { api } from '../api/modules'
import type { AiReport, MarketOverview, StrategySignal, WatchStock } from '../types/api'

const reports = ref<AiReport[]>([])
const report = ref<AiReport>()
const overview = ref<MarketOverview>()
const signals = ref<StrategySignal[]>([])
const watchStocks = ref<WatchStock[]>([])
const loading = ref(false)
const error = ref('')

const marketTone = computed(() => {
  if (!overview.value) return '-'
  if (overview.value.up_count > overview.value.down_count) return '偏暖'
  if (overview.value.up_count < overview.value.down_count) return '偏弱'
  return '震荡'
})

const plainLanguageSummary = computed(() => {
  const strongest = overview.value?.strongest
  const weakest = overview.value?.weakest
  if (!strongest || !weakest) {
    return '这份日报会把复杂指标翻译成普通话：谁更强、谁更弱、哪些只是观察、哪些需要谨慎。'
  }
  return `今天更强的是 ${strongest.name}，说明这类方向短线更受资金关注；更弱的是 ${weakest.name}，说明它暂时需要多看少动。WATCH 表示值得继续观察，CAUTION 表示风险偏高。`
})

async function loadReport(id: number) {
  loading.value = true
  error.value = ''
  try {
    report.value = await api.reportDetail(id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'AI 日报加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function loadLatest() {
  loading.value = true
  error.value = ''
  try {
    report.value = await api.latestReport()
    reports.value = await api.reports()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'AI 日报生成失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const [reportList, marketData, signalData, stockData] = await Promise.all([
    api.reports(),
    api.marketOverview(),
    api.signals(),
    api.watchStocks(),
  ])
  reports.value = reportList
  overview.value = marketData
  signals.value = signalData
  watchStocks.value = stockData
  if (reportList[0]) {
    await loadReport(reportList[0].id)
  }
})
</script>
