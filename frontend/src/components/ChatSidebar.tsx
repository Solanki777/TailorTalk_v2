import {
  FolderOpen,
  MessageSquare,
  Plus,
  Settings2,
  X,
} from "lucide-react";

type ChatSidebarProps = {
  open: boolean;
  activePage: "chat" | "settings";
  hasMessages: boolean;
  loading: boolean;
  onNewChat: () => void;
  onOpenSettings: () => void;
  onClose: () => void;
};

export default function ChatSidebar({
  open,
  activePage,
  hasMessages,
  loading,
  onNewChat,
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
        </div>

        <button
          onClick={onOpenSettings}
          className={`mt-2 flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${
            activePage === "settings"
              ? "bg-indigo-600 text-white"
              : "text-slate-300 hover:bg-[#172238]"
          }`}
        >
          <Settings2 size={18} />
          Settings & API Keys
        </button>

        <div className="mt-8">
          <p className="mb-3 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Conversations
          </p>
          {hasMessages ? (
            <button
              onClick={onNewChat}
              disabled={loading}
              className="flex w-full items-center gap-3 truncate rounded-xl px-3 py-3 text-left text-sm text-slate-300 hover:bg-[#172238] disabled:opacity-50"
            >
              <MessageSquare size={17} />
              Current conversation
            </button>
          ) : (
            <p className="px-3 text-sm text-slate-400">
              Your conversations will appear here.
            </p>
          )}
        </div>

        <div className="mt-auto border-t border-slate-200 pt-4">
          <div className="flex items-center gap-3 rounded-xl px-2 py-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 text-sm font-bold text-slate-700">
              T
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-slate-100">TailorTalk</p>
              <p className="text-xs text-slate-400">Personal workspace</p>
            </div>
            <Settings2 size={17} className="text-slate-400" />
          </div>
        </div>
      </aside>
    </>
  );
}
