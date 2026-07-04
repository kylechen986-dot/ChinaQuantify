# ChinaQuantify

ChinaQuantify 是一个聚焦国内 ETF 的 AI 量化研究与日报系统。MVP 阶段先做行情监控、技术指标、策略信号、轻量回测和 AI 日报展示，不做自动实盘交易。

## 技术栈

- Frontend: Vue 3 + Vite + TypeScript + Element Plus + ECharts
- Backend: Python 3.14 + FastAPI + Pandas / NumPy
- Infra: PostgreSQL / Redis via Docker Compose

## 本地启动

后端：

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

访问：

- 前端：http://127.0.0.1:5173
- 后端：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/docs

## AI 配置

后端默认支持 OpenAI、DeepSeek 和豆包/火山方舟 Chat Completions。复制 `backend/.env.example` 为 `backend/.env` 后填写：

```env
AI_PROVIDER=deepseek
OPENAI_API_KEY=你的 OpenAI API Key
OPENAI_MODEL=gpt-4o-mini

DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_MODEL=deepseek-v4-flash

DOUBAO_API_KEY=你的 API Key
DOUBAO_ENDPOINT_ID=方舟接入点 ID，可选
DOUBAO_MODEL=doubao-1-5-lite-32k-250115
```

如果需要切换到 OpenAI，将 `AI_PROVIDER` 改为 `openai`。如果 `DOUBAO_ENDPOINT_ID` 有值，后端会优先把它作为 Chat API 的 `model` 参数；否则使用 `DOUBAO_MODEL`。当当前 AI 供应商未配置或调用失败时，日报接口会优先尝试国内模型，按 DeepSeek、豆包、OpenAI 顺序兜底，最后自动回退到 Mock 内容，保证 MVP 页面可用。

## 当前 MVP 能力

- 国内 ETF 标的池接口
- 行情概览接口
- 指标快照接口
- 策略信号接口
- 回测摘要接口
- AI 日报接口
- Vue3 管理台基础页面
