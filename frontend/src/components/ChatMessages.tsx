import { FileText, Sparkles } from "lucide-react";
import type { Message } from "../types/chat";
import { chatSuggestions } from "../data/chatSuggestions";

type ChatMessagesProps = {
  messages: Message[];
  loading: boolean;
  onSuggestion: (prompt: string) => void;
};

export default function ChatMessages({
  messages,
  loading,
  onSuggestion,
}: ChatMessagesProps) {
  if (messages.length === 0) {
    return (
      <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col justify-center px-5 py-12 sm:px-8">
        <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
          <Sparkles size={28} />
        </div>
        <p className="mb-3 text-sm font-semibold text-indigo-600">
          YOUR PERSONAL FILE ASSISTANT
        </p>
        <h2 className="max-w-xl text-3xl font-bold leading-tight tracking-tight text-slate-100 sm:text-4xl">
          Your files, found through conversation.
        </h2>
        <p className="mt-4 max-w-xl text-base leading-7 text-slate-400">
          Tell TailorTalk what you are looking for. Search by file type, name,
          owner, or date without building complicated filters.
        </p>

        <div className="mt-10 grid gap-3 sm:grid-cols-3">
          {chatSuggestions.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.title}
                onClick={() => onSuggestion(item.prompt)}
                disabled={loading}
                className="group rounded-2xl border border-slate-200 bg-[#0D1422] p-4 text-left transition hover:border-indigo-300 hover:bg-indigo-50/40 disabled:opacity-50"
              >
                <Icon
                  size={21}
                  className="mb-5 text-indigo-600 transition group-hover:scale-110"
                />
                <p className="text-sm font-semibold text-slate-100">
                  {item.title}
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-400">
                  {item.description}
                </p>
              </button>
            );
          })}
        </div>
        <p className="mt-8 text-center text-xs text-slate-400">
          Try a suggestion or type your own search below.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl space-y-7 px-5 py-8 sm:px-8">
      {messages.map((message, index) => (
        <div
          key={`${index}-${message.role}`}
          className={`flex gap-3 ${
            message.role === "user" ? "justify-end" : "justify-start"
          }`}
        >
          {message.role === "assistant" && (
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white">
              <Sparkles size={17} />
            </div>
          )}

          <div
            className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
              message.role === "user"
                ? "whitespace-pre-wrap bg-indigo-600 text-white"
                : "min-w-0 border border-[#29364A] bg-[#0D1422] text-slate-200"
            }`}
          >
            <p className="whitespace-pre-wrap">{message.content}</p>
            {message.files?.map((file, fileIndex) => (
              <a
                key={file.id || `${file.name}-${fileIndex}`}
                href={file.webViewLink || undefined}
                target="_blank"
                rel="noreferrer"
                className="mt-3 flex items-start gap-3 rounded-xl border border-[#29364A] bg-[#111827] p-3 text-sm text-blue-300 transition hover:bg-indigo-50"
              >
                <FileText size={19} className="mt-0.5 shrink-0 text-indigo-600" />
                <span className="min-w-0 flex-1">
                  <span className="block break-words font-medium">{file.name}</span>
                  {file.mimeType && (
                    <span className="mt-1 block break-all text-xs text-slate-400">
                      {file.mimeType}
                    </span>
                  )}
                  {file.createdTime && (
                    <span className="mt-1 block text-xs text-slate-400">
                      Created: {new Date(file.createdTime).toLocaleDateString()}
                    </span>
                  )}
                  {file.webViewLink && (
                    <span className="mt-1 block text-xs font-medium">
                      Open in Google Drive ↗
                    </span>
                  )}
                </span>
              </a>
            ))}
          </div>
        </div>
      ))}

      {loading && (
        <div className="flex items-center gap-3 text-sm text-slate-400">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
            <Sparkles size={17} className="animate-pulse" />
          </div>
          Searching your Google Drive...
        </div>
      )}
    </div>
  );
}
