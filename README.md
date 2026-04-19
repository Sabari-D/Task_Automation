# Auto-Worker: AI Multi-Agent Task Automation System

An advanced, multi-agent AI system designed to autonomously plan, research, optimize, and execute complex workflows based on simple user prompts. Built with a modern technology stack to ensure high performance, maintainability, and an incredible user experience.

## 🚀 Features

- **Multi-Agent Orchestration**: Powered by CrewAI and LangChain, featuring specialized agents:
  - 🧠 **Planner Agent**: Deconstructs user requests into structured tasks.
  - 🔍 **Research Agent**: Gathers real-time web context using Tavily/Serper tools.
  - 💰 **Budget Optimizer**: Filters options to meet user constraints.
  - 🛠️ **Execution Agent**: Synthesizes a beautiful, comprehensive final report.
- **Real-Time Streaming**: Live WebSocket connections stream agent reasoning and status directly to a visually stunning React UI.
- **Modern Aesthetics**: Vibrant gradients, glassmorphism, and smooth animations using Next.js 15 and Tailwind CSS v4.
- **Robust Infrastructure**: Local environment entirely containerized with Docker, backing FastAPI and Redis.

## 🛠️ Technology Stack

- **Frontend**: Next.js, React, Tailwind CSS v4
- **Backend**: FastAPI, Python 3, WebSockets
- **AI Layer**: OpenAI GPT-4, CrewAI, LangChain, LangSmith (Observability)
- **Database/Caching**: PostgreSQL, Redis (managed via Docker Compose)

## 📦 Local Development Setup

### 1. Pre-requisites
- Docker & Docker Compose
- Node.js (v18+)
- Python (3.10+)

### 2. Environment Configuration
Create a `.env` file in the root directory and configure your keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT="auto_worker_system"
```

### 3. Start Database Infrastructure
```bash
docker-compose up -d
```

### 4. Run the AI Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/Scripts/activate # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 5. Run the Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:3000` to launch your multi-agent workforce!

## Architecture Flow
1. User provides a prompt (e.g., "Plan a 3-day trip to Goa under ₹10k").
2. Next.js `POST`s the prompt to FastAPI.
3. FastAPI triggers a `BackgroundTasks` function which instantiates the `Crew`.
4. The Crew sequentially executes the Planner -> Researcher -> Optimizer -> Executor.
5. While running, the backend pushes state changes over WebSockets to the frontend.
6. The frontend displays simulated reasoning logs and eventually renders the Markdown final result.
