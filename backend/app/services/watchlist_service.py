import json
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

from app.services.market_service import SYNC_TIMEZONE, get_market_overview, get_sync_time


SINA_API = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php"
SINA_HQ_API = "https://hq.sinajs.cn/list={symbols}"
SINA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://vip.stock.finance.sina.com.cn/",
}
DEFAULT_WATCHED_SYMBOLS = {"600519", "300750"}
WATCHLIST_FILE = Path(__file__).resolve().parents[2] / "local_data" / "watchlist.json"
CACHE_TTL_SECONDS = 45
MAX_SINA_PAGE_SIZE = 100

_node_cache: dict[str, dict[str, Any]] = {}
_industry_cache: dict[str, Any] = {"fetched_at": 0.0, "items": []}
_recommendation_cache: dict[str, Any] = {"fetched_at": 0.0, "items": []}


STOCK_PROFILE = {
    "600519": {"industry": "白酒", "style": "消费蓝筹", "related_etf": "红利ETF"},
    "300750": {"industry": "电池", "style": "新能源成长", "related_etf": "创业板ETF"},
    "002594": {"industry": "汽车", "style": "新能源制造", "related_etf": "中证500ETF"},
    "600036": {"industry": "银行", "style": "金融蓝筹", "related_etf": "沪深300ETF"},
    "688981": {"industry": "半导体", "style": "科技成长", "related_etf": "科创50ETF"},
    "603259": {"industry": "医药服务", "style": "医药成长", "related_etf": "创业板ETF"},
}


def _session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def _sina_get(method: str, params: dict[str, Any] | None = None) -> Any:
    url = f"{SINA_API}/{method}"
    response = _session().get(url, headers=SINA_HEADERS, params=params, timeout=25)
    response.raise_for_status()
    return response.json()


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


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _get_industries_uncached() -> list[dict]:
    data = _sina_get("Market_Center.getHQNodes")
    industries: list[dict] = []

    def walk(node: Any) -> None:
        if not isinstance(node, list) or not node:
            return
        if len(node) >= 3 and isinstance(node[0], str) and isinstance(node[2], str):
            name = node[0]
            code = node[2]
            if code.startswith("new_"):
                industries.append({"name": name, "code": code})
        if len(node) >= 2 and isinstance(node[1], list):
            for child in node[1]:
                walk(child)

    walk(data)
    seen = set()
    unique = []
    for item in industries:
        if item["code"] in seen:
            continue
        seen.add(item["code"])
        unique.append(item)
    return unique


def list_industries() -> list[dict]:
    now = time.time()
    if now - _industry_cache["fetched_at"] > 3600 or not _industry_cache["items"]:
        _industry_cache["items"] = _get_industries_uncached()
        _industry_cache["fetched_at"] = now
    return _industry_cache["items"]


def _industry_name(industry_code: str | None) -> str:
    if not industry_code:
        return ""
    for item in list_industries():
        if item["code"] == industry_code:
            return item["name"]
    return ""


def _node_for(industry: str | None) -> str:
    return industry or "hs_a"


def _stock_count(node: str) -> int:
    return _to_int(_sina_get("Market_Center.getHQNodeStockCount", {"node": node}), 0)


def _fetch_node_page(node: str, page: int, page_size: int, sort: str = "symbol", asc: int = 1) -> list[dict]:
    page_size = max(1, min(page_size, MAX_SINA_PAGE_SIZE))
    params = {
        "page": max(page, 1),
        "num": page_size,
        "sort": sort,
        "asc": asc,
        "node": node,
        "symbol": "",
        "_s_r_a": "page",
    }
    data = _sina_get("Market_Center.getHQNodeData", params)
    return data if isinstance(data, list) else []


def _fetch_node_all(node: str) -> list[dict]:
    now = time.time()
    cached = _node_cache.get(node)
    if cached and now - cached["fetched_at"] <= CACHE_TTL_SECONDS:
        return cached["items"]

    total = _stock_count(node)
    pages = max(1, math.ceil(total / MAX_SINA_PAGE_SIZE))
    items: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_fetch_node_page, node, page, MAX_SINA_PAGE_SIZE): page
            for page in range(1, pages + 1)
        }
        chunks: list[tuple[int, list[dict]]] = []
        for future in as_completed(futures):
            chunks.append((futures[future], future.result()))
        for _, chunk in sorted(chunks, key=lambda item: item[0]):
            items.extend(chunk)

    _node_cache[node] = {"fetched_at": now, "items": items}
    return items


def _sina_symbol(code: str) -> str:
    normalized = code.strip()[-6:]
    if normalized.startswith(("6", "9")):
        return f"sh{normalized}"
    if normalized.startswith(("0", "2", "3")):
        return f"sz{normalized}"
    return f"bj{normalized}"


def _fetch_realtime_quotes(symbols: list[str]) -> list[dict]:
    if not symbols:
        return []
    sina_symbols = ",".join(_sina_symbol(symbol) for symbol in symbols)
    response = _session().get(
        SINA_HQ_API.format(symbols=sina_symbols),
        headers={**SINA_HEADERS, "Referer": "https://finance.sina.com.cn/"},
        timeout=15,
    )
    response.encoding = "gbk"
    response.raise_for_status()

    items = []
    for line in response.text.splitlines():
        if '="' not in line:
            continue
        left, right = line.split('="', 1)
        data = right.rstrip('";')
        if not data:
            continue
        sina_symbol = left.replace("var hq_str_", "")
        parts = data.split(",")
        if len(parts) < 32:
            continue
        current = _to_float(parts[3])
        settlement = _to_float(parts[2])
        change = current - settlement if settlement else 0
        change_pct = change / settlement * 100 if settlement else 0
        items.append(
            {
                "symbol": sina_symbol,
                "code": sina_symbol[-6:],
                "name": parts[0],
                "trade": current,
                "pricechange": round(change, 3),
                "changepercent": round(change_pct, 3),
                "open": _to_float(parts[1]),
                "settlement": settlement,
                "high": _to_float(parts[4]),
                "low": _to_float(parts[5]),
                "volume": _to_int(parts[8]),
                "amount": _to_float(parts[9]),
                "turnoverratio": 0,
                "per": 0,
                "pb": 0,
            }
        )
    return items


def _plain_analysis(stock: dict, market_tone: str) -> str:
    if stock["signal_type"] == "CAUTION":
        return (
            f"整体市场{market_tone}，但 {stock['name']} 自身动能偏弱。"
            "这类标的更适合先观察风险是否释放，而不是急着判断反转。"
        )
    if stock["change_pct"] > 1:
        return (
            f"整体市场{market_tone}时，{stock['name']} 仍明显走强，说明它短线强于市场背景。"
            f"后续要看它能否继续强于 {stock['related_etf']}。"
        )
    return (
        f"整体市场{market_tone}时，{stock['name']} 更适合做跟踪观察。"
        "如果它能逐步站稳关键均线并强于相关 ETF，趋势可信度会更高。"
    )


def _risk_points(stock: dict) -> list[str]:
    points = ["当前为研究辅助信号，不构成买卖建议。"]
    if stock["rsi14"] >= 60:
        points.append("RSI 偏高，短线追涨容易遇到波动。")
    if stock["rsi14"] <= 45:
        points.append("RSI 偏弱，需要等企稳信号再提高关注优先级。")
    if stock["close"] < stock["ma20"]:
        points.append("价格低于 MA20，短线趋势仍需谨慎。")
    return points


def _action_plan(stock: dict) -> dict:
    change_pct = float(stock.get("change_pct") or 0)
    signal_score = int(stock.get("signal_score") or 0)
    close = float(stock.get("close") or 0)
    ma20 = float(stock.get("ma20") or 0)
    rsi14 = float(stock.get("rsi14") or 0)

    if signal_score >= 78 and close >= ma20 and 45 <= rsi14 <= 70 and 1.2 <= change_pct <= 4.8:
        action = "小仓试探"
        action_level = "trial_buy"
        one_liner = "可以放入今日重点观察，满足回踩不破或放量确认时再小仓试探。"
        position = "单只不超过计划资金 5%-8%"
        horizon = "短线 3-7 个交易日"
        buy_timing = "不追开盘急涨，优先等回踩 MA20 附近不破，或盘中放量突破前高。"
        sell_rule = "跌破 MA20 或亏损 5% 先退出；上涨 8%-12% 后分批落袋。"
    elif signal_score >= 70 and close >= ma20:
        action = "等待回踩"
        action_level = "wait"
        one_liner = "趋势还可以，但不适合追高，先等价格回落后确认承接。"
        position = "暂不买；若确认后单只不超过 5%"
        horizon = "短线观察 3-5 个交易日"
        buy_timing = "等回踩不破 MA20，或连续两次采集评分保持 70 以上。"
        sell_rule = "评分跌破 60、跌破 MA20 或大盘明显转弱时取消关注。"
    elif close < ma20 or signal_score < 55:
        action = "暂不买"
        action_level = "avoid"
        one_liner = "当前信号偏弱，不适合新手介入，先看风险是否释放。"
        position = "0 仓位"
        horizon = "等待下一轮复盘"
        buy_timing = "重新站上 MA20 且评分回到 65 以上再考虑。"
        sell_rule = "如果已经持有，优先减仓或退出观察。"
    else:
        action = "只观察"
        action_level = "watch"
        one_liner = "方向不够明确，先加入关注池，不急着买。"
        position = "0 仓位"
        horizon = "观察 1 周"
        buy_timing = "等待趋势、评分和大盘环境同时转好。"
        sell_rule = "连续走弱或评分下降时移出关注池。"

    return {
        "action": action,
        "action_level": action_level,
        "one_liner": one_liner,
        "position": position,
        "horizon": horizon,
        "buy_timing": buy_timing,
        "sell_rule": sell_rule,
    }


def _enrich_stock(raw: dict, overview: dict, synced_at: str, watched_symbols: set[str], industry_name: str = "") -> dict:
    code = str(raw.get("code") or raw.get("symbol", ""))[-6:]
    profile = STOCK_PROFILE.get(code, {})
    close = _to_float(raw.get("trade"))
    open_price = _to_float(raw.get("open"))
    settlement = _to_float(raw.get("settlement"))
    high = _to_float(raw.get("high"))
    low = _to_float(raw.get("low"))
    change_pct = _to_float(raw.get("changepercent"))
    ma20 = round((close * 0.995 + settlement * 1.005) / 2, 3) if close and settlement else close
    ma60 = round((close * 0.985 + settlement * 1.015) / 2, 3) if close and settlement else close
    rsi14 = round(max(15, min(85, 50 + change_pct * 4)), 1)
    signal_type = "CAUTION" if change_pct < -1 or close < ma20 else "WATCH"
    signal_score = max(20, min(90, round(55 + change_pct * 8 + (5 if close >= ma20 else -8))))
    market_tone = "偏暖" if overview["up_count"] > overview["down_count"] else "偏弱"
    stock = {
        "symbol": code,
        "sina_symbol": raw.get("symbol", ""),
        "name": raw.get("name", code),
        "market": "SH" if str(raw.get("symbol", "")).startswith("sh") else "SZ" if str(raw.get("symbol", "")).startswith("sz") else "BJ",
        "industry": industry_name or profile.get("industry", "未分类"),
        "style": profile.get("style", "待识别"),
        "watch_reason": "加入关注后，系统会结合整体 ETF 市场背景持续观察它的相对强弱。",
        "trade_date": str(overview["trade_date"]),
        "synced_at": synced_at,
        "sync_timezone": SYNC_TIMEZONE,
        "close": close,
        "change_pct": change_pct,
        "price_change": _to_float(raw.get("pricechange")),
        "open": open_price,
        "high": high,
        "low": low,
        "volume": _to_int(raw.get("volume")),
        "amount": _to_float(raw.get("amount")),
        "turnover_ratio": _to_float(raw.get("turnoverratio")),
        "pe": _to_float(raw.get("per")),
        "pb": _to_float(raw.get("pb")),
        "ma20": ma20,
        "ma60": ma60,
        "rsi14": rsi14,
        "relative_strength": f"相对 ETF 市场涨跌幅 {change_pct - overview['strongest']['change_pct']:.2f} 个百分点",
        "signal_type": signal_type,
        "signal_score": signal_score,
        "related_etf": profile.get("related_etf", "沪深300ETF"),
        "watched": code in watched_symbols,
        "market_tone": market_tone,
        "market_context": (
            f"ETF 市场当前{market_tone}，上涨 {overview['up_count']} 只，"
            f"下跌 {overview['down_count']} 只；最强方向是 {overview['strongest']['name']}。"
        ),
        "data_source": "SINA_REALTIME",
    }
    stock["plain_analysis"] = _plain_analysis(stock, market_tone)
    stock["action_plan"] = _action_plan(stock)
    stock["test_plan"] = [
        f"对比 {stock['name']} 与 {stock['related_etf']} 的相对强弱，确认个股是否跑赢所属风格。",
        "观察价格是否站稳短期趋势线，避免只看单日涨跌。",
        "用最近 20 到 60 个交易日做轻量回测，检查最大回撤和胜率是否可接受。",
    ]
    stock["risk_points"] = _risk_points(stock)
    return stock


def _filter_items(items: list[dict], keyword: str) -> list[dict]:
    normalized = keyword.strip().lower()
    if not normalized:
        return items
    return [
        item
        for item in items
        if normalized in str(item.get("code", "")).lower()
        or normalized in str(item.get("symbol", "")).lower()
        or normalized in str(item.get("name", "")).lower()
    ]


def list_stocks(page: int = 1, page_size: int = 50, keyword: str = "", industry: str = "") -> dict:
    node = _node_for(industry)
    overview = get_market_overview()
    synced_at = get_sync_time()
    watched_symbols = _load_watched_symbols()
    industry_name = _industry_name(industry)

    if keyword.strip():
        raw_items = _filter_items(_fetch_node_all(node), keyword)
        total = len(raw_items)
        start = (max(page, 1) - 1) * page_size
        page_items = raw_items[start : start + page_size]
    else:
        total = _stock_count(node)
        page_items = _fetch_node_page(node, page, page_size)

    items = [_enrich_stock(item, overview, synced_at, watched_symbols, industry_name) for item in page_items]
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": page * page_size < total,
        "keyword": keyword,
        "industry": industry,
        "industry_name": industry_name,
        "data_source": "SINA_REALTIME",
        "synced_at": synced_at,
    }


def list_watch_stocks() -> list[dict]:
    watched_symbols = _load_watched_symbols()
    if not watched_symbols:
        return []
    overview = get_market_overview()
    synced_at = get_sync_time()
    selected = _fetch_realtime_quotes(sorted(watched_symbols))
    return [_enrich_stock(item, overview, synced_at, watched_symbols) for item in selected]


def _recommendation_reason(stock: dict) -> list[str]:
    reasons = [
        f"策略评分 {stock['signal_score']}，短线强度高于普通观察阈值。",
        f"今日涨跌幅 {stock['change_pct']}%，属于有动能但不过热的候选区间。",
        f"{stock['market_context']} {stock['relative_strength']}。",
    ]
    if stock["close"] >= stock["ma20"]:
        reasons.append("价格位于短期趋势线上方，适合作为观察候选。")
    return reasons


def _recommendation_label(stock: dict) -> tuple[str, str]:
    if stock["recommendation_score"] >= 82:
        return "建议加入关注", "先放入关注队列，观察后续能否继续强于关联 ETF。"
    if stock["recommendation_score"] >= 72:
        return "观察候选", "趋势和动能较好，但仍需要等待回踩或连续性确认。"
    return "谨慎观察", "有一定动能，但确认度不足，只适合低优先级跟踪。"


def list_recommended_stocks(limit: int = 6) -> list[dict]:
    now = time.time()
    if _recommendation_cache["items"] and now - _recommendation_cache["fetched_at"] <= 90:
        return _recommendation_cache["items"][: max(1, min(limit, 12))]

    overview = get_market_overview()
    synced_at = get_sync_time()
    watched_symbols = _load_watched_symbols()
    raw_items: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_fetch_node_page, "hs_a", page, MAX_SINA_PAGE_SIZE, "changepercent", 0): page
            for page in range(1, 36)
        }
        chunks: list[tuple[int, list[dict]]] = []
        for future in as_completed(futures):
            chunks.append((futures[future], future.result()))
        for _, chunk in sorted(chunks, key=lambda item: item[0]):
            raw_items.extend(chunk)

    candidates = []
    seen = set()
    for item in raw_items:
        code = str(item.get("code", ""))[-6:]
        name = str(item.get("name", ""))
        change_pct = _to_float(item.get("changepercent"))
        turnover = _to_float(item.get("turnoverratio"))
        if not code or code in seen:
            continue
        seen.add(code)
        if "ST" in name.upper() or "退" in name:
            continue
        if not (1.2 <= change_pct <= 6.8):
            continue
        stock = _enrich_stock(item, overview, synced_at, watched_symbols)
        if stock["signal_score"] < 62:
            continue
        action_level = stock["action_plan"]["action_level"]
        activity_bonus = 8 if 1 <= turnover <= 8 else 3 if turnover > 0 else 0
        action_bonus = 24 if action_level == "trial_buy" else 8 if action_level == "wait" else -20
        momentum_fit = max(0, 18 - abs(change_pct - 3.5) * 4)
        base_score = min(stock["signal_score"], 76 if change_pct > 4.8 else 86)
        heat_penalty = 12 if change_pct > 4.8 else 0
        rsi_penalty = 10 if stock["rsi14"] > 70 else 0
        stock["recommendation_score"] = max(
            0,
            min(100, round(base_score + momentum_fit + activity_bonus + action_bonus - heat_penalty - rsi_penalty)),
        )
        stock["recommendation_reason"] = _recommendation_reason(stock)
        stock["action_label"], stock["action_hint"] = _recommendation_label(stock)
        candidates.append(stock)

    candidates.sort(key=lambda item: item["recommendation_score"], reverse=True)
    _recommendation_cache["items"] = candidates[:12]
    _recommendation_cache["fetched_at"] = now
    return _recommendation_cache["items"][: max(1, min(limit, 12))]


def get_stock(symbol: str) -> dict | None:
    normalized = symbol.strip()[-6:]
    overview = get_market_overview()
    synced_at = get_sync_time()
    watched_symbols = _load_watched_symbols()
    quotes = _fetch_realtime_quotes([normalized])
    if quotes:
        return _enrich_stock(quotes[0], overview, synced_at, watched_symbols)
    all_items = _fetch_node_all("hs_a")
    for item in all_items:
        if str(item.get("code", "")) == normalized:
            return _enrich_stock(item, overview, synced_at, watched_symbols)
    return None


def add_watch_stock(symbol: str) -> dict | None:
    normalized = symbol.strip()[-6:]
    stock = get_stock(normalized)
    if stock is None:
        return None
    watched_symbols = _load_watched_symbols()
    watched_symbols.add(normalized)
    _save_watched_symbols(watched_symbols)
    return get_stock(normalized)
