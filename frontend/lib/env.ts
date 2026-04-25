const DEFAULT_API_URL = "http://localhost:8000";
const DEFAULT_SITE_URL = "http://localhost:3000";

function normalizeUrl(value: string | undefined, fallback: string, name: string): string {
  const trimmed = value?.trim();
  if (!trimmed) {
    if (process.env.NODE_ENV === "production") {
      throw new Error(`${name} is required in production.`);
    }
    return fallback;
  }
  return trimmed.replace(/\/$/, "");
}

export function getPublicApiBaseUrl(): string {
  return normalizeUrl(process.env.NEXT_PUBLIC_API_URL, DEFAULT_API_URL, "NEXT_PUBLIC_API_URL");
}

export function getServerApiBaseUrl(): string {
  return normalizeUrl(
    process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL,
    DEFAULT_API_URL,
    "INTERNAL_API_URL or NEXT_PUBLIC_API_URL"
  );
}

export function getSiteUrl(): string {
  return normalizeUrl(process.env.NEXT_PUBLIC_SITE_URL, DEFAULT_SITE_URL, "NEXT_PUBLIC_SITE_URL");
}
