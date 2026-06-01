"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ADMIN_API_KEY,
  buildApiUrl,
  buildRequestHeaders,
  DEFAULT_COMPANY_ID,
} from "@/lib/copilot";

type UploadResponse = {
  filename: string;
  status: string;
  message: string;
  document_id?: string;
  chunks_created?: number;
};

type WebsiteScrapeResponse = {
  document_id: string;
  company_id: string;
  status: string;
  message: string;
  source_url: string;
  pages_scraped: number;
  chunks_created: number;
};

type DeleteDocumentResponse = {
  document_id: string;
  filename: string;
  status: string;
  message: string;
};

type ClearTenantResponse = {
  company_id: string;
  deleted_documents: number;
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

type CompanyProfile = {
  company_id: string;
  display_name: string;
  answer_mode: "sales" | "support" | "portfolio";
  chatbot_title: string;
  chatbot_subtitle: string;
};

export default function AdminPage() {
  const [companyId, setCompanyId] = useState(DEFAULT_COMPANY_ID);
  const [profile, setProfile] = useState<CompanyProfile | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [scrapeResult, setScrapeResult] = useState<WebsiteScrapeResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [query, setQuery] = useState("");
  const [retrieveResult, setRetrieveResult] = useState<RetrieveResponse | null>(null);
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [loadingScrape, setLoadingScrape] = useState(false);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [loadingRetrieve, setLoadingRetrieve] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [clearingTenant, setClearingTenant] = useState(false);
  const [fileInputKey, setFileInputKey] = useState(0);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const getApiUrl = useCallback((path: string) => buildApiUrl(path), []);

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
      const response = await fetch(getApiUrl("/api/documents"), {
        headers: buildRequestHeaders({
          apiKey: ADMIN_API_KEY,
          companyId,
        }),
      });
      if (!response.ok) {
        throw new Error(`Document list failed with status ${response.status}.`);
      }
      const data: DocumentListResponse = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error("Failed to load documents", error);
      setDocuments([]);
    } finally {
      setLoadingDocs(false);
    }
  }, [companyId, getApiUrl]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  const loadCompanyProfile = useCallback(async () => {
    try {
      const response = await fetch(getApiUrl("/api/company-profile"), {
        headers: buildRequestHeaders({
          apiKey: ADMIN_API_KEY,
          companyId,
        }),
      });
      if (!response.ok) {
        throw new Error(`Company profile failed with status ${response.status}.`);
      }
      const data: CompanyProfile = await response.json();
      setProfile(data);
    } catch (error) {
      console.error("Failed to load company profile", error);
      setProfile(null);
    }
  }, [companyId, getApiUrl]);

  useEffect(() => {
    void loadCompanyProfile();
  }, [loadCompanyProfile]);

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
        headers: buildRequestHeaders({
          apiKey: ADMIN_API_KEY,
          companyId,
        }),
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
          ...buildRequestHeaders({
            json: true,
            apiKey: ADMIN_API_KEY,
            companyId,
          }),
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

  const handleWebsiteScrape = async () => {
    const normalizedUrl = websiteUrl.trim();
    if (!normalizedUrl) {
      return;
    }

    try {
      setLoadingScrape(true);
      setScrapeResult(null);

      const response = await fetch(getApiUrl("/api/documents/scrape"), {
        method: "POST",
        headers: buildRequestHeaders({
          json: true,
          apiKey: ADMIN_API_KEY,
          companyId,
        }),
        body: JSON.stringify({
          url: normalizedUrl,
          max_pages: 4,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || "Website scrape failed.");
      }

      setScrapeResult(data as WebsiteScrapeResponse);
      await loadDocuments();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Website scrape failed.";
      setScrapeResult({
        document_id: "",
        company_id: companyId,
        status: "error",
        message,
        source_url: normalizedUrl,
        pages_scraped: 0,
        chunks_created: 0,
      });
    } finally {
      setLoadingScrape(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    try {
      setDeletingDocumentId(documentId);

      const response = await fetch(getApiUrl(`/api/documents/${documentId}`), {
        method: "DELETE",
        headers: buildRequestHeaders({
          apiKey: ADMIN_API_KEY,
          companyId,
        }),
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

  const handleSaveProfile = async () => {
    if (!profile) {
      return;
    }

    try {
      setSavingProfile(true);
      const response = await fetch(getApiUrl("/api/company-profile"), {
        method: "PUT",
        headers: buildRequestHeaders({
          json: true,
          apiKey: ADMIN_API_KEY,
          companyId,
        }),
        body: JSON.stringify({
          display_name: profile.display_name,
          answer_mode: profile.answer_mode,
          chatbot_title: profile.chatbot_title,
          chatbot_subtitle: profile.chatbot_subtitle,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || "Could not save company profile.");
      }

      setProfile(data as CompanyProfile);
    } catch (error) {
      console.error("Failed to save company profile", error);
    } finally {
      setSavingProfile(false);
    }
  };

  const handleClearTenant = async () => {
    const confirmed = window.confirm(
      `Clear all knowledge base documents for company "${companyId}"? This is useful before a fresh demo scrape.`
    );
    if (!confirmed) {
      return;
    }

    try {
      setClearingTenant(true);
      const response = await fetch(getApiUrl("/api/documents"), {
        method: "DELETE",
        headers: buildRequestHeaders({
          apiKey: ADMIN_API_KEY,
          companyId,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || "Could not clear tenant knowledge base.");
      }

      const clearResult = data as ClearTenantResponse;
      setUploadResult({
        filename: `${clearResult.deleted_documents} documents`,
        status: clearResult.status,
        message: clearResult.message,
      });
      setScrapeResult(null);
      setRetrieveResult(null);
      await loadDocuments();
    } catch (error) {
      console.error("Failed to clear tenant knowledge base", error);
      setUploadResult({
        filename: "",
        status: "error",
        message: error instanceof Error ? error.message : "Could not clear tenant knowledge base.",
      });
    } finally {
      setClearingTenant(false);
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
          <p className="eyebrow">Tenant</p>
          <h2 className="section-title mt-2 text-xl font-semibold text-white">Company Workspace</h2>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
            <input
              type="text"
              value={companyId}
              onChange={(event) => setCompanyId(event.target.value)}
              placeholder="Company ID"
              className="flex-1 rounded-2xl border border-[var(--border)] bg-[var(--surface-strong)] px-4 py-2 text-white outline-none placeholder:text-[var(--muted)]"
            />
            <button
              onClick={() => void loadDocuments()}
              className="rounded-full border border-[var(--border-strong)] bg-[var(--surface-strong)] px-5 py-2.5 text-sm text-white"
            >
              Load tenant
            </button>
          </div>
          <p className="mt-3 text-sm text-[var(--muted)]">
            This dashboard now scopes uploads, retrieval, and deletes to one company.
          </p>
          <div className="mt-4">
            <button
              onClick={() => void handleClearTenant()}
              disabled={clearingTenant}
              className="rounded-full border border-[var(--border-strong)] bg-[var(--surface-strong)] px-5 py-2.5 text-sm text-white disabled:opacity-60"
            >
              {clearingTenant ? "Clearing..." : "Clear tenant knowledge base"}
            </button>
          </div>
        </section>

        <section className="app-shell rounded-[28px] p-5 shadow-none">
          <p className="eyebrow">Tone</p>
          <h2 className="section-title mt-2 text-xl font-semibold text-white">Chatbot Voice</h2>
          {profile ? (
            <div className="mt-4 space-y-4">
              <input
                type="text"
                value={profile.display_name}
                onChange={(event) =>
                  setProfile((prev) => (prev ? { ...prev, display_name: event.target.value } : prev))
                }
                placeholder="Display name"
                className="w-full rounded-2xl border border-[var(--border)] bg-[var(--surface-strong)] px-4 py-2 text-white outline-none placeholder:text-[var(--muted)]"
              />
              <select
                value={profile.answer_mode}
                onChange={(event) =>
                  setProfile((prev) =>
                    prev
                      ? {
                          ...prev,
                          answer_mode: event.target.value as CompanyProfile["answer_mode"],
                        }
                      : prev
                  )
                }
                className="w-full rounded-2xl border border-[var(--border)] bg-[var(--surface-strong)] px-4 py-2 text-white outline-none"
              >
                <option value="sales">Sales Mode</option>
                <option value="support">Support Mode</option>
                <option value="portfolio">Portfolio Mode</option>
              </select>
              <input
                type="text"
                value={profile.chatbot_title}
                onChange={(event) =>
                  setProfile((prev) => (prev ? { ...prev, chatbot_title: event.target.value } : prev))
                }
                placeholder="Chatbot title"
                className="w-full rounded-2xl border border-[var(--border)] bg-[var(--surface-strong)] px-4 py-2 text-white outline-none placeholder:text-[var(--muted)]"
              />
              <textarea
                value={profile.chatbot_subtitle}
                onChange={(event) =>
                  setProfile((prev) => (prev ? { ...prev, chatbot_subtitle: event.target.value } : prev))
                }
                placeholder="Chatbot subtitle"
                className="min-h-[92px] w-full rounded-[22px] border border-[var(--border)] bg-[var(--surface-strong)] px-4 py-3 text-white outline-none placeholder:text-[var(--muted)]"
              />
              <div className="flex items-center gap-3">
                <button
                  onClick={() => void handleSaveProfile()}
                  disabled={savingProfile}
                  className="accent-button rounded-full px-5 py-2.5 text-sm font-medium disabled:opacity-60"
                >
                  {savingProfile ? "Saving..." : "Save profile"}
                </button>
                <p className="text-sm text-[var(--muted)]">
                  Sales = client-ready demo tone. Support = calm help desk tone. Portfolio = professional profile tone.
                </p>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-[var(--muted)]">Loading company profile...</p>
          )}
        </section>

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
          <p className="eyebrow">Website</p>
          <h2 className="section-title mt-2 text-xl font-semibold text-white">Scrape Client Website</h2>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
            <input
              type="url"
              value={websiteUrl}
              onChange={(event) => setWebsiteUrl(event.target.value)}
              placeholder="https://client-website.com"
              className="flex-1 rounded-2xl border border-[var(--border)] bg-[var(--surface-strong)] px-4 py-2 text-white outline-none placeholder:text-[var(--muted)]"
            />
            <button
              onClick={() => void handleWebsiteScrape()}
              disabled={loadingScrape}
              className="accent-button rounded-full px-5 py-2.5 text-sm font-medium disabled:opacity-60"
            >
              {loadingScrape ? "Scraping..." : "Scrape website"}
            </button>
          </div>
          <p className="mt-3 text-sm text-[var(--muted)]">
            Great for demos: index the client homepage and a few linked pages, then ask questions in chat.
          </p>

          {scrapeResult && (
            <div className="subtle-panel mt-4 rounded-2xl p-3 text-sm text-white">
              <p>
                Source URL: <span className="font-medium">{scrapeResult.source_url}</span>
              </p>
              <p className="mt-1">Status: {scrapeResult.status}</p>
              <p className="mt-1">Pages scraped: {scrapeResult.pages_scraped}</p>
              <p className="mt-1">Chunks created: {scrapeResult.chunks_created}</p>
              <p className="mt-1 text-[var(--muted)]">{scrapeResult.message}</p>
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
