import type { LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface PlaceholderCard {
  title: string;
  description: string;
}

interface PlaceholderPageProps {
  title: string;
  description: string;
  phase: number;
  icon: LucideIcon;
  cards?: PlaceholderCard[];
}

const DEFAULT_CARDS: PlaceholderCard[] = [
  { title: "Overview", description: "Summary metrics and KPIs" },
  { title: "Analytics", description: "Detailed analysis view" },
  { title: "Activity", description: "Recent activity feed" },
  { title: "Settings", description: "Module configuration" },
];

export function PlaceholderPage({
  title,
  description,
  phase,
  icon: Icon,
  cards = DEFAULT_CARDS,
}: PlaceholderPageProps) {
  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex flex-col gap-3">
        <div className="flex items-start gap-4">
          <div className="w-11 h-11 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0">
            <Icon className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-slate-100">{title}</h1>
              <Badge
                variant="outline"
                className="border-amber-500/40 text-amber-400 bg-amber-500/10 shrink-0"
              >
                Coming in Phase {phase}
              </Badge>
            </div>
            <p className="text-sm text-slate-400 mt-1">{description}</p>
          </div>
        </div>
      </div>

      {/* Top Stats Skeletons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card, i) => (
          <Card key={i} className="bg-slate-900 border-slate-800">
            <CardHeader className="pb-2 pt-5">
              <div className="flex items-center justify-between">
                <Skeleton className="h-3 w-20 bg-slate-800" />
                <Skeleton className="h-6 w-6 rounded bg-slate-800" />
              </div>
            </CardHeader>
            <CardContent>
              <Skeleton className="h-7 w-24 mb-2 bg-slate-800" />
              <Skeleton className="h-3 w-32 bg-slate-800" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 bg-slate-900 border-slate-800">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-36 bg-slate-800" />
              <Skeleton className="h-6 w-16 rounded bg-slate-800" />
            </div>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-52 w-full bg-slate-800 rounded-lg" />
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="pb-4">
            <Skeleton className="h-4 w-28 bg-slate-800" />
          </CardHeader>
          <CardContent className="space-y-2.5">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton
                key={i}
                className="h-11 w-full bg-slate-800 rounded-lg"
              />
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Bottom Row */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-44 bg-slate-800" />
            <Skeleton className="h-7 w-24 rounded bg-slate-800" />
          </div>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-36 w-full bg-slate-800 rounded-lg" />
        </CardContent>
      </Card>
    </div>
  );
}
