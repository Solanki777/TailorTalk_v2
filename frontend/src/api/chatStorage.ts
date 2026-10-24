
import type { Message } from "../types/chat";

const DB_NAME = "tailortalk-local";
const STORE_NAME = "chats";
const DB_VERSION = 1;

export type StoredChat = {
  id: string;
  messages: Message[];
  sessionId?: string;
  title?: string;
  createdAt: number;
  updatedAt: number;
};

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

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

function makeTitle(messages: Message[]): string {
  const firstUserMessage = messages.find((message) => message.role === "user");
  return firstUserMessage?.content.trim().slice(0, 60) || "New chat";
}

function requestResult<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/**
 * Migrate the legacy single-chat record without deleting its messages.
 */
async function migrateLegacyChat(db: IDBDatabase): Promise<void> {
  const tx = db.transaction(STORE_NAME, "readwrite");
  const store = tx.objectStore(STORE_NAME);
  const legacy = (await requestResult(
    store.get("current"),
  )) as StoredChat | undefined;

  if (legacy) {
    const newId = legacy.sessionId || crypto.randomUUID();
    const existing = await requestResult(store.get(newId));

    if (!existing) {
      store.put({
        ...legacy,
        id: newId,
        title: legacy.title || makeTitle(legacy.messages),
        createdAt: legacy.createdAt || Date.now(),
        updatedAt: legacy.updatedAt || Date.now(),
      } satisfies StoredChat);
    }

    store.delete("current");
  }

  await new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
}

export async function listChats(): Promise<StoredChat[]> {
  const db = await openDatabase();

  try {
    await migrateLegacyChat(db);
    const tx = db.transaction(STORE_NAME, "readonly");
    const chats = (await requestResult(
      tx.objectStore(STORE_NAME).getAll(),
    )) as StoredChat[];

    return chats.sort((a, b) => b.updatedAt - a.updatedAt);
  } finally {
    db.close();
  }
}

export async function loadChat(id: string): Promise<StoredChat | undefined> {
  const db = await openDatabase();

  try {
    await migrateLegacyChat(db);
    const tx = db.transaction(STORE_NAME, "readonly");
    return (await requestResult(
      tx.objectStore(STORE_NAME).get(id),
    )) as StoredChat | undefined;
  } finally {
    db.close();
  }
}

export async function saveChat(
  id: string,
  messages: Message[],
  sessionId?: string,
): Promise<void> {
  const db = await openDatabase();

  try {
    await migrateLegacyChat(db);
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    const existing = (await requestResult(store.get(id))) as
      | StoredChat
      | undefined;
    const now = Date.now();

    store.put({
      id,
      messages,
      sessionId: sessionId || existing?.sessionId,
      title: makeTitle(messages),
      createdAt: existing?.createdAt || now,
      updatedAt: now,
    } satisfies StoredChat);

    await new Promise<void>((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally {
    db.close();
  }
}

export async function deleteChat(id: string): Promise<void> {
  const db = await openDatabase();

  try {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).delete(id);

    await new Promise<void>((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally {
    db.close();
  }
}

/**
 * Backwards-compatible helpers for any existing imports.
 */
export async function loadCurrentChat(): Promise<StoredChat | undefined> {
  const chats = await listChats();
  return chats[0];
}

export async function saveCurrentChat(
  messages: Message[],
  sessionId?: string,
): Promise<void> {
  const id = sessionId || "local-current";
  await saveChat(id, messages, sessionId);
}

export async function clearCurrentChat(): Promise<void> {
  const db = await openDatabase();

  try {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).delete("current");
    tx.objectStore(STORE_NAME).delete("local-current");

    await new Promise<void>((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally {
    db.close();
  }
}
