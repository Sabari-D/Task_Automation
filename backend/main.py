import sys
import io
import os
import json
import uuid
import asyncio
import hashlib
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
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.models import AutoTaskRequest, AutoTaskResponse
from app.crew import AutoWorkerCrew
from app.database import init_db, get_db, TaskRecord, AsyncSessionLocal

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis_async.from_url(redis_url, decode_responses=True)
_main_loop = None

@app.on_event("startup")
async def startup():
    global _main_loop
    _main_loop = asyncio.get_event_loop()
    await init_db()
    # verify redis connection
    try:
        await redis_client.ping()
        print("Redis connected")
    except Exception as e:
        print("Redis connection failed:", e)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Auto-Worker backend is running"}

async def _notify_clients_async(task_id: str, status: str, result: str):
    message = json.dumps({"task_id": task_id, "status": status, "result": result})
    try:
        await redis_client.publish(f"task_updates:{task_id}", message)
    except Exception as e:
        print(f"Error publishing to redis: {e}")

async def _update_db_async(task_id: str, status: str, result: str = None):
    async with AsyncSessionLocal() as session:
        stmt = select(TaskRecord).where(TaskRecord.id == task_id)
        res = await session.execute(stmt)
        task = res.scalar_one_or_none()
        if task:
            task.status = status
            if result:
                task.result = result
            await session.commit()

        if status in ("completed", "failed") and task:
            prompt_hash = hashlib.sha256(task.prompt.encode()).hexdigest()
            try:
                await redis_client.set(f"cache:{prompt_hash}", json.dumps({
                    "status": status,
                    "result": result
                }), ex=86400) # 24 hrs
            except Exception as e:
                print(f"Error setting cache in redis: {e}")

def update_state_sync(task_id: str, status: str, result: str = None):
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(_update_db_async(task_id, status, result), _main_loop)
        asyncio.run_coroutine_threadsafe(_notify_clients_async(task_id, status, result), _main_loop)

def run_crew_task(task_id: str, prompt: str):
    update_state_sync(task_id, "running", None)

    try:
        crew = AutoWorkerCrew(user_prompt=prompt)
        result = crew.run()

        if hasattr(result, 'raw'):
            final_output = result.raw
        else:
            final_output = str(result)

        update_state_sync(task_id, "completed", final_output)
    except Exception as e:
        error_msg = str(e)
        if "insufficient_quota" in error_msg:
            error_msg = "OpenAI API quota exceeded."
        elif "rate_limit_exceeded" in error_msg or "RateLimitError" in error_msg or ("429" in error_msg and "groq" in error_msg.lower()):
            error_msg = "Groq API rate limit exceeded. Please wait ~60s and try again."
        update_state_sync(task_id, "failed", error_msg)

@app.post("/api/task", response_model=AutoTaskResponse)
async def create_task(request: AutoTaskRequest, background_tasks: BackgroundTasks):
    prompt_hash = hashlib.sha256(request.user_prompt.encode()).hexdigest()
    
    try:
        cached_data = await redis_client.get(f"cache:{prompt_hash}")
        if cached_data:
            data = json.loads(cached_data)
            task_id = str(uuid.uuid4())
            async with AsyncSessionLocal() as session:
                task = TaskRecord(id=task_id, prompt=request.user_prompt, status=data["status"], result=data["result"])
                session.add(task)
                await session.commit()
            return AutoTaskResponse(task_id=task_id, status="cached", message="Returned from cache")
    except Exception as e:
        print(f"Redis cache check failed: {e}")

    task_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        task = TaskRecord(id=task_id, prompt=request.user_prompt, status="pending", result=None)
        session.add(task)
        await session.commit()
        
    background_tasks.add_task(run_crew_task, task_id, request.user_prompt)
    return AutoTaskResponse(task_id=task_id, status="pending", message="Task started")

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(TaskRecord).where(TaskRecord.id == task_id)
        res = await session.execute(stmt)
        task = res.scalar_one_or_none()
        if not task:
            return {"error": "Task not found"}
        return {"id": task.id, "prompt": task.prompt, "status": task.status, "result": task.result}

@app.websocket("/ws/task/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    
    async with AsyncSessionLocal() as session:
        stmt = select(TaskRecord).where(TaskRecord.id == task_id)
        res = await session.execute(stmt)
        task = res.scalar_one_or_none()
        if task:
            try:
                await websocket.send_text(json.dumps({"task_id": task_id, "status": task.status, "result": task.result}))
                if task.status in ("completed", "failed", "cached"):
                    return
            except:
                return

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"task_updates:{task_id}")
    
    try:
        while True:
            async def read_ws():
                return await websocket.receive_text()
                
            async def read_pubsub():
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        return message["data"]
                        
            ws_task = asyncio.create_task(read_ws())
            ps_task = asyncio.create_task(read_pubsub())
            
            done, pending = await asyncio.wait([ws_task, ps_task], return_when=asyncio.FIRST_COMPLETED)
            
            for t in pending:
                t.cancel()
                
            if ws_task in done:
                break
                
            if ps_task in done:
                msg = ps_task.result()
                if msg:
                    await websocket.send_text(msg)
                    data = json.loads(msg)
                    if data.get("status") in ("completed", "failed"):
                        break
                        
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(f"task_updates:{task_id}")
