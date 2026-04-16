"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

type UploadResponse = {
    filename: string;
    status: string;
    message: string;
    document_id?: string;
    chunks_created?: number;
};

type DeleteDocumentResponse = {
  document_id: string;
  filename: string;
  status: string;
  message: string;
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
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [loadingRetrieve, setLoadingRetrieve] = useState(false);
  const [fileInputKey, setFileInputKey] = useState(0);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL;

  const getApiUrl = useCallback(
    (path: string) => (apiBase ? `${apiBase}${path}` : path),
    [apiBase]
  );

  const resetFileInput = () => {
    setFile(null);
    setFileInputKey((prev) => prev + 1);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const loadDocuments = useCallback(async () => {
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
  }, [getApiUrl]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  const handleUpload = async () => {
    if (!file) {
      fileInputRef.current?.click();
      setUploadResult(null);
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
      if (!response.ok) {
        throw new Error(data?.detail || "Upload failed.");
      }

      setUploadResult(data as UploadResponse);
      resetFileInput();
      await loadDocuments();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed.";
      setUploadResult({
        filename: file.name,
        status: "error",
        message,
      });
    } finally {
      setLoadingUpload(false);
    }
  };

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

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || "Search failed.");
      }

      setRetrieveResult(data as RetrieveResponse);
    } catch (error) {
      console.error("Retrieve failed", error);
      setRetrieveResult({ query, results: [] });
    } finally {
      setLoadingRetrieve(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    try {
      setDeletingDocumentId(documentId);

      const response = await fetch(getApiUrl(`/api/documents/${documentId}`), {
        method: "DELETE",
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || "Delete failed.");
      }

      const deleteResult = data as DeleteDocumentResponse;
      setUploadResult({
        filename: deleteResult.filename,
        status: deleteResult.status,
        message: deleteResult.message,
        document_id: deleteResult.document_id,
      });
      await loadDocuments();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Delete failed.";
      setUploadResult({
        filename: "",
        status: "error",
        message,
      });
    } finally {
      setDeletingDocumentId(null);
    }
  };

  return (
    <main className="min-h-screen px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="topbar flex items-center justify-between rounded-[28px] px-6 py-6">
          <div>
            <h1 className="text-3xl font-semibold tracking-[-0.04em] text-white">Admin</h1>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Upload documents and test retrieval.
            </p>
          </div>
          <Link
            href="/"
            className="rounded-full border border-[var(--border-strong)] bg-[var(--surface-strong)] px-4 py-2 text-sm text-white transition hover:bg-[var(--accent-soft)]"
          >
            Back
          </Link>
        </div>

        <section className="app-shell rounded-[28px] p-5 shadow-none">
          <p className="eyebrow">Upload</p>
          <h2 className="section-title mt-2 text-xl font-semibold text-white">Upload PDF</h2>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
            <input
              key={fileInputKey}
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="block rounded-xl text-sm text-[var(--muted)] file:mr-4 file:rounded-full file:border-0 file:bg-[var(--accent-soft)] file:px-4 file:py-2 file:text-sm file:font-medium file:text-white"
            />
            <button
              onClick={handleUpload}
              disabled={loadingUpload}
              className="accent-button rounded-full px-5 py-2.5 text-sm font-medium disabled:opacity-60"
            >
              {loadingUpload ? "Uploading..." : "Upload"}
            </button>
          </div>

          {file && (
            <p className="mt-3 text-sm text-[var(--muted)]">
              Selected document: <span className="font-medium text-white">{file.name}</span>
            </p>
          )}

          {uploadResult && (
            <div className="subtle-panel mt-4 rounded-2xl p-3 text-sm text-white">
              {uploadResult.filename && (
                <p>
                  Document: <span className="font-medium">{uploadResult.filename}</span>
                </p>
              )}
              <p className="mt-1">Status: {uploadResult.status}</p>
              <p className="mt-1 text-[var(--muted)]">{uploadResult.message}</p>
            </div>
          )}
        </section>

        <section className="app-shell rounded-[28px] p-5 shadow-none">
          <p className="eyebrow">Documents</p>
          <h2 className="section-title mt-2 text-xl font-semibold text-white">Documents</h2>
          <div className="mt-4 space-y-3">
            {loadingDocs ? (
              <p className="text-sm text-[var(--muted)]">Loading documents...</p>
            ) : documents.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">No documents uploaded yet.</p>
            ) : (
              documents.map((document) => (
                <div key={document.document_id} className="panel rounded-2xl p-3 text-white">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-medium">{document.filename}</p>
                      <p className="mt-1 text-sm text-[var(--muted)]">
                        Chunks: {document.chunks_created}
                      </p>
                    </div>
                    <button
                      onClick={() => void handleDeleteDocument(document.document_id)}
                      disabled={deletingDocumentId === document.document_id}
                      className="rounded-full border border-[var(--border-strong)] bg-[var(--surface-soft)] px-3 py-1.5 text-xs text-white disabled:opacity-60"
                    >
                      {deletingDocumentId === document.document_id ? "Removing..." : "Remove"}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="app-shell rounded-[28px] p-5 shadow-none">
          <p className="eyebrow">Retrieval</p>
          <h2 className="section-title mt-2 text-xl font-semibold text-white">Test Retrieval</h2>
          <div className="mt-4 flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search documents..."
              className="flex-1 rounded-2xl border border-[var(--border)] bg-[var(--surface-strong)] px-4 py-2 text-white outline-none placeholder:text-[var(--muted)]"
            />
            <button
              onClick={handleRetrieve}
              disabled={loadingRetrieve}
              className="rounded-full border border-[var(--border-strong)] bg-[var(--surface-strong)] px-5 py-2.5 text-sm text-white disabled:opacity-60"
            >
              {loadingRetrieve ? "Searching..." : "Search"}
            </button>
          </div>

          {retrieveResult && (
            <div className="mt-4 space-y-3">
              {retrieveResult.results.length === 0 ? (
                <p className="text-sm text-[var(--muted)]">No results found.</p>
              ) : (
                retrieveResult.results.map((item, index) => (
                  <div key={index} className="panel rounded-2xl p-3 text-white">
                    <p className="font-medium">
                      {item.filename} (chunk {item.chunk_index})
                    </p>
                    <p className="mt-2 text-sm text-[var(--muted)]">{item.content}</p>
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
