from datetime import date


SYMBOLS = [
    {"id": 1, "symbol": "510300", "name": "沪深300ETF", "market": "SH", "category": "ETF", "enabled": True},
    {"id": 2, "symbol": "159915", "name": "创业板ETF", "market": "SZ", "category": "ETF", "enabled": True},
    {"id": 3, "symbol": "588000", "name": "科创50ETF", "market": "SH", "category": "ETF", "enabled": True},
    {"id": 4, "symbol": "510500", "name": "中证500ETF", "market": "SH", "category": "ETF", "enabled": True},
    {"id": 5, "symbol": "515180", "name": "红利ETF", "market": "SH", "category": "ETF", "enabled": True},
]


def get_symbols() -> list[dict]:
    return SYMBOLS


def get_indicator_snapshots() -> list[dict]:
    return [
        {
            "symbol": item["symbol"],
            "name": item["name"],
            "trade_date": str(date.today()),
            "close": round(3.2 + idx * 0.37, 3),
            "change_pct": [0.42, -0.86, 1.12, 0.18, -0.24][idx],
            "ma20": round(3.1 + idx * 0.35, 3),
            "ma60": round(3.0 + idx * 0.33, 3),
            "rsi14": [56.8, 43.2, 61.5, 51.7, 48.9][idx],
            "macd_hist": [0.018, -0.012, 0.026, 0.004, -0.006][idx],
            "trend_state": ["UP", "DOWN", "STRONG_UP", "SIDEWAYS", "SIDEWAYS"][idx],
        }
        for idx, item in enumerate(SYMBOLS)
    ]


def get_market_overview() -> dict:
    snapshots = get_indicator_snapshots()
    up_count = sum(1 for item in snapshots if item["change_pct"] > 0)
    down_count = len(snapshots) - up_count
    return {
        "trade_date": str(date.today()),
        "symbol_count": len(snapshots),
        "up_count": up_count,
        "down_count": down_count,
        "strongest": max(snapshots, key=lambda item: item["change_pct"]),
        "weakest": min(snapshots, key=lambda item: item["change_pct"]),
        "snapshots": snapshots,
    }
