import numpy as np
import faiss
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import sqlite3
from typing import List, Dict, Tuple

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_FILE = "chat_history.db"
EMBEDDING_DIM = 1536  # OpenAI's text-embedding-ada-002 dimension

def get_embedding(text: str) -> List[float]:
    """Get embedding for a text using OpenAI's API."""
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0.0] * EMBEDDING_DIM

def init_vector_db():
    """Initialize or load the FAISS index."""
    try:
        if os.path.exists("chat_embeddings.index"):
            return faiss.read_index("chat_embeddings.index")
        else:
            return faiss.IndexFlatL2(EMBEDDING_DIM)
    except Exception as e:
        print(f"Error initializing vector DB: {e}")
        return faiss.IndexFlatL2(EMBEDDING_DIM)

def append_message_to_vector_db(index, message: Dict[str, str]):
    """Append a single message to the vector database."""
    try:
        if message["role"] == "system":  # Skip system messages
            return

        # Get embedding for the new message
        embedding = get_embedding(message["content"])
        embedding_array = np.array([embedding]).astype('float32')
        
        # Add to index
        index.add(embedding_array)
        
        # Save index
        faiss.write_index(index, "chat_embeddings.index")
        
        # Update message mapping
        try:
            with open("message_mapping.json", "r") as f:
                messages = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            messages = []
        
        messages.append(message)
        with open("message_mapping.json", "w") as f:
            json.dump(messages, f)
    except Exception as e:
        print(f"Error appending message to vector DB: {e}")

def update_vector_db(index, messages: List[Dict[str, str]]):
    """Update the vector database with new messages."""
    try:
        # Get embeddings for all messages
        embeddings = []
        for msg in messages:
            if msg["role"] != "system":  # Skip system messages
                embedding = get_embedding(msg["content"])
                embeddings.append(embedding)
        
        if embeddings:
            embeddings_array = np.array(embeddings).astype('float32')
            index.add(embeddings_array)
            faiss.write_index(index, "chat_embeddings.index")
            with open("message_mapping.json", "w") as f:
                json.dump(messages, f)
    except Exception as e:
        print(f"Error updating vector DB: {e}")

def get_relevant_context(query: str, index, k: int = 3) -> List[str]:
    """Retrieve relevant context from chat history based on query similarity."""
    try:
        # Get query embedding
        query_embedding = get_embedding(query)
        query_array = np.array([query_embedding]).astype('float32')
        
        # Search for similar messages
        distances, indices = index.search(query_array, k)
        
        # Load message mapping
        with open("message_mapping.json", "r") as f:
            messages = json.load(f)
        
        # Get relevant messages
        relevant_messages = []
        for idx in indices[0]:
            if idx < len(messages):
                relevant_messages.append(messages[idx]["content"])
        
        return relevant_messages
    except Exception as e:
        print(f"Error getting relevant context: {e}")
        return []

def load_chat_history_for_rag() -> List[Dict[str, str]]:
    """Load chat history from SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT role, content FROM chat_history ORDER BY id')
        messages = [{"role": role, "content": content} for role, content in c.fetchall()]
        conn.close()
        return messages
    except Exception as e:
        print(f"Error loading chat history: {e}")
        return [] 