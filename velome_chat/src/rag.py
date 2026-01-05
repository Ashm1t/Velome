import os
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from typing import List

# Directory containing the knowledge base files
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "chroma_db")

def load_and_chunk_documents() -> List[Document]:
    """Loads all markdown files from the data directory and splits them into chunks."""
    all_chunks = []
    
    # Check if data directory exists
    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError(f"Data directory not found at {DATA_DIR}")

    # Process all .md files in the directory
    md_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".md")]
    
    if not md_files:
        print("WARNING: No markdown files found in data directory.")
        return []

    for filename in md_files:
        file_path = os.path.join(DATA_DIR, filename)
        print(f"Indexing: {filename}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            markdown_text = f.read()

        # Split by headers first to keep context
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_header_splits = markdown_splitter.split_text(markdown_text)

        # Then split reasonably sized chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        splits = text_splitter.split_documents(md_header_splits)
        all_chunks.extend(splits)
    
    return all_chunks

def get_vectorstore():
    """Returns the Chroma vector store, creating it if it doesn't exist."""
    # Use generic generic/neutral embedding model
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Check if DB exists (simple check)
    if os.path.exists(DB_PATH) and os.listdir(DB_PATH):
        # Load existing
        vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embedding_function)
    else:
        # Create new
        docs = load_and_chunk_documents()
        vectorstore = Chroma.from_documents(documents=docs, embedding=embedding_function, persist_directory=DB_PATH)
    
    return vectorstore

def query_knowledge_base(query: str, vectorstore):
    """Queries the vector store."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    return docs
