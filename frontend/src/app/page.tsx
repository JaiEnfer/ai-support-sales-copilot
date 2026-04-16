"use client";

import { useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("");
  const [backendReply, setBackendReply] = useState("No message yet.");
  const [loading, setLoading] = useState(false);

  const checkBackend = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/demo`);
      const data = await response.json();
      setBackendReply(data.reply);
    } catch (error) {
      setBackendReply("Could not connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => {
    if (!message.trim()) return;
    setBackendReply(`Demo user message captured: ${message}`);
    setMessage("");
  };

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold mb-4">
          AI Support + Sales Copilot
        </h1>

        <p className="text-lg mb-8">
          Startup-focused AI chatbot for support and lead conversion.
        </p>

        <div className="bg-white rounded-2xl shadow p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4">Backend Connection Test</h2>

          <button
            onClick={checkBackend}
            className="px-4 py-2 rounded-xl bg-black text-white hover:opacity-90"
          >
            {loading ? "Checking..." : "Check Backend"}
          </button>

          <p className="mt-4 text-base">
            <strong>Backend reply:</strong> {backendReply}
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-2xl font-semibold mb-4">Chat UI Starter</h2>

          <div className="flex gap-3">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type a customer question..."
              className="flex-1 border rounded-xl px-4 py-3 outline-none"
            />
            <button
              onClick={handleSend}
              className="px-4 py-3 rounded-xl bg-black text-white hover:opacity-90"
            >
              Send
            </button>
          </div>

          <p className="mt-4 text-sm text-gray-600">
            This is the UI base. Later, this input will send queries to the RAG chatbot backend.
          </p>
        </div>
      </div>
    </main>
  );
}