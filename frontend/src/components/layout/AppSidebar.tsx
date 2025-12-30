import { NavLink } from 'react-router-dom';
import { MessageSquare, FileText, LogOut, BrainCircuit } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { cn } from '../../lib/utils';

export const AppSidebar = () => {
    const { logout } = useAuth();

    return (
        <div className="flex h-screen w-16 flex-col items-center border-r border-zinc-800 bg-zinc-900 py-4 sm:w-64">
            {/* Logo */}
            <div className="mb-8 flex h-12 w-full items-center justify-center px-4">
                <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
                        <BrainCircuit className="h-5 w-5 text-white" />
                    </div>
                    <span className="hidden text-lg font-bold text-white sm:block">RAG UI</span>
                </div>
            </div>

            {/* Nav Links */}
            <nav className="flex w-full flex-1 flex-col gap-2 px-2">
                <NavLink
                    to="/chat"
                    className={({ isActive }) =>
                        cn(
                            "flex items-center gap-3 rounded-lg px-3 py-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white",
                            isActive && "bg-zinc-800 text-white"
                        )
                    }
                >
                    <MessageSquare className="h-5 w-5" />
                    <span className="hidden sm:block">Chat</span>
                </NavLink>

                <NavLink
                    to="/documents"
                    className={({ isActive }) =>
                        cn(
                            "flex items-center gap-3 rounded-lg px-3 py-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white",
                            isActive && "bg-zinc-800 text-white"
                        )
                    }
                >
                    <FileText className="h-5 w-5" />
                    <span className="hidden sm:block">Documents</span>
                </NavLink>
            </nav>

            {/* Logout */}
            <div className="w-full px-2 mt-auto">
                <button
                    onClick={logout}
                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
                >
                    <LogOut className="h-5 w-5" />
                    <span className="hidden sm:block">Logout</span>
                </button>
            </div>
        </div>
    );
};
