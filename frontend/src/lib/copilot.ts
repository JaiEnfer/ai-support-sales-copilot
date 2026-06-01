export const DEFAULT_COMPANY_ID =
  process.env.NEXT_PUBLIC_DEFAULT_COMPANY_ID || "startup-demo-001";

export const CHAT_API_KEY = process.env.NEXT_PUBLIC_CHAT_API_KEY || "";
export const ADMIN_API_KEY = process.env.NEXT_PUBLIC_ADMIN_API_KEY || "";
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";
export const SHOW_ADMIN_LINK =
  process.env.NEXT_PUBLIC_SHOW_ADMIN_LINK === "true";

export function buildApiUrl(path: string) {
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

export function buildRequestHeaders(options?: {
  apiKey?: string;
  companyId?: string;
  json?: boolean;
}) {
  const headers: Record<string, string> = {};

  if (options?.json) {
    headers["Content-Type"] = "application/json";
  }

  if (options?.apiKey) {
    headers["X-API-Key"] = options.apiKey;
  }

  if (options?.companyId) {
    headers["X-Company-ID"] = options.companyId;
  }

  return headers;
}
