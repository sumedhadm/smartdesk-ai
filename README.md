# SmartDesk AI

LLM-powered productivity assistant: chat, sales analytics, and tool calling,
built with Python, Gemini, Pandas, and Streamlit.

## Features
- AI chat with Gemini (system prompt, session history)
- Tool calling: the model requests `analyze_sales` or `create_task`; the app
  validates the request and runs it from a fixed whitelist
- Sales analyzer: Pandas/NumPy statistics, CSV upload, chart, insights
- Login with salted PBKDF2 password hashes (SQLite) and per-user tasks
- Unit tests with pytest

## Architecture
User -> Streamlit UI (`app.py`) -> `SmartDeskAgent` (`agent.py`) -> Gemini API
-> tool-call request -> whitelist registry -> `tools.py` (Pandas) / `db.py` (SQLite)
-> tool result back to the model -> final answer

## Setup
```
git clone https://github.com/sumedhadm/smartdesk-ai.git
cd smartdesk-ai
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then add your Gemini API key
streamlit run app.py
```

## Tests
```
python -m pytest -v
```

## Security notes
- API key in `.env` (gitignored); passwords hashed with salted PBKDF2
- Parameterized SQL, HTML-escaped output, tool whitelist and argument validation
- Login and rate limits are demo-level, not production-grade

## Known limitations
- Gemini free-tier quotas are small (20 requests/day for gemini-2.5-flash
  on my project), so heavy use hits rate limits
- Tasks are stored in a local SQLite file

## Screenshots
Coming soon.