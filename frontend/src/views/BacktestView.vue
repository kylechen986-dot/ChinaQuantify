<template>
  <div class="backtest-workspace">
    <section class="backtest-hero">
      <div>
        <div class="eyebrow">策略体检报告</div>
        <h2>{{ verdict.title }}</h2>
        <p>{{ verdict.summary }}</p>
      </div>
      <el-tag :type="verdict.tagType" effect="dark">{{ verdict.label }}</el-tag>
    </section>

    <div class="page-grid">
      <MetricCard label="累计收益" :value="formatPercent(summary?.metrics.total_return)" hint="历史模拟赚了多少" />
      <MetricCard label="最大回撤" :value="formatPercent(summary?.metrics.max_drawdown)" hint="过程中最多亏到什么程度" />
      <MetricCard label="胜率" :value="formatPercent(summary?.metrics.win_rate)" hint="每 100 次大概赢几次" />
      <MetricCard label="交易次数" :value="summary?.metrics.trade_count ?? '-'" hint="样本太少时结论要打折" />
    </div>

    <div class="backtest-grid">
      <section class="backtest-panel backtest-chart-panel">
        <div class="backtest-panel-head">
          <div>
            <h3>资金曲线</h3>
            <p>{{ summary?.strategy_name ?? '-' }} · {{ summary?.name ?? '-' }}</p>
          </div>
          <el-tag effect="plain">{{ summary?.strategy_code ?? 'strategy' }}</el-tag>
        </div>
        <EquityChart :data="summary?.equity_curve ?? []" />
      </section>

      <aside class="backtest-panel">
        <div class="backtest-panel-head">
          <div>
            <h3>这个页面有什么用？</h3>
            <p>它不是预测未来，是检查策略过去有没有经得起测试。</p>
          </div>
        </div>
        <div class="backtest-explain-list">
          <article>
            <strong>一、先看收益</strong>
            <p>累计收益为正，说明这套规则在样例周期里赚过钱；但收益不能单独看。</p>
          </article>
          <article>
            <strong>二、再看回撤</strong>
            <p>最大回撤越小，代表中途亏损压力越轻。普通用户优先看这个风险指标。</p>
          </article>
          <article>
            <strong>三、最后看稳定性</strong>
            <p>胜率、夏普和交易次数一起看，判断策略是不是只靠一两次运气。</p>
          </article>
        </div>
      </aside>

      <section class="backtest-panel">
        <div class="backtest-panel-head">
          <div>
            <h3>关键指标翻译</h3>
            <p>把量化指标换成容易理解的判断。</p>
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

      <section class="backtest-panel">
        <div class="backtest-panel-head">
          <div>
            <h3>下一步怎么用</h3>
            <p>看懂后再决定是否继续观察。</p>
          </div>
        </div>
        <ul class="backtest-next-list">
          <li>如果收益为正且回撤可控，可以把它作为观察策略继续跟踪。</li>
          <li>如果回撤变大或胜率明显下降，说明策略可能不适合当前市场。</li>
          <li>当前 MVP 只做研究辅助，不会自动买入、卖出或下单。</li>
        </ul>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { api } from '../api/modules'
import EquityChart from '../components/EquityChart.vue'
import MetricCard from '../components/MetricCard.vue'
import type { BacktestSummary } from '../types/api'

const summary = ref<BacktestSummary>()

const verdict = computed(() => {
  const metrics = summary.value?.metrics
  if (!metrics) {
    return {
      title: '正在读取回测结果',
      summary: '系统正在加载历史模拟数据，用来检查策略过去的收益、亏损压力和稳定性。',
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
      title: '策略历史表现可继续观察',
      summary: '这套策略在样例周期里收益为正，回撤压力不大，胜率和夏普也处在可接受区间。它不是买卖指令，但值得继续跟踪。',
      label: '可观察',
      tagType: 'success' as const,
    }
  }
  if (drawdown > 0.06 || totalReturn < 0) {
    return {
      title: '策略历史风险偏高',
      summary: '回测中亏损压力偏大，或收益没有覆盖风险。当前更适合先复盘规则，不适合直接用于实盘判断。',
      label: '需谨慎',
      tagType: 'warning' as const,
    }
  }
  return {
    title: '策略表现中性，需要更多样本',
    summary: '当前结果没有明显失效，但也不够强。继续观察更多交易日，确认它不是短期运气。',
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

function formatPercent(value: number | undefined) {
  if (typeof value !== 'number') return '-'
  return `${(value * 100).toFixed(2)}%`
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

onMounted(async () => {
  summary.value = await api.backtestSummary()
})
</script>
