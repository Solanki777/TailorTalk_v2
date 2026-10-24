import type { Message } from "../types/chat";

export type StoredChat = {
  id: "current";
  messages: Message[];
  sessionId?: string;
  updatedAt: number;
};

const DB_NAME = "tailortalk-local";
const STORE_NAME = "chats";
const CURRENT_CHAT_ID = "current";

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: "id" });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function saveCurrentChat(
  messages: Message[],
  sessionId?: string,
): Promise<void> {
  const db = await openDatabase();

  try {
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, "readwrite");
      const chat: StoredChat = {
        id: CURRENT_CHAT_ID,
        messages,
        sessionId,
        updatedAt: Date.now(),
      };

      transaction.objectStore(STORE_NAME).put(chat);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(transaction.error);
    });
  } finally {
    db.close();
  }
}

export async function loadCurrentChat(): Promise<StoredChat | null> {
  const db = await openDatabase();

  try {
    return await new Promise((resolve, reject) => {
      const request = db
        .transaction(STORE_NAME, "readonly")
        .objectStore(STORE_NAME)
        .get(CURRENT_CHAT_ID);

      request.onsuccess = () =>
        resolve((request.result as StoredChat | undefined) ?? null);
      request.onerror = () => reject(request.error);
    });
  } finally {
    db.close();
  }
}

export async function clearCurrentChat(): Promise<void> {
  const db = await openDatabase();

  try {
    await new Promise<void>((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, "readwrite");
      transaction.objectStore(STORE_NAME).delete(CURRENT_CHAT_ID);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(transaction.error);
    });
  } finally {
    db.close();
  }
}
