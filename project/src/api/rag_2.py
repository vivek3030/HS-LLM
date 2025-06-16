import os
import re
import logging
import time
import json
from functools import lru_cache
from time import perf_counter
from html import escape
import chromadb
import requests
from langdetect import DetectorFactory, detect
from langchain_ollama import OllamaEmbeddings
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Generator, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
DetectorFactory.seed = 0  # For consistent language detection

class Settings(BaseSettings):
    chroma_host: str = "127.0.0.1"
    chroma_port: int = 8002
    ollama_url: str = "http://localhost:11434"
    lmstudio_url: str = "http://localhost:1234"
    max_input_length: int = 2000
    min_context_distance: float = 0.35
    default_model: str = "llama4:latest"
    default_embedding_model: str = "llama2:7b"
    cache_size: int = 100
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

class Timer:
    def __enter__(self):
        self.start = perf_counter()
        return self
    
    def __exit__(self, *args):
        self.end = perf_counter()
        self.duration = self.end - self.start

def validate_input(text: str) -> str:
    if len(text.strip()) < 5:
        raise ValueError("Input too short (minimum 5 characters)")
    if len(text) > settings.max_input_length:
        raise ValueError(f"Input exceeds {settings.max_input_length} characters")
    return escape(text).strip()

def detect_language_safe(text: str, fallback: str = "en") -> str:
    try:
        return detect(text)
    except Exception as e:
        logger.warning(f"Language detection failed: {str(e)}")
        return fallback

@lru_cache(maxsize=settings.cache_size)
def get_relevant_context(query: str, top_k: int = 5) -> str:
    try:
        client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port
        )
        
        collection_name = f"rag_documents_{settings.default_embedding_model.replace(':', '-')}"
        collection = client.get_collection(collection_name)
        embeddings = OllamaEmbeddings(model=settings.default_embedding_model)
        
        with Timer() as t:
            query_vector = embeddings.embed_query(query)
        logger.info(f"Embedding generated in {t.duration:.2f}s")
        
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "distances"]
        )
        
        filtered = [
            doc for doc, distance in zip(results["documents"][0], results["distances"][0])
            if distance < settings.min_context_distance
        ]
        
        return " ".join(filtered) if filtered else ""
        
    except Exception as e:
        logger.error(f"Context retrieval failed: {str(e)}")
        return ""

def postprocess_response(response: str) -> str:
    response = re.sub(
        r'(?i)(Original:.*?)(\n*\s*Improved:)', 
        r'\1\n\n\n\2', 
        response, 
        flags=re.DOTALL
    )
    response = response.replace("**", "").replace("__", "")
    lines = [line.strip() for line in response.split("\n") if line.strip()]
    return "\n".join(lines)[:5000]

@lru_cache(maxsize=settings.cache_size)
def get_model_response(messages: tuple, model: str, temperature: float) -> str:
    """Cached model response for repeated queries"""
    return call_ollama([dict(m) for m in messages], model, temperature)

def call_ollama(messages: list, model: str, temperature: float = 0.3) -> str:
    try:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
            "options": {
                "num_gpu": 1,  # GPU offloading
                "num_thread": 8,  # Use more threads
                "quantization": "q4_0"  # 4-bit quantization
            }
        }
        
        with Timer() as t:
            response = requests.post(
                f"{settings.ollama_url}/api/chat",
                json=payload,
                timeout=120
            )
        response.raise_for_status()
        logger.info(f"Ollama response received in {t.duration:.2f}s")
        return response.json()["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama API call failed: {str(e)}")
        raise


def call_ollama_stream(messages: list, model: str, temperature: float):
    """Streaming response generator"""
    url = f"{settings.ollama_url}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
        "options": {
            "num_gpu": 1,
            "num_thread": 8,
            "quantization": "q4_0"
        }
    }
    
    try:
        with requests.post(url, json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    if 'message' in chunk and 'content' in chunk['message']:
                        yield chunk['message']['content']
    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        yield f"Error: {str(e)}"-r1

def create_efficient_prompt(lang: str, context: str, text: str) -> list:
    detected_lang = detect(lang) if len(lang) > 3 else lang.lower()

    # Determine whether to include German translation
    include_german = detected_lang not in ["de", "german"]

    system_content = (
        f"Rule: Strictly give answer in {lang} language. "
        f"This description describes the renovation and other work inside the house. These include: "
        f"- Wall design: painting, wallpapering, covering walls. "
        f"- Ceilings: painting, paneling, installing new ceiling constructions. "
        f"- Floors: laying new floor coverings such as parquet, laminate, tiles, carpet. "
        f"- Sanitary: replacement or renovation of bathtubs, showers, washbasins, toilets. "
        f"- Kitchen: replacement or renovation of kitchen furniture, appliances and worktops. "
        f"- Electrics: replacement or renovation of wiring, sockets, light switches. "
        f"- Heating: replacement or renovation of radiators and heating systems. "
        f"- Other work: repairing damage to walls, ceilings or floors, fitting new fixtures and fittings. "
        f"Correct errors in the texts. Improve the texts to make them easier to read. Use technical vocabulary from construction and interior design. "
        f"Always give your response in the selected {lang} language. "
        f"Do not give any explanation.\n"
        f"Format: 'Here is the Improved Version.'\n\nImproved: [text in {lang}]"
    )

    if include_german:
        system_content += "\n\nGerman Improved: [text in German]"

    system_content += f"\n\nContext: {context[:500]}"

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": text}
    ]

def should_use_full_model(text: str) -> bool:
    """Use small model for simple texts, full model for complex"""
    word_count = len(text.split())
    return word_count > 1 or any(char in text for char in ['@', '#', '$'])  # Complex indicators


def main(user_prompt: str, use_streaming=False, **kwargs) -> str:
    try:
        clean_prompt = validate_input(user_prompt)
        lang = detect_language_safe(clean_prompt, "en")
        
        # Context retrieval
        with Timer() as t:
            context = get_relevant_context(clean_prompt)
        logger.info(f"Context retrieved in {t.duration:.2f}s")
        
        # Model selection
        base_model = "mistral-small3.1:24b"
        if not should_use_full_model(clean_prompt):
            model = "llama4:latest"  
        else:
            model = kwargs.get('model', base_model)
        
        # Prompt creation
        messages = create_efficient_prompt(lang, context, clean_prompt)
        
        # Response handling
        temperature = kwargs.get('temperature', 0.3)
        
        if use_streaming:
            return call_ollama_stream(messages, model, temperature)
        else:
            return get_model_response(tuple((tuple(m.items()) for m in messages)), model, temperature)
    
    except ValidationError as e:
        return f"Validation error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
