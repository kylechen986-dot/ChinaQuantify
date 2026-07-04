<template>
  <div class="stock-workspace">
    <section ref="stockListPanel" class="stock-list-panel">
      <div class="stock-list-header">
        <div>
          <h2>关注股票</h2>
          <p>真实行情来自新浪财经接口；列表支持搜索、行业筛选和滚动加载。</p>
        </div>
        <el-tag type="success" effect="plain">{{ stockPage?.data_source ?? 'SINA_REALTIME' }}</el-tag>
      </div>

      <el-tabs v-model="activeTab" class="stock-tabs" @tab-change="handleTabChange">
        <el-tab-pane label="我的关注" name="watched">
          <div class="watch-grid">
            <button
              v-for="stock in watchedStocks"
              :key="stock.symbol"
              class="watch-card"
              :class="{ active: selected?.symbol === stock.symbol }"
              type="button"
              @click="selectStock(stock)"
            >
              <span>{{ stock.name }}</span>
              <strong :class="stock.change_pct >= 0 ? 'text-up' : 'text-down'">{{ stock.change_pct }}%</strong>
              <small>{{ stock.symbol }} · {{ stock.industry }} · {{ stock.synced_at }}</small>
            </button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="股票列表" name="all">
          <div class="stock-filter-row">
            <el-input
              v-model="keyword"
              clearable
              placeholder="搜索股票名称 / 代码，例如 贵州茅台 或 600519"
              @keyup.enter="reloadStocks"
              @clear="reloadStocks"
            />
            <el-select v-model="industry" clearable filterable placeholder="行业筛选" @change="reloadStocks">
              <el-option
                v-for="item in industries"
                :key="item.code"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
            <el-button type="primary" @click="reloadStocks">查询</el-button>
          </div>

          <div ref="stockTableWrap" class="stock-scroll-list" @wheel.passive="handleWheel">
            <el-table class="stock-table" :data="stocks" :height="tableHeight" highlight-current-row @row-click="selectStock">
              <el-table-column prop="symbol" label="代码" width="96" />
              <el-table-column prop="name" label="名称" min-width="130" />
              <el-table-column prop="industry" label="行业" width="110" />
              <el-table-column prop="close" label="现价" width="90" />
              <el-table-column prop="change_pct" label="涨跌幅" width="100">
                <template #default="{ row }">
                  <span :class="row.change_pct >= 0 ? 'text-up' : 'text-down'">{{ row.change_pct }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="turnover_ratio" label="换手" width="90" />
              <el-table-column prop="signal_score" label="评分" width="86" />
              <el-table-column label="关注" width="106">
                <template #default="{ row }">
                  <el-tag v-if="row.watched" type="success" effect="plain">已关注</el-tag>
                  <el-button v-else size="small" @click.stop="addToWatch(row.symbol)">加入</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div class="stock-load-state">
              <span v-if="loading">正在加载真实行情...</span>
              <span v-else-if="stockPage?.has_more">向下滚动加载更多</span>
              <span v-else>已加载 {{ stocks.length }} / {{ stockPage?.total ?? stocks.length }} 只股票</span>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </section>

    <aside ref="stockDetailPanel" class="stock-detail-panel" v-if="selected">
      <div class="stock-detail-head">
        <div>
          <div class="eyebrow">个股技术研判</div>
          <h2>{{ selected.name }}</h2>
          <p>{{ selected.symbol }} · {{ selected.market }} · {{ selected.industry }} · {{ selected.synced_at }}</p>
        </div>
        <div class="stock-detail-actions">
          <el-tag :type="operationSignal.tagType" effect="dark">{{ operationSignal.label }}</el-tag>
          <el-button v-if="!selected.watched" type="primary" @click="addToWatch(selected.symbol)">
            加入关注队列
          </el-button>
          <el-tag v-else type="success" effect="plain">已关注</el-tag>
        </div>
      </div>

      <section class="stock-action-card" :class="operationSignal.className">
        <div>
          <span>研究操作倾向</span>
          <strong>{{ operationSignal.label }}</strong>
          <p>{{ operationSignal.message }}</p>
        </div>
        <div class="stock-confidence">
          <small>信号强度 {{ operationSignal.confidence }} / 100</small>
          <el-progress :percentage="operationSignal.confidence" :color="operationSignal.color" :show-text="false" />
        </div>
      </section>

      <div class="stock-quick-grid">
        <div><span>现价</span><strong>{{ selected.close }}</strong></div>
        <div><span>涨跌幅</span><strong :class="selected.change_pct >= 0 ? 'text-up' : 'text-down'">{{ selected.change_pct }}%</strong></div>
        <div><span>MA20 距离</span><strong :class="ma20Gap >= 0 ? 'text-up' : 'text-down'">{{ formatPct(ma20Gap) }}</strong></div>
        <div><span>RSI14</span><strong>{{ selected.rsi14 }}</strong></div>
      </div>

      <section class="stock-analysis-block">
        <div class="block-title-row">
          <h3>价格区间</h3>
          <span>低 {{ selected.low }} / 高 {{ selected.high }}</span>
        </div>
        <div class="price-range">
          <div class="price-range-track">
            <i :style="{ left: `${pricePosition}%` }"></i>
          </div>
          <div class="price-range-labels">
            <span>低点</span>
            <strong>现价位置 {{ pricePosition }}%</strong>
            <span>高点</span>
          </div>
        </div>
      </section>

      <section class="stock-analysis-block">
        <div class="block-title-row">
          <h3>技术参数</h3>
          <span>{{ operationSignal.shortHint }}</span>
        </div>
        <div class="technical-metrics">
          <div v-for="metric in technicalMetrics" :key="metric.label" class="technical-metric">
            <div>
              <span>{{ metric.label }}</span>
              <strong>{{ metric.value }}</strong>
            </div>
            <el-progress :percentage="metric.percentage" :color="metric.color" :show-text="false" />
            <small>{{ metric.hint }}</small>
          </div>
        </div>
      </section>

      <section class="stock-analysis-block">
        <h3>信号理由</h3>
        <ul><li v-for="item in operationSignal.reasons" :key="item">{{ item }}</li></ul>
      </section>

      <section class="stock-analysis-block">
        <h3>风险提醒</h3>
        <ul><li v-for="item in selected.risk_points" :key="item">{{ item }}</li></ul>
      </section>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { api } from '../api/modules'
import type { StockIndustry, StockPage, WatchStock } from '../types/api'

const activeTab = ref('watched')
const stocks = ref<WatchStock[]>([])
const watchedStocks = ref<WatchStock[]>([])
const industries = ref<StockIndustry[]>([])
const selected = ref<WatchStock>()
const stockPage = ref<StockPage>()
const keyword = ref('')
const industry = ref('')
const page = ref(1)
const loading = ref(false)
const scrollIntent = ref(0)
const consumedScrollIntent = ref(0)
const stockListPanel = ref<HTMLElement>()
const stockTableWrap = ref<HTMLElement>()
const stockDetailPanel = ref<HTMLElement>()
const tableHeight = ref(568)
let tableScrollEl: HTMLElement | null = null
let layoutObserver: ResizeObserver | undefined

const watchedSymbols = computed(() => new Set(watchedStocks.value.map((item) => item.symbol)))

const ma20Gap = computed(() => distancePct(selected.value?.close, selected.value?.ma20))
const ma60Gap = computed(() => distancePct(selected.value?.close, selected.value?.ma60))
const pricePosition = computed(() => {
  const stock = selected.value
  if (!stock || stock.high <= stock.low) return 50
  return Math.round(clamp(((stock.close - stock.low) / (stock.high - stock.low)) * 100, 0, 100))
})
const dayRangePct = computed(() => {
  const stock = selected.value
  if (!stock?.close) return 0
  return ((stock.high - stock.low) / stock.close) * 100
})
const technicalMetrics = computed(() => {
  const stock = selected.value
  if (!stock) return []
  return [
    {
      label: 'MA20',
      value: formatPct(ma20Gap.value),
      percentage: trendPercentage(ma20Gap.value),
      color: ma20Gap.value >= 0 ? '#d92d20' : '#039855',
      hint: ma20Gap.value >= 0 ? '价格站上短期均线' : '价格跌破短期均线',
    },
    {
      label: 'MA60',
      value: formatPct(ma60Gap.value),
      percentage: trendPercentage(ma60Gap.value),
      color: ma60Gap.value >= 0 ? '#d92d20' : '#039855',
      hint: ma60Gap.value >= 0 ? '中期趋势仍有支撑' : '中期趋势偏弱',
    },
    {
      label: 'RSI14',
      value: stock.rsi14.toFixed(1),
      percentage: Math.round(clamp(stock.rsi14, 0, 100)),
      color: stock.rsi14 >= 70 ? '#f79009' : stock.rsi14 >= 50 ? '#d92d20' : '#039855',
      hint: stock.rsi14 >= 70 ? '动能偏热，警惕追高' : stock.rsi14 >= 50 ? '动能处于强势区' : '动能仍偏弱',
    },
    {
      label: '日内位置',
      value: `${pricePosition.value}%`,
      percentage: pricePosition.value,
      color: pricePosition.value >= 60 ? '#d92d20' : pricePosition.value >= 35 ? '#1f7aec' : '#039855',
      hint: '越靠近 100 越接近日内高点',
    },
    {
      label: '波动幅度',
      value: formatPlainPct(dayRangePct.value),
      percentage: Math.round(clamp(dayRangePct.value * 12, 0, 100)),
      color: dayRangePct.value >= 6 ? '#f79009' : '#1f7aec',
      hint: '按当日高低价估算',
    },
    {
      label: '换手率',
      value: formatPlainPct(stock.turnover_ratio),
      percentage: Math.round(clamp(stock.turnover_ratio * 12, 0, 100)),
      color: stock.turnover_ratio >= 5 ? '#f79009' : '#1f7aec',
      hint: '越高说明交易越活跃',
    },
  ]
})
const operationSignal = computed(() => {
  const stock = selected.value
  if (!stock) {
    return {
      label: '等待数据',
      tagType: 'info' as const,
      className: 'is-neutral',
      color: '#667085',
      confidence: 0,
      shortHint: '暂无技术数据',
      message: '请先选择一只股票查看技术研判。',
      reasons: [],
    }
  }
  const aboveMa20 = ma20Gap.value >= 0
  const aboveMa60 = ma60Gap.value >= 0
  const momentumOk = stock.rsi14 >= 50 && stock.rsi14 < 70
  const overheated = stock.rsi14 >= 70
  const weakTrend = !aboveMa20 && !aboveMa60
  const strongSetup = stock.signal_score >= 75 && aboveMa20 && aboveMa60 && momentumOk
  const holdSetup = stock.signal_score >= 60 && aboveMa20 && !overheated
  const riskSetup = stock.signal_score <= 40 || weakTrend || (stock.change_pct < -2 && !aboveMa20)

  const reasons = [
    `策略评分 ${stock.signal_score}，短期均线距离 ${formatPct(ma20Gap.value)}，中期均线距离 ${formatPct(ma60Gap.value)}。`,
    `RSI14 为 ${stock.rsi14.toFixed(1)}，${rsiText(stock.rsi14)}。`,
    `${stock.market_context} ${stock.relative_strength}。`,
  ]

  if (strongSetup) {
    return {
      label: '买入观察',
      tagType: 'danger' as const,
      className: 'is-buy',
      color: '#d92d20',
      confidence: stock.signal_score,
      shortHint: '趋势、动能相对一致',
      message: '技术面进入买入候选区，但仍建议等回撤承接或分批验证，不做一键下单。',
      reasons,
    }
  }
  if (holdSetup) {
    return {
      label: '持有观察',
      tagType: 'warning' as const,
      className: 'is-hold',
      color: '#f79009',
      confidence: stock.signal_score,
      shortHint: '趋势尚未破坏',
      message: '当前更像持有或继续跟踪信号，适合观察能否继续站稳 MA20。',
      reasons,
    }
  }
  if (riskSetup) {
    return {
      label: '风险退出',
      tagType: 'success' as const,
      className: 'is-sell',
      color: '#039855',
      confidence: Math.max(55, 100 - stock.signal_score),
      shortHint: '风险控制优先',
      message: '技术面偏弱，已有仓位优先考虑控制风险；未持有时不适合追入。',
      reasons,
    }
  }
  return {
    label: '等待确认',
    tagType: 'info' as const,
    className: 'is-neutral',
    color: '#1f7aec',
    confidence: stock.signal_score,
    shortHint: '信号不够一致',
    message: '趋势、动能和市场背景暂未形成共振，先观察下一次放量或站稳信号。',
    reasons,
  }
})

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

function distancePct(current = 0, base = 0) {
  if (!current || !base) return 0
  return ((current - base) / base) * 100
}

function trendPercentage(value: number) {
  return Math.round(clamp(50 + value * 8, 0, 100))
}

function formatPct(value: number) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function formatPlainPct(value: number) {
  return `${value.toFixed(2)}%`
}

function rsiText(value: number) {
  if (value >= 70) return '动能偏热'
  if (value >= 50) return '动能偏强'
  if (value <= 35) return '动能偏弱'
  return '动能中性偏弱'
}

function getTableScrollEl() {
  return stockTableWrap.value?.querySelector<HTMLElement>('.el-scrollbar__wrap') ?? null
}

function bindTableScroll() {
  const scrollEl = getTableScrollEl()
  if (scrollEl === tableScrollEl) return
  tableScrollEl?.removeEventListener('scroll', handleTableScroll)
  tableScrollEl = scrollEl
  tableScrollEl?.addEventListener('scroll', handleTableScroll, { passive: true })
}

function updateTableHeight() {
  const wrapper = stockTableWrap.value
  const listPanel = stockListPanel.value
  const detailPanel = stockDetailPanel.value
  if (!wrapper || !listPanel || !detailPanel) return
  const loadStateHeight = wrapper.querySelector<HTMLElement>('.stock-load-state')?.offsetHeight ?? 45
  const wrapperOffset = wrapper.getBoundingClientRect().top - listPanel.getBoundingClientRect().top
  const bottomPadding = 18
  const nextHeight = Math.max(420, Math.round(detailPanel.offsetHeight - wrapperOffset - loadStateHeight - bottomPadding))
  if (nextHeight > 0) {
    tableHeight.value = nextHeight
  }
}

function handleTableScroll(event: Event) {
  void tryLoadNextPage(event.currentTarget as HTMLElement)
}

async function resetTableScroll() {
  scrollIntent.value = 0
  consumedScrollIntent.value = 0
  await nextTick()
  bindTableScroll()
  const scrollEl = getTableScrollEl()
  if (scrollEl) {
    scrollEl.scrollTop = 0
  }
  updateTableHeight()
}

async function loadWatched() {
  watchedStocks.value = await api.watchStocks()
  if (!selected.value && watchedStocks.value[0]) {
    selected.value = watchedStocks.value[0]
  }
}

async function loadStocks(reset = false) {
  if (loading.value) return
  if (reset) {
    page.value = 1
    stocks.value = []
  }
  loading.value = true
  try {
    const data = await api.stocks({
      page: page.value,
      page_size: 50,
      keyword: keyword.value,
      industry: industry.value,
    })
    stockPage.value = data
    const merged = data.items.map((item) => ({ ...item, watched: item.watched || watchedSymbols.value.has(item.symbol) }))
    stocks.value = reset ? merged : [...stocks.value, ...merged]
    if (!selected.value && stocks.value[0]) {
      selected.value = stocks.value[0]
    }
  } finally {
    loading.value = false
  }
}

async function reloadStocks() {
  await loadStocks(true)
  await resetTableScroll()
}

async function selectStock(row: WatchStock) {
  selected.value = await api.stockDetail(row.symbol)
}

async function addToWatch(symbol: string) {
  const updated = await api.addWatchStock(symbol)
  watchedStocks.value = await api.watchStocks()
  stocks.value = stocks.value.map((item) => (item.symbol === updated.symbol ? updated : item))
  selected.value = updated
  ElMessage.success(`${updated.name} 已加入关注队列`)
}

async function handleWheel(event: WheelEvent) {
  if (event.deltaY <= 0) return
  scrollIntent.value += 1
  await nextTick()
  bindTableScroll()
  const scrollEl = getTableScrollEl()
  if (scrollEl) {
    await tryLoadNextPage(scrollEl)
  }
}

async function tryLoadNextPage(target: HTMLElement) {
  const nearBottom = target.scrollTop + target.clientHeight >= target.scrollHeight - 80
  const hasNewUserIntent = consumedScrollIntent.value < scrollIntent.value
  if (!nearBottom || !hasNewUserIntent || loading.value || !stockPage.value?.has_more) return
  consumedScrollIntent.value = scrollIntent.value
  page.value += 1
  await loadStocks()
}

async function handleTabChange() {
  if (activeTab.value === 'all' && stocks.value.length === 0) {
    await loadStocks(true)
    await resetTableScroll()
  }
  await nextTick()
  bindTableScroll()
  updateTableHeight()
}

onMounted(async () => {
  const [industryData] = await Promise.all([api.industries(), loadWatched()])
  industries.value = industryData
  await nextTick()
  layoutObserver = new ResizeObserver(() => {
    updateTableHeight()
    bindTableScroll()
  })
  if (stockTableWrap.value) {
    layoutObserver.observe(stockTableWrap.value)
  }
  if (stockDetailPanel.value) {
    layoutObserver.observe(stockDetailPanel.value)
  }
  updateTableHeight()
  bindTableScroll()
})

onBeforeUnmount(() => {
  layoutObserver?.disconnect()
  tableScrollEl?.removeEventListener('scroll', handleTableScroll)
})

watch(selected, async () => {
  await nextTick()
  updateTableHeight()
})
</script>
