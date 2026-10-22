import { useState } from 'react'
import {
  ArrowUp,
  Clock3,
  FileSpreadsheet,
  FileText,
  FolderOpen,
  Menu,
  MessageSquare,
  Plus,
  Search,
  Settings2,
  Sparkles,
  X,
} from 'lucide-react'
import { sendChatMessage, type ChatFile } from './api/chat'

type Message = {
  role: 'user' | 'assistant'
  content: string
  files?: ChatFile[]
}

const suggestions = [
  {
    title: 'Find PDF files',
    description: 'Search your documents',
    icon: FileText,
    prompt: 'Find my PDF files',
  },
  {
    title: 'Find Excel files',
    description: 'Search your spreadsheets',
    icon: FileSpreadsheet,
    prompt: 'Find my Excel files',
  },
  {
    title: 'Recent files',
    description: 'Find recently created files',
    icon: Clock3,
    prompt: 'Find my recently created files',
  },
]

export default function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>()
  const [loading, setLoading] = useState(false)

  async function sendMessage(text = input) {
    const message = text.trim()

    if (!message || loading) return

    setMessages((current) => [
      ...current,
      { role: 'user', content: message },
    ])
    setInput('')
    setLoading(true)

    try {
      const result = await sendChatMessage(message, sessionId)

      setSessionId(result.session_id)

      const files = result.message.files ?? []
      const reply = files.length
        ? `Found ${files.length} matching file(s).`
        : 'No matching files found.'

      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: reply,
          files,
        },
      ])
    } catch (error) {
      const detail =
        error instanceof Error
          ? error.message
          : 'An unexpected error occurred.'

      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: `Could not complete the search. ${detail}`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  function startNewChat() {
    setMessages([])
    setInput('')
    setSessionId(undefined)
    setSidebarOpen(false)
  }

  return (
    <div className="flex h-dvh overflow-hidden bg-white text-slate-800">
      {sidebarOpen && (
        <button
          aria-label="Close sidebar backdrop"
          className="fixed inset-0 z-20 bg-black/30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-slate-200 bg-slate-50 p-4 transition-transform md:static md:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="mb-8 flex items-center justify-between px-1">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-sm">
              <MessageSquare size={21} />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-slate-900">
                TailorTalk
              </h1>
              <p className="text-xs text-slate-500">Your Drive assistant</p>
            </div>
          </div>

          <button
            aria-label="Close sidebar"
            onClick={() => setSidebarOpen(false)}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-200 md:hidden"
          >
            <X size={18} />
          </button>
        </div>

        <button
          onClick={startNewChat}
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
          <div className="flex items-center gap-3 rounded-xl bg-indigo-50 px-3 py-3 text-sm font-medium text-indigo-700">
            <FolderOpen size={18} />
            Google Drive search
          </div>
        </div>

        <div className="mt-8">
          <p className="mb-3 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Conversations
          </p>

          {messages.length > 0 ? (
            <button
              onClick={startNewChat}
              disabled={loading}
              className="flex w-full items-center gap-3 truncate rounded-xl px-3 py-3 text-left text-sm text-slate-600 hover:bg-slate-200 disabled:opacity-50"
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
              <p className="text-sm font-semibold text-slate-800">
                TailorTalk
              </p>
              <p className="text-xs text-slate-500">Personal workspace</p>
            </div>
            <Settings2 size={17} className="text-slate-400" />
          </div>
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-100 px-4 sm:px-7">
          <div className="flex items-center gap-3">
            <button
              aria-label="Open sidebar"
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 md:hidden"
            >
              <Menu size={20} />
            </button>

            <div>
              <p className="text-sm font-semibold text-slate-800">
                Google Drive assistant
              </p>
              <p className="text-xs text-slate-500">
                Search files using natural language
              </p>
            </div>
          </div>

          <div className="hidden items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-500 sm:flex">
            <span
              className={`h-2 w-2 rounded-full ${
                loading ? 'animate-pulse bg-amber-400' : 'bg-indigo-500'
              }`}
            />
            {loading ? 'Searching...' : 'API connection enabled'}
          </div>
        </header>

        <section className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col justify-center px-5 py-12 sm:px-8">
              <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
                <Sparkles size={28} />
              </div>

              <p className="mb-3 text-sm font-semibold text-indigo-600">
                YOUR PERSONAL FILE ASSISTANT
              </p>

              <h2 className="max-w-xl text-3xl font-bold leading-tight tracking-tight text-slate-900 sm:text-4xl">
                Your files, found through conversation.
              </h2>

              <p className="mt-4 max-w-xl text-base leading-7 text-slate-500">
                Tell TailorTalk what you are looking for. Search by file type,
                name, owner, or date without building complicated filters.
              </p>

              <div className="mt-10 grid gap-3 sm:grid-cols-3">
                {suggestions.map((item) => {
                  const Icon = item.icon

                  return (
                    <button
                      key={item.title}
                      onClick={() => sendMessage(item.prompt)}
                      disabled={loading}
                      className="group rounded-2xl border border-slate-200 bg-white p-4 text-left transition hover:border-indigo-300 hover:bg-indigo-50/40 disabled:opacity-50"
                    >
                      <Icon
                        size={21}
                        className="mb-5 text-indigo-600 transition group-hover:scale-110"
                      />
                      <p className="text-sm font-semibold text-slate-800">
                        {item.title}
                      </p>
                      <p className="mt-1 text-xs leading-5 text-slate-500">
                        {item.description}
                      </p>
                    </button>
                  )
                })}
              </div>

              <p className="mt-8 text-center text-xs text-slate-400">
                Try a suggestion or type your own search below.
              </p>
            </div>
          ) : (
            <div className="mx-auto w-full max-w-3xl space-y-7 px-5 py-8 sm:px-8">
              {messages.map((message, index) => (
                <div
                  key={`${index}-${message.role}`}
                  className={`flex gap-3 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white">
                      <Sparkles size={17} />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                      message.role === 'user'
                        ? 'whitespace-pre-wrap bg-indigo-600 text-white'
                        : 'min-w-0 border border-slate-200 bg-slate-50 text-slate-700'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>

                    {message.files?.map((file, fileIndex) => (
                      <a
                        key={file.id || `${file.name}-${fileIndex}`}
                        href={file.webViewLink || undefined}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-3 flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 text-sm text-indigo-700 transition hover:bg-indigo-50"
                      >
                        <FileText
                          size={19}
                          className="mt-0.5 shrink-0 text-indigo-600"
                        />
                        <span className="min-w-0 flex-1">
                          <span className="block break-words font-medium">
                            {file.name}
                          </span>
                          {file.mimeType && (
                            <span className="mt-1 block break-all text-xs text-slate-500">
                              {file.mimeType}
                            </span>
                          )}
                          {file.createdTime && (
                            <span className="mt-1 block text-xs text-slate-400">
                              Created:{' '}
                              {new Date(file.createdTime).toLocaleDateString()}
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
                <div className="flex items-center gap-3 text-sm text-slate-500">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                    <Sparkles size={17} className="animate-pulse" />
                  </div>
                  Searching your Google Drive...
                </div>
              )}
            </div>
          )}
        </section>

        <footer className="shrink-0 px-4 pb-5 pt-3 sm:px-8 sm:pb-7">
          <div className="mx-auto max-w-3xl">
            <form
              onSubmit={(event) => {
                event.preventDefault()
                void sendMessage()
              }}
              className="rounded-2xl border border-slate-200 bg-white p-2 shadow-sm transition focus-within:border-indigo-300 focus-within:ring-4 focus-within:ring-indigo-50"
            >
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault()
                    void sendMessage()
                  }
                }}
                placeholder={
                  loading
                    ? 'Searching your Google Drive...'
                    : 'Ask TailorTalk to find a file...'
                }
                rows={2}
                disabled={loading}
                className="w-full resize-none bg-transparent px-3 py-2 text-sm leading-6 text-slate-800 outline-none placeholder:text-slate-400 disabled:opacity-60"
              />

              <div className="flex items-center justify-between px-2 pb-1">
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Search size={15} />
                  <span>Natural language search · Enter to send</span>
                </div>

                <button
                  type="submit"
                  disabled={!input.trim() || loading}
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
      </main>
    </div>
  )
}
