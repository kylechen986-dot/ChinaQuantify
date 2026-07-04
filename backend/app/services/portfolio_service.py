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
                {
                    "id": "600519-1",
                    "buy_date": "2026-06-18 10:12:08",
                    "quantity": 50,
                    "cost_price": 1208.0,
                    "fee": 5.0,
                },
                {
                    "id": "600519-2",
                    "buy_date": "2026-06-27 14:23:35",
                    "quantity": 50,
                    "cost_price": 1198.0,
                    "fee": 5.0,
                },
            ],
        },
        {
            "symbol": "300750",
            "lots": [
                {
                    "id": "300750-1",
                    "buy_date": "2026-06-20 09:45:16",
                    "quantity": 60,
                    "cost_price": 386.0,
                    "fee": 5.0,
                },
                {
                    "id": "300750-2",
                    "buy_date": "2026-07-01 13:18:42",
                    "quantity": 40,
                    "cost_price": 376.88,
                    "fee": 3.0,
                },
            ],
        },
        {
            "symbol": "600288",
            "lots": [
                {
                    "id": "600288-1",
                    "buy_date": "2026-06-21 10:05:31",
                    "quantity": 600,
                    "cost_price": 12.2,
                    "fee": 5.0,
                },
                {"id": "600288-2", "buy_date": "2026-06-28 14:02:19", "quantity": 400, "cost_price": 13.2},
            ],
            "cashflows": [
                {"date": "2026-06-30 09:00:00", "type": "DIVIDEND", "amount": 32.0, "note": "示例分红入账"},
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


def _formula_money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}¥{abs(value):,.2f}"


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


def _lot_fee(lot: dict) -> float:
    return float(lot.get("fee", 0)) + float(lot.get("commission", 0)) + float(lot.get("tax", 0))


def _flow_type_text(value: str) -> str:
    mapping = {
        "BUY": "买入",
        "SELL": "卖出",
        "DIVIDEND": "分红",
        "FEE": "手续费",
        "TAX": "税费",
        "ADJUST": "资金调整",
    }
    return mapping.get(value, value)


def _flow_sort_key(item: dict) -> tuple[str, str]:
    return (str(item.get("date", "")), str(item.get("type", "")))


def _build_position(raw: dict) -> dict | None:
    symbol = str(raw.get("symbol", ""))[-6:]
    if not symbol:
        return None

    stock = get_stock(symbol)
    if stock is None:
        return None

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
        lot_fee = _lot_fee(lot)
        if lot_quantity <= 0:
            continue
        lot_trade_value = lot_cost_price * lot_quantity
        lot_cost_value = lot_trade_value + lot_fee
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
                "fee": _money(lot_fee),
                "current_price": _money(close),
                "cost_value": _money(lot_cost_value),
                "trade_value": _money(lot_trade_value),
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
        return None

    avg_cost_price = position_cost / quantity if quantity else 0
    realized_cashflow = sum(float(flow.get("amount", 0)) for flow in raw.get("cashflows", []))
    position_total_profit = position_holding_profit + realized_cashflow
    position_total_profit_pct = position_total_profit / position_cost * 100 if position_cost else 0

    return {
        "symbol": symbol,
        "name": stock["name"],
        "quantity": quantity,
        "avg_cost_price": _money(avg_cost_price),
        "current_price": _money(close),
        "market_value": _money(position_market_value),
        "cost_value": _money(position_cost),
        "today_profit": _money(position_today_profit),
        "today_profit_pct": _pct(stock["change_pct"]),
        "holding_profit": _money(position_total_profit),
        "holding_profit_pct": _pct(position_total_profit_pct),
        "message": _position_message(position_today_profit, position_total_profit),
        "lots": lots,
        "action_hint": _position_action(
            position_today_profit,
            position_total_profit_pct,
            float(stock.get("change_pct", 0)),
        ),
        "action_plan": stock.get("action_plan", {}),
        "data_source": stock["data_source"],
        "synced_at": stock["synced_at"],
        "_raw_cashflows": raw.get("cashflows", []),
    }


def get_portfolio_overview() -> dict:
    portfolio = _read_portfolio()
    positions = []
    market_value = 0.0
    cost_value = 0.0
    today_profit = 0.0
    holding_profit = 0.0

    for raw in portfolio["positions"]:
        position = _build_position(raw)
        if position is None:
            continue

        market_value += position["market_value"]
        cost_value += position["cost_value"]
        today_profit += position["today_profit"]
        holding_profit += position["holding_profit"]
        position.pop("_raw_cashflows", None)
        positions.append(position)

    cash_balance = float(portfolio["cash_balance"])
    total_assets = cash_balance + market_value
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


def get_stock_cashflows(symbol: str) -> dict | None:
    normalized = symbol.strip()[-6:]
    portfolio = _read_portfolio()
    raw_position = next(
        (item for item in portfolio["positions"] if str(item.get("symbol", ""))[-6:] == normalized),
        None,
    )
    if raw_position is None:
        return None

    position = _build_position(raw_position)
    if position is None:
        return None

    flows = []
    for lot in position["lots"]:
        amount = -float(lot["cost_value"])
        fee_text = f"，含费用 {lot['fee']} 元" if float(lot.get("fee", 0)) else ""
        calculation_text = (
            f"{_formula_money(float(lot['cost_price']))}/股 × {float(lot['quantity']):g} 股 "
            f"+ 收费 {_formula_money(float(lot['fee']))} = {_formula_money(amount)}"
        )
        flows.append(
            {
                "id": f"buy-{lot['id']}",
                "date": lot["buy_date"],
                "type": "BUY",
                "type_text": "买入",
                "quantity": lot["quantity"],
                "price": lot["cost_price"],
                "fee": lot["fee"],
                "amount": _money(amount),
                "direction": "out",
                "note": f"买入 {lot['quantity']} 股，买入价 {lot['cost_price']} 元{fee_text}",
                "calculation_text": calculation_text,
                "related_lot_id": lot["id"],
            }
        )

    for index, flow in enumerate(position.pop("_raw_cashflows", []), start=1):
        flow_type = str(flow.get("type", "ADJUST")).upper()
        amount = float(flow.get("amount", 0))
        calculation_text = str(flow.get("calculation_text") or f"{_flow_type_text(flow_type)}：{_formula_money(amount)}")
        flows.append(
            {
                "id": str(flow.get("id") or f"flow-{normalized}-{index}"),
                "date": flow.get("date", ""),
                "type": flow_type,
                "type_text": _flow_type_text(flow_type),
                "quantity": float(flow.get("quantity", 0)),
                "price": _money(float(flow.get("price", 0))),
                "fee": _money(float(flow.get("fee", 0))),
                "amount": _money(amount),
                "direction": "in" if amount >= 0 else "out",
                "note": flow.get("note", ""),
                "calculation_text": calculation_text,
                "related_lot_id": flow.get("related_lot_id", ""),
            }
        )

    flows.sort(key=_flow_sort_key, reverse=True)
    real_inflow = sum(float(item["amount"]) for item in flows if float(item["amount"]) > 0)
    total_outflow = sum(float(item["amount"]) for item in flows if float(item["amount"]) < 0)
    total_inflow = real_inflow + float(position["market_value"])
    net_cashflow = total_inflow + total_outflow
    position.pop("_raw_cashflows", None)
    return {
        "symbol": position["symbol"],
        "name": position["name"],
        "synced_at": position["synced_at"],
        "sync_timezone": SYNC_TIMEZONE,
        "current_price": position["current_price"],
        "quantity": position["quantity"],
        "market_value": position["market_value"],
        "cost_value": position["cost_value"],
        "holding_profit": position["holding_profit"],
        "holding_profit_pct": position["holding_profit_pct"],
        "today_profit": position["today_profit"],
        "total_inflow": _money(total_inflow),
        "total_outflow": _money(total_outflow),
        "net_cashflow": _money(net_cashflow),
        "flow_profit": _money(net_cashflow),
        "flows": flows,
    }
