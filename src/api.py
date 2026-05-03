import os
import json
import asyncio
from typing import List
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.llm_manager import TelvynManager
from src.ingestor import TelvynIngestor
from src.database import init_db, save_message, get_chat_history, get_total_tokens, get_all_sessions

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Telvyn Hybrid AI API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database and Manager
init_db()
telvyn = TelvynManager()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"

@app.get("/sessions")
async def sessions():
    return get_all_sessions()

@app.get("/history/{session_id}")
async def history(session_id: str):
    return get_chat_history(session_id)

@app.get("/telemetry/{session_id}")
async def telemetry(session_id: str):
    tokens = get_total_tokens(session_id)
    return {"total_tokens": tokens}

@app.post("/chat")
@limiter.limit("40/minute")
async def chat(request: ChatRequest, api_request: Request):
    async def event_generator():
        # Get history for context
        history_msgs = get_chat_history(request.session_id)
        
        # Save user message
        save_message(request.session_id, "human", request.message)
        
        full_response = ""
        # Stream response
        for chunk in telvyn.stream_response(request.message, history_msgs, request.session_id):
            # Check if chunk is a thought
            if chunk.startswith("THOUGHT:"):
                yield {"event": "thought", "data": chunk.replace("THOUGHT: ", "")}
            else:
                full_response += chunk
                yield {"data": chunk}
            await asyncio.sleep(0.01) # Yield to event loop
            
        # Save AI message after stream ends
        if full_response:
            save_message(request.session_id, "ai", full_response)

    return EventSourceResponse(event_generator())

@app.post("/sync")
async def sync_knowledge():
    try:
        ingestor = TelvynIngestor()
        ingestor.sync_knowledge()
        # Refresh manager
        global telvyn
        telvyn = TelvynManager()
        return {"status": "success", "message": "Knowledge base synced!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    knowledge_dir = os.getenv("KNOWLEDGE_DIR", "./knowledge")
    if not os.path.exists(knowledge_dir):
        os.makedirs(knowledge_dir)
    
    saved_files = []
    for file in files:
        file_path = os.path.join(knowledge_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        saved_files.append(file.filename)
        
    return {"status": "success", "files": saved_files}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
