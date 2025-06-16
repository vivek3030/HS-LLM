# doc_helper.py
import os
import shutil
import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, CSVLoader, UnstructuredExcelLoader
from langchain_ollama import OllamaEmbeddings

DOCUMENT_DIR = '/home/team-kasundra/RAG/documents'
PROCESSED_DIR = '/home/team-kasundra/RAG/processed'

def load_documents():
    documents = []
    for filename in os.listdir(DOCUMENT_DIR):
        filepath = os.path.join(DOCUMENT_DIR, filename)
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(filepath)
        elif filename.endswith(".docx"):
            loader = Docx2txtLoader(filepath)
        elif filename.endswith(".txt"):
            loader = TextLoader(filepath)
        elif filename.endswith(".csv"):
            loader = CSVLoader(filepath)
        elif filename.endswith(".json"):
            loader = JSONLoader(filepath)
        elif filename.endswith(".xlsx"):
            loader = UnstructuredExcelLoader(filepath)
        else:
            continue
        try:
            docs = loader.load()
            documents.extend(docs)
            shutil.move(filepath, os.path.join(PROCESSED_DIR, filename))
        except Exception as e:
            print(f"Failed to process {filename}: {e}")
    return documents

def save_embeddings_to_chroma(docs, model_name="llama2:7b"):
    #client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="/home/team-schick/chroma/"))
    client = chromadb.HttpClient(host="127.0.0.1", port=8002)
    collection = client.get_or_create_collection(name=f"rag_documents_{str(model_name).replace(":","-")}")
    embeddings = OllamaEmbeddings(model=model_name)
    
    for i, doc in enumerate(docs):
        try:
            text = doc.page_content
            metadata = doc.metadata
            vector = embeddings.embed_query(text)
            collection.add(documents=[text], embeddings=[vector], metadatas=[metadata], ids=[str(i)])
            print(f"Saved document content to collection {f"rag_documents_{str(model_name)}"}")
        except Exception as e:
            print(f"Failed to embed document {i}: {e}")

if __name__ == "__main__":
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    docs = load_documents()
    model="llama2:7b"
    #model="deepseek-r1-distill-llama-70b"
    if docs:
        print(f"Loaded {len(docs)} pages/documents.")
        save_embeddings_to_chroma(docs, model)
    else:
        print("No new documents found.")
        

