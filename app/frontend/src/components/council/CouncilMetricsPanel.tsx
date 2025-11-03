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

export function CouncilMetricsPanel({ metrics }: Props) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
      {/* Left Card: Statistics */}
      <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-6">
        <h3 className="text-lg font-semibold text-pantheon-text-primary mb-4 border-b border-pantheon-border pb-2">
          Trading Statistics
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-pantheon-text-secondary">
              Net Realized
            </span>
            <span
              className={`text-lg font-bold font-mono ${
                metrics.net_realized >= 0
                  ? "text-pantheon-secondary-500"
                  : "text-pantheon-accent-red"
              }`}
            >
              {formatCurrency(metrics.net_realized)}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-pantheon-text-secondary">
              Average Leverage
            </span>
            <span className="text-lg font-bold text-pantheon-primary-500">
              {metrics.average_leverage.toFixed(1)}X
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-pantheon-text-secondary">
              Average Confidence
            </span>
            <span className="text-lg font-bold text-pantheon-accent-blue">
              {formatPercentage(metrics.average_confidence)}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-pantheon-text-secondary">
              Biggest Win
            </span>
            <span className="text-lg font-bold text-pantheon-secondary-500">
              {formatCurrency(metrics.biggest_win)}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-pantheon-text-secondary">
              Biggest Loss
            </span>
            <span className="text-lg font-bold text-pantheon-accent-red">
              {formatCurrency(metrics.biggest_loss)}
            </span>
          </div>
        </div>
      </Card>

      {/* Right Card: Hold Times */}
      <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-6">
        <h3 className="text-lg font-semibold text-pantheon-text-primary mb-4 border-b border-pantheon-border pb-2">
          Hold Times
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-pantheon-text-secondary">Long:</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-pantheon-cosmic-bg rounded-full overflow-hidden">
                <div
                  className="h-full bg-pantheon-secondary-500"
                  style={{ width: `${metrics.hold_times.long}%` }}
                />
              </div>
              <span className="text-sm font-bold text-pantheon-secondary-500 w-12 text-right">
                {formatPercentage(metrics.hold_times.long)}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-pantheon-text-secondary">Short:</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-pantheon-cosmic-bg rounded-full overflow-hidden">
                <div
                  className="h-full bg-pantheon-accent-red"
                  style={{ width: `${metrics.hold_times.short}%` }}
                />
              </div>
              <span className="text-sm font-bold text-pantheon-accent-red w-12 text-right">
                {formatPercentage(metrics.hold_times.short)}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-pantheon-text-secondary">Flat:</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-pantheon-cosmic-bg rounded-full overflow-hidden">
                <div
                  className="h-full bg-pantheon-text-secondary"
                  style={{ width: `${metrics.hold_times.flat}%` }}
                />
              </div>
              <span className="text-sm font-bold text-pantheon-text-primary w-12 text-right">
                {formatPercentage(metrics.hold_times.flat)}
              </span>
            </div>
          </div>
        </div>

        {/* Summary */}
        <div className="mt-6 pt-4 border-t border-pantheon-border">
          <div className="text-xs text-pantheon-text-secondary text-center">
            Position distribution across trading directions
          </div>
        </div>
      </Card>
    </div>
  );
}
