"use client";

import Link from "next/link";
import { BookOpen, Boxes, ExternalLink, HelpCircle, Workflow } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/shared/page-header";
import { getPublicApiBaseUrl } from "@/lib/env";

const FAQ = [
  ["How do I load demo data?", "Run the demo setup script or use `make seed` to populate market data, features, models, and portfolio history."],
  ["What powers the signals?", "Signals come from the registered classification model and fall back to labelled data when no live inference output exists yet."],
  ["Where do I inspect experiments?", "Use Training Lab for experiment history and Model Registry for champion/challenger promotion workflow."],
  ["How is monitoring generated?", "The monitoring flow compares the current feature window to the reference dataset and writes daily monitoring reports."],
  ["Can I paper trade without a broker?", "Yes. The paper portfolio engine simulates next-session execution using market open prices and transaction costs."],
  ["Where are deployment steps documented?", "The deployment docs in `docs/deployment/` cover local Docker, Vercel, Render, and Supabase."],
];

export default function HelpDocsPage() {
  const apiBase = getPublicApiBaseUrl();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Help / Docs"
        subtitle="Everything needed to explain, demo, deploy, and extend AlgoTrade Sentinel without leaving the product."
      />

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3">
              <BookOpen className="h-5 w-5 text-cyan-400" />
              <CardTitle className="text-slate-100">Getting Started</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-slate-300">
            <p>1. Start the stack with Docker or the local dev commands from the README.</p>
            <p>2. Seed market data and datasets with `make seed` or `scripts/demo_setup.sh`.</p>
            <p>3. Visit the Dashboard for portfolio and operations health, then walk the product left-to-right through research, ML, trading, and ops.</p>
            <p>4. Use Admin Settings to tune thresholds, watchlist membership, and paper portfolio defaults.</p>
            <p>5. Use the Monitoring Center and Model Registry to explain how models are governed after deployment.</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3">
              <Boxes className="h-5 w-5 text-cyan-400" />
              <CardTitle className="text-slate-100">Architecture Overview</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <pre className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-xs leading-6 text-slate-300">
{`Market Data -> Feature Store -> Training -> Model Registry
       |               |              |            |
       v               v              v            v
Market Explorer   Strategy Lab   Training Lab   Signal Center
       |                                           |
       +-----------------> Paper Portfolio <-------+
                                |
                                v
                         Monitoring Center`}
            </pre>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3">
              <Workflow className="h-5 w-5 text-cyan-400" />
              <CardTitle className="text-slate-100">Pipeline Flow</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <pre className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-xs leading-6 text-slate-300">
{`ingest_flow
   -> feature_flow
      -> training_flow
         -> inference_flow
            -> monitoring_flow
               -> retrain_trigger
                  -> retraining_flow`}
            </pre>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3">
              <HelpCircle className="h-5 w-5 text-cyan-400" />
              <CardTitle className="text-slate-100">Module Guide</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-300">
            <p><strong>Dashboard:</strong> live executive view of portfolio, signals, monitoring, and pipelines.</p>
            <p><strong>Market Explorer / Strategy Lab:</strong> inspect price data, engineered features, and dataset quality.</p>
            <p><strong>Training Lab / Registry:</strong> train models, compare experiments, and manage champion promotion.</p>
            <p><strong>Backtesting / Signals / Paper Portfolio:</strong> evaluate strategy behavior, produce signals, and simulate execution.</p>
            <p><strong>Monitoring Center / Admin Settings:</strong> operate the platform after deployment and tune system behavior.</p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-900">
        <CardHeader className="pb-3">
          <CardTitle className="text-slate-100">FAQ</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          {FAQ.map(([question, answer]) => (
            <div key={question} className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <p className="font-medium text-slate-100">{question}</p>
              <p className="mt-2 text-sm text-slate-400">{answer}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-900">
        <CardHeader className="pb-3">
          <CardTitle className="text-slate-100">Useful Links</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          {[
            { label: "README", href: "https://github.com/your-username/algotrade-sentinel#readme" },
            { label: "Deployment Docs", href: "/docs/deployment/local_docker.md" },
            { label: "Swagger Docs", href: `${apiBase}/docs` },
            { label: "ReDoc", href: `${apiBase}/redoc` },
            { label: "MLflow UI", href: "http://localhost:5000" },
          ].map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3 text-sm text-slate-200 transition hover:border-cyan-500/40 hover:text-white"
            >
              <span>{link.label}</span>
              <ExternalLink className="h-4 w-4 text-cyan-400" />
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
