# 📚 RAG Document QA System

An intelligent document question-answering system based on **RAG (Retrieval-Augmented Generation)** architecture. Upload PDF, DOCX, or TXT files and ask questions using AI-powered semantic search.

---

## ✨ Features

* 📄 **Multi-format Upload** | Support PDF, DOCX, TXT files 
* 🔍 **Semantic Search** | Vector similarity search using pgvector
* 💬 **Multi-turn Conversation** | Follow-up questions like "what else", "tell me more"
* 📑 **Multi-document Q&A** | Select multiple documents for cross-document analysis
* 🎭 **Three Answer Modes** | Simple (one sentence) / Deep Thinking (detailed analysis) / Exact (original text)
* 🧠 **Conversation Memory** | Chat history stored in PostgreSQL |
* 🐳 **Docker Ready** | One-command deployment |

---

## 🛠 Tech Stack

| Layer            | Technology                   |
| ---------------- | ---------------------------- |
| Backend | FastAPI, Python 3.12+ |
| Frontend | React 18, TypeScript, TailwindCSS |
| Database | PostgreSQL 16 + pgvector |
| Cache | Redis 7.2 |
| Object Storage | MinIO (S3-compatible) |
| LLM Orchestration | LangChain |
| LLM Provider | Groq (Llama 3.3 70B) - Free |
| Embedding | Sentence Transformers (all-MiniLM-L6-v2) |

---

## 🚀 Quick Start

## 🐍 Requirements

* Docker & Docker Compose
* Python 3.12+
* Node.js 20+
* Groq API Key (free) → [console.groq.com](https://console.groq.com)

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/tuyi3008/rag-project.git
cd rag-project
```

---

### 2. Configure Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file in `backend/` directory:

```env
# Database
DATABASE_URL=postgresql+asyncpg://raguser:ragpass@localhost:5432/ragdb

# Redis
REDIS_URL=redis://localhost:6379

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Groq API (Required)
GROQ_API_KEY=your_groq_api_key_here
```

---

### 5. Start Services with Docker
```bash

docker-compose up -d
```

---


### 6. Setup Backend

```bash

cd backend
# Activate virtual environment
# On Windows: venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --reload --port 8000
```

### 7.  Setup Frontend

```bash

cd frontend
npm install
npm run dev
```

### 8. Open Browser

Frontend: http://localhost:5173

Backend API Docs: http://localhost:8000/docs

MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

---

## 📁 Project Structure

```text
rag-project/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── core/            # Config, database
│   │   ├── models/          # SQLAlchemy models
│   │   └── services/        # Business logic
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/      # React components
│       └── App.tsx
└── docker-compose.yml
```

---

## 🔄 System Architecture
```text
User → React Frontend (5173) → FastAPI Backend (8000)
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
                PostgreSQL       Redis            MinIO
                 (pgvector)      (Cache)          (Files)
                                      ↓
                                Groq LLM API
```


## 🎯 Use Cases

Resume vs Job Description - Upload both and ask "Does my resume match this JD?"

Multi-document Analysis - Compare contracts, reports, or research papers

Personal Knowledge Base - Build a Q&A system for your documents


## 🗄️ Database Schema

| Table | Purpose |
|-------|---------|
| `documents` | Document metadata (filename, size, status) |
| `document_chunks` | Text chunks with vector embeddings (384d) |
| `conversations` | Chat session metadata |
| `messages` | Conversation history (user + assistant) |


---

## 👨‍💻 Author

**Yi Tu**
Technological University Dublin, 2026