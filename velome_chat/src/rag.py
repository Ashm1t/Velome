import os
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from typing import List

# Path to the knowledge base
KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_base.md")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")

def load_and_chunk_documents() -> List[Document]:
    """Loads the markdown file and splits it into chunks."""
    # Ensure KB exists
    if not os.path.exists(KB_PATH):
        raise FileNotFoundError(f"Knowledge base not found at {KB_PATH}")

    # Read file content
    with open(KB_PATH, "r", encoding="utf-8") as f:
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
    return splits

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
