<template>
  <div class="monitor-workspace">
    <section class="monitor-hero">
      <div>
        <div class="eyebrow">自动监控 + 每周复盘</div>
        <h2>今天看哪几只、要不要动、买多少、什么时候出</h2>
        <p>
          这个系统面向看不懂专业行情软件的小白用户。它把推荐股票、关注股票、整体市场和策略回测浓缩成消息卡：
          先给一句话结论，再给仓位、周期、入场和退出条件。
        </p>
      </div>
      <div class="monitor-hero-actions">
        <el-tag :type="scheduler?.market_status === '开市中' ? 'success' : 'info'" effect="dark">
          {{ scheduler?.market_status ?? '读取中' }}
        </el-tag>
        <el-button :loading="collecting" type="primary" @click="collectNow">立即采集一次</el-button>
        <el-button :loading="reviewing" @click="buildReviewNow">生成周复盘</el-button>
      </div>
    </section>

    <div class="monitor-status-grid">
      <article v-for="item in statusCards" :key="item.label" class="monitor-status-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </div>

    <section class="monitor-panel">
      <div class="monitor-panel-head">
        <div>
          <h3>今日小白操作卡</h3>
          <p>先看结论：推荐哪几只、现在能不能买、最多买多少、短线还是长线、什么时候退出。</p>
        </div>
        <el-tag type="success" effect="plain">SINA_REALTIME</el-tag>
      </div>
      <div v-if="recommendations.length" class="recommend-grid">
        <article
          v-for="stock in recommendations"
          :key="stock.symbol"
          class="recommend-card"
          :class="`is-${stock.action_plan.action_level}`"
        >
          <div class="recommend-card-head">
            <div>
              <strong>{{ stock.name }}</strong>
              <span>{{ stock.symbol }} · {{ stock.market }} · {{ stock.industry }}</span>
            </div>
            <el-tag :type="actionTagType(stock.action_plan.action_level)" effect="dark">
              {{ stock.action_plan.action }}
            </el-tag>
          </div>
          <p class="action-one-liner">{{ stock.action_plan.one_liner }}</p>
          <div class="recommend-data-row">
            <span>买多少：{{ stock.action_plan.position }}</span>
            <span>周期：{{ stock.action_plan.horizon }}</span>
          </div>
          <div class="action-rule-box">
            <span>什么时候买</span>
            <strong>{{ stock.action_plan.buy_timing }}</strong>
          </div>
          <div class="action-rule-box">
            <span>什么时候出</span>
            <strong>{{ stock.action_plan.sell_rule }}</strong>
          </div>
          <el-collapse class="action-detail-collapse">
            <el-collapse-item title="为什么这么判断" :name="stock.symbol">
              <div class="recommend-data-row">
                <span>现价 {{ formatPrice(stock.close) }}</span>
                <span :class="stock.change_pct >= 0 ? 'text-up' : 'text-down'">{{ stock.change_pct }}%</span>
                <span>评分 {{ stock.recommendation_score ?? stock.signal_score }}</span>
              </div>
              <ul>
                <li v-for="reason in stock.recommendation_reason?.slice(0, 3)" :key="reason">{{ reason }}</li>
              </ul>
            </el-collapse-item>
          </el-collapse>
          <el-button v-if="!stock.watched" type="primary" plain @click="addRecommendation(stock.symbol)">
            加入关注队列
          </el-button>
          <el-tag v-else type="success" effect="plain">已在关注队列</el-tag>
        </article>
      </div>
      <el-skeleton v-else :rows="6" animated />
    </section>

    <div class="monitor-main-grid">
      <section class="monitor-panel monitor-panel-large">
        <div class="monitor-panel-head">
          <div>
            <h3>关注股监控快照</h3>
            <p>{{ latestSnapshot?.summary.market_brief ?? '还没有采集快照，点击“立即采集一次”即可生成。' }}</p>
          </div>
          <el-tag effect="plain">{{ latestSnapshot?.collected_at ?? '未采集' }}</el-tag>
        </div>

        <div v-if="latestSnapshot" class="snapshot-summary-grid">
          <article>
            <span>关注股</span>
            <strong>{{ latestSnapshot.watched_count }}</strong>
            <small>当前进入持续监控的股票数量</small>
          </article>
          <article>
            <span>重点观察</span>
            <strong>{{ latestSnapshot.summary.positive_count }}</strong>
            <small>趋势和动能相对配合</small>
          </article>
          <article>
            <span>等待确认</span>
            <strong>{{ latestSnapshot.summary.neutral_count }}</strong>
            <small>有信号，但还不够明确</small>
          </article>
          <article>
            <span>降低优先级</span>
            <strong>{{ latestSnapshot.summary.risk_count }}</strong>
            <small>趋势或评分偏弱</small>
          </article>
        </div>

        <div v-if="latestSnapshot?.watched_stocks.length" class="monitor-stock-list">
          <article v-for="stock in latestSnapshot.watched_stocks" :key="stock.symbol" class="monitor-stock-card">
            <div class="monitor-stock-head">
              <div>
                <strong>{{ stock.name }}</strong>
                <span>{{ stock.symbol }} · {{ stock.industry }} · {{ stock.synced_at }}</span>
              </div>
              <el-tag :type="monitorToneType(stock.monitor_tone)" effect="plain">
                {{ stock.action_plan.action }}
              </el-tag>
            </div>

            <div class="monitor-stock-data">
              <span>仓位：{{ stock.action_plan.position }}</span>
              <span>周期：{{ stock.action_plan.horizon }}</span>
            </div>
            <p>{{ stock.action_plan.one_liner }}</p>
            <div class="action-rule-grid">
              <div>
                <span>买入条件</span>
                <strong>{{ stock.action_plan.buy_timing }}</strong>
              </div>
              <div>
                <span>退出条件</span>
                <strong>{{ stock.action_plan.sell_rule }}</strong>
              </div>
            </div>

            <el-collapse>
              <el-collapse-item title="展开专业指标依据" :name="stock.symbol">
                <div class="monitor-stock-data">
                  <span>现价 {{ formatPrice(stock.close) }}</span>
                  <span :class="stock.change_pct >= 0 ? 'text-up' : 'text-down'">{{ stock.change_pct }}%</span>
                  <span>评分 {{ stock.signal_score }}</span>
                  <span>RSI {{ stock.rsi14 }}</span>
                </div>
                <div class="technical-strip">
                  <article v-for="check in stock.technical_checks" :key="check.label">
                    <div>
                      <span>{{ check.label }}</span>
                      <strong>{{ check.value }}</strong>
                    </div>
                    <el-progress :percentage="check.score" :show-text="false" />
                    <small>{{ check.plain }}</small>
                  </article>
                </div>
                <ul class="monitor-risk-list">
                  <li v-for="risk in stock.risk_points" :key="risk">{{ risk }}</li>
                </ul>
              </el-collapse-item>
            </el-collapse>
          </article>
        </div>

        <el-empty v-else description="暂无关注股快照">
          <el-button type="primary" @click="collectNow">立即采集一次</el-button>
        </el-empty>
      </section>

      <section class="monitor-panel">
        <div class="monitor-panel-head">
          <div>
            <h3>每周复盘看板</h3>
            <p>休市后把本周采集结果翻译成能执行的观察清单。</p>
          </div>
          <el-tag effect="plain">{{ weeklyReview?.generated_at ?? '未生成' }}</el-tag>
        </div>

        <template v-if="weeklyReview">
          <div class="weekly-conclusion">
            <strong>{{ weeklyReview.conclusion }}</strong>
            <p>{{ weeklyReview.market_summary }}</p>
          </div>
          <div class="weekly-review-list">
            <article v-for="item in weeklyReview.watch_reviews" :key="item.symbol">
              <div>
                <strong>{{ item.name }}</strong>
                <el-tag size="small" effect="plain">{{ item.action }}</el-tag>
              </div>
              <p>{{ item.action_plan.one_liner || item.plain_summary }}</p>
              <small>
                {{ item.action_plan.position }} · {{ item.action_plan.horizon }} ·
                本周最新涨跌 {{ item.change_pct }}%
              </small>
            </article>
          </div>
          <el-collapse class="weekly-guide">
            <el-collapse-item title="关键指标怎么理解" name="guide">
              <ul>
                <li v-for="guide in weeklyReview.indicator_guide" :key="guide">{{ guide }}</li>
              </ul>
            </el-collapse-item>
            <el-collapse-item title="下周观察动作" name="actions">
              <ul>
                <li v-for="action in weeklyReview.next_actions" :key="action">{{ action }}</li>
              </ul>
            </el-collapse-item>
          </el-collapse>
        </template>

        <el-empty v-else description="暂无周复盘">
          <el-button @click="buildReviewNow">生成周复盘</el-button>
        </el-empty>
      </section>
    </div>

    <div class="page-grid">
      <MetricCard label="策略结论" :value="verdict.label" hint="先判断策略能不能继续观察" />
      <MetricCard label="累计收益" :value="formatPercent(summary?.metrics.total_return)" hint="历史模拟赚了多少" />
      <MetricCard label="最大回撤" :value="formatPercent(summary?.metrics.max_drawdown)" hint="过程中最多亏到什么程度" />
      <MetricCard label="胜率" :value="formatPercent(summary?.metrics.win_rate)" hint="每 100 次大概赢几次" />
    </div>

    <div class="backtest-main-grid">
      <section class="backtest-panel">
        <div class="backtest-panel-head">
          <div>
            <h3>策略资金曲线</h3>
            <p>{{ summary?.strategy_name ?? '-' }} · {{ summary?.name ?? '-' }}</p>
          </div>
          <el-tag effect="plain">{{ summary?.strategy_code ?? 'strategy' }}</el-tag>
        </div>
        <EquityChart :data="summary?.equity_curve ?? []" />
      </section>

      <section class="backtest-panel">
        <div class="backtest-panel-head">
          <div>
            <h3>回测指标翻译</h3>
            <p>它回答策略过去是否值得继续观察，不代表未来收益。</p>
          </div>
        </div>
        <div class="backtest-score-list">
          <div v-for="item in metricInsights" :key="item.label" class="backtest-score-item">
            <div>
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
            <el-progress :percentage="item.score" :color="item.color" :show-text="false" />
            <small>{{ item.hint }}</small>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { api } from '../api/modules'
import EquityChart from '../components/EquityChart.vue'
import MetricCard from '../components/MetricCard.vue'
import type { BacktestSummary, MonitorDashboard } from '../types/api'

const summary = ref<BacktestSummary>()
const monitor = ref<MonitorDashboard>()
const collecting = ref(false)
const reviewing = ref(false)

const scheduler = computed(() => monitor.value?.scheduler)
const latestSnapshot = computed(() => monitor.value?.latest_snapshot)
const weeklyReview = computed(() => monitor.value?.latest_weekly_review)
const recommendations = computed(() => monitor.value?.recommendations ?? [])

const statusCards = computed(() => [
  {
    label: '采集规则',
    value: scheduler.value ? `${scheduler.value.collect_interval_minutes} 分钟/次` : '-',
    hint: scheduler.value?.collect_window ?? '工作日开市期间自动采集',
  },
  {
    label: '下次采集',
    value: scheduler.value?.next_collect_at ?? '-',
    hint: '精确到秒，按 Asia/Shanghai 计算',
  },
  {
    label: '最新快照',
    value: latestSnapshot.value?.collected_at ?? '-',
    hint: latestSnapshot.value?.summary.headline ?? '尚未生成关注股采集快照',
  },
  {
    label: '周复盘',
    value: weeklyReview.value?.generated_at ?? '-',
    hint: scheduler.value?.weekly_review_rule ?? '休市时生成每周复盘',
  },
])

const verdict = computed(() => {
  const metrics = summary.value?.metrics
  if (!metrics) {
    return {
      label: '加载中',
      tagType: 'info' as const,
    }
  }
  const totalReturn = metrics.total_return
  const drawdown = Math.abs(metrics.max_drawdown)
  const winRate = metrics.win_rate
  const sharpe = metrics.sharpe
  if (totalReturn > 0.02 && drawdown <= 0.03 && winRate >= 0.55 && sharpe >= 1) {
    return {
      label: '可观察',
      tagType: 'success' as const,
    }
  }
  if (drawdown > 0.06 || totalReturn < 0) {
    return {
      label: '需谨慎',
      tagType: 'warning' as const,
    }
  }
  return {
    label: '待验证',
    tagType: 'info' as const,
  }
})

const metricInsights = computed(() => {
  const metrics = summary.value?.metrics
  if (!metrics) return []
  const drawdown = Math.abs(metrics.max_drawdown)
  return [
    {
      label: '赚钱能力',
      value: formatPercent(metrics.total_return),
      score: clamp(Math.round(metrics.total_return * 1800), 0, 100),
      color: metrics.total_return >= 0 ? '#d92d20' : '#039855',
      hint: metrics.total_return > 0 ? '样例周期内资金曲线向上' : '样例周期内没有赚钱',
    },
    {
      label: '亏损压力',
      value: formatPercent(metrics.max_drawdown),
      score: clamp(Math.round(100 - drawdown * 1600), 0, 100),
      color: drawdown <= 0.03 ? '#039855' : drawdown <= 0.06 ? '#f79009' : '#d92d20',
      hint: drawdown <= 0.03 ? '中途回撤较轻' : '回撤偏大，需要警惕',
    },
    {
      label: '胜率',
      value: formatPercent(metrics.win_rate),
      score: clamp(Math.round(metrics.win_rate * 100), 0, 100),
      color: metrics.win_rate >= 0.55 ? '#1f7aec' : '#f79009',
      hint: metrics.win_rate >= 0.55 ? '赢面略占优' : '胜率不够稳定',
    },
    {
      label: '风险调整收益',
      value: metrics.sharpe.toFixed(2),
      score: clamp(Math.round(metrics.sharpe * 50), 0, 100),
      color: metrics.sharpe >= 1 ? '#1f7aec' : '#f79009',
      hint: metrics.sharpe >= 1 ? '收益和波动相对匹配' : '收益质量还需要验证',
    },
  ]
})

function monitorToneType(tone: string) {
  if (tone === 'positive') return 'success'
  if (tone === 'risk') return 'danger'
  return 'warning'
}

function actionTagType(level: string) {
  if (level === 'trial_buy') return 'danger'
  if (level === 'wait') return 'warning'
  if (level === 'avoid') return 'info'
  return 'success'
}

function formatPercent(value: number | undefined) {
  if (typeof value !== 'number') return '-'
  return `${(value * 100).toFixed(2)}%`
}

function formatPrice(value: number | undefined) {
  if (typeof value !== 'number') return '-'
  return value.toFixed(2)
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

async function refreshMonitor() {
  monitor.value = await api.monitorDashboard()
}

async function collectNow() {
  collecting.value = true
  try {
    await api.collectMonitorSnapshot()
    await refreshMonitor()
    ElMessage.success('已完成一次关注股采集')
  } finally {
    collecting.value = false
  }
}

async function buildReviewNow() {
  reviewing.value = true
  try {
    await api.buildWeeklyReview()
    await refreshMonitor()
    ElMessage.success('周复盘已生成')
  } finally {
    reviewing.value = false
  }
}

async function addRecommendation(symbol: string) {
  const updated = await api.addWatchStock(symbol)
  if (monitor.value) {
    monitor.value.recommendations = monitor.value.recommendations.map((stock) =>
      stock.symbol === updated.symbol ? { ...stock, watched: true } : stock,
    )
  }
  ElMessage.success(`${updated.name} 已加入关注队列`)
}

onMounted(async () => {
  const [backtestData, monitorData] = await Promise.all([api.backtestSummary(), api.monitorDashboard()])
  summary.value = backtestData
  monitor.value = monitorData
})
</script>
