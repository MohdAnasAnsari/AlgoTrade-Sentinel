import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "@/providers/theme-provider";
import { ToastProvider } from "@/providers/toast-provider";
import { QueryProvider } from "@/providers/query-provider";
import { getSiteUrl } from "@/lib/env";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });
const siteUrl = getSiteUrl();

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "AlgoTrade Sentinel",
    template: "%s | AlgoTrade Sentinel",
  },
  description:
    "AI-powered trading research, signal intelligence, backtesting, paper portfolio simulation, and MLOps platform.",
  applicationName: "AlgoTrade Sentinel",
  keywords: [
    "algorithmic trading",
    "paper trading",
    "mlops",
    "fastapi",
    "next.js",
    "monitoring",
    "model registry",
  ],
  openGraph: {
    title: "AlgoTrade Sentinel",
    description:
      "Research, monitor, and operate an end-to-end algo trading stack with market data, signals, backtesting, and MLOps.",
    url: siteUrl,
    siteName: "AlgoTrade Sentinel",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AlgoTrade Sentinel",
    description:
      "Research, monitor, and operate an end-to-end algo trading stack with market data, signals, backtesting, and MLOps.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          <QueryProvider>
            <ToastProvider>{children}</ToastProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
