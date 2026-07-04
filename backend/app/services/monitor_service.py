import json
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.market_service import SYNC_TIMEZONE, get_market_overview
from app.services.watchlist_service import list_recommended_stocks, list_watch_stocks


LOCAL_DATA_DIR = Path(__file__).resolve().parents[2] / "local_data" / "monitoring"
LATEST_SNAPSHOT_FILE = LOCAL_DATA_DIR / "latest_snapshot.json"
SNAPSHOT_INDEX_FILE = LOCAL_DATA_DIR / "snapshots.json"
LATEST_WEEKLY_REVIEW_FILE = LOCAL_DATA_DIR / "weekly_review_latest.json"
MAX_SNAPSHOT_HISTORY = 240
COLLECT_INTERVAL_MINUTES = 15
WEEKLY_REVIEW_DAY = "周五"
WEEKLY_REVIEW_TIME = "16:10:00"

_scheduler: BackgroundScheduler | None = None


def _now() -> datetime:
    return datetime.now(ZoneInfo(SYNC_TIMEZONE))


def _format_dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_market_open(moment: datetime | None = None) -> bool:
    current = moment or _now()
    if current.weekday() >= 5:
        return False
    current_time = current.time()
    return time(9, 30) <= current_time <= time(11, 30) or time(13, 0) <= current_time <= time(15, 0)


def _next_market_open(moment: datetime | None = None) -> datetime:
    current = moment or _now()
    current_time = current.time()
    if current.weekday() < 5:
        if current_time < time(9, 30):
            return current.replace(hour=9, minute=30, second=0, microsecond=0)
        if time(11, 30) < current_time < time(13, 0):
            return current.replace(hour=13, minute=0, second=0, microsecond=0)
        if current_time < time(15, 0):
            return current + timedelta(minutes=COLLECT_INTERVAL_MINUTES)

    next_day = current + timedelta(days=1)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    return next_day.replace(hour=9, minute=30, second=0, microsecond=0)


def _next_weekly_review(moment: datetime | None = None) -> datetime:
    current = moment or _now()
    target = current.replace(hour=16, minute=10, second=0, microsecond=0)
    days_until_friday = (4 - current.weekday()) % 7
    target = target + timedelta(days=days_until_friday)
    if target <= current:
        target += timedelta(days=7)
    return target


def _technical_summary(stock: dict) -> dict:
    close = float(stock.get("close") or 0)
    ma20 = float(stock.get("ma20") or 0)
    ma60 = float(stock.get("ma60") or 0)
    rsi14 = float(stock.get("rsi14") or 0)
    score = int(stock.get("signal_score") or 0)
    change_pct = float(stock.get("change_pct") or 0)

    if score >= 75 and close >= ma20 and 45 <= rsi14 <= 72:
        action = "继续重点观察"
        tone = "positive"
        explanation = "短期趋势和动能同时较好，但仍需要等后续确认，不把单日上涨当成买入理由。"
    elif close < ma20 or score < 55:
        action = "降低优先级"
        tone = "risk"
        explanation = "价格或评分偏弱，说明短线承接不足，先看风险释放。"
    else:
        action = "等待确认"
        tone = "neutral"
        explanation = "有一定信号，但趋势、强弱或成交还没有完全配合，适合继续观察。"

    checks = [
        {
            "label": "趋势线",
            "value": "站上 MA20" if close >= ma20 else "跌破 MA20",
            "plain": "MA20 可以粗略理解为近一个月平均成本，站上代表短线承接较好。",
            "score": 78 if close >= ma20 else 42,
        },
        {
            "label": "中期位置",
            "value": "强于 MA60" if close >= ma60 else "弱于 MA60",
            "plain": "MA60 更偏中期趋势，弱于它时不要急着判断趋势反转。",
            "score": 76 if close >= ma60 else 45,
        },
        {
            "label": "RSI",
            "value": f"{rsi14:.1f}",
            "plain": "RSI 低于 45 偏弱，高于 70 容易短线过热，中间区间更适合观察。",
            "score": max(10, min(100, round(100 - abs(rsi14 - 58) * 2))),
        },
        {
            "label": "今日强弱",
            "value": f"{change_pct:.2f}%",
            "plain": "涨跌幅只代表今天的强弱，需要和趋势线、市场背景一起看。",
            "score": max(10, min(100, round(55 + change_pct * 5))),
        },
    ]
    return {
        "action": action,
        "tone": tone,
        "explanation": explanation,
        "checks": checks,
    }


def _enrich_monitor_stock(stock: dict) -> dict:
    technical = _technical_summary(stock)
    return {
        **stock,
        "monitor_action": technical["action"],
        "monitor_tone": technical["tone"],
        "monitor_explanation": technical["explanation"],
        "technical_checks": technical["checks"],
    }


def _snapshot_summary(stocks: list[dict], overview: dict) -> dict:
    positive = sum(1 for item in stocks if item["monitor_tone"] == "positive")
    risk = sum(1 for item in stocks if item["monitor_tone"] == "risk")
    if not stocks:
        headline = "还没有关注股，先从推荐候选里加入观察队列"
    elif positive >= max(1, len(stocks) // 2):
        headline = "关注池整体偏积极，适合继续盯确认信号"
    elif risk:
        headline = "关注池出现风险项，先控制观察优先级"
    else:
        headline = "关注池信号中性，等待下一轮采集确认"
    return {
        "headline": headline,
        "positive_count": positive,
        "neutral_count": sum(1 for item in stocks if item["monitor_tone"] == "neutral"),
        "risk_count": risk,
        "market_brief": (
            f"ETF 市场上涨 {overview['up_count']} 只、下跌 {overview['down_count']} 只，"
            f"当前最强方向是 {overview['strongest']['name']}。"
        ),
    }


def collect_watchlist_snapshot(trigger: str = "manual") -> dict:
    collected_at = _now()
    overview = get_market_overview()
    watched_stocks = [_enrich_monitor_stock(item) for item in list_watch_stocks()]
    snapshot = {
        "id": collected_at.strftime("%Y%m%d%H%M%S"),
        "collected_at": _format_dt(collected_at),
        "trade_date": collected_at.strftime("%Y-%m-%d"),
        "trigger": trigger,
        "market_open": is_market_open(collected_at),
        "collect_rule": "工作日开市期间每 15 分钟自动采集关注股；休市可手动采集用于页面验证。",
        "data_source": "SINA_REALTIME",
        "sync_timezone": SYNC_TIMEZONE,
        "market_overview": overview,
        "watched_count": len(watched_stocks),
        "watched_stocks": watched_stocks,
        "summary": _snapshot_summary(watched_stocks, overview),
    }

    _write_json(LATEST_SNAPSHOT_FILE, snapshot)
    history = _read_json(SNAPSHOT_INDEX_FILE, [])
    history.insert(
        0,
        {
            "id": snapshot["id"],
            "collected_at": snapshot["collected_at"],
            "trade_date": snapshot["trade_date"],
            "watched_count": snapshot["watched_count"],
            "headline": snapshot["summary"]["headline"],
            "market_open": snapshot["market_open"],
            "trigger": trigger,
        },
    )
    _write_json(SNAPSHOT_INDEX_FILE, history[:MAX_SNAPSHOT_HISTORY])
    return snapshot


def _snapshots_this_week() -> list[dict]:
    now = _now()
    week_start = now - timedelta(days=now.weekday())
    history = _read_json(SNAPSHOT_INDEX_FILE, [])
    items = []
    for item in history:
        try:
            collected_at = datetime.strptime(item["collected_at"], "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=ZoneInfo(SYNC_TIMEZONE)
            )
        except (KeyError, ValueError):
            continue
        if collected_at >= week_start:
            items.append(item)
    return items


def build_weekly_review(trigger: str = "manual") -> dict:
    generated_at = _now()
    latest_snapshot = _read_json(LATEST_SNAPSHOT_FILE, None)
    if latest_snapshot is None:
        latest_snapshot = collect_watchlist_snapshot(trigger="weekly_review_bootstrap")

    snapshots = _snapshots_this_week()
    stocks = latest_snapshot.get("watched_stocks", [])
    review_items = []
    for stock in stocks:
        action = stock.get("monitor_action", "等待确认")
        review_items.append(
            {
                "symbol": stock["symbol"],
                "name": stock["name"],
                "action": stock.get("action_plan", {}).get("action", action),
                "action_plan": stock.get("action_plan", {}),
                "plain_summary": stock.get("monitor_explanation", stock.get("plain_analysis", "")),
                "change_pct": stock.get("change_pct", 0),
                "signal_score": stock.get("signal_score", 0),
                "technical_checks": stock.get("technical_checks", []),
                "risk_points": stock.get("risk_points", []),
            }
        )

    positive_count = sum(1 for item in review_items if item["action"] == "继续重点观察")
    risk_count = sum(1 for item in review_items if item["action"] == "降低优先级")
    conclusion = "本周关注池以观察为主，等待新的确认信号。"
    if positive_count:
        conclusion = f"本周有 {positive_count} 只关注股值得继续重点观察。"
    if risk_count:
        conclusion += f" 同时有 {risk_count} 只需要降低优先级，避免被短线波动拖住。"

    review = {
        "id": generated_at.strftime("%Y%m%d%H%M%S"),
        "generated_at": _format_dt(generated_at),
        "period_start": (generated_at - timedelta(days=generated_at.weekday())).strftime("%Y-%m-%d"),
        "period_end": generated_at.strftime("%Y-%m-%d"),
        "trigger": trigger,
        "snapshot_count": len(snapshots),
        "title": "每周复盘看板",
        "conclusion": conclusion,
        "market_summary": latest_snapshot.get("summary", {}).get("market_brief", ""),
        "watch_reviews": review_items,
        "indicator_guide": [
            "MA20：近一个月平均成本，价格站上它说明短线承接相对好。",
            "MA60：中期趋势参考线，弱于它时要降低追踪优先级。",
            "RSI：动能温度计，45 以下偏弱，70 以上容易短线过热。",
            "策略评分：把趋势、涨跌幅和市场背景压缩成 0-100 分，只用于排序观察。",
        ],
        "next_actions": [
            "开市后继续每 15 分钟采集关注股，观察信号是否连续。",
            "把评分较高但不过热的股票加入关注队列，不直接当作买入指令。",
            "对跌破 MA20 或评分下降的股票降低优先级，周复盘时重点解释原因。",
        ],
    }
    _write_json(LATEST_WEEKLY_REVIEW_FILE, review)
    return review


def _scheduled_collect_job() -> None:
    if is_market_open():
        collect_watchlist_snapshot(trigger="scheduler_15m")


def _scheduled_weekly_review_job() -> None:
    build_weekly_review(trigger="scheduler_weekly")


def start_monitor_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return
    scheduler = BackgroundScheduler(timezone=ZoneInfo(SYNC_TIMEZONE))
    scheduler.add_job(
        _scheduled_collect_job,
        "interval",
        minutes=COLLECT_INTERVAL_MINUTES,
        id="watchlist_collect_15m",
        name="关注股开市 15 分钟采集",
        max_instances=1,
        coalesce=True,
        next_run_time=_next_market_open(),
    )
    scheduler.add_job(
        _scheduled_weekly_review_job,
        "cron",
        day_of_week="fri",
        hour=16,
        minute=10,
        id="weekly_market_review",
        name="休市每周复盘",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler


def shutdown_monitor_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None


def _scheduler_next_run(job_id: str) -> str:
    if not _scheduler or not _scheduler.running:
        if job_id == "weekly_market_review":
            return _format_dt(_next_weekly_review())
        return _format_dt(_next_market_open())
    job = _scheduler.get_job(job_id)
    if not job or not job.next_run_time:
        return ""
    return _format_dt(job.next_run_time.astimezone(ZoneInfo(SYNC_TIMEZONE)))


def get_monitor_dashboard() -> dict:
    current = _now()
    latest_snapshot = _read_json(LATEST_SNAPSHOT_FILE, None)
    latest_weekly_review = _read_json(LATEST_WEEKLY_REVIEW_FILE, None)
    recent_snapshots = _read_json(SNAPSHOT_INDEX_FILE, [])[:8]
    return {
        "scheduler": {
            "enabled": bool(_scheduler and _scheduler.running),
            "timezone": SYNC_TIMEZONE,
            "market_status": "开市中" if is_market_open(current) else "休市中",
            "collect_interval_minutes": COLLECT_INTERVAL_MINUTES,
            "collect_window": "工作日 09:30-11:30、13:00-15:00",
            "weekly_review_rule": f"{WEEKLY_REVIEW_DAY} {WEEKLY_REVIEW_TIME} 收盘后生成",
            "next_collect_at": _scheduler_next_run("watchlist_collect_15m"),
            "next_weekly_review_at": _scheduler_next_run("weekly_market_review"),
        },
        "latest_snapshot": latest_snapshot,
        "latest_weekly_review": latest_weekly_review,
        "recent_snapshots": recent_snapshots,
        "recommendations": list_recommended_stocks(limit=6),
    }
