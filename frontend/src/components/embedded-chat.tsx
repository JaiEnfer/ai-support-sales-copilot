"use client";

import { useEffect, useRef, useState } from "react";

import { buildApiUrl, buildRequestHeaders } from "@/lib/copilot";

type EmbeddedChatProps = {
  companyId: string;
  title: string;
  subtitle: string;
  apiKey?: string;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type ChatResponse = {
  answer: string;
  needs_human: boolean;
};

type ErrorPayload = {
  detail?: string;
};

export function EmbeddedChat({
  companyId,
  title,
  subtitle,
  apiKey,
}: EmbeddedChatProps) {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: subtitle,
    },
  ]);
  const [isSending, setIsSending] = useState(false);
  const messagesRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!messagesRef.current) {
      return;
    }
    messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
  }, [messages]);

  const sendMessage = async () => {
    const currentMessage = message.trim();
    if (!currentMessage || isSending) {
      return;
    }

    const history = messages
      .filter((item, index) => !(index === 0 && item.role === "assistant"))
      .map((item) => ({ role: item.role, content: item.content }));

    setMessages((prev) => [...prev, { role: "user", content: currentMessage }]);
    setMessage("");

    try {
      setIsSending(true);
      const response = await fetch(buildApiUrl("/api/chat"), {
        method: "POST",
        headers: buildRequestHeaders({
          json: true,
          apiKey,
          companyId,
        }),
        body: JSON.stringify({
          message: currentMessage,
          conversation_history: history,
          company_id: companyId,
        }),
      });

      const data = (await response.json()) as ChatResponse | ErrorPayload;
      if (!response.ok) {
        const errorPayload = data as ErrorPayload;
        throw new Error(errorPayload.detail || "Chat request failed.");
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: (data as ChatResponse).answer,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: error instanceof Error ? error.message : "Could not reach the assistant.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(88,166,255,0.18),_transparent_28%),linear-gradient(180deg,#0a1425_0%,#07111f_50%,#050d18_100%)] p-3 text-white">
      <div className="flex h-[calc(100vh-24px)] flex-col overflow-hidden rounded-[26px] border border-white/10 bg-[#0e1a2c]/95 shadow-[0_24px_80px_rgba(1,7,18,0.55)] backdrop-blur">
        <div className="border-b border-white/10 px-4 py-4">
          <p className="text-[11px] uppercase tracking-[0.18em] text-[#58a6ff]">Website Assistant</p>
          <h1 className="mt-2 text-lg font-semibold">{title}</h1>
          <p className="mt-1 text-sm text-[#9db0c9]">Company: {companyId}</p>
        </div>

        <div ref={messagesRef} className="flex-1 space-y-3 overflow-y-auto px-3 py-4">
          {messages.map((item, index) => (
            <div
              key={`${item.role}-${index}`}
              className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                item.role === "user"
                  ? "ml-auto bg-[linear-gradient(135deg,#58a6ff,#2f7df6)]"
                  : "border border-white/10 bg-white/5 text-white"
              }`}
            >
              {item.content}
            </div>
          ))}
        </div>

        <div className="border-t border-white/10 p-3">
          <div className="flex gap-2">
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void sendMessage();
                }
              }}
              placeholder="Ask a question..."
              className="min-h-[78px] flex-1 rounded-2xl border border-white/10 bg-white/6 px-4 py-3 text-sm text-white outline-none placeholder:text-[#8fa3bf]"
            />
            <button
              onClick={() => void sendMessage()}
              disabled={isSending}
              className="rounded-2xl bg-[linear-gradient(135deg,#58a6ff,#2f7df6)] px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
            >
              {isSending ? "Sending..." : "Send"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
