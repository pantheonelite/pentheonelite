import { Card } from "../ui/card";

interface ActivePosition {
  id: number;
  symbol: string;
  side: "long" | "short";
  entry_price: number;
  current_price: number;
  quantity: number;
  leverage: number;
  unrealized_pnl: number;
  unrealized_pnl_percentage: number;
  opened_at: string;
  liquidation_price?: number;
}

interface Props {
  positions: ActivePosition[];
}

export function ActivePositionsTable({ positions }: Props) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else {
      return `${diffDays}d ago`;
    }
  };

  if (positions.length === 0) {
    return (
      <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-12 text-center">
        <p className="text-pantheon-text-secondary text-lg">
          No current positions
        </p>
      </Card>
    );
  }

  return (
    <Card className="bg-pantheon-cosmic-surface border-pantheon-border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-pantheon-cosmic-bg border-b border-pantheon-border">
            <tr>
              <th className="text-left py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Symbol
              </th>
              <th className="text-left py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Side
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Entry
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Current
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Quantity
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Notional Value
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Leverage
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Unrealized PnL
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Time
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-pantheon-border">
            {positions.map((position, index) => (
              <tr
                key={`${position.id}-${index}-${position.symbol}-${position.opened_at}`}
                className="hover:bg-pantheon-cosmic-bg/50 transition-colors"
              >
                <td className="py-4 px-6">
                  <span className="text-pantheon-text-primary font-bold text-lg">
                    {position.symbol}
                  </span>
                </td>
                <td className="py-4 px-6">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${
                      position.side === "long"
                        ? "bg-pantheon-secondary-500/20 text-pantheon-secondary-500"
                        : "bg-pantheon-accent-red/20 text-pantheon-accent-red"
                    }`}
                  >
                    {position.side}
                  </span>
                </td>
                <td className="py-4 px-6 text-right text-pantheon-text-primary font-mono">
                  {formatCurrency(position.entry_price)}
                </td>
                <td className="py-4 px-6 text-right text-pantheon-text-primary font-mono">
                  {formatCurrency(position.current_price)}
                </td>
                <td className="py-4 px-6 text-right text-pantheon-text-primary font-mono">
                  {position.quantity.toFixed(4)}
                </td>
                <td className="py-4 px-6 text-right text-pantheon-text-primary font-mono text-sm">
                  {formatCurrency(position.current_price * position.quantity)}
                </td>
                <td className="py-4 px-6 text-right">
                  <span className="text-pantheon-primary-500 font-bold">
                    {position.leverage}x
                  </span>
                </td>
                <td className="py-4 px-6 text-right">
                  <div
                    className={`font-bold font-mono ${
                      position.unrealized_pnl >= 0
                        ? "text-pantheon-secondary-500"
                        : "text-pantheon-accent-red"
                    }`}
                  >
                    {formatCurrency(position.unrealized_pnl)}
                  </div>
                  <div
                    className={`text-sm ${
                      position.unrealized_pnl >= 0
                        ? "text-pantheon-secondary-500"
                        : "text-pantheon-accent-red"
                    }`}
                  >
                    {formatPercentage(position.unrealized_pnl_percentage)}
                  </div>
                </td>
                <td className="py-4 px-6 text-right text-sm text-pantheon-text-secondary">
                  {formatDate(position.opened_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary footer */}
      <div className="bg-pantheon-cosmic-bg border-t border-pantheon-border px-6 py-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-pantheon-text-secondary">
            Current Positions: {positions.length}
          </span>
          <div className="text-right">
            <div className="text-sm text-pantheon-text-secondary mb-1">
              Total Unrealized PnL
            </div>
            <div
              className={`text-xl font-bold font-mono ${
                positions.reduce((sum, p) => sum + p.unrealized_pnl, 0) >= 0
                  ? "text-pantheon-secondary-500"
                  : "text-pantheon-accent-red"
              }`}
            >
              {formatCurrency(
                positions.reduce((sum, p) => sum + p.unrealized_pnl, 0)
              )}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

