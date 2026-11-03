# DARZFUSION AI - Backend

**DARZFUSION AI** is a production-ready, modular multimodal Generative AI assistant backend built with **FastAPI**, **Google Gemini API**, **ChromaDB**, and **SQLAlchemy**.

It provides complete backend services for AI conversations, document question-answering (RAG), live web search grounding, image intelligence (multimodal vision), audio transcription and summarization, active-recall study tools (notes, quizzes, flashcards), and secure multi-user conversation management.

---

## 1. Key Capabilities

- **AI-Powered Conversations:** Multi-turn chat using Google Gemini models (`gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`) with configurable temperature, token limits, and system instructions.
- **Document Intelligence & RAG:** Upload PDFs, TXTs, and DOCXs. Extracts text, normalizes whitespace, chunks text with overlap and page tracking, embeds into ChromaDB vector database, and generates citations grounded in source pages.
- **Live Web Research:** Integrated real search provider (defaulting to zero-config DuckDuckGo, with support for Tavily and SerpAPI) that feeds live search results to Gemini for grounded answers with URLs and publication dates.
- **Image Intelligence (Vision):** Multimodal image understanding and visual question answering supporting PNG, JPEG, WebP, and GIF.
- **Audio Intelligence:** Verbatim speech-to-text transcription and structured executive audio summaries (key takeaways and action items).
- **AI Study Tools:** High-yield text summarization, Markdown study notes, automated multiple-choice quiz generation with answer keys, spaced-repetition flashcards, and concept explanations with real-world analogies.
- **Prompt Engineering Lab & NLP Toolkit:** Benchmarking for prompt techniques (zero-shot, few-shot, role-based, structured output, step-by-step) and text utilities (NER, keywords, stats, preprocessing).
- **Authentication & Security:** JWT tokens, bcrypt password hashing, cross-user data isolation on documents and conversation history, safe file handling against path traversal.
- **Dual API Routing:** All endpoints are exposed on both `/api/...` and `/api/v1/...` to seamlessly connect with frontend clients without modification.

---

## 2. Technology Stack

| Component | Technology |
|---|---|
| **Language** | Python 3.9+ |
| **Framework** | FastAPI & Uvicorn |
| **Generative AI** | Google Gemini API (`google-generativeai`) |
| **Vector Database** | ChromaDB (Cosine similarity HNSW index) |
| **Relational Database** | SQLite (development) / PostgreSQL (production via SQLAlchemy) |
| **Authentication** | JWT (PyJWT) + Bcrypt password hashing |
| **Document Processing** | PyMuPDF (fitz) for PDF, python-docx for DOCX |
| **Web Search** | DuckDuckGo Search (`duckduckgo-search`), Tavily, SerpAPI |
| **Testing** | pytest & pytest-asyncio (38 automated unit & integration tests) |

---

## 3. Directory Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI application entrypoint & middleware
│   ├── core/
│   │   ├── config.py            # Pydantic Settings & environment validation
│   │   └── security.py          # Bcrypt hashing & PyJWT token handling
│   ├── api/
│   │   ├── auth.py              # User registration, login, profile
│   │   ├── chat.py              # Gemini chat & model endpoints
│   │   ├── documents.py         # File upload, parsing, deletion
│   │   ├── rag.py               # ChromaDB retrieval & RAG query
│   │   ├── search.py            # Live web research API
│   │   ├── vision.py            # Multimodal image analysis
│   │   ├── audio.py             # Audio transcription & summarization
│   │   ├── study_tools.py       # Summaries, notes, quizzes, flashcards
│   │   ├── history.py           # Conversation history CRUD & isolation
│   │   ├── prompt_lab.py        # Prompt engineering lab & capabilities
│   │   ├── nlp.py               # NLP utilities (NER, keywords, stats)
│   │   └── evaluation.py        # Retrieval and answer quality benchmarks
│   ├── services/
│   │   ├── gemini_service.py    # Google Gemini client wrapper
│   │   ├── embedding_service.py # Gemini embeddings with offline fallback
│   │   ├── document_service.py  # Text extraction & page chunking
│   │   ├── rag_service.py       # ChromaDB vector indexing & retrieval
│   │   ├── web_search_service.py# Web search engine integration
│   │   ├── vision_service.py    # Multimodal image service
│   │   ├── audio_service.py     # Speech-to-text & summarization
│   │   ├── study_service.py     # Educational tool algorithms
│   │   └── nlp_service.py       # NLP algorithms and text statistics
│   ├── models/
│   │   ├── user.py              # User SQLAlchemy model
│   │   ├── conversation.py      # Conversation & Message models
│   │   └── document.py          # Document metadata model
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── database/
│   │   ├── connection.py        # SQLAlchemy engine & session factory
│   │   └── initialization.py    # Table auto-creation routines
│   └── utils/
├── tests/                       # Complete pytest suite (38 tests)
├── uploads/                     # Upload storage directory
├── chroma_db/                   # ChromaDB persistent vector data
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
└── README.md
```

---

## 4. Local Installation & Setup

### Prerequisites
- Python 3.9, 3.10, 3.11, or 3.12
- Git

### Step-by-Step Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Google Gemini API key:
   ```ini
   GEMINI_API_KEY=your_actual_gemini_api_key
   ```

5. **Start the development server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access Interactive Documentation:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - Health check: `http://localhost:8000/health`

---

## 5. API Endpoints Reference

All endpoints are reachable under both `/api/{endpoint}` and `/api/v1/{endpoint}`:

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/health` | Application health status | No |
| `GET` | `/health/services` | Detailed status of external AI & DB services | No |
| `POST` | `/api/auth/register` | Register a new user | No |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT token | No |
| `GET` | `/api/auth/me` | Get authenticated user profile | Yes |
| `GET` | `/api/models` | List available Gemini models | No |
| `POST` | `/api/chat` | Send message and receive context-aware response | Optional (Guest/User) |
| `POST` | `/api/chat/feedback` | Record message thumbs-up/down feedback | No |
| `POST` | `/api/documents/upload` | Upload PDF, TXT, or DOCX and index into ChromaDB | Optional (Guest/User) |
| `GET` | `/api/documents` | List uploaded documents for user | Optional (Guest/User) |
| `GET` | `/api/documents/{id}` | Get document metadata (ownership enforced) | Optional (Guest/User) |
| `DELETE`| `/api/documents/{id}` | Delete document and remove ChromaDB vectors | Optional (Guest/User) |
| `POST` | `/api/rag/query` | Ask question answered from indexed documents | Optional (Guest/User) |
| `POST` | `/api/search` | Live web research with citations | No |
| `POST` | `/api/vision/analyze` | Upload image and ask visual questions | No |
| `POST` | `/api/audio/transcribe`| Verbatim audio transcription | No |
| `POST` | `/api/audio/summarize` | Audio summary with key takeaways & actions | No |
| `POST` | `/api/study/summarize` | Summarize long text (short/medium/long) | No |
| `POST` | `/api/study/notes` | Generate structured Markdown study notes | No |
| `POST` | `/api/study/quiz` | Generate multiple-choice quiz with answer keys | No |
| `POST` | `/api/study/flashcards`| Generate flashcard study deck (front/back/hint)| No |
| `POST` | `/api/study/explain` | Concept explainer with analogies | No |
| `GET` | `/api/history` | List saved conversations | Optional (Guest/User) |
| `POST` | `/api/history` | Create new conversation session | Optional (Guest/User) |
| `GET` | `/api/history/{id}` | Get conversation messages (ownership enforced)| Optional (Guest/User) |
| `PATCH` | `/api/history/{id}` | Rename conversation (ownership enforced) | Optional (Guest/User) |
| `DELETE`| `/api/history/{id}` | Delete conversation (ownership enforced) | Optional (Guest/User) |
| `DELETE`| `/api/history/{id}/clear`| Clear messages in conversation | Optional (Guest/User) |
| `GET` | `/api/prompt/capabilities`| Check temperature/token capabilities | No |
| `POST` | `/api/prompt/run` | Run prompt engineering techniques | No |
| `POST` | `/api/nlp/run` | NLP tools (summarize, keywords, NER, stats) | No |
| `POST` | `/api/evaluation/run` | Benchmark answer relevance & groundedness | No |
| `GET` | `/api/evaluation/history`| View historical benchmark scores | No |

---

## 6. Running Automated Tests

Run the full pytest suite:

```bash
cd backend
source venv/bin/activate
pytest -v
```

All 38 tests run against an in-memory database with mocked external AI calls, so the test suite runs in under 6 seconds without incurring API costs.

---

## 7. Manual Integration Testing with Real Gemini API

To test live external AI services with your actual Gemini API key:

1. Obtain an API key from Google AI Studio: [https://aistudio.google.com/](https://aistudio.google.com/)
2. Set `GEMINI_API_KEY=AIzaSy...` in `backend/.env`.
3. Start the server:
   ```bash
   uvicorn app.main:app --port 8000
   ```
4. Open Swagger UI at `http://localhost:8000/docs`.
5. Try the endpoints:
   - **Chat:** Call `POST /api/chat` with `{"message": "Hello DARZFUSION AI!"}`
   - **Document RAG:** Call `POST /api/documents/upload` with a PDF or TXT file, then `POST /api/rag/query` with a question about the document content.
   - **Web Search:** Call `POST /api/search` with `{"query": "Latest breakthroughs in AI 2026"}`.
   - **Vision:** Upload an image at `POST /api/vision/analyze`.
   - **Study Tools:** Call `POST /api/study/quiz` with educational text.

---

## 8. Deployment on Render

This backend is pre-configured for seamless deployment to **Render** as a Web Service.

### Render Configuration

1. **Create Web Service on Render:**
   - Connect your GitHub repository.
   - Root Directory: `backend`
   - Environment: `Python 3`
   - Build Command:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - Start Command:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

2. **Environment Variables in Render Dashboard:**
   - `PORT`: Automatically set by Render (handled dynamically by our code).
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `SECRET_KEY`: A strong 64-character random string for JWT signing.
   - `DATABASE_URL`:
     - For production persistence, provision a **Render PostgreSQL database** and set `DATABASE_URL=postgresql://...`
     - If using SQLite, attach a **Persistent Disk** on Render (e.g. mounted at `/var/data`) and configure:
       ```ini
       DATABASE_URL=sqlite:////var/data/darzfusion.db
       CHROMA_PERSIST_DIRECTORY=/var/data/chroma_db
       UPLOAD_DIR=/var/data/uploads
       ```
   - `CORS_ORIGINS`: Your deployed frontend URL (e.g. `https://your-frontend.onrender.com` or `*`).

3. **Persistent Storage Requirements:**
   - **Uploads & ChromaDB:** Containers on Render have ephemeral filesystems by default. To retain uploaded documents and indexed vector embeddings across restarts, mount a Render Disk and point `CHROMA_PERSIST_DIRECTORY` and `UPLOAD_DIR` to the disk mount point.
   - **Database:** Connect to a managed PostgreSQL database on Render for zero-maintenance persistent relational storage.
