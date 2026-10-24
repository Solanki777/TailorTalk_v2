import type { ChatFile } from "../api/chat";

export type Message = {
  role: "user" | "assistant";
  content: string;
  files?: ChatFile[];
};