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

# --- LIGHTWEIGHT KEYWORD RAG ---
# Purpose: Select only relevant context to stay under Groq's 6000 TPM limit.

KB_PATH = "knowledge_base.md"
try:
    with open(KB_PATH, "r", encoding="utf-8") as f:
        FULL_KB_TEXT = f.read()
except FileNotFoundError:
    print("WARNING: knowledge_base.md not found.")
    FULL_KB_TEXT = ""

# Simple segmentation of the KB (This effectively acts as a lightweight database)
# We assume the KB has headers like 'SECTION 1', 'SECTION 2', etc.
# If not, we fall back to keyword matching on the full text but truncated.

def get_relevant_context(query: str) -> str:
    """
    Returns specific sections of the KB based on keywords in the query.
    This reduces the prompt size drastically.
    """
    query_lower = query.lower()
    
    selected_context = []
    
    # 1. CORE INFO (Always include basics)
    # Extracts the intro summary part roughly
    selected_context.append(FULL_KB_TEXT[:2000]) 

    # 2. PRICING & PLANS
    if any(k in query_lower for k in ["price", "cost", "pay", "plan", "money", "rupee", "dollar"]):
        # Extract Section 4 rough approximation
        pricing_start = FULL_KB_TEXT.find("SECTION 4: PRICING")
        if pricing_start != -1:
             # Grab 3000 chars of pricing
            selected_context.append(FULL_KB_TEXT[pricing_start:pricing_start+4000])

    # 3. INSTALLATION & ACTIVATION
    if any(k in query_lower for k in ["install", "setup", "activate", "qrcode", "scan", "ios", "android", "help"]):
        # Extract Section 2 & 3 rough approximation
        install_start = FULL_KB_TEXT.find("SECTION 3: HOW VELOME WORKS")
        if install_start != -1:
            selected_context.append(FULL_KB_TEXT[install_start:install_start+5000])

    # 4. COVERAGE / COUNTRIES
    if any(k in query_lower for k in ["where", "country", "countries", "coverage", "japan", "korea", "vietnam", "china"]):
        # Extract coverage list
        matches = [line for line in FULL_KB_TEXT.split('\n') if "₹" in line or "Region" in line]
        selected_context.append("\n".join(matches))

    # Combine and Deduplicate (simple set check not perfect for text chunks but okay here)
    final_context = "\n---\n".join(selected_context)
    
    # HARD LIMIT: Truncate to ~12000 characters (~3000 tokens) to be safe
    return final_context[:12000]

# Initialize LLM
api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    temperature=0.3,
    groq_api_key=api_key,
    model_name="llama-3.1-8b-instant" 
)

# Template
prompt_template = ChatPromptTemplate.from_template(
    """
    You are Velo, the friendly AI travel assistant for Velome.travel.
    Use the context below to answer data-driven questions.
    If the exact answer isn't there, suggest contacting support@velome.travel.
    
    <CONTEXT>
    {context}
    </CONTEXT>

    User Question: {input}
    """
)

chain = prompt_template | llm

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Dynamic Context Retrieval
        relevant_context = get_relevant_context(request.message)
        
        response = chain.invoke({
            "context": relevant_context,
            "input": request.message
        })
        
        answer = response.content
        answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
        
        return {"response": answer}
    except Exception as e:
        print(f"Error: {e}")
        # Fallback for Rate Limits: Return a polite error asking to try again shortly
        if "413" in str(e) or "429" in str(e):
             return {"response": "I'm receiving too many messages right now. Please wait 10 seconds and try again!"}
        return {"response": "Sorry, I encountered an error. Please try again."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
