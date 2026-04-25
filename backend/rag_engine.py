import json
import time
import chromadb
from google import genai
from config import Config


gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 5  # seconds

chroma_client = chromadb.PersistentClient(path=Config.VECTOR_DB_PATH)
collection = chroma_client.get_or_create_collection(name="Constitution-of-Nepal-gemini")


def generate_embeddings(text: str):
    for attempt in range(MAX_RETRIES):
        try:
            response = gemini_client.models.embed_content(
                model="gemini-embedding-001",
                contents=text
            )
            return response.embeddings[0].values
        except Exception as e:
            if "429" in str(e) and attempt < MAX_RETRIES - 1:
                wait = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"Embedding rate limited, retrying in {wait}s (attempt {attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            print("Embedding Error:", e)
            return None


def chroma_search(query: str, top_k: int = 5):
    query_vector = generate_embeddings(query)
    if query_vector is None:
        return None
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas"]
    )
    return results


def get_answer(query: str) -> dict:
    """
    Main entry point.
    Returns {"summary": "...", "legal_references": "...", "title": "...", "is_legal": true/false}.
    Single Gemini call handles: answer + title + out-of-scope detection.
    """
    results = chroma_search(query)

    if not results or "documents" not in results or not results["documents"][0]:
        return {
            "summary": "No related context found for your question.",
            "legal_references": "",
            "title": query[:60],
            "is_legal": True
        }

    retrieved_docs = results["documents"][0]
    retrieved_metas = results["metadatas"][0]
    page_numbers = [meta.get("source") for meta in retrieved_metas]
    context = "\n\n".join(retrieved_docs)

    prompt = f"""You are an expert assistant specializing in the Constitution of Nepal.

First, determine if the user's question is related to Nepal's constitution, laws, legal system,
government structure, or any legal/constitutional topic of Nepal.

Return your answer as valid JSON with exactly four keys:

1. "is_legal" – true if the question is about Nepal law/constitution, false otherwise.

2. "title" – A very short title (max 6 words) summarizing the question for a chat sidebar.

3. "summary" – If is_legal is true: A clear, concise explanation in 3-6 sentences using simple
   English. Explain what the law means in plain language.
   If is_legal is false: Return exactly "I can only answer questions related to the Constitution and laws of Nepal. Please ask a legal question about Nepal's constitution, fundamental rights, government structure, or other constitutional provisions."

4. "legal_references" – If is_legal is true: A list of relevant constitutional provisions formatted
   as a readable string. Each provision on a new line in the form:
   • Article XX(YY): Short description
   Include page numbers {page_numbers} where applicable.
   If is_legal is false: Return empty string "".

RETRIEVED CONTEXT:
{context}

USER QUESTION:
{query}

Return ONLY the JSON object. No markdown fences, no extra text."""

    for attempt in range(MAX_RETRIES):
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
            parsed = json.loads(raw)
            return {
                "summary": parsed.get("summary", ""),
                "legal_references": parsed.get("legal_references", ""),
                "title": parsed.get("title", query[:60]),
                "is_legal": parsed.get("is_legal", True)
            }
        except json.JSONDecodeError:
            return {
                "summary": response.text,
                "legal_references": "",
                "title": query[:60],
                "is_legal": True
            }
        except Exception as e:
            if "429" in str(e) and attempt < MAX_RETRIES - 1:
                wait = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"Gemini rate limited, retrying in {wait}s (attempt {attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            print("RAG Error:", e)
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                return {
                    "summary": "The API quota has been exceeded. Please try again in a few minutes or contact the administrator.",
                    "legal_references": "",
                    "title": query[:60],
                    "is_legal": True
                }
            return {
                "summary": "The AI service is temporarily busy. Please wait a moment and try again.",
                "legal_references": "",
                "title": query[:60],
                "is_legal": True
            }
