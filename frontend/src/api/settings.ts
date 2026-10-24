
const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export type Provider = "groq";

export type KeyStatus = Record<Provider, boolean>;

export type SettingsStatus = {
  providers: KeyStatus;
  masked_keys: Record<Provider, string | null>;
};

type SaveKeyResponse = SettingsStatus & {
  success: boolean;
  message: string;
};

async function parseResponse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : `Request failed (${response.status})`,
    );
  }

  return data as T;
}

export async function getKeyStatus(): Promise<SettingsStatus> {
  const response = await fetch(`${API_BASE_URL}/settings/keys`);
  return parseResponse<SettingsStatus>(response);
}

export async function saveApiKey(
  provider: Provider,
  apiKey: string,
): Promise<SettingsStatus> {
  const response = await fetch(`${API_BASE_URL}/settings/keys`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      provider,
      api_key: apiKey,
    }),
  });

  return parseResponse<SaveKeyResponse>(response);
}

export async function deleteApiKey(
  provider: Provider,
): Promise<SettingsStatus> {
  const response = await fetch(
    `${API_BASE_URL}/settings/keys/${provider}`,
    { method: "DELETE" },
  );

  return parseResponse<SaveKeyResponse>(response);
}
