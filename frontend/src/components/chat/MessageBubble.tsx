import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, User, FileText } from 'lucide-react';
import type { ChatMessage } from '../../types';
import { cn } from '../../lib/utils';
import { format } from 'date-fns';

interface MessageBubbleProps {
    message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
    const isUser = message.role === 'user';

    return (
        <div
            className={cn(
                "flex w-full gap-4 p-6",
                isUser ? "bg-zinc-900/0" : "bg-zinc-900/30"
            )}
        >
            <div className={cn(
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                isUser ? "bg-zinc-800" : "bg-blue-600"
            )}>
                {isUser ? <User className="h-5 w-5 text-zinc-400" /> : <Bot className="h-5 w-5 text-white" />}
            </div>

            <div className="flex-1 space-y-2 overflow-hidden">
                <div className="flex items-center gap-2">
                    <span className="font-semibold text-white">
                        {isUser ? 'You' : 'Assistant'}
                    </span>
                    <span className="text-xs text-zinc-500">
                        {message.created_at ? format(new Date(message.created_at), 'h:mm a') : 'Just now'}
                    </span>
                </div>

                <div className="prose prose-invert max-w-none text-zinc-300">
                    <ReactMarkdown>{message.content || ' '}</ReactMarkdown>
                </div>

                {/* Sources Section */}
                {message.used_context && message.sources && message.sources.length > 0 && (
                    <div className="mt-4 rounded-lg bg-zinc-900/50 p-3">
                        <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase text-zinc-500">
                            <FileText className="h-3 w-3" />
                            <span>Sources Used</span>
                        </div>
                        <div className="grid gap-2 sm:grid-cols-2">
                            {message.sources.map((source, idx) => (
                                <div key={idx} className="rounded border border-zinc-800 bg-zinc-900 p-2 text-xs text-zinc-400">
                                    <div className="mb-1 font-medium text-blue-400 truncate" title={source.asset_id}>
                                        Document Reference
                                    </div>
                                    <p className="line-clamp-2 italic opacity-80">"{source.excerpt}"</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
