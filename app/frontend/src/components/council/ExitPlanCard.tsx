"use client";

type Props = {
  entryPrice?: number;
  profit_target?: number;
  stop_loss?: number;
  invalidation_condition?: string;
};

export default function ExitPlanCard({ entryPrice, profit_target, stop_loss, invalidation_condition }: Props) {
  return (
    <div className="border border-[--border] bg-[--background] rounded-lg p-4">
      <div className="text-sm text-[--text-secondary]">Exit Plan</div>
      <div className="mt-2 grid grid-cols-3 gap-3 text-sm">
        <Field label="Entry" value={formatMoney(entryPrice)} />
        <Field label="Target (TP)" value={formatMoney(profit_target)} />
        <Field label="Stop (SL)" value={formatMoney(stop_loss)} />
      </div>
      {invalidation_condition ? (
        <div className="mt-3 text-xs text-[--text-secondary]">
          Invalidation: <span className="text-[--text-primary]">{invalidation_condition}</span>
        </div>
      ) : null}
      <Bar entry={entryPrice} tp={profit_target} sl={stop_loss} />
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs uppercase text-[--text-secondary]">{label}</div>
      <div className="mt-0.5">{value}</div>
    </div>
  );
}

function Bar({ entry, tp, sl }: { entry?: number; tp?: number; sl?: number }) {
  // Simple relative bar visualization
  if (entry === undefined || entry === null) return null;
  const min = Math.min(sl ?? entry, entry, tp ?? entry);
  const max = Math.max(sl ?? entry, entry, tp ?? entry);
  const span = max - min || 1;
  const pct = (v?: number) => `${Math.round(((v ?? entry) - min) / span * 100)}%`;

  return (
    <div className="mt-4 h-2 w-full bg-[--surface] rounded relative">
      <div className="absolute top-0 h-2 w-0.5 bg-[--text-secondary]" style={{ left: pct(sl) }} />
      <div className="absolute top-0 h-2 w-0.5 bg-[--secondary-500]" style={{ left: pct(tp) }} />
      <div className="absolute top-0 h-2 w-0.5 bg-[--primary-500]" style={{ left: pct(entry) }} />
    </div>
  );
}

function formatMoney(v?: number): string {
  if (v === undefined || v === null) return "-";
  return `$${v.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}
