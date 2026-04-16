"use client";

import { useEffect, useRef, useState } from "react";

type UploadResponse = {
  filename: string;
  status: string;
  message: string;
  document_id?: string;
  chunks_created?: number;
};

type DocumentRecord = {
  document_id: string;
  filename: string;
  chunks_created: number;
};

type DocumentListResponse = {
  documents: DocumentRecord[];
};

type RetrieveResult = {
  content: string;
  filename: string;
  chunk_index: number;
};

type RetrieveResponse = {
  query: string;
  results: RetrieveResult[];
};

export default function AdminPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [query, setQuery] = useState("");
  const [retrieveResult, setRetrieveResult] = useState<RetrieveResponse | null>(null);

  const [loadingUpload, setLoadingUpload] = useState(false);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [loadingRetrieve, setLoadingRetrieve] = useState(false);

  const [fileInputKey, setFileInputKey] = useState(0);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL;

  const getApiUrl = (path: string) => apiBase ? `${apiBase}${path}` : path;

  const resetFileInput = () => {
    setFile(null);
    setFileInputKey((prev) => prev + 1);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // ================= LOAD DOCUMENTS =================
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

  useEffect(() => {
    loadDocuments();
  }, []);

  // ================= UPLOAD =================
  const handleUpload = async () => {
    if (!file) {
      if (fileInputRef.current) {
        fileInputRef.current.click();
      }
      setUploadResult(null);
      return;
    }

    if (!apiBase) {
      setUploadResult({
        filename: file.name,
        status: "error",
        message: "NEXT_PUBLIC_API_BASE_URL is not set.",
      });
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoadingUpload(true);

      const response = await fetch(getApiUrl("/api/documents/upload"), {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setUploadResult(data);

      if (response.ok) {
        resetFileInput();
        await loadDocuments();
      }
    } catch (error) {
      console.error("Upload failed", error);
      setUploadResult({
        filename: file.name,
        status: "error",
        message: "Upload failed. Check backend.",
      });
    } finally {
      setLoadingUpload(false);
    }
  };

  // ================= RETRIEVE =================
  const handleRetrieve = async () => {
    if (!query.trim()) return;

    try {
      setLoadingRetrieve(true);

      const response = await fetch(getApiUrl("/api/documents/retrieve"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          top_k: 4,
        }),
      });

      const data: RetrieveResponse = await response.json();
      setRetrieveResult(data);
    } catch (error) {
      console.error("Retrieve failed", error);
    } finally {
      setLoadingRetrieve(false);
    }
  };

  // ================= UI =================
  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 p-8">
      <div className="max-w-5xl mx-auto space-y-8">

        {/* HEADER */}
        <div>
          <h1 className="text-4xl font-bold">Admin Knowledge Base</h1>
          <p className="text-lg mt-2 text-gray-600">
            Upload company PDFs and test retrieval before customers use the chatbot.
          </p>
        </div>

        {/* ================= UPLOAD ================= */}
        <section className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-2xl font-semibold mb-4">Upload PDF</h2>

          <div className="flex gap-3 items-center">
            <input
              key={fileInputKey}
              ref={fileInputRef}
              name="file"
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block"
            />

            <button
              type="button"
              onClick={handleUpload}
              disabled={loadingUpload}
              className="px-4 py-2 rounded-xl bg-black text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loadingUpload ? "Uploading..." : "Upload"}
            </button>
          </div>

          {file && (
            <p className="text-sm text-gray-600 mt-2">
              Selected: {file.name}
            </p>
          )}

          {uploadResult && (
            <div className="mt-4 rounded-xl border p-4 bg-gray-50">
              <p><strong>Status:</strong> {uploadResult.status}</p>
              <p><strong>Message:</strong> {uploadResult.message}</p>

              {uploadResult.document_id && (
                <p><strong>Document ID:</strong> {uploadResult.document_id}</p>
              )}

              {uploadResult.chunks_created !== undefined && (
                <p><strong>Chunks created:</strong> {uploadResult.chunks_created}</p>
              )}
            </div>
          )}
        </section>

        {/* ================= DOCUMENT LIST ================= */}
        <section className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-2xl font-semibold mb-4">Ingested Documents</h2>

          {loadingDocs ? (
            <p>Loading documents...</p>
          ) : documents.length === 0 ? (
            <p className="text-gray-600">No documents uploaded yet.</p>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div key={doc.document_id} className="rounded-xl border p-4 bg-gray-50">
                  <p className="font-medium">{doc.filename}</p>
                  <p className="text-sm text-gray-600">Document ID: {doc.document_id}</p>
                  <p className="text-sm text-gray-600">Chunks: {doc.chunks_created}</p>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* ================= RETRIEVAL ================= */}
        <section className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-2xl font-semibold mb-4">Test Retrieval</h2>

          <div className="flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search the knowledge base..."
              className="flex-1 border rounded-xl px-4 py-3 outline-none"
            />

            <button
              onClick={handleRetrieve}
              disabled={loadingRetrieve}
              className="px-4 py-3 rounded-xl bg-black text-white disabled:opacity-50"
            >
              {loadingRetrieve ? "Searching..." : "Search"}
            </button>
          </div>

          {retrieveResult && (
            <div className="mt-6 space-y-3">
              {retrieveResult.results.length === 0 ? (
                <div className="rounded-xl border p-4 bg-gray-50 text-gray-600">
                  No matching chunks found.
                </div>
              ) : (
                retrieveResult.results.map((item, index) => (
                  <div key={index} className="rounded-xl border p-4 bg-gray-50">
                    <p className="font-medium">
                      {item.filename} (chunk {item.chunk_index})
                    </p>
                    <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">
                      {item.content}
                    </p>
                  </div>
                ))
              )}
            </div>
          )}
        </section>

      </div>
    </main>
  );
}