import httpx

from app.core.config import settings


SYSTEM_PROMPT = (
    "你是 ChinaQuantify 的 ETF 量化研究助理。"
    "请基于输入的行情、指标、策略信号和回测摘要生成中文日报。"
    "必须强调内容仅用于研究复盘，不构成投资建议，不触发自动交易。"
)


def _post_chat_completion(base_url: str, api_key: str, payload: dict) -> dict:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, json=payload, headers=headers)
        if response.is_error:
            raise RuntimeError(f"LLM API error {response.status_code}: {response.text[:500]}")
        return response.json()


def is_deepseek_configured() -> bool:
    return bool(settings.deepseek_api_key and settings.deepseek_model)


def generate_deepseek_report(prompt: str) -> dict:
    if not is_deepseek_configured():
        raise RuntimeError("DeepSeek API is not configured")

    payload = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1200,
    }
    data = _post_chat_completion(settings.deepseek_base_url, settings.deepseek_api_key, payload)
    content = data["choices"][0]["message"]["content"]
    return {
        "content": content.strip(),
        "model_provider": "DEEPSEEK",
        "model_name": settings.deepseek_model,
        "usage": data.get("usage", {}),
    }


def is_doubao_configured() -> bool:
    return bool(settings.doubao_api_key and (settings.doubao_endpoint_id or settings.doubao_model))


def generate_doubao_report(prompt: str) -> dict:
    if not is_doubao_configured():
        raise RuntimeError("Doubao API is not configured")

    model_id = settings.doubao_endpoint_id or settings.doubao_model
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1200,
    }
    data = _post_chat_completion(settings.doubao_base_url, settings.doubao_api_key, payload)
    content = data["choices"][0]["message"]["content"]
    return {
        "content": content.strip(),
        "model_provider": "DOUBAO",
        "model_name": model_id,
        "endpoint_id": settings.doubao_endpoint_id,
        "usage": data.get("usage", {}),
    }
