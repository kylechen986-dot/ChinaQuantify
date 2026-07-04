import { getData, postData } from './http'
import type { AiReport, BacktestSummary, IndicatorSnapshot, MarketOverview, StrategySignal, WatchStock } from '../types/api'

export const api = {
  health: () => getData<Record<string, string>>('/system/health'),
  marketOverview: () => getData<MarketOverview>('/market/overview'),
  indicators: () => getData<IndicatorSnapshot[]>('/indicators/latest'),
  signals: () => getData<StrategySignal[]>('/strategies/signals'),
  backtestSummary: () => getData<BacktestSummary>('/backtests/summary'),
  reports: () => getData<AiReport[]>('/reports'),
  reportDetail: (id: number) => getData<AiReport>(`/reports/${id}`),
  latestReport: () => getData<AiReport>('/reports/latest'),
  stocks: () => getData<WatchStock[]>('/stocks'),
  stockDetail: (symbol: string) => getData<WatchStock>(`/stocks/${symbol}`),
  addWatchStock: (symbol: string) => postData<WatchStock>(`/stocks/watchlist/${symbol}`),
  watchStocks: () => getData<WatchStock[]>('/stocks/watchlist'),
}
