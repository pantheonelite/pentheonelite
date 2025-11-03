"use client";

import { useEffect, useState } from "react";
import BehaviorAnalytics from "@/components/council/BehaviorAnalytics";
import DecisionCard from "@/components/council/DecisionCard";
import ExitPlanCard from "@/components/council/ExitPlanCard";

type Props = {
  councilId: number;
  baseUrl: string;
};

type Trade = {
  id: number;
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  created_at?: string;
};

type Debate = {
  id: number;
  role: string;
  content: string;
  created_at?: string;
};

type Position = {
  symbol: string;
  quantity: number;
  avg_entry_price: number;
  unrealized_pnl?: number;
};

export default function CouncilTabs({ councilId, baseUrl }: Props) {
  const [tab, setTab] = useState<string>("trades");

  return (
    <div className="bg-[--surface] border border-[--border] rounded-lg">
      <div className="flex flex-wrap gap-2 border-b border-[--border] p-2">
        {[
          { key: "trades", label: "Completed Trades" },
          { key: "debates", label: "Model Chat (Debates)" },
          { key: "positions", label: "Positions" },
          { key: "analytics", label: "Analytics" },
          { key: "readme", label: "README.TXT" },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all border ${
              tab === t.key
                ? "bg-[--primary-500] border-[--primary-600] text-white shadow"
                : "bg-[--background] border-[--border] text-[--text-secondary] hover:text-[--text-primary]"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="p-4">
        {tab === "trades" && <TradesPanel councilId={councilId} baseUrl={baseUrl} />}
        {tab === "debates" && <DebatesPanel councilId={councilId} baseUrl={baseUrl} />}
        {tab === "positions" && <PositionsPanel councilId={councilId} baseUrl={baseUrl} />}
        {tab === "analytics" && <AnalyticsPanel councilId={councilId} baseUrl={baseUrl} />}
        {tab === "readme" && <ReadmePanel />}
      </div>
    </div>
  );
}

function TradesPanel({ councilId, baseUrl }: Props) {
  const [trades, setTrades] = useState<Trade[]>([]);

  useEffect(() => {
    if (!baseUrl) return;
    const controller = new AbortController();
    (async () => {
      try {
        const res = await fetch(`${baseUrl}/api/v1/councils/${councilId}/trades?limit=50`, {
          signal: controller.signal,
        });
        if (res.ok) {
          setTrades(await res.json());
        }
      } catch {
        // Ignore fetch errors
      }
    })();
    return () => controller.abort();
  }, [baseUrl, councilId]);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-[--background]">
          <tr>
            <Th>Time</Th>
            <Th>Symbol</Th>
            <Th>Side</Th>
            <Th>Qty</Th>
            <Th>Price</Th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t) => (
            <tr key={t.id} className="border-t border-[--border]">
              <Td>{formatTime(t.created_at)}</Td>
              <Td>{t.symbol}</Td>
              <Td className={t.side === "BUY" ? "text-[--secondary-500]" : "text-[--accent-red]"}>{t.side}</Td>
              <Td>{t.quantity}</Td>
              <Td>${t.price?.toLocaleString()}</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DebatesPanel({ councilId, baseUrl }: Props) {
  const [debates, setDebates] = useState<Debate[]>([]);

  useEffect(() => {
    if (!baseUrl) return;
    const controller = new AbortController();
    (async () => {
      try {
        const res = await fetch(`${baseUrl}/api/v1/councils/${councilId}/debates?limit=50`, {
          signal: controller.signal,
        });
        if (res.ok) {
          setDebates(await res.json());
        }
      } catch {
        // Ignore fetch errors
      }
    })();
    return () => controller.abort();
  }, [baseUrl, councilId]);

  return (
    <div className="space-y-3">
      {debates.map((d) => (
        <div key={d.id} className="border border-[--border] rounded-lg p-3 bg-[--background]">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-[--primary-300] uppercase">{d.role}</div>
            <div className="text-xs text-[--text-secondary]">{formatTime(d.created_at)}</div>
          </div>
          <div className="mt-2 whitespace-pre-wrap text-sm leading-6">{d.content}</div>
        </div>
      ))}
      {debates.length === 0 && <div className="text-[--text-secondary]">No debates yet.</div>}
    </div>
  );
}

function PositionsPanel({ councilId, baseUrl }: Props) {
  const [positions, setPositions] = useState<Position[]>([]);

  useEffect(() => {
    if (!baseUrl) return;
    const controller = new AbortController();
    (async () => {
      try {
        // Using overview for now; replace with dedicated endpoint when available
        const res = await fetch(`${baseUrl}/api/v1/councils/${councilId}/overview`);
        if (res.ok) {
          const json = await res.json();
          const pos: Position[] = (json?.portfolio_overview?.positions || []).map((p: any) => ({
            symbol: p.symbol,
            quantity: p.quantity,
            avg_entry_price: p.avg_entry_price,
            unrealized_pnl: p.unrealized_pnl,
          }));
          setPositions(pos);
        }
      } catch {
        // Ignore fetch errors
      }
    })();
    return () => controller.abort();
  }, [baseUrl, councilId]);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-[--background]">
          <tr>
            <Th>Symbol</Th>
            <Th>Qty</Th>
            <Th>Avg Entry</Th>
            <Th>Unrealized PnL</Th>
          </tr>
        </thead>
        <tbody>
          {positions.map((p) => (
            <tr key={p.symbol} className="border-t border-[--border]">
              <Td>{p.symbol}</Td>
              <Td>{p.quantity}</Td>
              <Td>${p.avg_entry_price?.toLocaleString()}</Td>
              <Td className={(p.unrealized_pnl ?? 0) >= 0 ? "text-[--secondary-500]" : "text-[--accent-red]"}>
                {formatMoney(p.unrealized_pnl)}
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
      {positions.length === 0 && <div className="mt-3 text-[--text-secondary]">No open positions.</div>}
    </div>
  );
}

function AnalyticsPanel({ councilId, baseUrl }: Props) {
  const [trades, setTrades] = useState<Trade[]>([]);

  useEffect(() => {
    if (!baseUrl) return;
    const controller = new AbortController();
    (async () => {
      try {
        const res = await fetch(`${baseUrl}/api/v1/councils/${councilId}/trades?limit=200`, {
          signal: controller.signal,
        });
        if (res.ok) {
          setTrades(await res.json());
        }
      } catch {
        // Ignore fetch errors
      }
    })();
    return () => controller.abort();
  }, [baseUrl, councilId]);

  return (
    <div className="space-y-4">
      {/* Latest decision placeholders until backend provides structured actions */}
      <div className="grid md:grid-cols-2 gap-4">
        <DecisionCard decision={undefined} />
        <ExitPlanCard entryPrice={undefined} profit_target={undefined} stop_loss={undefined} invalidation_condition={undefined} />
      </div>
      <BehaviorAnalytics trades={trades} />
    </div>
  );
}

function ReadmePanel() {
  return (
    <div className="prose prose-invert max-w-none">
      <h3>README.TXT</h3>
      <p>
        This council view mirrors the model layout from the Alpha Arena and adapts it for
        multi-agent councils with debates and trades. Tabs above let you switch between
        Completed Trades, Model Chat (Debates), Positions, and this README.
      </p>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="p-3 text-left font-semibold text-[--text-primary]">{children}</th>;
}

function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`p-3 ${className}`}>{children}</td>;
}

function formatTime(iso?: string) {
  if (!iso) return "-";
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

function formatMoney(v?: number | null): string {
  if (v === null || v === undefined) return "-";
  const sign = v >= 0 ? "" : "-";
  return `${sign}$${Math.abs(v).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}
