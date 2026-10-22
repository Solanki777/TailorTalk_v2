
const API_URL = 'http://127.0.0.1:8000/api/v1/chat'

export type ChatFile = {
  id: string
  name: string
  mimeType?: string
  createdTime?: string
  webViewLink?: string
}

export type ChatResponse = {
  session_id: string
  message: {
    intent: Record<string, unknown>
    query: string
    files: ChatFile[]
  }
}

export async function sendChatMessage(
  message: string,
  sessionId?: string,
): Promise<ChatResponse> {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      ...(sessionId ? { session_id: sessionId } : {}),
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`API error (${response.status}): ${errorText}`)
  }

  return (await response.json()) as ChatResponse
}
