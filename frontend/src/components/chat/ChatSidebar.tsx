import { useEffect, useState } from 'react';
import { NavLink, useNavigate, useParams } from 'react-router-dom';
import { Plus, Loader2 } from 'lucide-react';
import api from '../../lib/api';
import type { ChatSession } from '../../types';
import { cn } from '../../lib/utils';
import { formatDistanceToNow } from 'date-fns';

export const ChatSidebar = () => {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [loading, setLoading] = useState(true);
    const { sessionId } = useParams();
    const navigate = useNavigate();

    const fetchSessions = async () => {
        try {
            const response = await api.get('/chat/sessions');
            setSessions(response.data.sessions);
        } catch (error) {
            console.error('Failed to fetch sessions', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSessions();
    }, [sessionId]); // Re-fetch when session changes to update timestamps/order if needed

    const handleNewChat = () => {
        navigate('/chat');
    };

    return (
        <div className="flex h-full w-64 flex-col border-r border-zinc-800 bg-zinc-900/50">
            <div className="p-4">
                <button
                    onClick={handleNewChat}
                    className="flex w-full items-center justify-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800 py-3 text-sm font-medium text-white transition-colors hover:bg-zinc-700 hover:text-white"
                >
                    <Plus className="h-4 w-4" />
                    New Chat
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-2">
                {loading ? (
                    <div className="flex justify-center py-4">
                        <Loader2 className="h-5 w-5 animate-spin text-zinc-500" />
                    </div>
                ) : sessions.length === 0 ? (
                    <div className="text-center text-sm text-zinc-500 py-4">No history yet</div>
                ) : (
                    <div className="space-y-1">
                        <h3 className="mb-2 px-2 text-xs font-semibold uppercase text-zinc-500">History</h3>
                        {sessions.map((session) => (
                            <NavLink
                                key={session.id}
                                to={`/chat/${session.id}`}
                                className={({ isActive }) =>
                                    cn(
                                        "group flex flex-col gap-1 rounded-lg px-3 py-3 transition-colors hover:bg-zinc-800",
                                        isActive || sessionId === session.id ? "bg-zinc-800" : ""
                                    )
                                }
                            >
                                <span className="line-clamp-1 text-sm font-medium text-zinc-200">
                                    {session.last_message || 'New Conversation'}
                                </span>
                                <span className="text-xs text-zinc-500">
                                    {formatDistanceToNow(new Date(session.updated_at), { addSuffix: true })}
                                </span>
                            </NavLink>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
