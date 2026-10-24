import { useEffect, useRef, useState } from "react";
import { Menu } from "lucide-react";
import Settings from "./Settings";
import { sendChatMessage } from "./api/chat";
import {
  clearCurrentChat,
  loadCurrentChat,
  saveCurrentChat,
} from "./api/chatStorage";
import ChatComposer from "./components/ChatComposer";
import ChatMessages from "./components/ChatMessages";
import ChatSidebar from "./components/ChatSidebar";
import type { Message } from "./types/chat";

export default function App() {
  const [activePage, setActivePage] = useState<"chat" | "settings">("chat");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [storageReady, setStorageReady] = useState(false);
  const requestInProgress = useRef(false);

  useEffect(() => {
    let cancelled = false;

    async function restoreChat() {
      try {
        const saved = await loadCurrentChat();
        if (!cancelled && saved) {
          setMessages(saved.messages);
          setSessionId(saved.sessionId);
        }
      } catch (error) {
        console.error("Could not restore chat history:", error);
      } finally {
        if (!cancelled) setStorageReady(true);
      }
    }

    void restoreChat();
    return () => {
      cancelled = true;
    };
  }, []);

  async function persistChat(nextMessages: Message[], nextSessionId?: string) {
    try {
      await saveCurrentChat(nextMessages, nextSessionId);
    } catch (error) {
      console.error("Could not save chat history:", error);
    }
  }

  async function sendMessage(text = input) {
    const message = text.trim();
    if (!message || loading || requestInProgress.current || !storageReady) return;

    requestInProgress.current = true;
    setLoading(true);
    setInput("");

    const userMessages: Message[] = [
      ...messages,
      { role: "user", content: message },
    ];
    setMessages(userMessages);

    // Save the user's message before making the network request.
    await persistChat(userMessages, sessionId);

    try {
          
    const result = await sendChatMessage(message, sessionId);
    const nextSessionId = result.session_id;
    setSessionId(nextSessionId);

    const files = result.message.files ?? [];
    const reply = result.message.reply;

    const assistantMessages: Message[] = [
      ...userMessages,
      {
        role: "assistant",
        content: reply,
        files,
      },
    ];

setMessages(assistantMessages);
await persistChat(assistantMessages, nextSessionId);

    } catch (error) {
      const detail =
        error instanceof Error ? error.message : "An unexpected error occurred.";
      const errorMessages: Message[] = [
        ...userMessages,
        {
          role: "assistant",
          content: `Could not complete the search. ${detail}`,
        },
      ];
      setMessages(errorMessages);
      await persistChat(errorMessages, sessionId);
    } finally {
      requestInProgress.current = false;
      setLoading(false);
    }
  }

  async function startNewChat() {
    if (loading) return;

    try {
      await clearCurrentChat();
    } catch (error) {
      console.error("Could not clear saved chat:", error);
    }

    setMessages([]);
    setInput("");
    setSessionId(undefined);
    setSidebarOpen(false);
  }

  return (
    <div className="flex h-dvh overflow-hidden bg-[#05070B] text-slate-100">
      <ChatSidebar
        open={sidebarOpen}
        activePage={activePage}
        hasMessages={messages.length > 0}
        loading={loading || !storageReady}
        onNewChat={() => void startNewChat()}
        onOpenSettings={() => {
          setActivePage("settings");
          setSidebarOpen(false);
        }}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        {activePage === "settings" ? (
          <>
            <header className="flex h-16 shrink-0 items-center border-b border-[#243149] bg-[#05070B] px-4 sm:px-7">
              <h1 className="text-sm font-semibold text-slate-100">
                TailorTalk Settings
              </h1>
            </header>
            <Settings onBack={() => setActivePage("chat")} />
          </>
        ) : (
          <>
            <header className="flex h-16 shrink-0 items-center justify-between border-b border-[#243149] bg-[#05070B] px-4 sm:px-7">
              <div className="flex items-center gap-3">
                <button
                  aria-label="Open sidebar"
                  onClick={() => setSidebarOpen(true)}
                  className="rounded-lg p-2 text-slate-300 hover:bg-slate-100 md:hidden"
                >
                  <Menu size={20} />
                </button>
                <div>
                  <p className="text-sm font-semibold text-slate-100">
                    Google Drive assistant
                  </p>
                  <p className="text-xs text-slate-400">
                    Search files using natural language
                  </p>
                </div>
              </div>
              <div className="hidden items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-400 sm:flex">
                <span
                  className={`h-2 w-2 rounded-full ${
                    loading ? "animate-pulse bg-amber-400" : "bg-indigo-500"
                  }`}
                />
                {loading ? "Searching..." : "API connection enabled"}
              </div>
            </header>

            <section className="flex-1 overflow-y-auto">
              <ChatMessages
                messages={messages}
                loading={loading}
                onSuggestion={(prompt: string) => void sendMessage(prompt)}
              />
            </section>

            <ChatComposer
              value={input}
              loading={loading}
              storageReady={storageReady}
              onChange={setInput}
              onSend={() => void sendMessage()}
            />
          </>
        )}
      </main>
    </div>
  );
}
