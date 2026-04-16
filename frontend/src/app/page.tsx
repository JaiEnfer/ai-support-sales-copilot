"use client";

import { useState } from "react";
import Link from "next/link";

type SourceItem = {
  title: string;
  snippet: string;
};

type ChatResponse = {
  answer: string;
  sources: SourceItem[];
  needs_human: boolean;
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [chatReply, setChatReply] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim()) return;

    try {
      setLoading(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          conversation_history: [],
          company_id: "startup-demo-001",
        }),
      });

      const data = await response.json();
      setChatReply(data);
      setMessage("");
    } catch (error) {
      setChatReply({
        answer: "Could not connect to backend.",
        sources: [],
        needs_human: true,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-4xl font-bold">AI Support + Sales Copilot</h1>
        <Link
          href="/admin"
          className="px-4 py-2 rounded-xl border bg-white hover:bg-gray-50"
        >
          Open Admin
        </Link>
      </div>

      <p className="text-lg mb-8">
        Startup-focused AI chatbot for support and lead conversion.
      </p>

      <div className="bg-white rounded-2xl shadow p-6">
        <h2 className="text-2xl font-semibold mb-4">Chat Demo</h2>

        <div className="flex gap-3">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask a question like: What does your pricing include?"
            className="flex-1 border rounded-xl px-4 py-3 outline-none"
          />
          <button
            onClick={sendMessage}
            className="px-4 py-3 rounded-xl bg-black text-white hover:opacity-90"
          >
            {loading ? "Sending..." : "Send"}
          </button>
        </div>

        {chatReply && (
          <div className="mt-6 border-t pt-4">
            <p className="mb-3">
              <strong>Answer:</strong> {chatReply.answer}
            </p>

            <p className="mb-3">
              <strong>Needs human:</strong> {chatReply.needs_human ? "Yes" : "No"}
            </p>

            <div>
              <strong>Sources:</strong>
              {chatReply.sources.length === 0 ? (
                <p className="text-sm text-gray-600 mt-2">No sources available.</p>
              ) : (
                <ul className="mt-2 space-y-2">
                  {chatReply.sources.map((source, index) => (
                    <li key={index} className="border rounded-xl p-3 bg-gray-50">
                      <p className="font-medium">{source.title}</p>
                      <p className="text-sm text-gray-600">{source.snippet}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}