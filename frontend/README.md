# RAG Chatbot Frontend

The frontend interface for the RAG (Retrieval Augmented Generation) Chatbot system. Built with modern web technologies to provide a seamless user experience for document management and AI-powered interaction.

## Features

- **Chat Interface**: Real-time chat with streaming responses (Server-Sent Events).
- **Document Management**: Drag-and-drop file uploads (PDF, DOCX, Images) with processing status indicators.
- **Markdown Support**: Renders AI responses with formatted text and code blocks.
- **Authentication**: Secure login and registration flows with JWT integration.
- **Responsive Design**: Clean, modern UI built with Tailwind CSS.

## Tech Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS 4
- **Routing**: React Router DOM 7
- **HTTP Client**: Axios + Microsoft Fetch Event Source (for streaming)
- **Icons**: Lucide React
- **Markdown**: React Markdown

## Prerequisites

- Node.js (v18 or higher recommended)
- npm or yarn

## Installation

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

## Environment Configuration

Create a `.env` file in the `frontend` directory (or `.env.local`) to configure the connection to the backend API.

```env
VITE_API_URL=http://localhost:8000/api
```

- **VITE_API_URL**: The base URL for the Django backend API.

## Development

To start the development server with Hot Module Replacement (HMR):

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

## Building for Production

To create an optimized production build:

```bash
npm run build
```

The output files will be generated in the `dist` directory. You can preview the production build locally using:

```bash
npm run preview
```

## Project Structure

- `src/components`: Reusable UI components (Chat, Documents, Layouts).
- `src/context`: React Context providers (Authentication state).
- `src/lib`: Utility functions and API configuration.
- `src/pages`: Main application views (Chat, Documents, Login, Register).
- `src/types.ts`: TypeScript interfaces and type definitions.
