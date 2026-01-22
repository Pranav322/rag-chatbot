# RAG Chatbot Application

A production-ready RAG (Retrieval Augmented Generation) application featuring a Django backend and a React frontend. This system allows users to upload documents (PDF, DOCX, Images), process them using OCR and AI Vision, and chat with their content using advanced retrieval mechanisms.

## System Architecture

The project consists of two main components:

- **Backend**: Built with Django and Django REST Framework. Handles document processing, vector storage (PostgreSQL + pgvector), authentication (JWT), and the RAG pipeline.
- **Frontend**: Built with React, TypeScript, and Vite. Provides a modern user interface for file management and real-time chat.

## Key Features

- **JWT Authentication**: Secure user management with access and refresh tokens.
- **Cloud Storage**: Integration with Cloudinary for secure file storage.
- **Advanced Document Processing**:
  - Support for PDF, DOCX, and Image formats.
  - Intelligent OCR (Tesseract) and Vision API integration for extracting text from images.
- **RAG Pipeline**:
  - Semantic search using pgvector and OpenAI embeddings.
  - Context-aware responses powered by GPT-4.
  - Source tracking to cite documents used in answers.
- **Real-time Interaction**: Streaming chat responses for a responsive user experience.
- **Data Isolation**: Strict user-level isolation for all uploaded data and chat history.

## Prerequisites

Before running the application, ensure you have the following services available:

- Docker and Docker Compose (recommended for full stack execution)
- OpenAI API Key
- Cloudinary Credentials (Cloud Name, API Key, API Secret)
- PostgreSQL Database URL (if running locally without Docker)

## Quick Start (Docker)

The easiest way to run the entire application is using Docker Compose.

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd rag-chatbot
    ```

2.  **Configure Environment Variables**:
    Create a `.env` file in the root directory or ensure the `backend` directory has its `.env` configured. You will need to set the following variables:

    ```env
    DATABASE_URL=postgresql://user:pass@host:5432/db
    OPENAI_API_KEY=sk-...
    CLOUDINARY_CLOUD_NAME=...
    CLOUDINARY_API_KEY=...
    CLOUDINARY_API_SECRET=...
    DJANGO_SECRET_KEY=...
    ```

3.  **Run with Docker Compose**:
    ```bash
    docker-compose up --build
    ```

    The application will be accessible at:
    - Frontend: `http://localhost`
    - Backend API: `http://localhost:8000`

## Manual Installation

If you prefer to run the services individually, please refer to the README files in each directory:

- [Backend Documentation](backend/README.md) - Detailed setup for Python, Django, and Celery/Workers.
- [Frontend Documentation](frontend/README.md) - Setup for Node.js and React.

### Backend Setup Summary

1.  Navigate to `backend/`.
2.  Install dependencies using `uv` or `pip`.
3.  Configure `.env` file.
4.  Run migrations: `python manage.py migrate`.
5.  Start the server: `python manage.py runserver`.

### Frontend Setup Summary

1.  Navigate to `frontend/`.
2.  Install dependencies: `npm install`.
3.  Start the development server: `npm run dev`.

## Project Structure

- `backend/` - Django application code, API configuration, and RAG logic.
- `frontend/` - React application source code.
- `docker-compose.yml` - Orchestration for running the full stack.
