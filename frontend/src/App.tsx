
import { useCallback, useEffect, useRef, useState } from "react";
import { Menu } from "lucide-react";
import Settings from "./Settings";
import {
  createConversation,
  deleteConversation,
  getConversation,
  listConversations,
  sendChatMessage,
  type ConversationSummary,
} from "./api/chat";
import {
  deleteChat,
  listChats,
  loadChat,
  saveChat,
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
  const [activeConversationId, setActiveConversationId] = useState<
    string | undefined
  >();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [storageReady, setStorageReady] = useState(false);
  const requestInProgress = useRef(false);
  const creatingChat = useRef(false);

  
  const refreshConversations = useCallback(async () => {
    const [serverResult, localResult] = await Promise.allSettled([
      listConversations(),
      listChats(),
    ]);

    const serverConversations: ConversationSummary[] =
      serverResult.status === "fulfilled"
        ? serverResult.value
        : [];

    const localChats =
      localResult.status === "fulfilled"
        ? localResult.value
        : [];

    const serverIds = new Set(
      serverConversations.map((conversation) => conversation.id),
    );

    const localOnlyConversations: ConversationSummary[] = localChats
      .filter((chat) => !serverIds.has(chat.sessionId || chat.id))
      .map((chat) => ({
        id: chat.sessionId || chat.id,
        title: chat.title || "New chat",
        updated_at: new Date(chat.updatedAt).toISOString(),
      }));

    const combined = [
      ...serverConversations,
      ...localOnlyConversations,
    ].sort((a, b) => {
      const timeA = a.updated_at ? Date.parse(a.updated_at) : 0;
      const timeB = b.updated_at ? Date.parse(b.updated_at) : 0;
      return timeB - timeA;
    });

    setConversations(combined);
  }, []);



  useEffect(() => {
    let cancelled = false;

    async function restoreChat() {
      try {
        await refreshConversations();

        const localChats = await listChats();
        if (cancelled) return;

        if (localChats.length > 0) {
          const saved = localChats[0];
          setMessages(saved.messages);
          setActiveConversationId(saved.id);
          setSessionId(saved.sessionId || saved.id);
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
  }, [refreshConversations]);

  async function persistChat(
    id: string,
    nextMessages: Message[],
    nextSessionId?: string,
  ) {
    try {
      await saveChat(id, nextMessages, nextSessionId);
    } catch (error) {
      console.error("Could not save chat history:", error);
    }
  }

  async function sendMessage(text = input) {
    const message = text.trim();

    if (
      !message ||
      loading ||
      requestInProgress.current ||
      !storageReady ||
      !activeConversationId
    ) {
      return;
    }

    requestInProgress.current = true;
    setLoading(true);
    setInput("");

    const conversationId = activeConversationId;
    const currentSessionId = sessionId || conversationId;
    const userMessages: Message[] = [
      ...messages,
      { role: "user", content: message },
    ];

    setMessages(userMessages);
    await persistChat(conversationId, userMessages, currentSessionId);

    try {
      const result = await sendChatMessage(message, currentSessionId);
      const nextSessionId = result.session_id;
      const assistantMessages: Message[] = [
        ...userMessages,
        {
          role: "assistant",
          content: result.message.reply,
          files: result.message.files ?? [],
        },
      ];

      setSessionId(nextSessionId);
      setActiveConversationId(nextSessionId);
      setMessages(assistantMessages);

      // Move a local-only conversation to the server's session ID if needed.
      if (conversationId !== nextSessionId) {
        await deleteChat(conversationId).catch(() => undefined);
      }

      await persistChat(nextSessionId, assistantMessages, nextSessionId);
      await refreshConversations();
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
      await persistChat(conversationId, errorMessages, currentSessionId);
    } finally {
      requestInProgress.current = false;
      setLoading(false);
    }
  }

    
const startNewChat = useCallback(async () => {
  // Prevent duplicate creation from rapid clicks.
  if (creatingChat.current) return;

  // Reuse the current conversation if no message has been sent.
  const hasUserMessage = messages.some(
    (message) =>
      message.role === "user" && message.content.trim().length > 0,
  );

  if (activeConversationId && !hasUserMessage) {
    setActivePage("chat");
    setSidebarOpen(false);
    return;
  }

  creatingChat.current = true;

  try {
    const conversation = await createConversation();

    // Immediately open the newly created conversation.
    setActivePage("chat");
    setInput("");
    setMessages([]);
    setSessionId(conversation.id);
    setActiveConversationId(conversation.id);
    setSidebarOpen(false);

    // Use the existing storage function signature.
    await persistChat(conversation.id, [], conversation.id);

    await refreshConversations();
  } catch (error) {
    console.error("Failed to create conversation:", error);
    window.alert("Could not create a new chat. Please try again.");
  } finally {
    creatingChat.current = false;
  }
}, [messages, activeConversationId, refreshConversations]);


  

  async function openConversation(id: string) {
    if (loading || id === activeConversationId) {
      setSidebarOpen(false);
      return;
    }

    try {
      const local = await loadChat(id);

      if (local) {
        setMessages(local.messages);
        setSessionId(local.sessionId || id);
        setActiveConversationId(id);
      } else {
        const saved = await getConversation(id);
        const restoredMessages: Message[] = saved.messages.map((message) => ({
          role: message.role,
          content: message.content,
        }));

        setMessages(restoredMessages);
        setSessionId(saved.id);
        setActiveConversationId(saved.id);
        await persistChat(saved.id, restoredMessages, saved.id);
      }

      setInput("");
      setActivePage("chat");
      setSidebarOpen(false);
    } catch (error) {
      console.error("Could not open conversation:", error);
      window.alert("Could not open this conversation. Please try again.");
    }
  }

  async function removeConversation(id: string) {
    if (loading) return;

    const confirmed = window.confirm(
      "Delete this conversation? This cannot be undone.",
    );

    if (!confirmed) return;

    try {
      try {
        await deleteConversation(id);
      } catch (error) {
        // A local-only conversation may not exist on the server.
        console.warn("Server delete skipped or failed:", error);
      }

      await deleteChat(id);

      if (activeConversationId === id) {
        setMessages([]);
        setSessionId(undefined);
        setActiveConversationId(undefined);
        setInput("");
      }

      await refreshConversations();
    } catch (error) {
      console.error("Could not delete conversation:", error);
      window.alert("Could not delete this conversation.");
    }
  }

  return (
    <div className="flex h-dvh overflow-hidden bg-[#05070B] text-slate-100">
      <ChatSidebar
        open={sidebarOpen}
        activePage={activePage}
        conversations={conversations}
        activeConversationId={activeConversationId}
        loading={loading || !storageReady}
        onNewChat={() => void startNewChat()}
        onSelectConversation={(id) => void openConversation(id)}
        onDeleteConversation={(id) => void removeConversation(id)}
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
                  className="rounded-lg p-2 text-slate-300 hover:bg-slate-800 md:hidden"
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

              <div className="hidden items-center gap-2 rounded-full border border-[#243149] px-3 py-1.5 text-xs text-slate-400 sm:flex">
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
