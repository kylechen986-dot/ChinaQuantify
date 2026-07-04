<template>
  <div class="dashboard-stack">
    <el-alert
      v-if="portfolio?.is_sample"
      class="dashboard-alert"
      title="当前为本地持仓账本示例数据，接入券商账户后这里会显示真实账户余额和真实持仓。"
      type="info"
      show-icon
      :closable="false"
    />
    <el-alert
      v-if="errors.length"
      class="dashboard-alert"
      :title="errors.join('；')"
      type="warning"
      show-icon
      :closable="false"
    />

    <section class="account-hero" :class="`is-${portfolio?.tone ?? 'flat'}`">
      <div>
        <div class="eyebrow">账户总览</div>
        <h2>{{ portfolio?.headline ?? '正在读取账户收益' }}</h2>
        <p>
          当前总资产 {{ formatMoney(portfolio?.total_assets) }}，可用余额
          {{ formatMoney(portfolio?.cash_balance) }}，股票市值 {{ formatMoney(portfolio?.market_value) }}。
        </p>
      </div>
      <div class="account-hero-profit">
        <span>今日盈亏</span>
        <strong :class="profitClass(portfolio?.today_profit)">
          {{ signedMoney(portfolio?.today_profit) }}
        </strong>
        <small>{{ signedPercent(portfolio?.today_profit_pct) }}</small>
      </div>
    </section>

    <div class="account-metric-grid">
      <article class="account-metric-card">
        <span>账户余额</span>
        <strong>{{ formatMoney(portfolio?.cash_balance) }}</strong>
        <small>当前可用现金</small>
      </article>
      <article class="account-metric-card">
        <span>股票市值</span>
        <strong>{{ formatMoney(portfolio?.market_value) }}</strong>
        <small>{{ portfolio?.position_count ?? 0 }} 只持仓</small>
      </article>
      <article class="account-metric-card">
        <span>持仓累计盈亏</span>
        <strong :class="profitClass(portfolio?.holding_profit)">
          {{ signedMoney(portfolio?.holding_profit) }}
        </strong>
        <small>{{ signedPercent(portfolio?.holding_profit_pct) }}</small>
      </article>
      <article class="account-metric-card">
        <span>同步时间</span>
        <strong class="account-time">{{ portfolio?.synced_at ?? '-' }}</strong>
        <small>{{ portfolio?.sync_timezone ?? 'Asia/Shanghai' }}</small>
      </article>
    </div>

    <section class="dashboard-panel">
      <div class="dashboard-panel-head">
        <div>
          <h3>我的持仓今天怎么样</h3>
          <p>先看每只股票今天赚了还是亏了，再决定要不要去操作看板看详细建议。</p>
        </div>
        <el-button size="small" :loading="loading" @click="loadDashboard">刷新</el-button>
      </div>

      <div v-if="portfolio?.positions.length" class="holding-card-grid">
        <article
          v-for="position in portfolio.positions"
          :key="position.symbol"
          class="holding-card"
          :class="profitClass(position.today_profit)"
        >
          <div class="holding-card-head">
            <div>
              <strong>{{ position.name }}</strong>
              <span>{{ position.symbol }} · {{ position.quantity }} 股</span>
            </div>
            <el-tag :type="position.today_profit > 0 ? 'danger' : position.today_profit < 0 ? 'success' : 'info'" effect="dark">
              {{ position.today_profit > 0 ? '今天赚钱' : position.today_profit < 0 ? '今天亏钱' : '今天持平' }}
            </el-tag>
          </div>

          <div class="holding-profit-row">
            <div>
              <span>今天</span>
              <strong :class="profitClass(position.today_profit)">{{ signedMoney(position.today_profit) }}</strong>
              <small>{{ signedPercent(position.today_profit_pct) }}</small>
            </div>
            <div>
              <span>累计</span>
              <strong :class="profitClass(position.holding_profit)">{{ signedMoney(position.holding_profit) }}</strong>
              <small>{{ signedPercent(position.holding_profit_pct) }}</small>
            </div>
          </div>

          <p>{{ position.message }}</p>
          <div class="holding-action-box">
            <span>现在怎么处理</span>
            <strong>{{ position.action_hint }}</strong>
          </div>
          <router-link class="holding-flow-link" :to="`/portfolio/${position.symbol}/cashflows`">
            查看资金流水
          </router-link>
          <div class="holding-data-row">
            <span>总份额 {{ position.quantity }} 股</span>
            <span>持仓均价 {{ formatMoney(position.avg_cost_price) }}</span>
            <span>现价 {{ formatMoney(position.current_price) }}</span>
            <span>市值 {{ formatMoney(position.market_value) }}</span>
          </div>

          <el-collapse class="holding-lot-collapse">
            <el-collapse-item title="查看每笔买入赚赔" :name="position.symbol">
              <div class="holding-lot-list">
                <article v-for="lot in position.lots" :key="lot.id" class="holding-lot-item">
                  <div>
                    <strong>{{ lot.buy_date || '买入批次' }}</strong>
                    <span>{{ lot.quantity }} 股 · 买入价 {{ formatMoney(lot.cost_price) }}</span>
                  </div>
                  <div>
                    <b :class="profitClass(lot.profit)">{{ signedMoney(lot.profit) }}</b>
                    <small>{{ signedPercent(lot.profit_pct) }}</small>
                  </div>
                </article>
              </div>
            </el-collapse-item>
          </el-collapse>
        </article>
      </div>
      <el-skeleton v-else-if="loading" :rows="8" animated />
      <el-empty v-else description="暂无持仓数据" />
    </section>

    <div class="dashboard-grid">
      <section class="dashboard-panel">
        <div class="dashboard-panel-head">
          <div>
            <h3>今天市场背景</h3>
            <p>用来解释你的持仓是顺着市场涨跌，还是自己更强/更弱。</p>
          </div>
          <el-tag effect="plain">{{ overview?.synced_at ?? '-' }}</el-tag>
        </div>
        <div class="market-message-card">
          <strong>{{ marketTone }} · {{ marketHeadline }}</strong>
          <p>{{ marketSummary }}</p>
          <div class="dashboard-chip-row">
            <el-tag effect="plain">最强 {{ overview?.strongest.name ?? '-' }}</el-tag>
            <el-tag type="info" effect="plain">最弱 {{ overview?.weakest.name ?? '-' }}</el-tag>
            <el-tag type="success" effect="plain">上涨 {{ overview?.up_count ?? '-' }} 只</el-tag>
            <el-tag type="warning" effect="plain">下跌 {{ overview?.down_count ?? '-' }} 只</el-tag>
          </div>
        </div>
      </section>

      <section class="dashboard-panel">
        <div class="dashboard-panel-head">
          <div>
            <h3>AI 日报摘要</h3>
            <p>{{ report?.model_provider ?? 'AI' }} · {{ report?.report_date ?? '今日' }}</p>
          </div>
        </div>
        <template v-if="report">
          <h4 class="dashboard-report-title">{{ report.title }}</h4>
          <p class="dashboard-report-summary">{{ report.summary }}</p>
        </template>
        <el-skeleton v-else-if="reportLoading" :rows="5" animated />
        <el-empty v-else description="暂无日报摘要" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { api } from '../api/modules'
import type { AiReport, MarketOverview, PortfolioOverview } from '../types/api'

const overview = ref<MarketOverview>()
const portfolio = ref<PortfolioOverview>()
const report = ref<AiReport>()
const loading = ref(false)
const reportLoading = ref(false)
const errors = ref<string[]>([])

const marketTone = computed(() => {
  if (!overview.value) return '同步中'
  if (overview.value.up_count > overview.value.down_count) return '偏暖'
  if (overview.value.up_count < overview.value.down_count) return '偏弱'
  return '震荡'
})

const marketHeadline = computed(() => {
  const strongest = overview.value?.strongest
  if (!strongest) return '等待行情数据'
  return `${strongest.name} 领涨 ${strongest.change_pct}%`
})

const marketSummary = computed(() => {
  const current = overview.value
  if (!current) return '正在读取市场背景。'
  return `当前跟踪 ${current.symbol_count} 只 ETF，上涨 ${current.up_count} 只、下跌 ${current.down_count} 只。最强方向是 ${current.strongest.name}，最弱方向是 ${current.weakest.name}。`
})

function formatMoney(value: number | undefined) {
  if (typeof value !== 'number') return '-'
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function signedMoney(value: number | undefined) {
  if (typeof value !== 'number') return '-'
  if (value > 0) return `+${formatMoney(value)}`
  if (value < 0) return `-¥${Math.abs(value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  return formatMoney(value)
}

function signedPercent(value: number | undefined) {
  if (typeof value !== 'number') return '-'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

function profitClass(value: number | undefined) {
  if (!value) return 'is-flat'
  return value > 0 ? 'is-profit' : 'is-loss'
}

async function loadDashboard() {
  loading.value = true
  reportLoading.value = true
  errors.value = []
  try {
    const [portfolioResult, marketResult, reportResult] = await Promise.allSettled([
      api.portfolioOverview(),
      api.marketOverview(),
      api.latestReport(),
    ])
    if (portfolioResult.status === 'fulfilled') {
      portfolio.value = portfolioResult.value
    } else {
      errors.value.push('账户数据加载失败')
    }
    if (marketResult.status === 'fulfilled') {
      overview.value = marketResult.value
    } else {
      errors.value.push('市场背景加载失败')
    }
    if (reportResult.status === 'fulfilled') {
      report.value = reportResult.value
    }
  } finally {
    loading.value = false
    reportLoading.value = false
  }
}

onMounted(loadDashboard)
</script>
