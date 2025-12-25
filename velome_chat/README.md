# Velome Chatbot

LLM-powered chatbot for Velome.travel, using RAG to answer queries from the knowledge base.

## Components
- **Backend**: FastAPI with LangChain and ChromaDB (`src/`).
- **Frontend**: HTML/JS chat widget (`static/`).
- **Knowledge Base**: `data/knowledge_base.md`.

## Setup
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Environment Variables**:
   Copy `.env.example` to `.env` and set your `OPENAI_API_KEY`.
   ```bash
   cp .env.example .env
   # Edit .env
   ```

## Running
1. **Navigate to project directory** (if not already there):
   ```bash
   cd velome_chat
   ```
2. **Start Backend**:
   ```bash
   python -m uvicorn src.main:app --reload --port 8000
   ```
2. **Test Frontend**:
   Open `static/chat-widget.html` in your browser.

## Integration
To integrate into Velome website, include the CSS and JS files, and paste the HTML structure (or dynamically inject it). Update `API_URL` in `static/chat.js` if the backend is hosted elsewhere.
