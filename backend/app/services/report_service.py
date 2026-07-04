from datetime import date
from textwrap import dedent

from app.services.backtest_service import get_backtest_summary
from app.core.config import settings
from app.services.llm_service import generate_deepseek_report, generate_doubao_report, generate_openai_report
from app.services.market_service import get_market_overview
from app.services.strategy_service import get_strategy_signals

REPORT_CONTENT = """今日国内 ETF 市场整体偏震荡，沪深300ETF 和科创50ETF 相对强于创业板ETF。

策略层面，均线 + RSI 趋势观察策略对沪深300ETF、科创50ETF 给出可关注提示，对创业板ETF 给出谨慎提示。

风险方面，当前仍处于 MVP 研究阶段，所有信号仅用于辅助复盘，不构成投资建议，也不会触发自动下单。"""


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

        输出要求：
        1. 使用中文。
        2. 包含市场概览、策略信号解读、风险提示三段。
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
    provider_order = [settings.ai_provider, "openai", "deepseek", "doubao"]

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
        "id": 1,
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
    report = get_latest_report()
    return [report]
