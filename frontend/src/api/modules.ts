import { getData, postData } from './http'
import type {
  AiReport,
  BacktestSummary,
  IndicatorSnapshot,
  MarketOverview,
  MonitorDashboard,
  MonitorSnapshot,
  StockIndustry,
  StockPage,
  StrategySignal,
  WatchStock,
  WeeklyReview,
} from '../types/api'

export const api = {
  health: () => getData<Record<string, string>>('/system/health'),
  marketOverview: () => getData<MarketOverview>('/market/overview'),
  indicators: () => getData<IndicatorSnapshot[]>('/indicators/latest'),
  signals: () => getData<StrategySignal[]>('/strategies/signals'),
  backtestSummary: () => getData<BacktestSummary>('/backtests/summary'),
  reports: () => getData<AiReport[]>('/reports'),
  reportDetail: (id: number) => getData<AiReport>(`/reports/${id}`),
  latestReport: () => getData<AiReport>('/reports/latest'),
  stocks: (params?: { page?: number; page_size?: number; keyword?: string; industry?: string }) => getData<StockPage>('/stocks', params),
  industries: () => getData<StockIndustry[]>('/stocks/industries'),
  stockDetail: (symbol: string) => getData<WatchStock>(`/stocks/${symbol}`),
  addWatchStock: (symbol: string) => postData<WatchStock>(`/stocks/watchlist/${symbol}`),
  watchStocks: () => getData<WatchStock[]>('/stocks/watchlist'),
  stockRecommendations: (limit = 6) => getData<WatchStock[]>('/stocks/recommendations', { limit }),
  monitorDashboard: () => getData<MonitorDashboard>('/monitor/dashboard'),
  collectMonitorSnapshot: () => postData<MonitorSnapshot>('/monitor/collect'),
  buildWeeklyReview: () => postData<WeeklyReview>('/monitor/weekly-review'),
}
