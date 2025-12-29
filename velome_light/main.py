import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/static/chat-widget.html")

# --- CONTEXT STUFFING SETUP ---
# Load Knowledge Base into Memory
KB_PATH = "knowledge_base.md"
try:
    with open(KB_PATH, "r", encoding="utf-8") as f:
        KNOWLEDGE_BASE_TEXT = f.read()
except FileNotFoundError:
    print("WARNING: knowledge_base.md not found.")
    KNOWLEDGE_BASE_TEXT = "No knowledge base found."

# Initialize LLM (No RAG, just ChatGroq)
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("WARNING: GROQ_API_KEY not found.")

llm = ChatGroq(
    temperature=0.3,
    groq_api_key=api_key,
    model_name="llama-3.1-8b-instant" # Faster model for lite demo
)

# Template with Context Stuffing
prompt_template = ChatPromptTemplate.from_template(
    """
    You are Velo, the friendly and enthusiastic AI travel assistant for Velome.travel.
    You help users with eSIM plans, pricing, installation, and troubleshooting.

    INSTRUCTIONS:
    1. Be friendly, helpful, and concise. Use emojis occasionally (👋, 🌍, ✈️).
    2. Use the provided KNOWLEDGE BASE below to answer questions.
    3. If the answer is not in the knowledge base, say "I'm not sure about that, but I can help with Velome eSIMs!" then provide support contact info (support@velome.travel).
    4. Format your answers nicely with Markdown (bolding, lists).

    <KNOWLEDGE BASE>
    {context}
    </KNOWLEDGE BASE>

    User Question: {input}
    """
)

chain = prompt_template | llm

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Context Stuffing: We pass the ENTIRE KB text as 'context'
        response = chain.invoke({
            "context": KNOWLEDGE_BASE_TEXT,
            "input": request.message
        })
        
        # Cleanup
        answer = response.content
        answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
        
        return {"response": answer}
    except Exception as e:
        print(f"Error: {e}")
        return {"response": "Sorry, I encountered an error. Please try again."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
