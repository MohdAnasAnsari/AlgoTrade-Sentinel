import { BarChart2 } from "lucide-react";
import { PlaceholderPage } from "@/components/shared/placeholder-page";

export const metadata = { title: "Backtesting Center" };

export default function BacktestingPage() {
  return (
    <PlaceholderPage
      title="Backtesting Center"
      description="Run vectorized and event-driven backtests with detailed performance attribution and drawdown analysis."
      phase={2}
      icon={BarChart2}
      cards={[
        { title: "Backtest Runner", description: "Configure and launch backtests" },
        { title: "Performance Report", description: "Sharpe, drawdown, alpha, beta" },
        { title: "Trade Analysis", description: "Per-trade breakdown and heatmap" },
        { title: "Walk-Forward", description: "Out-of-sample validation" },
      ]}
    />
  );
}
