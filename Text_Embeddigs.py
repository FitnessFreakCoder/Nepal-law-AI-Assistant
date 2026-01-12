import os
import json
from openai import OpenAI

import chromadb
import pandas as pd
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Read key from environment
Api_key = os.getenv("OPENAI_API_KEY")


# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="vector_db")
collection = chroma_client.get_or_create_collection(
    name="Constitution-of-Nepal",
    metadata={"hnsw:space": "cosine"}   # cosine distance best for embeddings
)

# OpenAI Client
client = OpenAI(api_key=Api_key)

print('Generating Embeddings.....')

Jsons = os.listdir('Json_text')

# Generate embedding
def Generate_embeddings(prompt):
    result = client.embeddings.create(
        input=prompt,
        model="text-embedding-3-large"
    )
    return result.data[0].embedding


for json_file in Jsons:
    

    with open(f'Json_text/{json_file}', 'r', encoding='utf-8') as f:
        content = json.load(f)

    print(f'Generating embeddings for {json_file}....')

    text = content['Text']     # The text you want to embed
    page_id = json_file.replace(".json", "")  # Example: "Page_001"

    embedding = Generate_embeddings(text)

    # --------------------------
    # ADD TO CHROMADB
    # --------------------------
    collection.add(
        ids=[page_id],                     # Unique ID
        embeddings=[embedding],            # Vector
        documents=[text],                  # Original text
        metadatas=[{"source": page_id}]    # Metadata (optional)
    )

   

    print(f"Stored → {page_id} | embedding size: {len(embedding)}")

print("\nAll embeddings saved to ChromaDB successfully!")


