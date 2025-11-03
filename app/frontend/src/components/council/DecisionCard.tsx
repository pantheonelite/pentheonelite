"use client";

type Decision = {
  coin?: string;
  signal?: "buy" | "sell" | "hold" | "close" | string;
  quantity?: number;
  leverage?: number;
  profit_target?: number;
  stop_loss?: number;
  invalidation_condition?: string;
  confidence?: number; // 0..1
  justification?: string;
  timestamp?: string;
};

type Props = {
  decision?: Decision | null;
};

export default function DecisionCard({ decision }: Props) {
  const conf = decision?.confidence ?? null;
  const sig = (decision?.signal || "-").toUpperCase();
  const sideClass =
    sig === "BUY"
      ? "text-[--secondary-500]"
      : sig === "SELL"
      ? "text-[--accent-red]"
      : "text-[--text-primary]";

  return (
    <div className="border border-[--border] bg-[--background] rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="text-sm text-[--text-secondary]">Latest Decision</div>
        <ConfidenceBadge confidence={conf} />
      </div>
      <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <Field label="Coin" value={decision?.coin || "-"} />
        <Field
          label="Signal"
          value={<span className={`font-semibold ${sideClass}`}>{sig}</span>}
        />
        <Field
          label="Qty"
          value={decision?.quantity?.toLocaleString() ?? "-"}
        />
        <Field label="Lev" value={decision?.leverage ?? "-"} />
        <Field label="TP" value={formatMoney(decision?.profit_target)} />
        <Field label="SL" value={formatMoney(decision?.stop_loss)} />
        <Field
          label="Invalidation"
          value={decision?.invalidation_condition || "-"}
        />
        <Field label="Time" value={formatTime(decision?.timestamp)} />
      </div>
      {decision?.justification ? (
        <div className="mt-3 text-sm whitespace-pre-wrap leading-6">
          {decision.justification}
        </div>
      ) : null}
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase text-[--text-secondary]">{label}</div>
      <div className="mt-0.5">{value}</div>
    </div>
  );
}

function ConfidenceBadge({ confidence }: { confidence: number | null }) {
  if (confidence === null)
    return (
      <span className="text-xs px-2 py-1 rounded bg-[--surface] border border-[--border]">
        Conf: -
      </span>
    );
  const pct = Math.round(confidence * 100);
  const cls =
    pct >= 66
      ? "bg-[--secondary-600]"
      : pct >= 33
      ? "bg-[--accent-orange]"
      : "bg-[--accent-red]";
  return (
    <span className={`text-xs px-2 py-1 rounded text-white ${cls}`}>
      Conf: {pct}%
    </span>
  );
}

function formatMoney(v?: number): string {
  if (v === undefined || v === null) return "-";
  return `$${v.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function formatTime(iso?: string): string {
  if (!iso) return "-";
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
}
