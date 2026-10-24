
import { useEffect, useState } from "react";
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
} from "lucide-react";

import {
  deleteApiKey,
  getKeyStatus,
  saveApiKey,
  type Provider,
  type SettingsStatus,
} from "./api/settings";

type SettingsProps = {
  onBack?: () => void;
};

const providers: {
  id: Provider;
  name: string;
  description: string;
  placeholder: string;
}[] = [
  {
    id: "groq",
    name: "Groq",
    description:
      "Powers conversation, language understanding, and document Q&A.",
    placeholder: "Enter your Groq API key",
  },
];

export default function Settings({ onBack }: SettingsProps) {
  const [status, setStatus] = useState<SettingsStatus | null>(null);
  const [keys, setKeys] = useState<Record<Provider, string>>({
    groq: "",
  });
  const [visible, setVisible] = useState<Record<Provider, boolean>>({
    groq: false,
  });
  const [busy, setBusy] = useState<Provider | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function refreshStatus() {
    setLoading(true);
    setError("");

    try {
      const result = await getKeyStatus();
      setStatus(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load API key settings.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshStatus();
  }, []);

  async function handleSave(provider: Provider) {
    const apiKey = keys[provider].trim();

    if (!apiKey) {
      setError("Enter your Groq API key first.");
      return;
    }

    setBusy(provider);
    setError("");
    setNotice("");

    try {
      const result = await saveApiKey(provider, apiKey);

      setStatus(result);
      setKeys((current) => ({ ...current, [provider]: "" }));
      setVisible((current) => ({ ...current, [provider]: false }));
      setNotice("Groq API key validated and saved successfully.");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not validate or save the API key.",
      );
    } finally {
      setBusy(null);
    }
  }

  async function handleDelete(provider: Provider) {
    const confirmed = window.confirm(
      "Remove the saved Groq API key? Features that depend on Groq will stop working until you add a valid key again.",
    );

    if (!confirmed) return;

    setBusy(provider);
    setError("");
    setNotice("");

    try {
      const result = await deleteApiKey(provider);

      setStatus(result);
      setKeys((current) => ({ ...current, [provider]: "" }));
      setVisible((current) => ({ ...current, [provider]: false }));
      setNotice("Groq API key removed successfully.");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not remove the saved API key.",
      );
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <button
          type="button"
          onClick={onBack}
          className="mb-6 inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 transition hover:bg-slate-800 hover:text-white"
        >
          <ArrowLeft size={16} />
          Back
        </button>

        <div className="mb-8">
          <div className="mb-3 flex items-center gap-3">
            <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-3">
              <KeyRound className="text-indigo-400" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                API Settings
              </h1>
              <p className="mt-1 text-sm text-slate-400">
                Manage the API key used by TailorTalk.
              </p>
            </div>
          </div>

          <div className="mt-5 flex items-start gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
            <ShieldCheck
              className="mt-0.5 shrink-0 text-emerald-400"
              size={20}
            />
            <div>
              <p className="text-sm font-medium text-emerald-300">
                Secure key storage
              </p>
              <p className="mt-1 text-sm leading-6 text-slate-400">
                Your key is validated by the backend and stored using encrypted
                storage. TailorTalk displays only a masked version of a saved
                key, never the complete secret.
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div
            role="alert"
            className="mb-5 flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300"
          >
            <XCircle className="mt-0.5 shrink-0" size={18} />
            <span>{error}</span>
          </div>
        )}

        {notice && (
          <div
            role="status"
            className="mb-5 flex items-start gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-300"
          >
            <CheckCircle2 className="mt-0.5 shrink-0" size={18} />
            <span>{notice}</span>
          </div>
        )}

        <div className="space-y-5">
          {providers.map((provider) => {
            const connected = status?.providers[provider.id] ?? false;
            const maskedKey = status?.masked_keys[provider.id] ?? null;
            const isBusy = busy === provider.id;

            return (
              <section
                key={provider.id}
                className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 sm:p-6"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="rounded-xl bg-slate-800 p-3">
                      <KeyRound size={21} className="text-slate-300" />
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold">
                        {provider.name}
                      </h2>
                      <p className="mt-1 max-w-lg text-sm leading-6 text-slate-400">
                        {provider.description}
                      </p>
                    </div>
                  </div>

                  <span
                    className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${
                      connected
                        ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                        : "border-slate-700 bg-slate-800 text-slate-400"
                    }`}
                  >
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        connected ? "bg-emerald-400" : "bg-slate-500"
                      }`}
                    />
                    {loading
                      ? "Checking..."
                      : connected
                        ? "Connected"
                        : "Not configured"}
                  </span>
                </div>

                {connected && (
                  <div className="mt-5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                    <div className="flex items-start gap-3">
                      <CheckCircle2
                        className="mt-0.5 shrink-0 text-emerald-400"
                        size={18}
                      />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-emerald-300">
                          API key saved
                        </p>
                        <p className="mt-2 break-all font-mono text-sm text-slate-300">
                          {maskedKey ?? "Saved key (masked preview unavailable)"}
                        </p>
                        <p className="mt-2 text-xs leading-5 text-slate-500">
                          This is a masked preview, not the complete API key.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="mt-5">
                  <label
                    htmlFor={`${provider.id}-key`}
                    className="mb-2 block text-sm font-medium text-slate-300"
                  >
                    {connected ? "Replace API key" : "API key"}
                  </label>

                  <div className="relative">
                    <input
                      id={`${provider.id}-key`}
                      type={visible[provider.id] ? "text" : "password"}
                      value={keys[provider.id]}
                      onChange={(event) => {
                        setKeys((current) => ({
                          ...current,
                          [provider.id]: event.target.value,
                        }));
                        setError("");
                        setNotice("");
                      }}
                      placeholder={
                        connected
                          ? "Enter a new key to replace the saved key"
                          : provider.placeholder
                      }
                      autoComplete="new-password"
                      disabled={isBusy || loading}
                      className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 pr-12 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50"
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setVisible((current) => ({
                          ...current,
                          [provider.id]: !current[provider.id],
                        }))
                      }
                      aria-label={
                        visible[provider.id] ? "Hide entered key" : "Show entered key"
                      }
                      className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-1 text-slate-400 hover:text-white"
                    >
                      {visible[provider.id] ? (
                        <EyeOff size={18} />
                      ) : (
                        <Eye size={18} />
                      )}
                    </button>
                  </div>

                  <p className="mt-2 text-xs leading-5 text-slate-500">
                    {connected
                      ? "Leave this field empty to keep your current key. Enter a new key only when you want to replace it."
                      : "Your key is sent to the TailorTalk backend for validation before being saved."}
                  </p>
                </div>

                <div className="mt-5 flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => void handleSave(provider.id)}
                    disabled={
                      isBusy || loading || !keys[provider.id].trim()
                    }
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-500 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isBusy ? (
                      <LoaderCircle size={17} className="animate-spin" />
                    ) : (
                      <ShieldCheck size={17} />
                    )}
                    {isBusy
                      ? "Please wait..."
                      : connected
                        ? "Validate & replace"
                        : "Validate & save"}
                  </button>

                  {connected && (
                    <button
                      type="button"
                      onClick={() => void handleDelete(provider.id)}
                      disabled={isBusy || loading}
                      className="inline-flex items-center justify-center gap-2 rounded-xl border border-red-500/30 px-4 py-2.5 text-sm font-medium text-red-300 transition hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {isBusy ? (
                        <LoaderCircle size={17} className="animate-spin" />
                      ) : (
                        <Trash2 size={17} />
                      )}
                      Remove key
                    </button>
                  )}
                </div>
              </section>
            );
          })}
        </div>

        <p className="mt-6 text-center text-xs leading-5 text-slate-500">
          Only enter API keys into a TailorTalk instance you trust. Never share
          your complete API key in screenshots or messages.
        </p>
      </div>
    </div>
  );
}
