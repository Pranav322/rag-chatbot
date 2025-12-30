import { ChatSidebar } from '../components/chat/ChatSidebar';
import { ChatWindow } from '../components/chat/ChatWindow';

export const ChatPage = () => {
    return (
        <div className="flex h-full overflow-hidden">
            <ChatSidebar />
            <div className="flex-1">
                <ChatWindow />
            </div>
        </div>
    );
};
