import { getData } from './http'
import type { AiReport, BacktestSummary, IndicatorSnapshot, MarketOverview, StrategySignal } from '../types/api'

export const api = {
  health: () => getData<Record<string, string>>('/system/health'),
  marketOverview: () => getData<MarketOverview>('/market/overview'),
  indicators: () => getData<IndicatorSnapshot[]>('/indicators/latest'),
  signals: () => getData<StrategySignal[]>('/strategies/signals'),
  backtestSummary: () => getData<BacktestSummary>('/backtests/summary'),
  latestReport: () => getData<AiReport>('/reports/latest'),
}
