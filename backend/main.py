# main.py (place next to run.py)
import os, asyncio
from fastapi import FastAPI, Request
import importlib
from app.models.schemas import ScraperInput  # your Pydantic models

app = FastAPI(title="CredenceAI")

@app.on_event("startup")
async def startup():
    # create queue and start agent
    app.state.agent_queue = asyncio.Queue(maxsize=1000)
    agent = importlib.import_module("agent.worker")
    app.state.agent_task = asyncio.create_task(agent.start_agent(asyncio.get_event_loop(), app.state.agent_queue))

@app.on_event("shutdown")
async def shutdown():
    agent = importlib.import_module("agent.worker")
    stop = getattr(agent, "stop_agent", None)
    if stop:
        maybe = stop()
        if asyncio.iscoroutine(maybe):
            await maybe
    if getattr(app.state, "agent_task", None):
        app.state.agent_task.cancel()
        try:
            await app.state.agent_task
        except asyncio.CancelledError:
            pass

@app.post("/ingest/scraper", status_code=202)
async def ingest(payload: ScraperInput, request: Request):
    q = request.app.state.agent_queue
    await q.put(payload.dict())
    return {"status":"accepted", "claim_id": payload.claim_id}
