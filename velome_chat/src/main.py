from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.models import ChatRequest, ChatResponse
from src.rag import get_vectorstore
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv
import os

load_dotenv()

# Global state for RAG components
rag_state = {
    "chain": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- LIFESPAN STARTING ---")
    # Startup
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("WARNING: GROQ_API_KEY not found. RAG will not work.")
        
        print("Initializing RAG system...")
        vectorstore = get_vectorstore()
        # Use Groq model (Llama3-8b-8192 failed, using user-listed Qwen)
        llm = ChatGroq(temperature=0, groq_api_key=api_key, model_name="qwen/qwen3-32b")
        
        prompt = ChatPromptTemplate.from_template("""
        You are Velo, the friendly and helpful AI assistant for Velome.travel.
        
        INSTRUCTIONS:
        1. PERSONA: Be warm, professional, and enthusiastic about travel.
        2. CONVERSATIONAL: Use natural language. dynamic sentence structures, and connecting phrases. Avoid robotic lists unless necessary for clarity.
        3. HELPFUL: Always guide the user to the next step (e.g., "Would you like to see pricing for that?" or "I can help you install it!").
        4. ACCURACY: Use ONLY the provided context. If unsure, strictly say "I'm not sure about that, but our support team is available 24/7 to help!"
        5. FORMATTING: Use Markdown for emphasis (bold, italic) and lists where appropriate to make text readable.
        
        <context>
        {context}
        </context>

        Question: {input}
        """)

        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = vectorstore.as_retriever()
        rag_state["chain"] = create_retrieval_chain(retriever, document_chain)
        print("RAG System Initialized Successfully")
    except Exception as e:
        print(f"Failed to initialize RAG system: {e}")
    
    yield
    # Shutdown

from fastapi.staticfiles import StaticFiles

from fastapi.responses import RedirectResponse

app = FastAPI(lifespan=lifespan)

# Mount static files using absolute path
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    print(f"WARNING: Static directory not found at {static_dir}")

# Allow CORS for widget integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return RedirectResponse(url="/static/chat-widget.html")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not rag_state["chain"]:
         # Fallback if RAG isn't working (e.g. no API key)
        if not os.getenv("GROQ_API_KEY"):
             return ChatResponse(response="System is missing API Key. Please configure the backend.")
        raise HTTPException(status_code=503, detail="RAG system is initializing or failed to load.")
    
    try:
        response = rag_state["chain"].invoke({"input": request.message})
        
        # Clean response of <think> tags (common in reasoning models like Qwen)
        import re
        answer = response["answer"]
        answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
        
        # Deduplicate sources
        sources = list(set([
            doc.metadata.get("Header 2") or doc.metadata.get("Header 1") or "General Info" 
            for doc in response.get("context", [])
        ]))
        
        return ChatResponse(
            response=answer,
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok", "rag_ready": rag_state["chain"] is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
