"use client";

import { useEffect, useState } from "react";

type CouncilOverview = {
  id: number;
  name: string;
  description?: string | null;
  total_pnl?: number | null;
  total_pnl_percentage?: number | null;
  win_rate?: number | null;
  status?: string | null;
};

type Props = {
  councilId: number;
  baseUrl: string;
};

export default function CouncilHeader({ councilId, baseUrl }: Props) {
  const [data, setData] = useState<CouncilOverview | null>(null);

  useEffect(() => {
    if (!baseUrl || !councilId) return;
    const controller = new AbortController();
    (async () => {
      try {
        const res = await fetch(
          `${baseUrl}/api/v1/councils/${councilId}/overview`,
          {
            signal: controller.signal,
          }
        );
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch {
        // ignore
      }
    })();
    return () => controller.abort();
  }, [baseUrl, councilId]);

  return (
    <div className="bg-[--surface] border border-[--border] rounded-lg p-4 shadow-[0_0_10px_var(--primary-300)]">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-[--text-primary]">
            {data?.name ?? `Council #${councilId}`}
          </h1>
          {data?.description ? (
            <p className="text-[--text-secondary] mt-1 max-w-3xl">
              {data.description}
            </p>
          ) : null}
        </div>
        <div className="grid grid-cols-3 gap-4">
          <Metric
            label="Total PnL"
            value={formatMoney(data?.total_pnl)}
            positive={Number(data?.total_pnl) >= 0}
          />
          <Metric
            label="PnL %"
            value={formatPercent(data?.total_pnl_percentage)}
            positive={Number(data?.total_pnl_percentage) >= 0}
          />
          <Metric
            label="Win Rate"
            value={formatPercent(data?.win_rate)}
            positive={true}
          />
        </div>
      </div>
      <div className="mt-4 h-2 w-full bg-[--background] rounded">
        <div
          className="h-2 rounded bg-[--primary-500] shadow-[0_0_6px_var(--shadow)]"
          style={{ width: "100%" }}
        />
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  positive,
}: {
  label: string;
  value: string;
  positive: boolean;
}) {
  return (
    <div className="bg-[--background] rounded-lg p-3 border border-[--border]">
      <div className="text-sm text-[--text-secondary] uppercase tracking-wide">
        {label}
      </div>
      <div
        className={`text-lg font-semibold ${
          positive ? "text-[--secondary-500]" : "text-[--accent-red]"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function formatMoney(v?: number | null): string {
  if (v === null || v === undefined) return "-";
  const sign = v >= 0 ? "" : "-";
  return `${sign}$${Math.abs(v).toLocaleString(undefined, {
    maximumFractionDigits: 2,
  })}`;
}

function formatPercent(v?: number | null): string {
  if (v === null || v === undefined) return "-";
  return `${(v * 100).toFixed(2)}%`;
}
