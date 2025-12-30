# RAG Backend API Documentation

**Base URL:** `http://localhost:8000/api`

> This documentation covers all endpoints needed to build a complete frontend application.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Documents & Assets](#documents--assets)
3. [Chat](#chat)
4. [Chat Streaming (SSE)](#chat-streaming-sse)
5. [Chat History](#chat-history)
6. [Error Handling](#error-handling)
7. [TypeScript Types](#typescript-types)

---

## Authentication

All endpoints (except auth) require a Bearer token in the header:

```http
Authorization: Bearer <access_token>
```

### Register User

**POST** `/auth/register`

Creates a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "yourpassword123",
  "confirm_password": "yourpassword123"
}
```

**Success Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "message": "User registered successfully"
}
```

**Error Response (400):**
```json
{
  "email": ["user with this email already exists."],
  "password": ["This field is required."]
}
```

---

### Login

**POST** `/auth/login`

Authenticates user and returns JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "yourpassword123"
}
```

**Success Response (200):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Token Lifetimes:**
- `access`: 1 hour
- `refresh`: 7 days

**Error Response (401):**
```json
{
  "detail": "No active account found with the given credentials"
}
```

---

### Refresh Token

**POST** `/auth/refresh`

Get a new access token using refresh token.

**Request Body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Response (401):**
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

## Documents & Assets

### Upload Document/Image

**POST** `/documents/upload`

Upload a PDF, DOCX, or image file. The file is stored in Cloudinary and processed for RAG.

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (FormData):**
```
file: <File> (PDF, DOCX, PNG, JPG, JPEG)
```

**JavaScript Example:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/documents/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});
```

**Success Response (201):**
```json
{
  "asset_id": "0fb6115c-eaad-4886-ad24-867fc4d7b4f3",
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "chunks_created": 5,
  "doc_type": "pdf",
  "cloudinary_url": "https://res.cloudinary.com/xxx/raw/upload/v123/rag_uploads/document.pdf",
  "message": "Successfully processed document with 5 chunks"
}
```

**For Images:**
```json
{
  "asset_id": "0fb6115c-eaad-4886-ad24-867fc4d7b4f3",
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "chunks_created": 1,
  "doc_type": "image",
  "cloudinary_url": "https://res.cloudinary.com/xxx/image/upload/v123/rag_uploads/photo.png",
  "message": "Successfully processed document with 1 chunks"
}
```

**Error Response (400):**
```json
{
  "error": "Unsupported file type. Allowed: pdf, docx, png, jpg, jpeg"
}
```

```json
{
  "error": "No content could be extracted from the file"
}
```

**Notes:**
- Supported types: `.pdf`, `.docx`, `.png`, `.jpg`, `.jpeg`
- Images are processed with OCR + AI Vision
- Maximum file size depends on your Cloudinary plan
- Processing may take 10-60 seconds for large files

---

### List Assets

**GET** `/assets`

Get all uploaded files for the authenticated user.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "assets": [
    {
      "id": "0fb6115c-eaad-4886-ad24-867fc4d7b4f3",
      "asset_type": "pdf",
      "cloudinary_url": "https://res.cloudinary.com/xxx/raw/upload/v123/rag_uploads/document.pdf",
      "original_filename": "my-document.pdf",
      "created_at": "2024-12-28T13:45:00.000Z"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "asset_type": "image",
      "cloudinary_url": "https://res.cloudinary.com/xxx/image/upload/v123/rag_uploads/photo.png",
      "original_filename": "test_image.png",
      "created_at": "2024-12-28T14:00:00.000Z"
    }
  ],
  "total": 2
}
```

**Asset Types:**
- `pdf` - PDF document
- `docx` - Word document
- `image` - PNG/JPG/JPEG image

---

### Delete Asset

**DELETE** `/assets/{asset_id}`

Delete an asset and all its associated chunks.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**URL Parameter:**
- `asset_id` (UUID) - The asset ID to delete

**Success Response (200):**
```json
{
  "message": "Asset deleted successfully"
}
```

**Error Response (404):**
```json
{
  "error": "Asset not found or access denied"
}
```

**Notes:**
- This also deletes the file from Cloudinary
- All document chunks are cascade deleted
- User can only delete their own assets

---

## Chat

### Send Message (Non-Streaming)

**POST** `/chat`

Send a chat message and get a complete response.

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "What is machine learning?",
  "session_id": "5a8726ef-6327-4717-9601-f78c1b676dae"  // Optional
}
```

**Success Response (200):**
```json
{
  "session_id": "5a8726ef-6327-4717-9601-f78c1b676dae",
  "answer": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed...",
  "used_context": true,
  "sources": [
    {
      "asset_id": "0fb6115c-eaad-4886-ad24-867fc4d7b4f3",
      "excerpt": "Machine learning algorithms build a model based on sample data..."
    },
    {
      "asset_id": "123e4567-e89b-12d3-a456-426614174000",
      "excerpt": "The primary aim is to allow computers to learn automatically..."
    }
  ]
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `session_id` | UUID | Chat session ID (use to continue conversation) |
| `answer` | string | AI-generated response |
| `used_context` | boolean | Whether user's documents were used |
| `sources` | array \| null | Source snippets if context was used |

**Source Object:**
| Field | Type | Description |
|-------|------|-------------|
| `asset_id` | UUID | ID of the source asset |
| `excerpt` | string | First 100 characters of the relevant chunk |

**Notes:**
- If `session_id` is omitted, a new session is created
- If `session_id` is provided, the conversation continues
- `sources` is only present when `used_context` is true

---

## Chat Streaming (SSE)

### Send Message (Streaming)

**POST** `/chat/stream`

Send a chat message and receive streaming response via Server-Sent Events.

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: text/event-stream
```

**Request Body:**
```json
{
  "message": "Explain quantum computing",
  "session_id": "5a8726ef-6327-4717-9601-f78c1b676dae"  // Optional
}
```

**Response:** `text/event-stream`

**Event Types:**

1. **Session Event** (sent first)
```
data: {"type": "session", "session_id": "5a8726ef-6327-4717-9601-f78c1b676dae"}
```

2. **Token Events** (streaming content)
```
data: {"type": "token", "content": "Quantum"}
data: {"type": "token", "content": " computing"}
data: {"type": "token", "content": " is"}
data: {"type": "token", "content": " a"}
...
```

3. **Done Event** (final, with metadata)
```
data: {"type": "done", "used_context": true, "sources": [...]}
```

4. **Error Event** (if something goes wrong)
```
data: {"type": "error", "message": "Failed to generate response"}
```

**JavaScript Example:**
```javascript
async function streamChat(message, sessionId, onToken, onDone) {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message, session_id: sessionId })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        if (data.type === 'session') {
          sessionId = data.session_id;
        } else if (data.type === 'token') {
          onToken(data.content);
        } else if (data.type === 'done') {
          onDone(data);
        } else if (data.type === 'error') {
          throw new Error(data.message);
        }
      }
    }
  }

  return sessionId;
}

// Usage
let content = '';
const sessionId = await streamChat(
  'What is AI?',
  null,
  (token) => {
    content += token;
    updateUI(content);  // Update your UI in real-time
  },
  (metadata) => {
    console.log('Used context:', metadata.used_context);
    console.log('Sources:', metadata.sources);
  }
);
```

**React Hook Example:**
```typescript
function useChatStream() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [content, setContent] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);

  const sendMessage = async (message: string) => {
    setIsStreaming(true);
    setContent('');

    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message, session_id: sessionId })
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const lines = decoder.decode(value).split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'session') {
            setSessionId(data.session_id);
          } else if (data.type === 'token') {
            setContent(prev => prev + data.content);
          } else if (data.type === 'done') {
            setIsStreaming(false);
          }
        }
      }
    }
  };

  return { sendMessage, content, isStreaming, sessionId };
}
```

---

## Chat History

### List Sessions

**GET** `/chat/sessions`

Get all chat sessions for the authenticated user.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "sessions": [
    {
      "id": "5a8726ef-6327-4717-9601-f78c1b676dae",
      "created_at": "2024-12-28T13:45:00.000Z",
      "updated_at": "2024-12-28T14:30:00.000Z",
      "message_count": 6,
      "last_message": "I'm here to help! Could you please let me know what..."
    },
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "created_at": "2024-12-27T10:00:00.000Z",
      "updated_at": "2024-12-27T10:15:00.000Z",
      "message_count": 4,
      "last_message": "Machine learning is a subset of artificial intelligence..."
    }
  ],
  "total": 2
}
```

**Session Object:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Session identifier |
| `created_at` | ISO8601 | When session started |
| `updated_at` | ISO8601 | Last message time |
| `message_count` | number | Total messages in session |
| `last_message` | string \| null | Preview of last message (100 chars) |

---

### Get Session Messages

**GET** `/chat/sessions/{session_id}`

Get full conversation history for a session.

**Headers:**
```http
Authorization: Bearer <access_token>
```

**URL Parameter:**
- `session_id` (UUID) - The session to retrieve

**Success Response (200):**
```json
{
  "id": "5a8726ef-6327-4717-9601-f78c1b676dae",
  "created_at": "2024-12-28T13:45:00.000Z",
  "updated_at": "2024-12-28T14:30:00.000Z",
  "messages": [
    {
      "id": "msg-001",
      "role": "user",
      "content": "Hello, this is my first message!",
      "used_context": false,
      "created_at": "2024-12-28T13:45:00.000Z"
    },
    {
      "id": "msg-002",
      "role": "assistant",
      "content": "Hello! Welcome! How can I assist you today?",
      "used_context": false,
      "created_at": "2024-12-28T13:45:02.000Z"
    },
    {
      "id": "msg-003",
      "role": "user",
      "content": "What's in my uploaded documents?",
      "used_context": false,
      "created_at": "2024-12-28T14:00:00.000Z"
    },
    {
      "id": "msg-004",
      "role": "assistant",
      "content": "Based on your uploaded documents, I found...",
      "used_context": true,
      "created_at": "2024-12-28T14:00:05.000Z"
    }
  ]
}
```

**Message Object:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Message identifier |
| `role` | "user" \| "assistant" | Who sent the message |
| `content` | string | Message content |
| `used_context` | boolean | Whether documents were used (only for assistant) |
| `created_at` | ISO8601 | When message was sent |

**Error Response (404):**
```json
{
  "error": "Session not found or access denied"
}
```

---

## Error Handling

### Standard Error Format

All error responses follow this format:

```json
{
  "error": "Brief error description",
  "detail": "More detailed explanation or validation errors"
}
```

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET, successful POST (chat) |
| 201 | Created | Successful registration, successful upload |
| 400 | Bad Request | Validation error, unsupported file type |
| 401 | Unauthorized | Missing/invalid/expired token |
| 404 | Not Found | Asset/session doesn't exist or not owned |
| 500 | Server Error | Unexpected error (check logs) |

### Common Errors

**Token Expired:**
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid or expired"
    }
  ]
}
```
➡️ Solution: Use `/auth/refresh` to get new access token

**File Too Large (Cloudinary):**
```json
{
  "error": "Upload failed",
  "detail": "File exceeds maximum allowed size"
}
```

**No Token Provided:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## TypeScript Types

```typescript
// ============ Auth Types ============

interface RegisterRequest {
  email: string;
  password: string;
  confirm_password: string;
}

interface RegisterResponse {
  id: string;
  email: string;
  message: string;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access: string;
  refresh: string;
}

interface RefreshRequest {
  refresh: string;
}

interface RefreshResponse {
  access: string;
  refresh: string;
}

// ============ Asset Types ============

type AssetType = 'pdf' | 'docx' | 'image';

interface Asset {
  id: string;
  asset_type: AssetType;
  cloudinary_url: string;
  original_filename: string;
  created_at: string;
}

interface AssetListResponse {
  assets: Asset[];
  total: number;
}

interface UploadResponse {
  asset_id: string;
  document_id: string;
  chunks_created: number;
  doc_type: string;
  cloudinary_url: string;
  message: string;
}

// ============ Chat Types ============

interface Source {
  asset_id: string;
  excerpt: string;
}

interface ChatRequest {
  message: string;
  session_id?: string;
}

interface ChatResponse {
  session_id: string;
  answer: string;
  used_context: boolean;
  sources?: Source[];
}

// ============ Streaming Types ============

interface StreamSessionEvent {
  type: 'session';
  session_id: string;
}

interface StreamTokenEvent {
  type: 'token';
  content: string;
}

interface StreamDoneEvent {
  type: 'done';
  used_context: boolean;
  sources?: Source[];
}

interface StreamErrorEvent {
  type: 'error';
  message: string;
}

type StreamEvent = 
  | StreamSessionEvent 
  | StreamTokenEvent 
  | StreamDoneEvent 
  | StreamErrorEvent;

// ============ Chat History Types ============

interface ChatSession {
  id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message: string | null;
}

interface ChatSessionListResponse {
  sessions: ChatSession[];
  total: number;
}

type MessageRole = 'user' | 'assistant';

interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  used_context: boolean;
  created_at: string;
}

interface ChatSessionDetail {
  id: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

// ============ Error Types ============

interface ApiError {
  error: string;
  detail?: string | Record<string, string[]>;
}
```

---

## Quick Reference

### Endpoints Summary

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | ❌ | Create account |
| POST | `/auth/login` | ❌ | Get tokens |
| POST | `/auth/refresh` | ❌ | Refresh token |
| POST | `/documents/upload` | ✅ | Upload file |
| GET | `/assets` | ✅ | List files |
| DELETE | `/assets/{id}` | ✅ | Delete file |
| POST | `/chat` | ✅ | Chat (complete) |
| POST | `/chat/stream` | ✅ | Chat (streaming) |
| GET | `/chat/sessions` | ✅ | List sessions |
| GET | `/chat/sessions/{id}` | ✅ | Get session |

### File Support

| Type | Extensions | Processing |
|------|------------|------------|
| PDF | `.pdf` | Text extraction |
| Word | `.docx` | Text extraction |
| Image | `.png`, `.jpg`, `.jpeg` | OCR + AI Vision |

---

## Notes for Frontend Developers

1. **Token Storage**: Store tokens securely (httpOnly cookies or secure storage)

2. **Token Refresh**: Implement automatic refresh when access token expires

3. **File Upload**: Use `FormData` for file uploads, not JSON

4. **Streaming**: Use `fetch` with `response.body.getReader()` for SSE

5. **Session Management**: Save `session_id` to continue conversations

6. **Error Handling**: Check `used_context` to show/hide sources section

7. **Loading States**: 
   - File upload: 10-60 seconds (large files)
   - Chat: 2-10 seconds
   - Streaming: Real-time tokens

8. **CORS**: Backend allows all origins in development

---

*Generated on 2024-12-28 | Django RAG Backend v1.0*
