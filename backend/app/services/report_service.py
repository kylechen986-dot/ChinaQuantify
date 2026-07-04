from datetime import date


REPORT_CONTENT = """今日国内 ETF 市场整体偏震荡，沪深300ETF 和科创50ETF 相对强于创业板ETF。

策略层面，均线 + RSI 趋势观察策略对沪深300ETF、科创50ETF 给出可关注提示，对创业板ETF 给出谨慎提示。

风险方面，当前仍处于 MVP 研究阶段，所有信号仅用于辅助复盘，不构成投资建议，也不会触发自动下单。"""


def get_latest_report() -> dict:
    return {
        "id": 1,
        "report_date": str(date.today()),
        "report_type": "DAILY_ETF",
        "title": f"{date.today()} 国内 ETF AI 量化日报",
        "summary": "市场整体震荡，科创50ETF 相对强势，创业板ETF 偏弱。",
        "content": REPORT_CONTENT,
        "model_provider": "OPENAI",
        "model_name": "mock-provider",
    }


def list_reports() -> list[dict]:
    report = get_latest_report()
    return [report]
