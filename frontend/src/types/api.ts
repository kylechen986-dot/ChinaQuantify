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
  synced_at: string
  sync_timezone: string
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
  synced_at: string
  sync_timezone: string
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
  market_tone?: string
  llm_usage?: Record<string, unknown>
  llm_error?: string
}

export interface WatchStock {
  symbol: string
  sina_symbol: string
  name: string
  market: string
  industry: string
  style: string
  watch_reason: string
  trade_date: string
  synced_at: string
  sync_timezone: string
  close: number
  change_pct: number
  price_change: number
  open: number
  high: number
  low: number
  volume: number
  amount: number
  turnover_ratio: number
  pe: number
  pb: number
  ma20: number
  ma60: number
  rsi14: number
  relative_strength: string
  signal_type: string
  signal_score: number
  related_etf: string
  watched: boolean
  market_tone: string
  market_context: string
  plain_analysis: string
  action_plan: {
    action: string
    action_level: 'trial_buy' | 'wait' | 'avoid' | 'watch'
    one_liner: string
    position: string
    horizon: string
    buy_timing: string
    sell_rule: string
  }
  test_plan: string[]
  risk_points: string[]
  data_source: string
  recommendation_score?: number
  recommendation_reason?: string[]
  action_label?: string
  action_hint?: string
}

export interface StockPage {
  items: WatchStock[]
  page: number
  page_size: number
  total: number
  has_more: boolean
  keyword: string
  industry: string
  industry_name: string
  data_source: string
  synced_at: string
}

export interface StockIndustry {
  name: string
  code: string
}

export interface MonitorTechnicalCheck {
  label: string
  value: string
  plain: string
  score: number
}

export interface MonitorStock extends WatchStock {
  monitor_action: string
  monitor_tone: 'positive' | 'neutral' | 'risk'
  monitor_explanation: string
  technical_checks: MonitorTechnicalCheck[]
}

export interface MonitorSnapshot {
  id: string
  collected_at: string
  trade_date: string
  trigger: string
  market_open: boolean
  collect_rule: string
  data_source: string
  sync_timezone: string
  market_overview: MarketOverview
  watched_count: number
  watched_stocks: MonitorStock[]
  summary: {
    headline: string
    positive_count: number
    neutral_count: number
    risk_count: number
    market_brief: string
  }
}

export interface WeeklyReview {
  id: string
  generated_at: string
  period_start: string
  period_end: string
  trigger: string
  snapshot_count: number
  title: string
  conclusion: string
  market_summary: string
  watch_reviews: Array<{
    symbol: string
    name: string
    action: string
    action_plan: WatchStock['action_plan']
    plain_summary: string
    change_pct: number
    signal_score: number
    technical_checks: MonitorTechnicalCheck[]
    risk_points: string[]
  }>
  indicator_guide: string[]
  next_actions: string[]
}

export interface MonitorDashboard {
  scheduler: {
    enabled: boolean
    timezone: string
    market_status: string
    collect_interval_minutes: number
    collect_window: string
    weekly_review_rule: string
    next_collect_at: string
    next_weekly_review_at: string
  }
  latest_snapshot: MonitorSnapshot | null
  latest_weekly_review: WeeklyReview | null
  recent_snapshots: Array<{
    id: string
    collected_at: string
    trade_date: string
    watched_count: number
    headline: string
    market_open: boolean
    trigger: string
  }>
  recommendations: WatchStock[]
}

export interface PortfolioPosition {
  symbol: string
  name: string
  quantity: number
  avg_cost_price: number
  current_price: number
  market_value: number
  cost_value: number
  today_profit: number
  today_profit_pct: number
  holding_profit: number
  holding_profit_pct: number
  message: string
  lots: Array<{
    id: string
    buy_date: string
    quantity: number
    cost_price: number
    current_price: number
    cost_value: number
    market_value: number
    profit: number
    profit_pct: number
    today_profit: number
    is_profit: boolean
    message: string
  }>
  action_hint: string
  action_plan: WatchStock['action_plan']
  data_source: string
  synced_at: string
}

export interface PortfolioOverview {
  synced_at: string
  sync_timezone: string
  currency: string
  is_sample: boolean
  headline: string
  tone: 'profit' | 'loss' | 'flat'
  cash_balance: number
  market_value: number
  total_assets: number
  today_profit: number
  today_profit_pct: number
  holding_profit: number
  holding_profit_pct: number
  position_count: number
  positions: PortfolioPosition[]
}

export interface PortfolioCashflow {
  id: string
  date: string
  type: string
  type_text: string
  quantity: number
  price: number
  amount: number
  direction: 'in' | 'out'
  note: string
  related_lot_id: string
}

export interface PortfolioCashflowDetail {
  symbol: string
  name: string
  synced_at: string
  sync_timezone: string
  current_price: number
  quantity: number
  market_value: number
  cost_value: number
  holding_profit: number
  holding_profit_pct: number
  today_profit: number
  total_inflow: number
  total_outflow: number
  net_cashflow: number
  flow_profit: number
  flows: PortfolioCashflow[]
}
