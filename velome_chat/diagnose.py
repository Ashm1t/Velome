import os
from dotenv import load_dotenv
import traceback

print("--- DIAGNOSTIC START ---")

# 1. Check .env load
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("FATAL: GROQ_API_KEY not found in environment.")
else:
    print(f"SUCCESS: GROQ_API_KEY found. Length: {len(api_key)}")
    print(f"Key preview: {api_key[:4]}...{api_key[-4:]}")

# 2. Check Dependencies
try:
    print("Importing langchain_groq...")
    from langchain_groq import ChatGroq
    print("Importing embeddings...")
    from langchain_huggingface import HuggingFaceEmbeddings
    print("Importing vectorstore...")
    from langchain_community.vectorstores import Chroma
    print("SUCCESS: Dependencies imported.")
except ImportError as e:
    print(f"FATAL: Dependency missing: {e}")
    exit(1)

# 3. Test LLM
try:
    print("Testing ChatGroq initialization...")
    llm = ChatGroq(temperature=0, groq_api_key=api_key, model_name="qwen/qwen3-32b")
    # Optional: Try a simple invoke if you want to test the key validity strictly
    # print("Testing LLM connectivity...")
    # llm.invoke("Hi")
    print("SUCCESS: ChatGroq initialized.")
except Exception as e:
    print(f"FATAL: ChatGroq initialization failed: {e}")
    traceback.print_exc()

# 4. Test Embeddings (Heavy)
try:
    print("Testing Embeddings initialization (all-MiniLM-L6-v2)...")
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    print("SUCCESS: Embeddings initialized.")
except Exception as e:
    print(f"FATAL: Embeddings initialization failed: {e}")
    traceback.print_exc()

print("--- DIAGNOSTIC END ---")
