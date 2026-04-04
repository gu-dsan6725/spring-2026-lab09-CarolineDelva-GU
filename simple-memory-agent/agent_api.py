import logging
import uuid
from typing import Dict, Optional, Any, AsyncGenerator
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from agent import Agent
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Memory Agent API",
    description="Multi-tenant conversational agent with semantic memory",
    version="1.0.0"
)


_session_cache: Dict[str, Agent] = {}


def get_or_create_agent(user_id: str, run_id: str) -> Agent:
    if run_id in _session_cache:
        return _session_cache[run_id]

    logger.info(f"Creating agent | user_id={user_id} run_id={run_id}")

    agent = Agent(
        user_id=user_id,
        run_id=run_id
    )

    _session_cache[run_id] = agent
    return agent


class InvocationRequest(BaseModel):
    user_id: str = Field(..., description="User identifier for memory isolation")
    run_id: Optional[str] = Field(None, description="Session ID (optional)")
    query: str = Field(..., description="User message")
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    stream: Optional[bool] = Field(
        default=True,
        description="Whether to stream the response (default: true)"
    )


class PingResponse(BaseModel):
    status: str
    message: str

async def stream_response(agent: Agent, query: str) -> AsyncGenerator[str, None]:
    try:
        response = agent.chat(query)

        yield f"data: {response}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.exception("Streaming error")
        yield f"data: ERROR: {str(e)}\n\n"



@app.get("/ping", response_model=PingResponse)
async def ping():
    return PingResponse(
        status="ok",
        message="Memory Agent API is running"
    )


@app.post("/invocation")
async def invocation(request: InvocationRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    run_id = request.run_id or str(uuid.uuid4())[:8]

    logger.info(
        f"Invocation | user_id={request.user_id} "
        f"run_id={run_id} stream={request.stream}"
    )

    agent = get_or_create_agent(
        user_id=request.user_id,
        run_id=run_id
    )

    if request.stream:
        return StreamingResponse(
            stream_response(agent, request.query),
            media_type="text/event-stream",
            headers={"X-Run-ID": run_id}
        )

    try:
        response = agent.chat(request.query)

        return JSONResponse(
            content={
                "run_id": run_id,
                "user_id": request.user_id,
                "response": response
            }
        )

    except Exception as e:
        logger.exception("Invocation error")
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )
