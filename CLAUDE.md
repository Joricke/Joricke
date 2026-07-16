# Research Chat System

Educational AI chat system for PhD research on student-AI interactions.

## Quick Commands

```bash
# Start backend
cd backend && python main.py

# Test API
curl http://localhost:8000/health
```

## Key Files

- `backend/main.py` — FastAPI server, API endpoints
- `backend/prompts.py` — Socratic system prompts (edit to modify pedagogy)
- `backend/config.py` — Environment configuration
- `frontend/index.html` — Student chat UI
- `frontend/admin.html` — Researcher dashboard

## Architecture

```
Student Browser → FastAPI → LLM API (OpenAI/Anthropic)
                    ↓
               SQLite DB (all messages logged)
```

## Testing

The system uses httpx for async HTTP calls. Test endpoints:
- `POST /api/chat` — Send message, get AI response
- `GET /admin/transcripts` — List all conversations
- `GET /admin/export/csv` — Export data
