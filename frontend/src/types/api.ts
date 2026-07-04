export interface ApiResponse<T> {
  success: boolean
  data: T
  message: string
  request_id: string
}

export interface IndicatorSnapshot {
  symbol: string
  name: string
  trade_date: string
  close: number
  change_pct: number
  ma20: number
  ma60: number
  rsi14: number
  macd_hist: number
  trend_state: string
}

export interface MarketOverview {
  trade_date: string
  symbol_count: number
  up_count: number
  down_count: number
  strongest: IndicatorSnapshot
  weakest: IndicatorSnapshot
  snapshots: IndicatorSnapshot[]
}

export interface StrategySignal {
  symbol: string
  name: string
  strategy_code: string
  strategy_name: string
  trade_date: string
  signal_type: string
  signal_score: number
  reason: string
}

export interface BacktestSummary {
  strategy_code: string
  strategy_name: string
  symbol: string
  name: string
  metrics: {
    total_return: number
    annual_return: number
    max_drawdown: number
    win_rate: number
    trade_count: number
    sharpe: number
  }
  equity_curve: Array<{ date: string; equity: number }>
}

export interface AiReport {
  id: number
  report_date: string
  report_type: string
  title: string
  summary: string
  content: string
  model_provider: string
  model_name: string
}
