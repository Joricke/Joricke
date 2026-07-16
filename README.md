# Research Chat System

A minimal, production-ready AI chat system for educational research where all student-AI interactions are logged and controlled by the researcher.

Built for PhD-level research on AI literacy, assessment-as-pedagogy, and learning analytics in TVET and higher education contexts.

## Quick Start

### Prerequisites

- Python 3.9+
- An API key from OpenAI or Anthropic

### Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API key

# Run the server
python main.py
```

### Access

- **Student Chat**: Open `frontend/index.html` in a browser
- **Admin Dashboard**: Open `frontend/admin.html` in a browser
- **API Docs**: Visit `http://localhost:8000/docs`

## Architecture

```
research-chat-system/
├── backend/
│   ├── main.py              # FastAPI application (entry point)
│   ├── database.py          # Database operations and queries
│   ├── config.py            # Configuration management
│   ├── prompts.py           # Pedagogical system prompts
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variables template
├── frontend/
│   ├── index.html           # Student chat interface
│   └── admin.html           # Researcher dashboard
├── database/
│   └── schema.sql           # Database schema documentation
└── README.md
```

## Features

| Feature | Description |
|---------|-------------|
| Full logging | Every message stored with timestamps, roles, and metadata |
| Configurable LLM | Switch between OpenAI and Anthropic via environment variables |
| Pedagogical control | Customisable Socratic system prompts |
| Admin dashboard | View transcripts, filter by student/task, export data |
| Export formats | CSV and JSON for analysis in Excel/SPSS/R/Python |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Submit student message, get AI response |
| `/api/history/{chat_id}` | GET | Get conversation history |
| `/admin/transcripts` | GET | List all conversations |
| `/admin/transcript/{chat_id}` | GET | Get full transcript |
| `/admin/export/csv` | GET | Export as CSV |
| `/admin/export/json` | GET | Export as JSON |
| `/admin/stats` | GET | Get summary statistics |
| `/health` | GET | Health check |

## Configuration

Key environment variables (see `.env.example` for full list):

| Variable | Default |
|----------|---------|
| `LLM_PROVIDER` | `anthropic` |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `LLM_TEMPERATURE` | `0.7` |
| `LLM_MAX_TOKENS` | `1024` |
| `DATABASE_URL` | `sqlite:///./data/research_chat.db` |

## Pedagogical System Prompts

The system enforces Socratic teaching through task-specific prompts selected automatically based on `task_id` keywords:

| Keywords in task_id | Prompt Type |
|---------------------|-------------|
| `code`, `prog`, `python`, `java` | Programming guidance |
| `essay`, `write`, `report` | Writing support |
| `math`, `calc`, `equation` | Mathematics scaffolding |
| `research`, `analys`, `data` | Research methodology |

Edit `backend/prompts.py` to customise the pedagogical approach.

## Moodle Integration

This system can be embedded in Moodle using two approaches:

### Option 1: iframe Embedding (Simple)

Add an iframe to a Moodle page, book, or label:

```html
<iframe 
    src="https://your-server.com/?student_id=%%USER_ID%%&task_id=TASK_NAME" 
    width="100%" 
    height="700" 
    frameborder="0"
    allow="clipboard-write">
</iframe>
```

**Passing user context via URL parameters:**
- Modify `frontend/index.html` to read URL parameters and auto-fill the student ID
- Use Moodle's `%%USER_ID%%` or `%%USERNAME%%` placeholders (available in Labels/Pages)

**Pros:** Simple, no plugins required  
**Cons:** Limited integration, students could bypass the iframe

### Option 2: LTI Integration (Recommended for Production)

LTI (Learning Tools Interoperability) provides secure, authenticated embedding.

**Steps:**

1. **Add LTI endpoint to the backend** — Implement `/lti/launch` that validates LTI signatures and extracts user info:

```python
# backend/lti.py (conceptual outline)
from fastapi import Request
from pylti1p3.contrib.fastapi import FlaskMessageLaunch

@app.post("/lti/launch")
async def lti_launch(request: Request):
    launch = FlaskMessageLaunch(request, tool_conf)
    student_id = launch.get_launch_data().get("sub")  # LTI user ID
    # Redirect to chat interface with session token
```

2. **Register as External Tool in Moodle:**
   - Site Administration → Plugins → External tools
   - Add tool URL: `https://your-server.com/lti/launch`
   - Configure OAuth credentials

3. **Add the tool to courses** — Teachers embed via "External Tool" activity

**LTI Library:** Use `PyLTI1p3` for Python: `pip install PyLTI1p3`

**Pros:** Secure authentication, gradebook integration possible, professional  
**Cons:** Requires HTTPS, more setup

### Security Considerations for Moodle

| Concern | Mitigation |
|---------|------------|
| Cross-origin requests | Configure CORS to allow only your Moodle domain |
| User impersonation | Use LTI for authenticated context |
| Data exposure | Run behind institutional SSO/proxy |
| HTTPS | Required for LTI; recommended for iframe |

### Recommended Production Setup

```
Moodle Server                    Research Chat System
┌─────────────┐                 ┌────────────────────────┐
│   Moodle    │                 │   Nginx (reverse proxy)│
│   Course    │ ──── LTI ────►  │         ↓              │
│   Activity  │                 │   FastAPI Backend      │
└─────────────┘                 │         ↓              │
                                │   PostgreSQL DB        │
                                └────────────────────────┘
```

Deploy with:
- **Docker Compose** for containerisation
- **Nginx** as reverse proxy with SSL (Let's Encrypt)
- **PostgreSQL** for production database
- **Gunicorn** with multiple workers for concurrency

---

## Extending the System

### Adding Authentication

For standalone use (without Moodle LTI), add simple API key auth:

```python
# In main.py
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("RESEARCH_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.post("/api/chat", dependencies=[Depends(verify_api_key)])
async def chat(request: ChatRequest):
    ...
```

### Streaming Responses

For longer responses, implement Server-Sent Events:

```python
from fastapi.responses import StreamingResponse

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        # Use streaming API from OpenAI/Anthropic
        async for chunk in stream_llm_response(...):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Multiple Experimental Conditions

Use different system prompts per condition:

```python
# prompts.py
CONDITION_PROMPTS = {
    "control": "You are a helpful AI assistant...",
    "socratic": BASE_SYSTEM_PROMPT,  # Current default
    "minimal": "Provide brief hints only...",
}

# Pass condition via task_id: "prog_hw_1_socratic"
```

---

## Data Analysis

### Accessing the Data

**SQLite (development):**
```bash
sqlite3 data/research_chat.db
.mode csv
.headers on
.output chat_export.csv
SELECT * FROM messages;
```

**Python/Pandas:**
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("data/research_chat.db")
df = pd.read_sql("SELECT * FROM messages", conn)
df.to_csv("analysis_export.csv", index=False)
```

### Key Metrics for Research

| Metric | SQL Query |
|--------|-----------|
| Messages per student | `SELECT student_id, COUNT(*) FROM messages GROUP BY student_id` |
| Avg conversation length | `SELECT AVG(cnt) FROM (SELECT COUNT(*) cnt FROM messages GROUP BY chat_id)` |
| Response latency | Compare timestamps between consecutive user/assistant messages |
| Word count | `SELECT LENGTH(message) - LENGTH(REPLACE(message, ' ', '')) + 1` |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS errors | Check `allow_origins` in `main.py`; for dev, `["*"]` is fine |
| API key errors | Verify `.env` file exists and key is valid |
| Database locked | SQLite limitation; use PostgreSQL for concurrent access |
| Slow responses | Check LLM API latency; consider streaming |
| 502 Bad Gateway | LLM API returned error; check logs for details |

---

## License

This system is provided for educational research purposes.
