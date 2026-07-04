import json
from pathlib import Path

from app.services.market_service import SYNC_TIMEZONE, get_market_overview, get_sync_time


STOCK_UNIVERSE = [
    {
        "symbol": "600519",
        "name": "贵州茅台",
        "market": "SH",
        "industry": "白酒",
        "style": "消费蓝筹",
        "watch_reason": "偏大盘价值和消费防御方向，适合观察市场风险偏好偏弱时的承接能力。",
        "close": 1488.6,
        "change_pct": -0.32,
        "ma20": 1502.4,
        "ma60": 1476.8,
        "rsi14": 47.6,
        "relative_strength": "弱于科创50ETF，接近红利ETF",
        "signal_type": "WATCH",
        "signal_score": 58,
        "related_etf": "红利ETF",
    },
    {
        "symbol": "300750",
        "name": "宁德时代",
        "market": "SZ",
        "industry": "电池",
        "style": "新能源成长",
        "watch_reason": "偏成长制造方向，适合观察科创成长风格走强时，个股是否同步增强。",
        "close": 221.35,
        "change_pct": 1.46,
        "ma20": 216.8,
        "ma60": 209.4,
        "rsi14": 59.3,
        "relative_strength": "强于沪深300ETF，略强于创业板ETF",
        "signal_type": "WATCH",
        "signal_score": 74,
        "related_etf": "创业板ETF",
    },
    {
        "symbol": "002594",
        "name": "比亚迪",
        "market": "SZ",
        "industry": "汽车",
        "style": "新能源制造",
        "watch_reason": "同时受成长风格、汽车产业链和消费预期影响，适合观察产业趋势是否扩散。",
        "close": 258.2,
        "change_pct": 0.68,
        "ma20": 253.7,
        "ma60": 247.9,
        "rsi14": 55.8,
        "relative_strength": "强于中证500ETF，接近科创50ETF",
        "signal_type": "WATCH",
        "signal_score": 69,
        "related_etf": "中证500ETF",
    },
    {
        "symbol": "600036",
        "name": "招商银行",
        "market": "SH",
        "industry": "银行",
        "style": "金融蓝筹",
        "watch_reason": "偏金融权重方向，适合观察大盘企稳时金融板块是否参与修复。",
        "close": 35.18,
        "change_pct": 0.21,
        "ma20": 35.0,
        "ma60": 34.42,
        "rsi14": 52.1,
        "relative_strength": "接近沪深300ETF",
        "signal_type": "WATCH",
        "signal_score": 63,
        "related_etf": "沪深300ETF",
    },
    {
        "symbol": "688981",
        "name": "中芯国际",
        "market": "SH",
        "industry": "半导体",
        "style": "科技成长",
        "watch_reason": "半导体方向弹性高，适合观察科创50ETF 走强时是否形成板块共振。",
        "close": 92.46,
        "change_pct": 2.08,
        "ma20": 88.2,
        "ma60": 84.6,
        "rsi14": 64.7,
        "relative_strength": "强于科创50ETF",
        "signal_type": "WATCH",
        "signal_score": 82,
        "related_etf": "科创50ETF",
    },
    {
        "symbol": "603259",
        "name": "药明康德",
        "market": "SH",
        "industry": "医药服务",
        "style": "医药成长",
        "watch_reason": "医药成长方向波动较大，适合观察弱势行业是否出现修复。",
        "close": 42.76,
        "change_pct": -1.18,
        "ma20": 44.1,
        "ma60": 45.3,
        "rsi14": 39.6,
        "relative_strength": "弱于创业板ETF",
        "signal_type": "CAUTION",
        "signal_score": 35,
        "related_etf": "创业板ETF",
    },
]

DEFAULT_WATCHED_SYMBOLS = {"600519", "300750"}
WATCHLIST_FILE = Path(__file__).resolve().parents[2] / "local_data" / "watchlist.json"


def _load_watched_symbols() -> set[str]:
    if not WATCHLIST_FILE.exists():
        return set(DEFAULT_WATCHED_SYMBOLS)

    try:
        data = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set(DEFAULT_WATCHED_SYMBOLS)

    symbols = data.get("symbols", [])
    return {str(symbol) for symbol in symbols if symbol}


def _save_watched_symbols(symbols: set[str]) -> None:
    WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATCHLIST_FILE.write_text(
        json.dumps({"symbols": sorted(symbols)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _market_tone(overview: dict) -> str:
    if overview["up_count"] > overview["down_count"]:
        return "偏暖"
    if overview["up_count"] < overview["down_count"]:
        return "偏弱"
    return "震荡"


def _stock_explanation(stock: dict, market_tone: str) -> str:
    if stock["signal_type"] == "CAUTION":
        return (
            f"整体市场{market_tone}，但 {stock['name']} 自身动能偏弱。"
            "这类标的更适合先观察风险是否释放，而不是急着判断反转。"
        )
    if stock["change_pct"] > 1:
        return (
            f"整体市场{market_tone}时，{stock['name']} 仍明显走强，"
            f"说明它短线强于市场背景。后续要看它能否继续强于 {stock['related_etf']}。"
        )
    return (
        f"整体市场{market_tone}时，{stock['name']} 更适合做跟踪观察。"
        "如果它能逐步站稳均线并强于相关 ETF，趋势可信度会更高。"
    )


def _test_plan(stock: dict) -> list[str]:
    return [
        f"对比 {stock['name']} 与 {stock['related_etf']} 的相对强弱，确认个股是否跑赢所属风格。",
        "观察价格是否站稳 MA20 和 MA60，避免只看单日涨跌。",
        "用最近 20 到 60 个交易日做轻量回测，检查最大回撤和胜率是否可接受。",
    ]


def _risk_points(stock: dict) -> list[str]:
    points = ["当前为研究辅助信号，不构成买卖建议。"]
    if stock["rsi14"] >= 60:
        points.append("RSI 偏高，短线追涨容易遇到波动。")
    if stock["rsi14"] <= 45:
        points.append("RSI 偏弱，需要等企稳信号再提高关注优先级。")
    if stock["close"] < stock["ma20"]:
        points.append("价格低于 MA20，短线趋势仍需谨慎。")
    return points


def _enrich_stock(stock: dict, overview: dict, synced_at: str, watched_symbols: set[str]) -> dict:
    market_tone = _market_tone(overview)
    return {
        **stock,
        "watched": stock["symbol"] in watched_symbols,
        "trade_date": overview["trade_date"],
        "synced_at": synced_at,
        "sync_timezone": SYNC_TIMEZONE,
        "market_tone": market_tone,
        "market_context": (
            f"ETF 市场当前{market_tone}，上涨 {overview['up_count']} 只，"
            f"下跌 {overview['down_count']} 只；最强方向是 {overview['strongest']['name']}。"
        ),
        "plain_analysis": _stock_explanation(stock, market_tone),
        "test_plan": _test_plan(stock),
        "risk_points": _risk_points(stock),
    }


def list_stocks() -> list[dict]:
    overview = get_market_overview()
    synced_at = get_sync_time()
    watched_symbols = _load_watched_symbols()
    return [_enrich_stock(stock, overview, synced_at, watched_symbols) for stock in STOCK_UNIVERSE]


def list_watch_stocks() -> list[dict]:
    return [stock for stock in list_stocks() if stock["watched"]]


def get_stock(symbol: str) -> dict | None:
    normalized = symbol.strip()
    for stock in list_stocks():
        if stock["symbol"] == normalized:
            return stock
    return None


def add_watch_stock(symbol: str) -> dict | None:
    normalized = symbol.strip()
    exists = any(stock["symbol"] == normalized for stock in STOCK_UNIVERSE)
    if not exists:
        return None
    watched_symbols = _load_watched_symbols()
    watched_symbols.add(normalized)
    _save_watched_symbols(watched_symbols)
    return get_stock(normalized)
