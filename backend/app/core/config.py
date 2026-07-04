from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "ChinaQuantify"
    app_env: str = "development"
    database_url: str = "sqlite:///./china_quantify.db"
    redis_url: str = "redis://localhost:6379/0"
    ai_provider: str = "deepseek"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_base_url: str = "https://api.deepseek.com"
    doubao_api_key: str = ""
    doubao_endpoint_id: str = ""
    doubao_model: str = "doubao-1-5-lite-32k-250115"
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    market_data_provider: str = "akshare"
    scheduler_enabled: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
