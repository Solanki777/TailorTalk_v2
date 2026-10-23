
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

export type Provider = 'groq' | 'gemini'

export type KeyStatus = Record<Provider, boolean>

type KeyStatusResponse = {
  providers: KeyStatus
}

type SaveKeyResponse = {
  success: boolean
  message: string
  providers: KeyStatus
}

async function parseResponse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(
      typeof data.detail === 'string'
        ? data.detail
        : `Request failed (${response.status})`,
    )
  }

  return data as T
}

export async function getKeyStatus(): Promise<KeyStatus> {
  const response = await fetch(`${API_BASE_URL}/settings/keys`)
  const data = await parseResponse<KeyStatusResponse>(response)
  return data.providers
}

export async function saveApiKey(
  provider: Provider,
  apiKey: string,
): Promise<KeyStatus> {
  const response = await fetch(`${API_BASE_URL}/settings/keys`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      provider,
      api_key: apiKey,
    }),
  })

  const data = await parseResponse<SaveKeyResponse>(response)
  return data.providers
}

export async function deleteApiKey(
  provider: Provider,
): Promise<KeyStatus> {
  const response = await fetch(
    `${API_BASE_URL}/settings/keys/${provider}`,
    { method: 'DELETE' },
  )

  const data = await parseResponse<SaveKeyResponse>(response)
  return data.providers
}
