import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, StopCircle, Bot } from 'lucide-react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useAuth } from '../../context/AuthContext';
import { MessageBubble } from './MessageBubble';
import type { ChatMessage, Source } from '../../types';
import api from '../../lib/api';

export const ChatWindow = () => {
    const { sessionId: routeSessionId } = useParams();
    const navigate = useNavigate();
    const { accessToken } = useAuth();

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(routeSessionId || null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    // Initialize session or load messages
    useEffect(() => {
        if (routeSessionId) {
            setCurrentSessionId(routeSessionId);
            loadMessages(routeSessionId);
        } else {
            setMessages([]);
            setCurrentSessionId(null);
        }
    }, [routeSessionId]);

    const loadMessages = async (id: string) => {
        try {
            const response = await api.get(`/chat/sessions/${id}`);
            setMessages(response.data.messages);
        } catch (error) {
            console.error('Failed to load messages', error);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: ChatMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            used_context: false,
            created_at: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        const botMessageId = (Date.now() + 1).toString();
        setMessages((prev) => [
            ...prev,
            {
                id: botMessageId,
                role: 'assistant',
                content: '',
                used_context: false,
                created_at: new Date().toISOString(),
            },
        ]);

        abortControllerRef.current = new AbortController();

        try {
            let finalContent = '';
            let usedContext = false;
            let sources: Source[] = [];
            let newSessionId = currentSessionId;

            await fetchEventSource(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`,
                    'Accept': 'text/event-stream',
                },
                body: JSON.stringify({
                    message: userMessage.content,
                    ...(currentSessionId && { session_id: currentSessionId }),
                }),
                signal: abortControllerRef.current.signal,
                onopen(response) {
                    if (response.ok) {
                        return Promise.resolve();
                    }
                    throw new Error(`Failed to send message: ${response.statusText}`);
                },
                onmessage(msg) {
                    if (msg.event === 'close') {
                        // connection closed
                        return;
                    }

                    try {
                        const data = JSON.parse(msg.data);

                        if (data.type === 'session') {
                            newSessionId = data.session_id;
                        } else if (data.type === 'token') {
                            finalContent += data.content;
                            setMessages((prev) =>
                                prev.map((m) =>
                                    m.id === botMessageId ? { ...m, content: finalContent } : m
                                )
                            );
                        } else if (data.type === 'done') {
                            usedContext = data.used_context;
                            sources = data.sources;

                            setMessages((prev) =>
                                prev.map((m) =>
                                    m.id === botMessageId
                                        ? { ...m, used_context: usedContext, sources: sources }
                                        : m
                                )
                            );
                        } else if (data.type === 'error') {
                            throw new Error(data.message);
                        }
                    } catch (e) {
                        console.error('Error parsing stream', e);
                    }
                },
                onerror(err) {
                    console.error('Stream error', err);
                    throw err;
                }
            });

            // After stream complete
            if (!currentSessionId && newSessionId) {
                // If this was a new chat, navigate to the session URL so history works
                navigate(`/chat/${newSessionId}`, { replace: true });
                setCurrentSessionId(newSessionId);
            }

        } catch (error) {
            console.error('Chat error', error);
            setMessages((prev) =>
                prev.map((m) =>
                    m.id === botMessageId
                        ? { ...m, content: m.content + '\n\n*[Error generating response]*' }
                        : m
                )
            );
        } finally {
            setIsLoading(false);
            abortControllerRef.current = null;
        }
    };

    const handleStop = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-full flex-col bg-zinc-950">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-10">
                <div className="mx-auto max-w-3xl space-y-6">
                    {messages.length === 0 ? (
                        <div className="mt-20 flex flex-col items-center justify-center text-center text-zinc-500">
                            <div className="mb-4 rounded-full bg-zinc-900 p-4">
                                <Bot className="h-10 w-10 text-white" />
                            </div>
                            <h2 className="text-xl font-medium text-white">How can I help you today?</h2>
                            <p className="mt-2 max-w-sm text-sm">
                                Upload documents to give me contexts, or just ask me anything.
                            </p>
                        </div>
                    ) : (
                        messages.map((msg) => (
                            <MessageBubble key={msg.id} message={msg} />
                        ))
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <div className="border-t border-zinc-800 bg-zinc-950 p-4 pb-6">
                <div className="mx-auto max-w-3xl">
                    <form onSubmit={handleSend} className="relative flex items-end gap-2 rounded-xl border border-zinc-800 bg-zinc-900 p-2 shadow-lg transition-colors focus-within:border-zinc-700">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Message..."
                            className="max-h-32 min-h-[44px] w-full resize-none bg-transparent px-3 py-2.5 text-white placeholder-zinc-500 focus:outline-none"
                            disabled={isLoading}
                        />
                        <div className="pb-1 pr-1">
                            {isLoading ? (
                                <button
                                    type="button"
                                    onClick={handleStop}
                                    className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20"
                                >
                                    <StopCircle className="h-5 w-5" />
                                </button>
                            ) : (
                                <button
                                    type="submit"
                                    disabled={!input.trim()}
                                    className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-500"
                                >
                                    <Send className="h-4 w-4" />
                                </button>
                            )}
                        </div>
                    </form>
                    <div className="mt-2 text-center text-xs text-zinc-500">
                        AI can make mistakes. Check important info.
                    </div>
                </div>
            </div>
        </div>
    );
};
