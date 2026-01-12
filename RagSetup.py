from openai import OpenAI
import chromadb

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Read key from environment
Api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI Client
client = OpenAI(api_key=Api_key)

# Initialize Chroma Client
chroma_client = chromadb.PersistentClient(path="vector_db")

# Connect to your collection
collection = chroma_client.get_or_create_collection(
    name="Constitution-of-Nepal"
)
print("Connected to collection:", collection.name)


os.makedirs('Output', exist_ok=True)

# -----------------------------
# 1. Generate Embeddings
# -----------------------------
def generate_embeddings(text: str):
    try:
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print("Embedding Error:", e)
        return None


# -----------------------------
# 2. Search Similarity in Chroma
# -----------------------------
def chroma_search(query: str, top_k: int = 5):
    query_vector = generate_embeddings(query)

    if query_vector is None:
        return None

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas" ]

    )
   

    
    return results

print('Total Pages: ',collection.count())
# chroma_search('Right to freedom')

# -----------------------------
# 3. Generate RAG Answer
# -----------------------------
def rag_answer(query: str):
    results = chroma_search(query)

    if not results or "documents" not in results:
        return "No related context found."

    retrieved_docs = results["documents"][0]
    retrieved_metas = results["metadatas"][0]

    # *** FIXED HERE ***
    # extract page number from your metadata = {"source": page_id}
    page_numbers = [meta.get("source") for meta in retrieved_metas]

    context = "\n\n".join(retrieved_docs)

    prompt = f"""
You are an expert assistant specializing in the Constitution of Nepal.

Read the retrieved context and prepare a structured output in Nepali+English language with the following format:

-----------------------------------------------------
PAGE NUMBER : {page_numbers} 

Section: with {page_numbers} and section

Clause: with {page_numbers} and clause

📝 SUMMARY:
Provide a clear, concise summary of the retrieved text in 3-5 lines,
explaining the meaning in simple formal language.
Nepali language here
-----------------------------------------------------
English language here

### RETRIEVED CONTEXT:
{context}

### USER QUESTION:
{query}

Generate the output strictly in the structure above.
"""

    
    print('Wait for 5-10 Seconds')
    response = client.responses.create(
        model="gpt-5.1",
        input=prompt
    )

    return response.output_text


# -----------------------------
# 4. Test
# -----------------------------
if __name__ == "__main__":
    User_query = input('Ask Everything about Constitution of Nepal: ')
    answer = rag_answer(User_query)

    # print(answer)

    with open('Output/Response.txt', 'w' , encoding='utf-8') as f:
        f.write(answer)

    print('Response saved to Output/Response.txt')
