# 🇳🇵 AI Constitution of Nepal

An AI-powered legal assistant designed to help users explore and understand the **Constitution of Nepal** using modern Natural Language Processing and Retrieval-Augmented Generation (RAG).

This system allows anyone to ask questions in natural language and receive precise, context-based answers directly from the Constitution — including relevant articles and clauses.

---

## 🚀 What This Project Does

This AI does not guess or hallucinate.  
It answers only from the official Constitution text.

It works by:
1. Converting the Constitution into vector embeddings  
2. Storing them in a vector database  
3. Retrieving the most relevant articles for each query  
4. Using a language model to generate accurate legal answers  

---

## 🧠 System Architecture

User Question
↓
Embedding Model (Ollama / Sentence Transformers)
↓
Vector Database (Chroma / FAISS)
↓
Relevant Articles from Constitution
↓
LLM (GPT / LLaMA / Mistral)
↓
Final Answer with Legal Context


---

## 📚 Data Source

The complete **Constitution of Nepal (2015)** was used as the knowledge base.

The document was:
- Cleaned
- Chunked
- Embedded
- Stored for semantic search

---

## 🛠️ Tech Stack

- **LLM** – OpenAI / LLaMA / Mistral  
- **Embeddings** – Ollama / SentenceTransformers  
- **Vector Database** – ChromaDB / FAISS  
- **Backend** – Python  
- **Frontend (optional)** – Flask + HTML  

---

## 🧪 Example Questions

- “What are the fundamental rights of citizens?”
- “What does the constitution say about freedom of speech?”
- “How is the Prime Minister appointed?”
- “What is the role of the Supreme Court?”

The AI retrieves the relevant constitutional articles before answering.

---

## ⚖️ Why This Matters

Most legal chatbots:
- Guess answers
- Hallucinate laws
- Are unsafe

This system:
- Uses the actual Constitution
- Is fully auditable
- Is suitable for students, lawyers, and researchers

---

## 📂 How It Works

1. Constitution text is split into chunks  
2. Each chunk is converted to an embedding  
3. Stored in a vector database  
4. User queries are embedded  
5. Most relevant constitutional articles are retrieved  
6. LLM generates a legally grounded response  

---

## 🔧 How to Run

```bash
pip install -r requirements.txt
python ingest.py      # create constitution embeddings
python RagSetup.py         # start legal assistant
