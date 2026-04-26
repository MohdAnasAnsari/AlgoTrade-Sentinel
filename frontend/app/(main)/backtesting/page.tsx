import { redirect } from "next/navigation";

export const metadata = { title: "Backtesting Center" };

export default function BacktestingPage() {
  redirect("/backtesting-center");
}
