"use client";

type Trade = {
  id: number;
  side: string; // BUY/SELL
  quantity: number;
  created_at?: string;
};

type Props = {
  trades: Trade[];
};

export default function BehaviorAnalytics({ trades }: Props) {
  const mix = computeLongShortMix(trades);
  const freqPerDay = computeTradesPerDay(trades);
  const sizeStats = computeSizeStats(trades);

  return (
    <div className="grid md:grid-cols-3 gap-4">
      <Card title="Long vs Short Mix">
        <Stat label="Long" value={`${mix.long}%`} pos />
        <Stat label="Short" value={`${mix.short}%`} />
      </Card>
      <Card title="Trade Frequency">
        <Stat label="Trades / day" value={freqPerDay.toFixed(2)} />
      </Card>
      <Card title="Position Size (Qty)">
        <Stat label="Avg" value={fmt(sizeStats.avg)} />
        <Stat label="P50" value={fmt(sizeStats.p50)} />
        <Stat label="P90" value={fmt(sizeStats.p90)} />
      </Card>
    </div>
  );
}

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border border-[--border] bg-[--background] rounded-lg p-4">
      <div className="text-sm text-[--text-secondary] mb-2">{title}</div>
      <div className="grid grid-cols-3 gap-3 text-sm">{children}</div>
    </div>
  );
}

function Stat({
  label,
  value,
  pos = false,
}: {
  label: string;
  value: string;
  pos?: boolean;
}) {
  return (
    <div>
      <div className="text-xs uppercase text-[--text-secondary]">{label}</div>
      <div
        className={`mt-0.5 font-semibold ${
          pos ? "text-[--secondary-500]" : ""
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function computeLongShortMix(trades: Trade[]) {
  const total = trades.length || 1;
  const long = trades.filter((t) => t.side?.toUpperCase() === "BUY").length;
  const short = trades.filter((t) => t.side?.toUpperCase() === "SELL").length;
  return {
    long: Math.round((long / total) * 100),
    short: Math.round((short / total) * 100),
  };
}

function computeTradesPerDay(trades: Trade[]) {
  if (trades.length === 0) return 0;
  const times = trades
    .map((t) => (t.created_at ? new Date(t.created_at).getTime() : NaN))
    .filter((x) => !Number.isNaN(x))
    .sort((a, b) => a - b);
  if (times.length < 2) return trades.length; // insufficient window
  const days =
    (times[times.length - 1] - times[0]) / (1000 * 60 * 60 * 24) || 1;
  return trades.length / days;
}

function computeSizeStats(trades: Trade[]) {
  const sizes = trades
    .map((t) => Number(t.quantity || 0))
    .filter((n) => Number.isFinite(n))
    .sort((a, b) => a - b);
  if (sizes.length === 0) return { avg: 0, p50: 0, p90: 0 };
  const avg = sizes.reduce((a, b) => a + b, 0) / sizes.length;
  const p = (q: number) =>
    sizes[Math.min(sizes.length - 1, Math.floor(q * sizes.length))];
  return { avg, p50: p(0.5), p90: p(0.9) };
}

function fmt(n: number) {
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
