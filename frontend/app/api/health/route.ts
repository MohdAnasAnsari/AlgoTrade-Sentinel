import { NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/lib/env";

export async function GET() {
  const backendBaseUrl = getServerApiBaseUrl();
  try {
    const response = await fetch(`${backendBaseUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    const backend = await response.json();
    return NextResponse.json({
      frontend: { status: "ok", version: "0.1.0" },
      backend,
    });
  } catch {
    return NextResponse.json({
      frontend: { status: "ok", version: "0.1.0" },
      backend: { status: "unreachable", url: backendBaseUrl },
    });
  }
}
