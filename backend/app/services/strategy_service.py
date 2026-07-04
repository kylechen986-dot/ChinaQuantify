from datetime import date


def get_strategy_signals() -> list[dict]:
    return [
        {
            "symbol": "510300",
            "name": "沪深300ETF",
            "strategy_code": "ma_rsi_v1",
            "strategy_name": "均线 + RSI 趋势观察",
            "trade_date": str(date.today()),
            "signal_type": "WATCH",
            "signal_score": 72,
            "reason": "价格站上 MA20，RSI 位于中性偏强区间，适合继续观察趋势延续。",
        },
        {
            "symbol": "159915",
            "name": "创业板ETF",
            "strategy_code": "ma_rsi_v1",
            "strategy_name": "均线 + RSI 趋势观察",
            "trade_date": str(date.today()),
            "signal_type": "CAUTION",
            "signal_score": 38,
            "reason": "价格低于 MA20，MACD 柱为负，短线动能偏弱。",
        },
        {
            "symbol": "588000",
            "name": "科创50ETF",
            "strategy_code": "ma_rsi_v1",
            "strategy_name": "均线 + RSI 趋势观察",
            "trade_date": str(date.today()),
            "signal_type": "WATCH",
            "signal_score": 78,
            "reason": "价格位于 MA20 和 MA60 上方，趋势结构较好，但仍需留意波动。",
        },
    ]
