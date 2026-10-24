import { ArrowUp, Search } from "lucide-react";

type ChatComposerProps = {
  value: string;
  loading: boolean;
  storageReady: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
};

export default function ChatComposer({
  value,
  loading,
  storageReady,
  onChange,
  onSend,
}: ChatComposerProps) {
  return (
    <footer className="shrink-0 px-4 pb-5 pt-3 sm:px-8 sm:pb-7">
      <div className="mx-auto max-w-3xl">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            onSend();
          }}
          className="rounded-2xl border border-[#29364A] bg-[#0D1422] p-2 shadow-sm transition focus-within:border-indigo-300 focus-within:ring-4 focus-within:ring-indigo-50"
        >
          <textarea
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                onSend();
              }
            }}
            placeholder={
              !storageReady
                ? "Restoring your conversation..."
                : loading
                  ? "Searching your Google Drive..."
                  : "Ask TailorTalk to find a file..."
            }
            rows={2}
            disabled={loading || !storageReady}
            className="w-full resize-none bg-transparent px-3 py-2 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-400 disabled:opacity-60"
          />
          <div className="flex items-center justify-between px-2 pb-1">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Search size={15} />
              <span>Natural language search · Enter to send</span>
            </div>
            <button
              type="submit"
              disabled={!value.trim() || loading || !storageReady}
              aria-label="Send message"
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
            >
              <ArrowUp size={19} />
            </button>
          </div>
        </form>
        <p className="mt-3 text-center text-xs text-slate-400">
          TailorTalk · Google Drive search assistant
        </p>
      </div>
    </footer>
  );
}
