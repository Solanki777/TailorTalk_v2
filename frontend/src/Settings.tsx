
import { useEffect, useState } from 'react'
import {
  ArrowLeft,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  ShieldCheck,
  Trash2,
  XCircle,
} from 'lucide-react'
import {
  deleteApiKey,
  getKeyStatus,
  saveApiKey,
  type KeyStatus,
  type Provider,
} from './api/settings'

type SettingsProps = {
  onBack: () => void
}

const providers: {
  id: Provider
  name: string
  description: string
  placeholder: string
}[] = [
  {
    id: 'groq',
    name: 'Groq',
    description: 'Powers conversation and language understanding.',
    placeholder: 'Enter your Groq API key',
  },
  {
    id: 'gemini',
    name: 'Google Gemini',
    description: 'Powers document content extraction and analysis.',
    placeholder: 'Enter your Gemini API key',
  },
]

export default function Settings({ onBack }: SettingsProps) {
  const [status, setStatus] = useState<KeyStatus | null>(null)
  const [keys, setKeys] = useState<Record<Provider, string>>({
    groq: '',
    gemini: '',
  })
  const [visible, setVisible] = useState<Record<Provider, boolean>>({
    groq: false,
    gemini: false,
  })
  const [busy, setBusy] = useState<Provider | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function refreshStatus() {
    try {
      const result = await getKeyStatus()
      setStatus(result)
      setError('')
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not load API key settings.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refreshStatus()
  }, [])

  async function handleSave(provider: Provider) {
    const key = keys[provider].trim()

    if (!key) {
      setError(`Enter your ${provider === 'groq' ? 'Groq' : 'Gemini'} API key first.`)
      setNotice('')
      return
    }

    setBusy(provider)
    setError('')
    setNotice('')

    try {
      const result = await saveApiKey(provider, key)
      setStatus(result)
      setKeys((current) => ({ ...current, [provider]: '' }))
      setNotice(
        `${provider === 'groq' ? 'Groq' : 'Gemini'} API key validated and saved.`,
      )
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Could not save the API key.',
      )
    } finally {
      setBusy(null)
    }
  }

  async function handleDelete(provider: Provider) {
    const name = provider === 'groq' ? 'Groq' : 'Gemini'

    if (!window.confirm(`Remove your saved ${name} API key?`)) return

    setBusy(provider)
    setError('')
    setNotice('')

    try {
      const result = await deleteApiKey(provider)
      setStatus(result)
      setKeys((current) => ({ ...current, [provider]: '' }))
      setNotice(`${name} API key removed.`)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Could not remove the API key.',
      )
    } finally {
      setBusy(null)
    }
  }

  return (
    <section className="flex-1 overflow-y-auto bg-[#05070B] text-slate-100">
      <div className="mx-auto w-full max-w-3xl px-5 py-8 sm:px-8 sm:py-10">
        <button
          onClick={onBack}
          className="mb-7 inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300 transition hover:bg-[#111827]"
        >
          <ArrowLeft size={17} />
          Back to chat
        </button>

        <div className="mb-8 flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-indigo-600/15 text-indigo-400">
            <KeyRound size={25} />
          </div>
          <div>
            <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
              API Settings
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Configure your AI providers once. TailorTalk will use your saved
              credentials when the backend integrates them into chat and document
              processing.
            </p>
          </div>
        </div>

        <div className="mb-6 flex items-start gap-3 rounded-xl border border-emerald-900/70 bg-emerald-950/30 p-4">
          <ShieldCheck className="mt-0.5 shrink-0 text-emerald-400" size={20} />
          <div>
            <p className="text-sm font-semibold text-emerald-300">
              Encrypted backend storage
            </p>
            <p className="mt-1 text-xs leading-5 text-slate-400">
              Keys are sent to your backend for validation and encrypted storage.
              They are not displayed again after saving. Only enter keys into a
              trusted TailorTalk instance.
            </p>
          </div>
        </div>

        {error && (
          <div
            role="alert"
            className="mb-5 flex items-start gap-2 rounded-xl border border-red-900/70 bg-red-950/30 p-4 text-sm text-red-300"
          >
            <XCircle size={18} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {notice && (
          <div
            role="status"
            className="mb-5 flex items-start gap-2 rounded-xl border border-emerald-900/70 bg-emerald-950/30 p-4 text-sm text-emerald-300"
          >
            <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
            <span>{notice}</span>
          </div>
        )}

        {loading ? (
          <div className="flex items-center gap-3 py-10 text-sm text-slate-400">
            <LoaderCircle size={19} className="animate-spin" />
            Loading API settings...
          </div>
        ) : (
          <div className="space-y-5">
            {providers.map((provider) => {
              const connected = status?.[provider.id] ?? false
              const saving = busy === provider.id

              return (
                <article
                  key={provider.id}
                  className="rounded-2xl border border-[#29364A] bg-[#0D1422] p-5 sm:p-6"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold">{provider.name}</h3>
                      <p className="mt-1 text-sm text-slate-400">
                        {provider.description}
                      </p>
                    </div>

                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
                        connected
                          ? 'bg-emerald-950 text-emerald-300'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          connected ? 'bg-emerald-400' : 'bg-slate-500'
                        }`}
                      />
                      {connected ? 'Key saved' : 'Not configured'}
                    </span>
                  </div>

                  <label
                    htmlFor={`${provider.id}-key`}
                    className="mb-2 mt-5 block text-sm font-medium text-slate-300"
                  >
                    {connected ? 'Replace API key' : 'API key'}
                  </label>

                  <div className="flex gap-2">
                    <div className="relative min-w-0 flex-1">
                      <input
                        id={`${provider.id}-key`}
                        type={visible[provider.id] ? 'text' : 'password'}
                        autoComplete="new-password"
                        spellCheck={false}
                        value={keys[provider.id]}
                        onChange={(event) =>
                          setKeys((current) => ({
                            ...current,
                            [provider.id]: event.target.value,
                          }))
                        }
                        placeholder={provider.placeholder}
                        disabled={saving}
                        className="w-full rounded-xl border border-[#29364A] bg-[#080D17] px-4 py-3 pr-11 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-60"
                      />
                      <button
                        type="button"
                        aria-label={
                          visible[provider.id] ? 'Hide API key' : 'Show API key'
                        }
                        onClick={() =>
                          setVisible((current) => ({
                            ...current,
                            [provider.id]: !current[provider.id],
                          }))
                        }
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                      >
                        {visible[provider.id] ? (
                          <EyeOff size={18} />
                        ) : (
                          <Eye size={18} />
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-3">
                    <button
                      type="button"
                      onClick={() => void handleSave(provider.id)}
                      disabled={saving || !keys[provider.id].trim()}
                      className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {saving && <LoaderCircle size={16} className="animate-spin" />}
                      {saving
                        ? 'Please wait...'
                        : connected
                          ? 'Validate & replace'
                          : 'Validate & save'}
                    </button>

                    {connected && (
                      <button
                        type="button"
                        onClick={() => void handleDelete(provider.id)}
                        disabled={saving}
                        className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#29364A] px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:border-red-800 hover:text-red-300 disabled:opacity-50"
                      >
                        <Trash2 size={16} />
                        Remove key
                      </button>
                    )}
                  </div>
                </article>
              )
            })}
          </div>
        )}

        <p className="mt-6 text-xs leading-5 text-slate-500">
          Connection status means a key is saved. It does not guarantee the
          provider is available at all times. Keep your backend master encryption
          key secure and never commit it to source control.
        </p>
      </div>
    </section>
  )
}
