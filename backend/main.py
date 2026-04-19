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

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

load_dotenv()

app = FastAPI(
    title="AI Multi-Agent Task Automation System API",
    description="Backend for the Auto-Worker system",
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
from app.database import init_db, get_db, TaskRecord, AsyncSessionLocal

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis_async.from_url(redis_url, decode_responses=True, socket_connect_timeout=5)
except Exception:
    redis_client = None

_main_loop = None

@app.on_event("startup")
async def startup():
    global _main_loop
    _main_loop = asyncio.get_event_loop()
    await init_db()

# ── Direct Gemini execution (fast, no CrewAI overhead) ──────────────────────

def _call_gemini_direct(prompt: str) -> str:
    """Call Gemini directly for sub-5 second AI responses."""
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("No GEMINI_API_KEY or GOOGLE_API_KEY set in environment.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"temperature": 0.4, "max_output_tokens": 1500},
    )

    system_prompt = """You are the Auto-Worker Engine — a team of four AI agents: 
Planner, Researcher, Budget Optimizer, and Executor.

Given the user's task, respond as if all four agents have collaborated and reached a final consensus.
Produce a beautifully-formatted, detailed Markdown response with:
- A short Executive Summary
- A Step-by-Step Plan
- Key Research Findings (with realistic figures/estimates)
- Budget Breakdown (if applicable)
- Clear Final Recommendations

Be comprehensive, practical and specific. Show the final polished output only."""

    response = model.generate_content(f"{system_prompt}\n\nUser Task: {prompt}")
    return response.text


def _run_task_in_thread(task_id: str, prompt: str):
    """Run in a background thread, update DB when done."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_execute_task(task_id, prompt))
    finally:
        loop.close()


async def _execute_task(task_id: str, prompt: str):
    # Mark as running
    async with AsyncSessionLocal() as session:
        stmt = select(TaskRecord).where(TaskRecord.id == task_id)
        res = await session.execute(stmt)
        task = res.scalar_one_or_none()
        if task:
            task.status = "running"
            await session.commit()

    try:
        # Call Gemini directly — fast!
        result = await asyncio.get_event_loop().run_in_executor(
            None, _call_gemini_direct, prompt
        )
        status = "completed"
    except Exception as e:
        result = f"Agent error: {str(e)}"
        status = "failed"

    # Save result to DB
    async with AsyncSessionLocal() as session:
        stmt = select(TaskRecord).where(TaskRecord.id == task_id)
        res = await session.execute(stmt)
        task = res.scalar_one_or_none()
        if task:
            task.status = status
            task.result = result
            await session.commit()

    # Cache result in Redis
    if redis_client:
        try:
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
            await redis_client.set(
                f"cache:{prompt_hash}",
                json.dumps({"status": status, "result": result}),
                ex=86400
            )
        except Exception:
            pass

    # Notify WebSocket subscribers via Redis pub/sub
    if redis_client:
        try:
            await redis_client.publish(
                f"task_updates:{task_id}",
                json.dumps({"task_id": task_id, "status": status, "result": result})
            )
        except Exception:
            pass


# ── REST Endpoints ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "Auto-Worker API is live", "version": "1.0.0"}

@app.post("/api/task", response_model=AutoTaskResponse)
async def create_task(request: AutoTaskRequest, background_tasks: BackgroundTasks):
    # Check Redis cache first
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
        except Exception:
            pass

    # Create new task record
    task_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        task = TaskRecord(id=task_id, prompt=request.user_prompt, status="pending", result=None)
        session.add(task)
        await session.commit()

    # Run in background thread (non-blocking)
    thread = threading.Thread(target=_run_task_in_thread, args=(task_id, request.user_prompt), daemon=True)
    thread.start()

    return AutoTaskResponse(task_id=task_id, status="pending", message="Task started")


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """REST polling endpoint — frontend polls this every 2 seconds."""
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


# ── WebSocket (kept for live streaming via Redis pub/sub) ────────────────────

@app.websocket("/ws/task/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()

    # Send current state immediately
    async with AsyncSessionLocal() as session:
        stmt = select(TaskRecord).where(TaskRecord.id == task_id)
        res = await session.execute(stmt)
        task = res.scalar_one_or_none()
        if task:
            try:
                await websocket.send_text(json.dumps({
                    "task_id": task_id,
                    "status": task.status,
                    "result": task.result
                }))
                if task.status in ("completed", "failed", "cached"):
                    await websocket.close()
                    return
            except Exception:
                return

    # Listen for updates via Redis pub/sub OR keep-alive polling
    if redis_client:
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(f"task_updates:{task_id}")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await websocket.send_text(message["data"])
                    data = json.loads(message["data"])
                    if data.get("status") in ("completed", "failed"):
                        break
        except Exception:
            pass
    else:
        # Fallback: poll DB every 2s and push to WebSocket
        try:
            for _ in range(150):  # max 5 minutes
                await asyncio.sleep(2)
                async with AsyncSessionLocal() as session:
                    stmt = select(TaskRecord).where(TaskRecord.id == task_id)
                    res = await session.execute(stmt)
                    task = res.scalar_one_or_none()
                    if task and task.status in ("completed", "failed"):
                        await websocket.send_text(json.dumps({
                            "task_id": task_id,
                            "status": task.status,
                            "result": task.result
                        }))
                        break
        except WebSocketDisconnect:
            pass
        except Exception:
            pass
