
import {
  FolderOpen,
  MessageSquare,
  Plus,
  Settings2,
  Trash2,
  X,
} from "lucide-react";
import type { ConversationSummary } from "../api/chat";

type ChatSidebarProps = {
  open: boolean;
  activePage: "chat" | "settings";
  conversations: ConversationSummary[];
  activeConversationId?: string;
  loading: boolean;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onOpenSettings: () => void;
  onClose: () => void;
};

export default function ChatSidebar({
  open,
  activePage,
  conversations,
  activeConversationId,
  loading,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  onOpenSettings,
  onClose,
}: ChatSidebarProps) {
  return (
    <>
      {open && (
        <button
          aria-label="Close sidebar backdrop"
          className="fixed inset-0 z-20 bg-black/30 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-[#243149] bg-[#0B1428] p-4 transition-transform md:static md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-8 flex items-center justify-between px-1">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-sm">
              <MessageSquare size={21} />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-slate-100">
                TailorTalk
              </h1>
              <p className="text-xs text-slate-400">Your Drive assistant</p>
            </div>
          </div>
          <button
            aria-label="Close sidebar"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-200 md:hidden"
          >
            <X size={18} />
          </button>
        </div>

        <button
          onClick={onNewChat}
          disabled={loading}
          className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-50"
        >
          <Plus size={18} />
          New chat
        </button>

        <div className="mt-8">
          <p className="mb-3 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Workspace
          </p>
          <button
            onClick={onOpenSettings}
            className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${
              activePage === "settings"
                ? "bg-indigo-600 text-white"
                : "text-slate-300 hover:bg-[#172238]"
            }`}
          >
            <Settings2 size={18} />
            Settings & API Keys
          </button>
        </div>

        <div className="mt-8 min-h-0 flex-1 overflow-y-auto">
          <p className="mb-3 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Conversations
          </p>

          {conversations.length === 0 ? (
            <p className="px-3 text-sm text-slate-400">
              Your conversations will appear here.
            </p>
          ) : (
            <div className="space-y-1">
              {conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={`group flex items-center gap-1 rounded-xl ${
                    activeConversationId === conversation.id
                      ? "bg-[#172238]"
                      : "hover:bg-[#172238]"
                  }`}
                >
                  <button
                    onClick={() => onSelectConversation(conversation.id)}
                    disabled={loading}
                    title={conversation.title}
                    className="flex min-w-0 flex-1 items-center gap-3 truncate px-3 py-3 text-left text-sm text-slate-300 disabled:opacity-50"
                  >
                    <MessageSquare size={16} className="shrink-0" />
                    <span className="truncate">
                      {conversation.title || "New chat"}
                    </span>
                  </button>

                  <button
                    aria-label={`Delete ${conversation.title || "conversation"}`}
                    title="Delete conversation"
                    disabled={loading}
                    onClick={() => onDeleteConversation(conversation.id)}
                    className="mr-1 rounded-lg p-2 text-slate-500 hover:bg-red-500/10 hover:text-red-400 disabled:opacity-50"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-4 border-t border-[#243149] pt-4">
          <div className="flex items-center gap-3 rounded-xl px-2 py-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 text-sm font-bold text-slate-700">
              T
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-slate-100">TailorTalk</p>
              <p className="text-xs text-slate-400">Personal workspace</p>
            </div>
            <FolderOpen size={17} className="text-slate-400" />
          </div>
        </div>
      </aside>
    </>
  );
}
