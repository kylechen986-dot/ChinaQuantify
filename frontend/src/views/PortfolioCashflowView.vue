<template>
  <div class="cashflow-workspace">
    <section class="cashflow-hero">
      <div>
        <div class="eyebrow">资金流水详情</div>
        <h2>{{ detail?.name ?? '读取中' }} {{ detail?.symbol ?? '' }}</h2>
        <p>
          这里不看复杂术语，只看钱有没有对上：买入花出去是负数，卖出和分红收回来是正数，
          当前还拿着的股票市值也是正数，全部加起来就是这支股票现在赚还是赔。
        </p>
      </div>
      <el-button @click="router.back()">返回</el-button>
    </section>

    <div class="cashflow-summary-grid">
      <article>
        <span>当前持仓</span>
        <strong>{{ detail?.quantity ?? '-' }} 股</strong>
        <small>现价 {{ formatMoney(detail?.current_price) }}</small>
      </article>
      <article>
        <span>当前市值</span>
        <strong>{{ formatMoney(detail?.market_value) }}</strong>
        <small>成本 {{ formatMoney(detail?.cost_value) }}</small>
      </article>
      <article>
        <span>这支总赚赔</span>
        <strong :class="profitClass(detail?.holding_profit)">{{ signedMoney(detail?.holding_profit) }}</strong>
        <small>{{ signedPercent(detail?.holding_profit_pct) }}</small>
      </article>
      <article>
        <span>流水相加</span>
        <strong :class="profitClass(detail?.flow_profit)">{{ signedMoney(detail?.flow_profit) }}</strong>
        <small>收回 {{ formatMoney(detail?.total_inflow) }} / 花出 {{ formatMoney(detail?.total_outflow) }}</small>
      </article>
    </div>

    <section class="cashflow-panel">
      <div class="dashboard-panel-head">
        <div>
          <h3>钱是怎么算出来的</h3>
          <p>{{ detail?.synced_at ?? '-' }} · {{ detail?.sync_timezone ?? 'Asia/Shanghai' }}</p>
        </div>
        <el-tag effect="plain">{{ detail?.flows.length ?? 0 }} 条</el-tag>
      </div>

      <div v-if="detail?.flows.length" class="cashflow-timeline">
        <article v-for="flow in detail.flows" :key="flow.id" class="cashflow-item">
          <div class="cashflow-date">
            <strong>{{ flow.date || '-' }}</strong>
            <el-tag :type="flow.amount >= 0 ? 'danger' : 'success'" effect="plain">{{ flow.type_text }}</el-tag>
          </div>
          <div class="cashflow-main">
            <div>
              <strong>{{ flow.note || flow.type_text }}</strong>
              <span v-if="flow.quantity">数量 {{ flow.quantity }} 股 · 单价 {{ formatMoney(flow.price) }}</span>
            </div>
            <em>{{ flow.calculation_text }}</em>
            <b :class="profitClass(flow.amount)">{{ signedMoney(flow.amount) }}</b>
          </div>
        </article>
      </div>
      <el-skeleton v-else-if="loading" :rows="8" animated />
      <el-empty v-else description="暂无流水" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '../api/modules'
import type { PortfolioCashflowDetail } from '../types/api'

const route = useRoute()
const router = useRouter()
const detail = ref<PortfolioCashflowDetail>()
const loading = ref(false)

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

onMounted(async () => {
  loading.value = true
  try {
    detail.value = await api.portfolioCashflows(String(route.params.symbol))
  } finally {
    loading.value = false
  }
})
</script>
