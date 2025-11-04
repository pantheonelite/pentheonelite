import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ActivePositionData,
  AgentInfo,
  CouncilOverviewResponse,
  councilsV2Service,
  DebateMessage,
  TradeRecord,
  TradingMetrics,
} from "../../services/councils-v2-api";
import { ActivePositionsTable } from "../council/ActivePositionsTable";
import { RecentTradesTable } from "../council/RecentTradesTable";
import { TradingMetricsPanel } from "../council/TradingMetricsPanel";
import { Card } from "../ui/card";
import { Skeleton } from "../ui/skeleton";

interface DetailedCouncilData {
  overview: CouncilOverviewResponse;
  trading_metrics: TradingMetrics | null;
  active_positions: ActivePositionData[];
  recent_trades_list: TradeRecord[];
}

export function CouncilDetailPage() {
  const { councilId } = useParams<{ councilId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<DetailedCouncilData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!councilId) {
        setError("Council ID not provided");
        setLoading(false);
        return;
      }

      try {
        // Fetch council overview with all includes + metrics + positions + recent trades
        const [overview, metricsResponse, positionsResponse, tradesResponse] = await Promise.all([
          councilsV2Service.getCouncilOverview(parseInt(councilId), {
            includeAgents: true,
            includeDebates: true,
            includeTrades: false,
            includePortfolio: true,
          }),
          councilsV2Service.getTradingMetrics(parseInt(councilId))
            .catch(() => null),
          councilsV2Service.getActivePositions(parseInt(councilId))
            .then(res => res.positions)
            .catch(() => []),
          councilsV2Service.getRecentTrades(parseInt(councilId), 25)
            .catch(() => []),
        ]);

        setData({
          overview,
          trading_metrics: metricsResponse,
          active_positions: positionsResponse,
          recent_trades_list: tradesResponse,
        });
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load council data"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [councilId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-pantheon-cosmic-bg py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <Skeleton className="h-12 w-3/4 mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-64" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-pantheon-cosmic-bg py-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-pantheon-accent-red">
            {error || "Failed to load council data"}
          </p>
          <button
            onClick={() => navigate("/")}
            className="mt-4 px-6 py-2 bg-pantheon-primary-500 text-pantheon-text-primary rounded-lg hover:bg-pantheon-primary-600"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  const { overview, trading_metrics, active_positions, recent_trades_list } = data;
  const agents: AgentInfo[] = overview.agents || [];
  const recent_debates: DebateMessage[] = overview.recent_debates || [];
  const recent_trades: TradeRecord[] = overview.recent_trades || [];

  // Separate closed trades (for counting)
  // Closed: has exit price or explicitly closed status
  const closed_orders = recent_trades.filter(
    (t: TradeRecord) => t.exit_price || t.status === "closed"
  );

  // Use active_positions for open positions count (more accurate)
  // Prefer active_positions array if available, otherwise use overview.open_positions_count
  const open_positions_count = active_positions && active_positions.length > 0
    ? active_positions.length
    : (overview.open_positions_count || 0);
  const closed_positions_count = overview.closed_positions_count || closed_orders.length || 0;

  // Calculate total unrealized PnL for display
  const totalUnrealizedPnL = active_positions && active_positions.length > 0
    ? active_positions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0)
    : 0;

  // Format currency
  const formatCurrency = (value: string | number | null | undefined) => {
    if (!value && value !== 0) return "$0.00";
    const numValue = typeof value === "string" ? parseFloat(value) : value;
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(numValue);
  };

  // Format percentage
  const formatPercentage = (value: string | number | null | undefined) => {
    if (!value && value !== 0) return "0.00%";
    const num = typeof value === "string" ? parseFloat(value) : value;
    return `${num > 0 ? "+" : ""}${num.toFixed(2)}%`;
  };

  // Get sentiment color
  const getSentimentColor = (sentiment: string | null) => {
    if (!sentiment) return "text-pantheon-text-secondary";
    switch (sentiment.toLowerCase()) {
      case "bullish":
        return "text-pantheon-secondary-500";
      case "bearish":
        return "text-pantheon-accent-red";
      default:
        return "text-pantheon-accent-blue";
    }
  };

  return (
    <div className="min-h-screen bg-pantheon-cosmic-bg py-20 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Back button */}
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-pantheon-text-secondary hover:text-pantheon-primary-500 mb-6 transition-colors"
        >
          <ArrowLeft size={20} />
          Back to Arena
        </button>

        {/* Header */}
        <div className="mb-12">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-4xl md:text-5xl font-mythic font-bold text-pantheon-text-primary mb-2">
                {overview.name}
              </h1>
              <p className="text-lg text-pantheon-text-secondary max-w-3xl">
                {overview.description}
              </p>
            </div>
            {overview.is_public && (
              <span className="px-4 py-2 bg-pantheon-secondary-500/20 text-pantheon-secondary-500 rounded-full text-sm font-semibold">
                PUBLIC
              </span>
            )}
          </div>

          <div className="flex items-center gap-4 text-sm text-pantheon-text-secondary flex-wrap">
            <span className="flex items-center gap-2">
              <span className="font-semibold">Strategy:</span>{" "}
              {overview.strategy}
            </span>
            <span className="flex items-center gap-2">
              <span className="font-semibold">Wallet Name:</span>{" "}
              <span className="text-pantheon-primary-500">
                {overview.wallet_name || "Not set"}
              </span>
            </span>
          </div>
        </div>

        {/* Key Performance Metrics - List format */}
        <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-4 mb-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col items-center text-center">
              <span className="text-xs text-pantheon-text-secondary uppercase tracking-wide mb-1">
                Total P&L
              </span>
              <div
                className={`text-sm font-bold ${
                  (overview.total_pnl ?? 0) >= 0
                    ? "text-pantheon-secondary-500"
                    : "text-pantheon-accent-red"
                }`}
              >
                {formatCurrency(overview.total_pnl ?? 0)}
              </div>
              <div className="text-xs text-pantheon-text-secondary mt-0.5">
                {formatPercentage(overview.total_pnl_percentage ?? 0)}
              </div>
            </div>

            <div className="flex flex-col items-center text-center">
              <span className="text-xs text-pantheon-text-secondary uppercase tracking-wide mb-1">
                Win Rate
              </span>
              <div className="text-sm font-bold text-pantheon-text-primary">
                {overview.win_rate ? `${overview.win_rate.toFixed(0)}%` : "0%"}
              </div>
              <div className="text-xs text-pantheon-text-secondary mt-0.5">
                {overview.total_trades || 0} trades
              </div>
            </div>
          </div>
        </Card>

        {/* Other Performance metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
          <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-4 text-center">
            <div className="text-xs text-pantheon-text-secondary mb-1">
              Portfolio Value
            </div>
            <div className="text-lg font-bold text-pantheon-text-primary">
              {formatCurrency(overview.current_capital)}
            </div>
            <div className="text-xs text-pantheon-text-secondary mt-0.5">
              {totalUnrealizedPnL !== 0 && (
                <span
                  className={
                    totalUnrealizedPnL >= 0
                      ? "text-pantheon-secondary-500"
                      : "text-pantheon-accent-red"
                  }
                >
                  {totalUnrealizedPnL >= 0 ? "+" : ""}
                  {formatCurrency(totalUnrealizedPnL)} unrealized
                </span>
              )}
              {totalUnrealizedPnL === 0 && (
                <span>From {formatCurrency(overview.initial_capital)}</span>
              )}
            </div>
          </Card>

          <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-4 text-center">
            <div className="text-xs text-pantheon-text-secondary mb-1">
              Available Cash
            </div>
            <div className="text-lg font-bold text-pantheon-primary-500">
              {formatCurrency(overview.available_capital)}
            </div>
            <div className="text-xs text-pantheon-text-secondary mt-0.5">
              Ready to trade
            </div>
          </Card>

          <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-4 text-center">
            <div className="text-xs text-pantheon-text-secondary mb-1">
              Open Positions
            </div>
            <div className="text-lg font-bold text-pantheon-primary-500">
              {open_positions_count}
            </div>
            <div className="text-xs text-pantheon-text-secondary mt-0.5">
              {closed_positions_count} closed
            </div>
          </Card>

          <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-4 text-center">
            <div className="text-xs text-pantheon-text-secondary mb-1">
              Original Cash
            </div>
            <div className="text-lg font-bold text-pantheon-text-primary">
              {formatCurrency(overview.initial_capital)}
            </div>
            <div className="text-xs text-pantheon-text-secondary mt-0.5">
              -
            </div>
          </Card>
        </div>

        {/* Trading Metrics */}
        {trading_metrics && (
          <TradingMetricsPanel metrics={trading_metrics} />
        )}

        {/* Active Positions */}
        <div className="mb-12">
          <h2 className="text-2xl font-mythic font-semibold text-pantheon-text-primary mb-6">
            Active Positions
          </h2>
          <ActivePositionsTable positions={active_positions || []} />
        </div>

        {/* Recent Trades */}
        {recent_trades_list && recent_trades_list.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-mythic font-semibold text-pantheon-text-primary mb-6">
              Recent Trades (Last 25)
            </h2>
            <RecentTradesTable trades={recent_trades_list} />
          </div>
        )}

        {/* Council Members/Agents */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-pantheon-text-primary mb-4">
            Council Members
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {agents.map((agent: AgentInfo) => (
              <Card
                key={agent.id}
                className="bg-pantheon-cosmic-surface border-pantheon-border p-3"
              >
                <div className="flex items-start gap-3">
                  {/* Agent icon/avatar placeholder */}
                  <div className="w-10 h-10 rounded-full bg-pantheon-primary-500/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-lg font-bold text-pantheon-primary-500">
                      {agent.name.charAt(0)}
                    </span>
                  </div>

                  {/* Agent details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <div className="min-w-0">
                        <h3 className="text-sm font-semibold text-pantheon-text-primary truncate">
                          {agent.name}
                        </h3>
                        <p className="text-xs text-pantheon-primary-500 truncate">
                          {agent.role}
                        </p>
                      </div>
                      <span className="px-2 py-0.5 bg-pantheon-cosmic-bg rounded text-xs font-semibold text-pantheon-text-secondary uppercase flex-shrink-0">
                        {agent.type.replace("_", " ")}
                      </span>
                    </div>

                    {/* Traits */}
                    {agent.traits && agent.traits.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-1">
                        {agent.traits.slice(0, 3).map((trait: string, index: number) => (
                          <span
                            key={index}
                            className="px-1.5 py-0.5 bg-pantheon-primary-500/10 text-pantheon-primary-500 rounded text-xs"
                          >
                            {trait}
                          </span>
                        ))}
                        {agent.traits.length > 3 && (
                          <span className="px-1.5 py-0.5 text-pantheon-text-secondary rounded text-xs">
                            +{agent.traits.length - 3}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Specialty */}
                    {agent.specialty && (
                      <p className="text-xs text-pantheon-text-secondary truncate">
                        {agent.specialty}
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Agent Debates */}
        <div className="mt-6">
          <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-6">
            <h3 className="text-lg font-semibold text-pantheon-text-primary mb-4">
              Agent Debates
            </h3>
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {recent_debates.length === 0 ? (
                <p className="text-pantheon-text-secondary text-center py-8">
                  No debates available yet
                </p>
              ) : (
                recent_debates.map((debate: DebateMessage) => (
                  <div
                    key={debate.id}
                    className={`p-4 rounded-lg border ${
                      debate.message_type === "consensus"
                        ? "bg-pantheon-primary-500/10 border-pantheon-primary-500"
                        : "bg-pantheon-cosmic-bg border-pantheon-border"
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <span className="font-semibold text-pantheon-primary-500">
                          {debate.agent_name}
                        </span>
                        {debate.market_symbol && (
                          <span className="px-2 py-1 bg-pantheon-cosmic-bg rounded text-xs text-pantheon-text-secondary">
                            {debate.market_symbol}
                          </span>
                        )}
                        {debate.sentiment && (
                          <span
                            className={`text-xs font-medium ${getSentimentColor(
                              debate.sentiment
                            )}`}
                          >
                            {debate.sentiment.toUpperCase()}
                          </span>
                        )}
                      </div>
                      {debate.confidence && (
                        <span className="text-xs text-pantheon-text-secondary">
                          {(debate.confidence ?? 0) * 100}% confidence
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-pantheon-text-secondary leading-relaxed">
                      {debate.message}
                    </p>
                    {debate.created_at && (
                      <div className="text-xs text-pantheon-text-secondary mt-2">
                        {new Date(debate.created_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
