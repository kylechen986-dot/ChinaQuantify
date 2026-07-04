from datetime import date, timedelta
from textwrap import dedent

from app.services.backtest_service import get_backtest_summary
from app.core.config import settings
from app.services.llm_service import generate_deepseek_report, generate_doubao_report, generate_openai_report
from app.services.market_service import get_market_overview
from app.services.strategy_service import get_strategy_signals
from app.services.watchlist_service import list_watch_stocks

REPORT_CONTENT = """今日国内 ETF 市场整体偏震荡，沪深300ETF 和科创50ETF 相对强于创业板ETF。

策略层面，均线 + RSI 趋势观察策略对沪深300ETF、科创50ETF 给出可关注提示，对创业板ETF 给出谨慎提示。

风险方面，当前仍处于 MVP 研究阶段，所有信号仅用于辅助复盘，不构成投资建议，也不会触发自动下单。"""


def _report_id(report_date: date) -> int:
    return int(report_date.strftime("%Y%m%d"))


def _historical_reports() -> list[dict]:
    templates = [
        {
            "offset": 1,
            "summary": "市场小幅反弹，沪深300ETF 企稳，创业板ETF 仍偏弱。",
            "content": "昨日 ETF 市场呈现温和修复。沪深300ETF 率先企稳，说明大盘资产承接力有所恢复；创业板ETF 仍处弱势，短线资金对高波动方向保持谨慎。策略信号以观察为主，适合记录趋势是否延续，不适合直接作为买卖依据。",
            "tone": "修复",
        },
        {
            "offset": 2,
            "summary": "市场分化明显，科创50ETF 相对强势，红利ETF 横盘。",
            "content": "当日市场没有形成一致方向，科创50ETF 表现更强，说明成长方向有阶段性资金关注；红利ETF 继续横盘，防御资产缺少新的趋势推动。普通用户可以理解为：市场还没有全面转强，只是部分方向先动起来。",
            "tone": "分化",
        },
        {
            "offset": 3,
            "summary": "ETF 标的多数震荡，策略信号整体偏谨慎。",
            "content": "当日多数 ETF 在均线附近震荡，趋势确认度不高。策略给出的 WATCH 表示值得继续观察，CAUTION 表示短线风险偏高。两类标签都不是交易指令，只是帮助复盘时快速判断哪些标的更强、哪些标的需要回避波动。",
            "tone": "震荡",
        },
        {
            "offset": 4,
            "summary": "行情偏弱，创业板ETF 和中证500ETF 承压。",
            "content": "当日市场风险偏好下降，创业板ETF 和中证500ETF 承压更明显。对不熟悉股票的人来说，可以把这理解为：资金暂时不太愿意追逐高弹性方向，系统会降低相关标的的观察优先级。",
            "tone": "偏弱",
        },
    ]
    reports = []
    for item in templates:
        report_date = date.today() - timedelta(days=item["offset"])
        reports.append(
            {
                "id": _report_id(report_date),
                "report_date": str(report_date),
                "report_type": "DAILY_ETF",
                "title": f"{report_date} 国内 ETF AI 量化日报",
                "summary": item["summary"],
                "content": item["content"],
                "model_provider": "ARCHIVE",
                "model_name": "snapshot",
                "market_tone": item["tone"],
                "llm_usage": {},
                "llm_error": "",
            }
        )
    return reports


def build_report_prompt() -> str:
    return dedent(
        f"""
        请生成一份国内 ETF AI 量化日报，日期：{date.today()}。

        行情概览：
        {get_market_overview()}

        策略信号：
        {get_strategy_signals()}

        回测摘要：
        {get_backtest_summary()}

        关注个股：
        {list_watch_stocks()}

        输出要求：
        1. 使用中文。
        2. 包含市场概览、策略信号解读、关注个股研判、风险提示四段。
        3. 不要给出买卖指令，只给研究复盘视角。
        """
    ).strip()


def get_latest_report() -> dict:
    model_provider = "MOCK"
    model_name = "mock-provider"
    content = REPORT_CONTENT
    llm_usage = {}
    llm_error = ""

    providers = {
        "openai": generate_openai_report,
        "deepseek": generate_deepseek_report,
        "doubao": generate_doubao_report,
    }
    provider_order = [settings.ai_provider, "deepseek", "doubao", "openai"]

    try:
        prompt = build_report_prompt()
        result = None
        errors = []
        for provider in dict.fromkeys(provider_order):
            generator = providers.get(provider.lower())
            if not generator:
                continue
            try:
                result = generator(prompt)
                break
            except Exception as exc:
                errors.append(f"{provider}: {exc}")
        if result is None:
            raise RuntimeError("; ".join(errors))
        content = result["content"]
        model_provider = result["model_provider"]
        model_name = result["model_name"]
        llm_usage = result.get("usage", {})
    except Exception as exc:
        llm_error = str(exc)

    return {
        "id": _report_id(date.today()),
        "report_date": str(date.today()),
        "report_type": "DAILY_ETF",
        "title": f"{date.today()} 国内 ETF AI 量化日报",
        "summary": "市场整体震荡，科创50ETF 相对强势，创业板ETF 偏弱。",
        "content": content,
        "model_provider": model_provider,
        "model_name": model_name,
        "llm_usage": llm_usage,
        "llm_error": llm_error,
    }


def list_reports() -> list[dict]:
    today = date.today()
    latest_summary = {
        "id": _report_id(today),
        "report_date": str(today),
        "report_type": "DAILY_ETF",
        "title": f"{today} 国内 ETF AI 量化日报",
        "summary": "市场整体震荡，科创50ETF 相对强势，创业板ETF 偏弱。",
        "content": "",
        "model_provider": settings.ai_provider.upper(),
        "model_name": "latest",
        "market_tone": "分化",
        "llm_usage": {},
        "llm_error": "",
    }
    return [latest_summary, *_historical_reports()]


def get_report(report_id: int) -> dict:
    latest_id = _report_id(date.today())
    if report_id == latest_id:
        return get_latest_report()

    for report in _historical_reports():
        if report["id"] == report_id:
            return report

    return {
        **list_reports()[0],
        "id": report_id,
        "title": "未找到对应日报",
        "summary": "请从左侧历史日报列表选择已有日期。",
        "content": "当前 MVP 暂未持久化该日期的日报内容。后续接入数据库后，会支持完整历史日报归档。",
        "model_provider": "SYSTEM",
        "model_name": "not-found",
        "market_tone": "未知",
    }
