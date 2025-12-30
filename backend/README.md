# RAG Backend with Django

A production-ready RAG (Retrieval Augmented Generation) backend built with Django, featuring JWT authentication, Cloudinary storage, OCR + Vision processing, chat history, and streaming responses.

## Features

- 🔐 **JWT Authentication** - Secure email-based auth with access/refresh tokens
- ☁️ **Cloudinary Storage** - No local file storage, everything on cloud
- 📄 **Multi-format Support** - PDF, DOCX, PNG, JPG, JPEG
- 🖼️ **Smart Image Processing** - OCR with conditional AI Vision
- 💬 **Chat History** - Persistent sessions and messages
- 📚 **Source Tracking** - Know which documents were used in responses
- 🌊 **Streaming Responses** - Real-time token streaming with SSE
- 🔒 **User Isolation** - Users can only access their own data

---

## How It Works

### 📤 Document Upload Pipeline

```
User uploads file
       │
       ▼
┌─────────────────────────────────────────────────┐
│  1. Upload to Cloudinary (no local storage)     │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  2. Detect file type                            │
│     ├─ PDF/DOCX → Text extraction               │
│     └─ Image → OCR + Vision pipeline            │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  3. Chunk text (500 chars, 50 overlap)          │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  4. Generate embeddings (all-MiniLM-L6-v2)      │
│     384-dimensional vectors                     │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  5. Store in PostgreSQL + pgvector              │
└─────────────────────────────────────────────────┘
```

---

### 🖼️ Image Processing (OCR + Vision)

When you upload an image, the system intelligently decides whether to use just OCR or also call the Vision API:

```
Image uploaded
       │
       ▼
┌─────────────────────────────────────────────────┐
│  1. Resize if > 2000px (prevent timeout)        │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  2. Run Tesseract OCR                           │
│     Extract text + compute quality signals:     │
│     • confidence (avg OCR confidence)           │
│     • text_coverage (% of image with text)      │
│     • box_density (text boxes per area)         │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  3. Check if Vision API needed                  │
│     TRIGGERS if ANY of:                         │
│     • text_coverage < 0.1 (sparse text)         │
│     • box_density < 0.05 (few text regions)     │
│     • confidence < 50 (low OCR quality)         │
└─────────────────────────────────────────────────┘
       │
       ├─── NO → Use OCR text only
       │
       └─── YES ───▶ Call GPT-4o-mini Vision API
                           │
                           ▼
                    ┌─────────────────────────┐
                    │ "Describe this image    │
                    │  concisely for search"  │
                    └─────────────────────────┘
                           │
                           ▼
                    Merge: Vision description + OCR text
```

**Example:**
- 📄 Scanned document with clear text → OCR only (fast, cheap)
- 🏞️ Photo with minimal text → Vision API called (gets AI description)
- 📊 Chart/diagram → Vision API called (describes visual content)

---

### 💬 Chat Query Classification

When a user sends a message, the system first classifies the query to decide whether to retrieve documents:

```
User message received
       │
       ▼
┌─────────────────────────────────────────────────┐
│  Query Classifier (LLM-based)                   │
│                                                 │
│  Classifies into one of:                        │
│  • DOCUMENT_QUERY - needs user's documents      │
│  • GENERAL_KNOWLEDGE - can answer directly      │
│  • GREETING - simple greeting/chitchat          │
│  • CLARIFICATION - needs more info from user    │
└─────────────────────────────────────────────────┘
       │
       ▼
   Needs retrieval?
       │
       ├─── NO (greeting/general) ───▶ Answer directly
       │
       └─── YES (document query) ───▶ Retrieve context
```

**Examples:**
| Query | Classification | Retrieves Docs? |
|-------|---------------|-----------------|
| "Hello!" | GREETING | ❌ No |
| "What is Python?" | GENERAL_KNOWLEDGE | ❌ No |
| "What's in my documents?" | DOCUMENT_QUERY | ✅ Yes |
| "Summarize my uploaded PDF" | DOCUMENT_QUERY | ✅ Yes |

---

### 🔍 RAG Pipeline (Retrieval + Generation)

When documents need to be retrieved:

```
Query classified as DOCUMENT_QUERY
       │
       ▼
┌─────────────────────────────────────────────────┐
│  1. EMBED the query                             │
│     Same model: all-MiniLM-L6-v2                │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  2. VECTOR SEARCH (pgvector)                    │
│     • Cosine similarity search                  │
│     • Filter by user_id (isolation)             │
│     • Return top-k chunks (default: 8)          │
│     • Threshold: similarity > 0.25              │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  3. CHECK relevance                             │
│     If no chunks above threshold:               │
│     → used_context = false                      │
│     → Answer without documents                  │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  4. FORMAT context                              │
│     Combine top chunks into prompt:             │
│     "Based on these documents: {chunks}"        │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  5. GENERATE answer (GPT-4)                     │
│     System prompt + context + question          │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  6. EXTRACT sources                             │
│     Top 3 chunks → asset_id + excerpt           │
└─────────────────────────────────────────────────┘
       │
       ▼
Return: { answer, used_context, sources, session_id }
```

---

### 📊 Response Structure

```json
{
  "session_id": "abc123...",
  "answer": "Based on your documents...",
  "used_context": true,
  "sources": [
    {
      "asset_id": "0fb6115c-eaad...",
      "excerpt": "First 100 chars of the relevant chunk..."
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `session_id` | Unique conversation ID (use to continue chat) |
| `answer` | AI-generated response |
| `used_context` | `true` if your documents were used |
| `sources` | Which documents contributed (when used_context=true) |

---

### 🗑️ Asset Deletion (Cascade)

When you delete an asset, everything is cleaned up:

```
DELETE /api/assets/{id}
       │
       ├─→ Delete from Cloudinary ☁️
       │
       └─→ Delete Asset from database
            │
            └─→ CASCADE: All DocumentChunks deleted
                 (embeddings removed from pgvector)
```

---

### 🔐 User Isolation

Every query is scoped to the authenticated user:

- **Uploads**: `asset.user = request.user`
- **Retrieval**: `WHERE user_id = current_user.id`
- **Chat sessions**: `session.user = request.user`
- **Asset list**: `Asset.objects.filter(user=request.user)`

Users can **never** see or query other users' data.

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL with pgvector extension (or Neon)
- Tesseract OCR
- Cloudinary account (free tier works)
- OpenAI API key

### Install Tesseract OCR

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

---

## Installation

### Option 1: Using UV (Recommended) ⚡

[UV](https://github.com/astral-sh/uv) is a fast Python package manager. This is the recommended way.

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repo
git clone <your-repo-url>
cd backend

# Create virtual environment and install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env

# Run migrations
uv run python manage.py migrate

# Create superuser (for admin panel)
uv run python manage.py createsuperuser

# Start server
uv run uvicorn config.asgi:application --reload --port 8000
```

### Option 2: Using pip + requirements.txt

```bash
# Clone the repo
git clone <your-repo-url>
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env

# Run migrations
python manage.py migrate

# Create superuser (for admin panel)
python manage.py createsuperuser

# Start server
uvicorn config.asgi:application --reload --port 8000
```

---

## Environment Variables

Create a `.env` file in the backend folder:

```env
# Django
SECRET_KEY=your-super-secret-key-here
DEBUG=True

# Database (PostgreSQL with pgvector)
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Cloudinary (get from cloudinary.com dashboard)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# JWT Token Lifetimes (optional)
JWT_ACCESS_HOURS=1
JWT_REFRESH_DAYS=7

# OCR Thresholds (optional - defaults work well)
OCR_TEXT_COVERAGE_THRESHOLD=0.1
OCR_BOX_DENSITY_THRESHOLD=0.05
OCR_CONFIDENCE_THRESHOLD=50
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, get tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| POST | `/api/documents/upload` | Upload PDF/DOCX/Image |
| GET | `/api/assets` | List user's assets |
| DELETE | `/api/assets/{id}` | Delete asset |
| POST | `/api/chat` | Chat (non-streaming) |
| POST | `/api/chat/stream` | Chat (streaming SSE) |
| GET | `/api/chat/sessions` | List chat sessions |
| GET | `/api/chat/sessions/{id}` | Get session messages |

📖 **Full API documentation:** See `API_DOCUMENTATION.md`

---

## Usage Examples

### Register and Login

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123", "confirm_password": "pass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'
```

### Upload a Document

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@document.pdf"
```

### Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is in my documents?"}'
```

---

## Admin Panel

Access the Django admin at: `http://localhost:8000/admin`

Login with your superuser credentials to:
- View/manage users
- Browse uploaded assets (with image previews)
- Inspect document chunks
- View chat sessions and messages

---

## Project Structure

```
backend/
├── accounts/           # User authentication
│   ├── models.py      # Custom User model
│   ├── views.py       # Register view
│   └── serializers.py
├── rag/               # RAG functionality
│   ├── models.py      # Asset, DocumentChunk, ChatSession, ChatMessage
│   ├── views.py       # All API views
│   ├── serializers.py
│   ├── admin.py       # Admin configuration
│   ├── pipeline/      # RAG pipeline
│   │   ├── retriever.py
│   │   ├── generator.py
│   │   └── query_classifier.py
│   └── services/      # External services
│       ├── llm.py            # OpenAI integration
│       ├── embeddings.py     # Sentence transformers
│       ├── cloudinary_service.py
│       ├── ocr_service.py    # Tesseract OCR
│       ├── vision_service.py # GPT-4 Vision
│       └── image_processor.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py
├── .env.example
├── pyproject.toml
├── requirements.txt
└── API_DOCUMENTATION.md
```

---

## Development

### Database Migrations

```bash
# Using uv
uv run python manage.py makemigrations
uv run python manage.py migrate

# Using pip
python manage.py makemigrations
python manage.py migrate
```

### Collect Static Files (for production)

```bash
# Using uv
uv run python manage.py collectstatic --noinput

# Using pip
python manage.py collectstatic --noinput
```

---

## Deployment

### Environment Variables for Production

```env
DEBUG=False
SECRET_KEY=<generate-a-strong-key>
ALLOWED_HOSTS=your-domain.com
CORS_ALLOWED_ORIGINS=https://your-frontend.com
```

### Recommended Platforms

- **Railway** - Easy Django deployment
- **Render** - Free tier available
- **Fly.io** - Global edge deployment
- **AWS/GCP** - Enterprise scale

---

## Tech Stack

- **Framework:** Django 5.1 + Django REST Framework
- **Async:** ADRF (Async Django REST Framework)
- **Database:** PostgreSQL with pgvector
- **Auth:** djangorestframework-simplejwt
- **Storage:** Cloudinary
- **AI:** OpenAI GPT-4
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- **OCR:** Tesseract
- **Server:** Uvicorn (ASGI)

---

## License

MIT

---

## Contributing

PRs welcome! Please ensure all tests pass before submitting.
