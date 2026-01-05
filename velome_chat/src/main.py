from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.models import ChatRequest, ChatResponse
from src.rag import get_vectorstore
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv
import os

load_dotenv()

# Global state for RAG components
# Global state for RAG components
rag_state = {
    "chain": None
}

# Simple in-memory session store
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

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
        # Use Fast Groq model (Llama 3.1 8B Instant)
        llm = ChatGroq(temperature=0, groq_api_key=api_key, model_name="llama-3.1-8b-instant")
        
        # 1. History-Aware Retriever (Fixes "Goldfish Memory")
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        retriever = vectorstore.as_retriever()
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        # 2. Natural System Prompt (Fixes Looping/Rigid Behavior)
        system_prompt = (
            "You are Velo, a friendly travel expert for Velome.travel. "
            "Your personality is helpful, concise, and professional (like a helpful WhatsApp contact).\n\n"
            "YOUR GOALS:\n"
            "1. Help users find and book the right eSIM.\n"
            "2. When they mention a destination, confirm it and ask for duration (ONLY if duration isn't in history).\n"
            "3. Once duration is known, ask for quantity and departure timing (ONLY if not in history).\n"
            "4. **LOOK UP PRICE**: Check the context for the specific country's 'Daily Rate'. Calculate Total = Rate * Days * Qty.\n"
            "5. Provide the final calculation and the DIRECT booking link from context.\n"
            "6. Answer technical/support questions immediately using the context links (e.g., /support, /how-to-use).\n\n"
            "CONSTRAINTS:\n"
            "- Stop repeating the same phrase (e.g., 'Vietnam is beautiful') if you've already said it.\n"
            "- If the user provides a number like '3', check your context/history to see if it refers to days or eSIMs.\n"
            "- Be brief: 1-2 sentences max.\n"
            "- Do not provide 'Buy' links until the user is ready (after pricing is shared).\n\n"
            "Context:\n{context}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        # 3. Combine it all
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        
        # Create final retrieval chain
        retrieval_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        # Wrap with Message History
        rag_state["chain"] = RunnableWithMessageHistory(
            retrieval_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )
        print("RAG System Initialized with History-Aware Retrieval")
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
        # Pass session_id to Config
        response = rag_state["chain"].invoke(
            {"input": request.message},
            config={"configurable": {"session_id": request.session_id}}
        )
        
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
