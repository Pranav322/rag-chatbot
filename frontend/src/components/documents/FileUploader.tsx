import React, { useCallback, useState } from 'react';
import { Upload, X, Loader2 } from 'lucide-react';
import api from '../../lib/api';
import { cn } from '../../lib/utils';
import type { UploadResponse } from '../../types';

interface FileUploaderProps {
    onUploadComplete: () => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onUploadComplete }) => {
    const [isDragOver, setIsDragOver] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    }, []);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            uploadFile(files[0]);
        }
    };

    const uploadFile = async (file: File) => {
        setUploading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            await api.post<UploadResponse>('/documents/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            onUploadComplete();
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to upload file');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="w-full">
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                    "relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-zinc-700 bg-zinc-800/50 p-12 text-center transition-colors",
                    isDragOver && "border-blue-500 bg-blue-500/10",
                    uploading && "opacity-50 pointer-events-none"
                )}
            >
                <input
                    type="file"
                    id="file-upload"
                    className="hidden"
                    onChange={handleFileSelect}
                    accept=".pdf,.docx,.png,.jpg,.jpeg"
                    disabled={uploading}
                />

                {uploading ? (
                    <div className="flex flex-col items-center gap-2">
                        <Loader2 className="h-10 w-10 animate-spin text-blue-500" />
                        <p className="text-sm text-zinc-400">Processing file... this may take up to a minute</p>
                    </div>
                ) : (
                    <>
                        <div className="mb-4 rounded-full bg-zinc-800 p-4">
                            <Upload className="h-8 w-8 text-zinc-400" />
                        </div>
                        <h3 className="mb-1 text-lg font-medium text-white">
                            Drop files here or click to upload
                        </h3>
                        <p className="mb-4 text-sm text-zinc-400">
                            PDF, DOCX, or Images (max 10MB)
                        </p>
                        <label
                            htmlFor="file-upload"
                            className="cursor-pointer rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
                        >
                            Select File
                        </label>
                    </>
                )}
            </div>

            {error && (
                <div className="mt-4 flex items-center justify-between rounded-lg bg-red-500/10 p-3 text-sm text-red-500">
                    <span>{error}</span>
                    <button onClick={() => setError(null)}><X className="h-4 w-4" /></button>
                </div>
            )}
        </div>
    );
};
