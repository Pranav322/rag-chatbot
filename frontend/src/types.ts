export interface User {
    id: string;
    email: string;
}

export interface AuthResponse {
    access: string;
    refresh: string;
}

export type AssetType = 'pdf' | 'docx' | 'image';

export interface Asset {
    id: string;
    asset_type: AssetType;
    cloudinary_url: string;
    original_filename: string;
    created_at: string;
}

export interface UploadResponse {
    asset_id: string;
    document_id: string;
    chunks_created: number;
    doc_type: string;
    cloudinary_url: string;
    message: string;
}

export interface ChatSession {
    id: string;
    created_at: string;
    updated_at: string;
    message_count: number;
    last_message: string | null;
}

export interface Source {
    asset_id: string;
    excerpt: string;
}

export interface ChatResponse {
    session_id: string;
    answer: string;
    used_context: boolean;
    sources?: Source[];
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    used_context: boolean;
    created_at: string;
    sources?: Source[];
}
