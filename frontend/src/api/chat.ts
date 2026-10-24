
export type ChatFile = {
  id?: string;
  name: string;
  mimeType?: string;
  webViewLink?: string;
  createdTime?: string;
  [key: string]: unknown;
};

export type ChatResponse = {
  session_id: string;
  message: {
    type: "conversation" | "search";
    reply: string;
    intent: Record<string, unknown> | null;
    query: string | null;
    files: ChatFile[];
  };
};

export type ConversationSummary = {
  id: string;
  title: string;
  created_at?: string;
  updated_at?: string;
};

export type ConversationMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ConversationDetail = {
  id: string;
  title: string;
  messages: ConversationMessage[];
  last_intent?: Record<string, unknown> | null;
  created_at?: string;
  updated_at?: string;
};

const API_BASE_URL = "http://127.0.0.1:8000/api/v1";
const CHAT_URL = `${API_BASE_URL}/chat`;
const CONVERSATIONS_URL = `${API_BASE_URL}/conversations`;

async function readError(response: Response): Promise<string> {
  const detail = await response.text();
  return detail || `Request failed (${response.status})`;
}

export async function sendChatMessage(
  message: string,
  sessionId?: string,
): Promise<ChatResponse> {
  const response = await fetch(CHAT_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId ?? null,
    }),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as ChatResponse;
}

export async function listConversations(): Promise<ConversationSummary[]> {
  const response = await fetch(CONVERSATIONS_URL);

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const data = (await response.json()) as {
    conversations: ConversationSummary[];
  };

  return data.conversations;
}

export async function createConversation(): Promise<ConversationDetail> {
  const response = await fetch(CONVERSATIONS_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as ConversationDetail;
}

export async function getConversation(
  id: string,
): Promise<ConversationDetail> {
  const response = await fetch(
    `${CONVERSATIONS_URL}/${encodeURIComponent(id)}`,
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return (await response.json()) as ConversationDetail;
}

export async function deleteConversation(id: string): Promise<void> {
  const response = await fetch(
    `${CONVERSATIONS_URL}/${encodeURIComponent(id)}`,
    { method: "DELETE" },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }
}
