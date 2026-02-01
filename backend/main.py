"""FastAPI application for Research Chat System.

Entry point for the backend server. Provides API endpoints for:
- Student chat interactions (with LLM proxy)
- Admin transcript viewing and export
- Health checks
"""

import json
import logging
import uuid
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

import config
import database
from prompts import get_system_prompt

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("research-chat")

# --- App Setup ---
app = FastAPI(
    title="Research Chat System",
    description="A controlled AI chat system for educational research",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Startup ---
@app.on_event("startup")
async def startup():
    logger.info("Initializing Research Chat System...")
    database.init_db()
    status = config.validate_config()
    logger.info(f"Database ready: {config.DATABASE_URL}")
    logger.info(f"LLM Provider: {status['provider']}")
    logger.info(f"API Key configured: {'Yes' if status['api_key_configured'] else 'No'}")


# --- Request/Response Models ---
class ChatRequest(BaseModel):
    message: str
    student_id: str
    task_id: str = ""
    chat_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    chat_id: str


# --- LLM Calls ---
async def call_openai(messages: list[dict], model: str, api_key: str) -> str:
    """Call the OpenAI Chat Completions API."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": config.LLM_TEMPERATURE,
                "max_tokens": config.LLM_MAX_TOKENS,
            },
        )
        if resp.status_code != 200:
            logger.error(f"OpenAI API error: {resp.status_code} {resp.text}")
            raise HTTPException(status_code=502, detail="LLM API error")
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def call_anthropic(messages: list[dict], system_prompt: str, model: str, api_key: str) -> str:
    """Call the Anthropic Messages API."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": config.LLM_MAX_TOKENS,
                "temperature": config.LLM_TEMPERATURE,
                "system": system_prompt,
                "messages": messages,
            },
        )
        if resp.status_code != 200:
            logger.error(f"Anthropic API error: {resp.status_code} {resp.text}")
            raise HTTPException(status_code=502, detail="LLM API error")
        data = resp.json()
        return data["content"][0]["text"]


async def call_llm(conversation_history: list[dict], system_prompt: str) -> str:
    """Route the LLM call to the configured provider."""
    api_key = config.get_api_key()
    model = config.get_model()

    if not api_key:
        raise HTTPException(status_code=500, detail="No API key configured")

    if config.LLM_PROVIDER == "openai":
        # OpenAI expects system prompt as the first message
        messages = [{"role": "system", "content": system_prompt}] + conversation_history
        return await call_openai(messages, model, api_key)
    elif config.LLM_PROVIDER == "anthropic":
        return await call_anthropic(conversation_history, system_prompt, model, api_key)
    else:
        raise HTTPException(status_code=500, detail=f"Unknown provider: {config.LLM_PROVIDER}")


# --- Chat Endpoint ---
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle a student chat message.

    1. Assign or reuse a chat_id
    2. Log the student message
    3. Build conversation context from history
    4. Call the LLM
    5. Log the AI response
    6. Return the response
    """
    chat_id = request.chat_id or str(uuid.uuid4())

    # 1. Log student message
    database.save_message(
        chat_id=chat_id,
        student_id=request.student_id,
        task_id=request.task_id,
        role="user",
        message=request.message,
        model="",
        provider="",
    )

    # 2. Build conversation history for LLM context
    history = database.get_history(chat_id)
    conversation = [
        {"role": msg["role"], "content": msg["message"]}
        for msg in history
        if msg["role"] in ("user", "assistant")
    ]

    # 3. Get system prompt based on task
    system_prompt = get_system_prompt(request.task_id)

    # 4. Call LLM
    try:
        ai_response = await call_llm(conversation, system_prompt)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to get AI response")

    # 5. Log AI response
    database.save_message(
        chat_id=chat_id,
        student_id=request.student_id,
        task_id=request.task_id,
        role="assistant",
        message=ai_response,
        model=config.get_model(),
        provider=config.LLM_PROVIDER,
    )

    return ChatResponse(response=ai_response, chat_id=chat_id)


# --- History Endpoint ---
@app.get("/api/history/{chat_id}")
async def get_history(chat_id: str):
    """Get conversation history for a chat session."""
    messages = database.get_history(chat_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"chat_id": chat_id, "messages": messages}


# --- Admin Endpoints ---
@app.get("/admin/stats")
async def admin_stats():
    """Get summary statistics for the admin dashboard."""
    return database.get_stats()


@app.get("/admin/transcripts")
async def admin_transcripts(
    student_id: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None),
):
    """List all conversations with summary info."""
    return database.get_all_transcripts(student_id=student_id, task_id=task_id)


@app.get("/admin/transcript/{chat_id}")
async def admin_transcript(chat_id: str):
    """Get full transcript for a specific conversation."""
    messages = database.get_transcript(chat_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"chat_id": chat_id, "messages": messages}


@app.get("/admin/export/csv")
async def admin_export_csv(
    student_id: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Export all messages as CSV."""
    csv_data = database.export_csv(
        student_id=student_id,
        task_id=task_id,
        start_date=start_date,
        end_date=end_date,
    )
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chat_data.csv"},
    )


@app.get("/admin/export/json")
async def admin_export_json(
    student_id: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Export all messages as JSON, grouped by conversation."""
    data = database.export_json(
        student_id=student_id,
        task_id=task_id,
        start_date=start_date,
        end_date=end_date,
    )
    return JSONResponse(content=data)


# --- Health Check ---
@app.get("/health")
async def health():
    """Health check endpoint."""
    status = config.validate_config()
    return {
        "status": "ok",
        "provider": status["provider"],
        "model": status["model"],
        "api_key_configured": status["api_key_configured"],
    }


# --- Run ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=True)
