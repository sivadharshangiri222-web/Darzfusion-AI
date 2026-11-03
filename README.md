# DARZFUSION AI

<div align="center">
  <img src="logo.png" alt="DARZFUSION AI Logo" width="120" />
  <h3>Production-Ready Multimodal Generative AI Intelligence Platform</h3>
</div>

---

## Overview

**DARZFUSION AI** is an advanced multimodal generative AI platform powered by **Google Gemini**, **ChromaDB**, **FastAPI**, and a reactive high-performance Single Page Application (SPA).

It delivers end-to-end intelligent capabilities:
- **Multimodal AI Chat:** Multi-turn conversations using Google Gemini (`gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`) with configurable temperature, token limits, and prompt engineering presets.
- **Document Intelligence (RAG):** Document processing (PDF, DOCX, TXT), intelligent page-tracked chunking, ChromaDB vector embedding retrieval, and sourced citation generation.
- **Live Web Research:** DuckDuckGo / Tavily real-time web search integration grounding Gemini responses with live URLs and publication dates.
- **Vision Intelligence:** Multimodal image comprehension, object detection, visual question answering, and OCR analysis.
- **Audio Intelligence:** Verbatim speech-to-text audio transcription and structured executive summaries with key takeaways and action items.
- **Active-Recall Study Suite:** Automated study notes, multi-choice quizzes with explanations, spaced-repetition flashcards, and analogy-driven concept breakdowns.
- **NLP & Prompt Engineering Lab:** Benchmarking for prompt styles (zero-shot, few-shot, role-based, structured JSON) and NLP analytics.
- **Dual Routing Architecture:** Full dual-routing at `/api/...` and `/api/v1/...` for flexible client connectivity.

---

## Project Structure

```
DARZFUSION AI/
├── index.html                   # High-performance Single Page Web Application
├── DARZFUSION AI (preview).html # Standalone offline preview application
├── logo.png                     # Application icon / brand logo
├── logo_full.jpg                # Full banner brand asset
├── vercel.json                  # Vercel deployment configuration & SPA rewrites
├── .gitignore                   # Production git ignore configuration
├── README.md                    # Root project documentation
└── backend/                     # Modular FastAPI Application
    ├── app/
    │   ├── main.py              # Application entrypoint & CORS middleware
    │   ├── core/                # App configuration & JWT security
    │   ├── api/                 # Modular API endpoints (auth, chat, rag, vision, etc.)
    │   ├── services/            # Gemini, ChromaDB, document, and search services
    │   ├── models/              # SQLAlchemy database models
    │   ├── schemas/             # Pydantic request/response schemas
    │   ├── database/            # Connection pooling and initialization
    │   └── static/              # Static frontend assets for monolithic serving
    ├── tests/                   # Automated pytest suite (38 unit & integration tests)
    ├── requirements.txt         # Python dependencies
    ├── pytest.ini               # Test configuration
    ├── .env.example             # Example environment variables
    └── README.md                # Dedicated backend documentation
```

---

## Quickstart (Local Development)

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and supply your GEMINI_API_KEY

# Run the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Run Automated Tests

DARZFUSION AI includes a complete automated test suite with 38 unit and integration tests:

```bash
cd backend
source venv/bin/activate
pytest
```

---

## Deployment

### Deploying Frontend to Vercel

The frontend is ready for zero-config Vercel deployment:

1. **Push this repository to GitHub:**
   ```bash
   git push -u origin main
   ```
2. **Import into Vercel:**
   - Log in to your [Vercel Dashboard](https://vercel.com/new).
   - Select **Add New...** > **Project**.
   - Select the **Darzfusion-AI** repository.
   - Leave the build settings as default (Framework Preset: **Other**, Output Directory: root).
   - Click **Deploy**.
3. **Connect API Endpoint:**
   - In `vercel.json`, you can optionally add a proxy rewrite to forward `/api/:path*` directly to your deployed backend URL.

### Deploying Backend to Render / Railway / Docker

Because ChromaDB and SQLite manage stateful vectors and databases, the backend is recommended to run on a container or server environment:

- **Render / Railway / Fly.io:** Set build command `pip install -r backend/requirements.txt` and start command `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`.
- Set environment variables:
  - `GEMINI_API_KEY`: Your Google Gemini API Key
  - `SECRET_KEY`: A secure 64+ character random string for JWT auth
  - `CORS_ORIGINS`: Your Vercel frontend URL (e.g. `https://your-darzfusion.vercel.app`)

---

## License

Proprietary - Developed for DARZFUSION AI.

