"""
Re-index all documents from old OpenAI collection into a new Gemini-based collection.
Run once: python reindex_gemini.py
"""
import sys
import time
import chromadb
from google import genai
from config import Config

gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
chroma_client = chromadb.PersistentClient(path=Config.VECTOR_DB_PATH)

# Source (old OpenAI embeddings)
old_col = chroma_client.get_collection("Constitution-of-Nepal")

# Target (new Gemini embeddings)
new_col = chroma_client.get_or_create_collection("Constitution-of-Nepal-gemini")

# Check if already done
if new_col.count() > 0:
    print(f"Target collection already has {new_col.count()} docs. Skipping.")
    sys.exit(0)

# Get all documents from old collection
total = old_col.count()
print(f"Re-indexing {total} documents with Gemini embeddings...")

batch_size = 20
all_data = old_col.get(include=["documents", "metadatas"])

ids = all_data["ids"]
docs = all_data["documents"]
metas = all_data["metadatas"]

for i in range(0, total, batch_size):
    batch_ids = ids[i:i+batch_size]
    batch_docs = docs[i:i+batch_size]
    batch_metas = metas[i:i+batch_size]

    # Generate Gemini embeddings for batch
    embeddings = []
    for doc in batch_docs:
        try:
            resp = gemini_client.models.embed_content(
                model="gemini-embedding-001",
                contents=doc
            )
            embeddings.append(resp.embeddings[0].values)
        except Exception as e:
            print(f"  Error embedding doc: {e}")
            embeddings.append(None)
        time.sleep(0.1)  # Rate limit

    # Filter out failed embeddings
    valid = [(eid, edoc, emeta, emb) for eid, edoc, emeta, emb
             in zip(batch_ids, batch_docs, batch_metas, embeddings) if emb is not None]

    if valid:
        v_ids, v_docs, v_metas, v_embs = zip(*valid)
        new_col.add(
            ids=list(v_ids),
            documents=list(v_docs),
            metadatas=list(v_metas),
            embeddings=list(v_embs)
        )

    print(f"  Indexed {min(i+batch_size, total)}/{total}")

print(f"\n✅ Done! New collection has {new_col.count()} documents.")
