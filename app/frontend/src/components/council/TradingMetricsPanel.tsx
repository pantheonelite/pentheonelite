import { Card } from "../ui/card";

interface TradingMetrics {
  net_realized: number;
  average_leverage: number;
  average_confidence: number;
  biggest_win: number;
  biggest_loss: number;
  hold_times: {
    long: number;
    short: number;
    flat: number;
  };
}

interface Props {
  metrics: TradingMetrics;
}

export function TradingMetricsPanel({ metrics }: Props) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
      {/* Left Card: Net Realized, Avg Leverage, Avg Confidence, Biggest Win, Biggest Loss */}
      <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-4">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-pantheon-text-secondary uppercase tracking-wide">
              Net Realized
            </span>
            <span
              className={`text-sm font-bold ${
                metrics.net_realized >= 0
                  ? "text-pantheon-secondary-500"
                  : "text-pantheon-accent-red"
              }`}
            >
              {formatCurrency(metrics.net_realized)}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-pantheon-text-secondary uppercase tracking-wide">
              Avg Leverage
            </span>
            <span className="text-sm font-bold text-pantheon-primary-500">
              {metrics.average_leverage.toFixed(1)}x
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-pantheon-text-secondary uppercase tracking-wide">
              Avg Confidence
            </span>
            <span className="text-sm font-bold text-pantheon-accent-blue">
              {formatPercentage(metrics.average_confidence)}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-pantheon-text-secondary uppercase tracking-wide">
              Biggest Win
            </span>
            <span className="text-sm font-bold text-pantheon-secondary-500">
              {formatCurrency(metrics.biggest_win)}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-pantheon-text-secondary uppercase tracking-wide">
              Biggest Loss
            </span>
            <span className="text-sm font-bold text-pantheon-accent-red">
              {formatCurrency(metrics.biggest_loss)}
            </span>
          </div>
        </div>
      </Card>

      {/* Right Card: Hold Times */}
      <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-4">
        <div className="flex flex-col">
          <div className="text-xs text-pantheon-text-secondary uppercase tracking-wide mb-3">
            Hold Times
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-pantheon-text-secondary">Long:</span>
              <span className="text-sm font-bold text-pantheon-secondary-500">
                {formatPercentage(metrics.hold_times.long)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-pantheon-text-secondary">Short:</span>
              <span className="text-sm font-bold text-pantheon-accent-red">
                {formatPercentage(metrics.hold_times.short)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-pantheon-text-secondary">Flat:</span>
              <span className="text-sm font-bold text-pantheon-text-primary">
                {formatPercentage(metrics.hold_times.flat)}
              </span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

