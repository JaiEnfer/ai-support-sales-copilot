"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState, useTransition } from "react";

type ChatResponse = {
  answer: string;
  needs_human: boolean;
};

type ConversationMessage = {
  role: "user" | "assistant";
  content: string;
  needs_human?: boolean;
  animate?: boolean;
};

type DocumentRecord = {
  document_id: string;
  filename: string;
  chunks_created: number;
  created_at: string;
};

type DocumentListResponse = {
  documents: DocumentRecord[];
};

function AnimatedAssistantMessage({
  content,
  animate,
}: {
  content: string;
  animate?: boolean;
}) {
  const [visibleContent, setVisibleContent] = useState("");

  useEffect(() => {
    if (!animate) {
      return;
    }

    let index = 0;
    const chunkSize = Math.max(1, Math.ceil(content.length / 90));
    const intervalId = window.setInterval(() => {
      index += chunkSize;
      setVisibleContent(content.slice(0, index));

      if (index < content.length) {
        return;
      }
      window.clearInterval(intervalId);
    }, 18);

    return () => window.clearInterval(intervalId);
  }, [animate, content]);

  if (!animate) {
    return <div className="whitespace-pre-wrap text-sm leading-6">{content}</div>;
  }

  return (
    <div className="whitespace-pre-wrap text-sm leading-6">
      {visibleContent}
      {animate && visibleContent.length < content.length ? (
        <span className="ml-0.5 inline-block h-4 w-2 animate-pulse rounded-full bg-[var(--accent)] align-middle" />
      ) : null}
    </div>
  );
}

export default function Home() {
  const [message, setMessage] = useState("");
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [isPending, startTransition] = useTransition();
  const messagesRef = useRef<HTMLDivElement | null>(null);
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL;

  const getApiUrl = useCallback(
    (path: string) => (apiBase ? `${apiBase}${path}` : path),
    [apiBase]
  );

  useEffect(() => {
    if (!messagesRef.current) return;
    messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
  }, [conversation]);

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setLoadingDocs(true);
        const response = await fetch(getApiUrl("/api/documents"));
        const data: DocumentListResponse = await response.json();
        setDocuments(data.documents || []);
      } catch (error) {
        console.error("Failed to load documents", error);
      } finally {
        setLoadingDocs(false);
      }
    };

    void loadDocuments();
  }, [getApiUrl]);

  const sendMessage = async () => {
    const currentMessage = message.trim();
    if (!currentMessage || isPending) return;

    const userMessage: ConversationMessage = {
      role: "user",
      content: currentMessage,
    };

    startTransition(() => {
      setConversation((prev) => [...prev, userMessage]);
      setMessage("");
    });

    try {
      const response = await fetch(getApiUrl("/api/chat"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: currentMessage,
          conversation_history: conversation.map((item) => ({
            role: item.role,
            content: item.content,
          })),
          company_id: "startup-demo-001",
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || "Chat request failed.");
      }

      const chatResponse = data as ChatResponse;
      startTransition(() => {
        setConversation((prev) => [
          ...prev,
          {
            role: "assistant",
            content: chatResponse.answer,
            needs_human: chatResponse.needs_human,
            animate: true,
          },
        ]);
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Could not connect to backend.";

      startTransition(() => {
        setConversation((prev) => [
          ...prev,
          {
            role: "assistant",
            content: errorMessage,
            needs_human: true,
            animate: true,
          },
        ]);
      });
    }
  };

  const clearConversation = () => {
    startTransition(() => {
      setConversation([]);
      setMessage("");
    });
  };

  return (
    <main className="min-h-screen px-4 py-8">
      <div className="mx-auto max-w-6xl">
        <div className="topbar mb-6 flex flex-col gap-5 rounded-[28px] px-6 py-6 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <p className="eyebrow">Customer Workspace</p>
            <h1 className="section-title mt-3 text-4xl font-semibold text-white md:text-5xl">
              AI Support + Sales Copilot
            </h1>
            <p className="mt-3 text-base text-[var(--muted)]">
              Ask questions based on your uploaded documents.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden rounded-full border border-[var(--border-strong)] bg-[var(--surface-soft)] px-4 py-2 text-sm text-[var(--muted)] md:block">
              Grounded chat
            </div>
            <Link
              href="/admin"
              className="rounded-full border border-[var(--border-strong)] bg-[var(--surface-strong)] px-4 py-2 text-sm font-medium text-white transition hover:bg-[var(--accent-soft)]"
            >
              Open admin
            </Link>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
          <div className="app-shell rounded-[28px] p-4 sm:p-5">
            <div className="mb-4 flex items-center justify-between border-b border-[var(--border)] pb-4">
              <div>
                <p className="eyebrow">Live Chat</p>
                <h2 className="section-title mt-2 text-2xl font-semibold text-white">
                  Assistant Conversation
                </h2>
              </div>
              <button
                onClick={clearConversation}
                className="rounded-full border border-[var(--border-strong)] bg-[var(--surface-strong)] px-4 py-2 text-sm text-white transition hover:bg-[var(--accent-soft)]"
              >
                Clear chat
              </button>
            </div>

            <div
              ref={messagesRef}
              className="panel h-[470px] space-y-4 overflow-y-auto rounded-[24px] p-4"
            >
              {conversation.length === 0 ? (
                <div className="subtle-panel rounded-[22px] p-6">
                  <p className="text-sm text-[var(--muted)]">
                    Start a conversation by asking a question.
                  </p>
                </div>
              ) : (
                conversation.map((item, index) => (
                  <div
                    key={`${item.role}-${index}`}
                    className={`max-w-[86%] rounded-[22px] px-4 py-3.5 ${
                      item.role === "user"
                        ? "ml-auto bg-[linear-gradient(135deg,var(--accent),var(--accent-strong))] text-white shadow-[0_18px_35px_rgba(47,125,246,0.28)]"
                        : "panel text-white"
                    }`}
                  >
                    <p className="mb-2 text-[11px] uppercase tracking-[0.18em] opacity-70">
                      {item.role === "user" ? "You" : "Assistant"}
                    </p>
                    {item.role === "assistant" ? (
                      <AnimatedAssistantMessage
                        content={item.content}
                        animate={item.animate}
                      />
                    ) : (
                      <div className="whitespace-pre-wrap text-sm leading-6">{item.content}</div>
                    )}

                    {item.role === "assistant" && item.needs_human !== undefined && (
                      <p className="mt-3 text-xs text-[var(--muted)]">
                        Human follow-up: {item.needs_human ? "recommended" : "not needed"}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="mt-4 flex gap-3">
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Type your question..."
                className="min-h-[92px] flex-1 rounded-[22px] border border-[var(--border)] bg-[var(--surface-strong)] px-4 py-3 text-white outline-none placeholder:text-[var(--muted)]"
              />
              <div className="flex flex-col gap-2">
                <button
                  onClick={() => void sendMessage()}
                  disabled={isPending}
                  className="accent-button rounded-full px-5 py-2.5 text-sm font-medium disabled:opacity-60"
                >
                  {isPending ? "Sending..." : "Send"}
                </button>
                <button
                  onClick={clearConversation}
                  className="rounded-full border border-[var(--border-strong)] bg-[var(--surface-strong)] px-5 py-2.5 text-sm text-white"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="app-shell rounded-[28px] p-5">
              <p className="eyebrow">Documents</p>
              <h3 className="section-title mt-2 text-xl font-semibold text-white">
                Uploaded knowledge base
              </h3>
              <div className="mt-4 space-y-3">
                {loadingDocs ? (
                  <p className="text-sm text-[var(--muted)]">Loading documents...</p>
                ) : documents.length === 0 ? (
                  <p className="text-sm text-[var(--muted)]">No documents uploaded yet.</p>
                ) : (
                  documents.map((document) => (
                    <div
                      key={document.document_id}
                      className="subtle-panel rounded-2xl px-4 py-3"
                    >
                      <p className="text-sm font-medium text-white">{document.filename}</p>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        Chunks: {document.chunks_created}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="app-shell rounded-[28px] p-5">
              <p className="eyebrow">Status</p>
              <div className="mt-3 space-y-3">
                <div className="subtle-panel flex items-center justify-between rounded-2xl px-4 py-3">
                  <span className="text-sm text-[var(--muted)]">Conversation</span>
                  <span className="text-sm font-medium text-white">
                    {conversation.length === 0 ? "Empty" : "Active"}
                  </span>
                </div>
                <div className="subtle-panel flex items-center justify-between rounded-2xl px-4 py-3">
                  <span className="text-sm text-[var(--muted)]">Messages</span>
                  <span className="text-sm font-medium text-white">
                    {conversation.length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
