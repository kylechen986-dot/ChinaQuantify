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

## 当前 MVP 能力

- 国内 ETF 标的池接口
- 行情概览接口
- 指标快照接口
- 策略信号接口
- 回测摘要接口
- AI 日报接口
- Vue3 管理台基础页面
