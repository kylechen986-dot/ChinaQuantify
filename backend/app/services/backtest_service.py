def get_backtest_summary() -> dict:
    equity_curve = [
        {"date": "2026-06-24", "equity": 100000},
        {"date": "2026-06-25", "equity": 100820},
        {"date": "2026-06-26", "equity": 100310},
        {"date": "2026-06-29", "equity": 101120},
        {"date": "2026-06-30", "equity": 101860},
        {"date": "2026-07-01", "equity": 101430},
        {"date": "2026-07-02", "equity": 102240},
        {"date": "2026-07-03", "equity": 102680},
    ]
    return {
        "strategy_code": "ma_rsi_v1",
        "strategy_name": "均线 + RSI 趋势观察",
        "symbol": "510300",
        "name": "沪深300ETF",
        "metrics": {
            "total_return": 0.0268,
            "annual_return": 0.118,
            "max_drawdown": -0.014,
            "win_rate": 0.58,
            "trade_count": 12,
            "sharpe": 1.21,
        },
        "equity_curve": equity_curve,
    }
