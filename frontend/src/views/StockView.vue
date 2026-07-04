<template>
  <div class="stock-workspace">
    <section class="stock-list-panel">
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

          <div class="stock-scroll-list" @scroll="handleScroll" @wheel.passive="handleWheel">
            <el-table :data="stocks" highlight-current-row @row-click="selectStock">
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

    <aside class="stock-detail-panel" v-if="selected">
      <div class="stock-detail-head">
        <div>
          <div class="eyebrow">个股专项研判</div>
          <h2>{{ selected.name }}</h2>
          <p>{{ selected.symbol }} · {{ selected.market }} · {{ selected.industry }} · {{ selected.synced_at }}</p>
        </div>
        <el-button v-if="!selected.watched" type="primary" @click="addToWatch(selected.symbol)">
          加入关注队列
        </el-button>
        <el-tag v-else type="success" effect="plain">已在关注队列</el-tag>
      </div>

      <div class="stock-quick-grid">
        <div><span>现价</span><strong>{{ selected.close }}</strong></div>
        <div><span>涨跌幅</span><strong :class="selected.change_pct >= 0 ? 'text-up' : 'text-down'">{{ selected.change_pct }}%</strong></div>
        <div><span>策略评分</span><strong>{{ selected.signal_score }}</strong></div>
        <div><span>换手率</span><strong>{{ selected.turnover_ratio }}%</strong></div>
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
        <ul><li v-for="item in selected.test_plan" :key="item">{{ item }}</li></ul>
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
import { computed, onMounted, ref } from 'vue'

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

const watchedSymbols = computed(() => new Set(watchedStocks.value.map((item) => item.symbol)))

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

async function handleScroll(event: Event) {
  const target = event.target as HTMLElement
  await tryLoadNextPage(target)
}

async function handleWheel(event: WheelEvent) {
  if (event.deltaY <= 0) return
  scrollIntent.value += 1
  await tryLoadNextPage(event.currentTarget as HTMLElement)
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
  }
}

onMounted(async () => {
  const [industryData] = await Promise.all([api.industries(), loadWatched()])
  industries.value = industryData
})
</script>
