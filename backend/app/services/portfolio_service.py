import json
from pathlib import Path
from typing import Any

from app.services.market_service import SYNC_TIMEZONE, get_sync_time
from app.services.watchlist_service import get_stock


PORTFOLIO_FILE = Path(__file__).resolve().parents[2] / "local_data" / "portfolio.json"

DEFAULT_PORTFOLIO = {
    "cash_balance": 100000.0,
    "currency": "CNY",
    "is_sample": True,
    "positions": [
        {
            "symbol": "600519",
            "lots": [
                {"buy_date": "2026-06-18", "quantity": 50, "cost_price": 1208.0},
                {"buy_date": "2026-06-27", "quantity": 50, "cost_price": 1198.0},
            ],
        },
        {
            "symbol": "300750",
            "lots": [
                {"buy_date": "2026-06-20", "quantity": 60, "cost_price": 386.0},
                {"buy_date": "2026-07-01", "quantity": 40, "cost_price": 376.88},
            ],
        },
        {
            "symbol": "600288",
            "lots": [
                {"buy_date": "2026-06-21", "quantity": 600, "cost_price": 12.2},
                {"buy_date": "2026-06-28", "quantity": 400, "cost_price": 13.2},
            ],
        },
    ],
}


def _read_portfolio() -> dict:
    if not PORTFOLIO_FILE.exists():
        return DEFAULT_PORTFOLIO
    try:
        data = json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_PORTFOLIO
    return {
        "cash_balance": float(data.get("cash_balance", 0)),
        "currency": data.get("currency", "CNY"),
        "is_sample": bool(data.get("is_sample", False)),
        "positions": data.get("positions", []),
    }


def _money(value: float) -> float:
    return round(value, 2)


def _pct(value: float) -> float:
    return round(value, 2)


def _position_message(today_profit: float, holding_profit: float) -> str:
    if today_profit > 0:
        return f"今天赚了 {_money(today_profit)} 元，持仓累计盈亏 {_money(holding_profit)} 元。"
    if today_profit < 0:
        return f"今天亏了 {_money(abs(today_profit))} 元，持仓累计盈亏 {_money(holding_profit)} 元。"
    return f"今天基本没变化，持仓累计盈亏 {_money(holding_profit)} 元。"


def _position_action(today_profit: float, holding_profit_pct: float, change_pct: float) -> str:
    if today_profit > 0 and holding_profit_pct >= 8:
        return "已有明显浮盈，可考虑分批落袋。"
    if today_profit < 0 and holding_profit_pct <= -5:
        return "今天走弱且累计亏损偏大，优先看止损线。"
    if change_pct > 0:
        return "今天上涨，先看能否延续强势。"
    if change_pct < 0:
        return "今天下跌，先别急着补仓。"
    return "波动不大，继续观察。"


def _position_lots(raw: dict) -> list[dict]:
    lots = raw.get("lots")
    if isinstance(lots, list) and lots:
        return lots
    return [
        {
            "buy_date": raw.get("buy_date", ""),
            "quantity": raw.get("quantity", 0),
            "cost_price": raw.get("cost_price", 0),
        }
    ]


def get_portfolio_overview() -> dict:
    portfolio = _read_portfolio()
    positions = []
    market_value = 0.0
    cost_value = 0.0
    today_profit = 0.0

    for raw in portfolio["positions"]:
        symbol = str(raw.get("symbol", ""))[-6:]
        if not symbol:
            continue

        stock = get_stock(symbol)
        if stock is None:
            continue

        close = float(stock.get("close", 0))
        price_change = float(stock.get("price_change", 0))
        lots = []
        quantity = 0.0
        position_cost = 0.0
        position_market_value = 0.0
        position_holding_profit = 0.0
        position_today_profit = 0.0

        for index, lot in enumerate(_position_lots(raw), start=1):
            lot_quantity = float(lot.get("quantity", 0))
            lot_cost_price = float(lot.get("cost_price", 0))
            if lot_quantity <= 0:
                continue
            lot_cost_value = lot_cost_price * lot_quantity
            lot_market_value = close * lot_quantity
            lot_profit = lot_market_value - lot_cost_value
            lot_profit_pct = lot_profit / lot_cost_value * 100 if lot_cost_value else 0
            lot_today_profit = price_change * lot_quantity
            quantity += lot_quantity
            position_cost += lot_cost_value
            position_market_value += lot_market_value
            position_holding_profit += lot_profit
            position_today_profit += lot_today_profit
            lots.append(
                {
                    "id": str(lot.get("id") or f"{symbol}-{index}"),
                    "buy_date": lot.get("buy_date", ""),
                    "quantity": lot_quantity,
                    "cost_price": _money(lot_cost_price),
                    "current_price": _money(close),
                    "cost_value": _money(lot_cost_value),
                    "market_value": _money(lot_market_value),
                    "profit": _money(lot_profit),
                    "profit_pct": _pct(lot_profit_pct),
                    "today_profit": _money(lot_today_profit),
                    "is_profit": lot_profit >= 0,
                    "message": (
                        f"这笔赚了 {_money(lot_profit)} 元"
                        if lot_profit >= 0
                        else f"这笔亏了 {_money(abs(lot_profit))} 元"
                    ),
                }
            )

        if quantity <= 0:
            continue

        avg_cost_price = position_cost / quantity if quantity else 0
        position_market_value = close * quantity
        position_holding_profit_pct = (
            position_holding_profit / position_cost * 100 if position_cost else 0
        )

        market_value += position_market_value
        cost_value += position_cost
        today_profit += position_today_profit
        positions.append(
            {
                "symbol": symbol,
                "name": stock["name"],
                "quantity": quantity,
                "avg_cost_price": _money(avg_cost_price),
                "current_price": _money(close),
                "market_value": _money(position_market_value),
                "cost_value": _money(position_cost),
                "today_profit": _money(position_today_profit),
                "today_profit_pct": _pct(stock["change_pct"]),
                "holding_profit": _money(position_holding_profit),
                "holding_profit_pct": _pct(position_holding_profit_pct),
                "message": _position_message(position_today_profit, position_holding_profit),
                "lots": lots,
                "action_hint": _position_action(
                    position_today_profit,
                    position_holding_profit_pct,
                    float(stock.get("change_pct", 0)),
                ),
                "action_plan": stock.get("action_plan", {}),
                "data_source": stock["data_source"],
                "synced_at": stock["synced_at"],
            }
        )

    cash_balance = float(portfolio["cash_balance"])
    total_assets = cash_balance + market_value
    holding_profit = market_value - cost_value
    holding_profit_pct = holding_profit / cost_value * 100 if cost_value else 0

    if today_profit > 0:
        headline = f"今天整体赚了 {_money(today_profit)} 元"
        tone = "profit"
    elif today_profit < 0:
        headline = f"今天整体亏了 {_money(abs(today_profit))} 元"
        tone = "loss"
    else:
        headline = "今天持仓基本没变化"
        tone = "flat"

    return {
        "synced_at": get_sync_time(),
        "sync_timezone": SYNC_TIMEZONE,
        "currency": portfolio["currency"],
        "is_sample": portfolio["is_sample"],
        "headline": headline,
        "tone": tone,
        "cash_balance": _money(cash_balance),
        "market_value": _money(market_value),
        "total_assets": _money(total_assets),
        "today_profit": _money(today_profit),
        "today_profit_pct": _pct(today_profit / cost_value * 100 if cost_value else 0),
        "holding_profit": _money(holding_profit),
        "holding_profit_pct": _pct(holding_profit_pct),
        "position_count": len(positions),
        "positions": positions,
    }
