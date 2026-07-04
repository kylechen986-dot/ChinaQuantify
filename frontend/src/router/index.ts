import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '../layouts/AppLayout.vue'
import BacktestView from '../views/BacktestView.vue'
import DashboardView from '../views/DashboardView.vue'
import MarketView from '../views/MarketView.vue'
import PortfolioCashflowView from '../views/PortfolioCashflowView.vue'
import ReportView from '../views/ReportView.vue'
import SettingsView from '../views/SettingsView.vue'
import StockView from '../views/StockView.vue'
import StrategyView from '../views/StrategyView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      redirect: '/dashboard',
      children: [
        { path: 'dashboard', component: DashboardView, meta: { title: '总览' } },
        { path: 'portfolio/:symbol/cashflows', component: PortfolioCashflowView, meta: { title: '资金流水' } },
        { path: 'market', component: MarketView, meta: { title: '国内 ETF 行情' } },
        { path: 'stocks', component: StockView, meta: { title: '关注股票' } },
        { path: 'strategy', component: StrategyView, meta: { title: '策略与信号' } },
        { path: 'backtest', component: BacktestView, meta: { title: '操作看板' } },
        { path: 'report', component: ReportView, meta: { title: 'AI 日报' } },
        { path: 'settings', component: SettingsView, meta: { title: '系统设置' } },
      ],
    },
  ],
})
