import sys
import io
import os
import json
import uuid
import asyncio
import hashlib
import threading
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import redis.asyncio as redis_async
from sqlalchemy.future import select

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

load_dotenv()

app = FastAPI(
    title="AI Multi-Agent Task Automation System API",
    description="Auto-Worker: Fast multi-agent AI powered by Gemini",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.models import AutoTaskRequest, AutoTaskResponse
from app.database import (
    init_db, AsyncSessionLocal, TaskRecord,
    sync_update_task, SyncSessionLocal
)

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis_async.from_url(redis_url, decode_responses=True, socket_connect_timeout=5)
except Exception:
    redis_client = None

@app.on_event("startup")
async def startup():
    await init_db()

# ── Direct Gemini Call (synchronous — safe in background threads) ────────────

def call_gemini_sync(prompt: str) -> str:
    """Calls Gemini 1.5 Flash directly. Returns the markdown result string."""
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured in environment variables.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-pro",
        generation_config={"temperature": 0.4, "max_output_tokens": 1500},
    )

    system_prompt = """You are the Auto-Worker Engine — a powerful AI multi-agent system composed of:
1. Planner Agent: Breaks down complex tasks into structured steps
2. Research Agent: Gathers data, facts, and relevant information  
3. Budget Optimizer Agent: Ensures plans stay within cost constraints
4. Executor Agent: Produces the final, polished output

Given the user's task below, produce a comprehensive response as if all four agents collaborated.
Format your output in beautiful Markdown with:
- ## Executive Summary
- ## Step-by-Step Plan
- ## Key Research & Findings
- ## Budget Breakdown (if applicable)
- ## Final Recommendations

Be specific, practical, and detailed."""

    response = model.generate_content(f"{system_prompt}\n\n**User Task:** {prompt}")
    return response.text


def background_task_runner(task_id: str, prompt: str):
    """Runs in a background thread. Uses sync DB — no event loop issues."""
    # Mark as running
    sync_update_task(task_id, "running")

    try:
        result = call_gemini_sync(prompt)
        sync_update_task(task_id, "completed", result)
        print(f"[AutoWorker] Task {task_id} completed successfully.")
    except Exception as e:
        error_msg = str(e)
        print(f"[AutoWorker] Task {task_id} failed: {error_msg}")
        sync_update_task(task_id, "failed", f"Agent error: {error_msg}")


# ── REST Endpoints ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "Auto-Worker API is live", "version": "1.0.0"}


@app.post("/api/task", response_model=AutoTaskResponse)
async def create_task(request: AutoTaskRequest):
    # Check Redis cache
    if redis_client:
        try:
            prompt_hash = hashlib.sha256(request.user_prompt.encode()).hexdigest()
            cached = await redis_client.get(f"cache:{prompt_hash}")
            if cached:
                data = json.loads(cached)
                task_id = str(uuid.uuid4())
                async with AsyncSessionLocal() as session:
                    task = TaskRecord(
                        id=task_id,
                        prompt=request.user_prompt,
                        status=data["status"],
                        result=data["result"]
                    )
                    session.add(task)
                    await session.commit()
                return AutoTaskResponse(task_id=task_id, status="cached", message="Returned from cache")
        except Exception as e:
            print(f"Redis cache error: {e}")

    # Create task in DB
    task_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        task = TaskRecord(id=task_id, prompt=request.user_prompt, status="pending", result=None)
        session.add(task)
        await session.commit()

    # Dispatch to background thread — non-blocking
    thread = threading.Thread(
        target=background_task_runner,
        args=(task_id, request.user_prompt),
        daemon=True
    )
    thread.start()

    return AutoTaskResponse(task_id=task_id, status="pending", message="Task started")


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """Polling endpoint checked by frontend every 2 seconds."""
    async with AsyncSessionLocal() as session:
        stmt = select(TaskRecord).where(TaskRecord.id == task_id)
        res = await session.execute(stmt)
        task = res.scalar_one_or_none()
        if not task:
            return {"error": "Task not found"}
        return {
            "task_id": task.id,
            "status": task.status,
            "result": task.result
        }


@app.websocket("/ws/task/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket kept for compatibility — polls DB and pushes updates."""
    await websocket.accept()
    try:
        for _ in range(180):  # poll for up to 6 minutes
            async with AsyncSessionLocal() as session:
                stmt = select(TaskRecord).where(TaskRecord.id == task_id)
                res = await session.execute(stmt)
                task = res.scalar_one_or_none()
                if task:
                    await websocket.send_text(json.dumps({
                        "task_id": task_id,
                        "status": task.status,
                        "result": task.result
                    }))
                    if task.status in ("completed", "failed", "cached"):
                        break
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
