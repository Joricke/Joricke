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

## License

This system is provided for educational research purposes.
