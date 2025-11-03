import { Card } from "../ui/card";

interface Trade {
  id: number;
  symbol: string;
  order_type: string;
  side: string;
  quantity: number;
  entry_price: number;
  exit_price?: number;
  pnl?: number;
  pnl_percentage?: number;
  status: string;
  opened_at: string;
  closed_at?: string;
}

interface Props {
  trades: Trade[];
}

export function RecentTradesTable({ trades }: Props) {

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getTimeAgo = (dateString: string) => {
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
    } else if (diffDays < 30) {
      return `${diffDays}d ago`;
    } else {
      return formatDate(dateString);
    }
  };

  const getHoldingTime = (openedAt: string, closedAt?: string) => {
    const startDate = new Date(openedAt);
    const endDate = closedAt ? new Date(closedAt) : new Date();
    const diffMs = endDate.getTime() - startDate.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return `${diffMins}m`;
    } else if (diffHours < 24) {
      return `${diffHours}h`;
    } else {
      return `${diffDays}d`;
    }
  };

  if (trades.length === 0) {
    return (
      <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-12 text-center">
        <p className="text-pantheon-text-secondary text-lg">No trades yet</p>
      </Card>
    );
  }

  return (
    <Card className="bg-pantheon-cosmic-surface border-pantheon-border overflow-hidden">

      {/* Trades table */}
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
                Entry Price
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Notional Entry
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Exit Price
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Notional Exit
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Qty
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Holding Time
              </th>
              <th className="text-right py-4 px-6 text-sm font-semibold text-pantheon-text-secondary uppercase tracking-wide">
                Time
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-pantheon-border">
            {trades.map((trade) => (
              <tr
                key={trade.id}
                className="hover:bg-pantheon-cosmic-bg/50 transition-colors"
              >
                <td className="py-4 px-6">
                  <span className="text-pantheon-text-primary font-bold">
                    {trade.symbol}
                  </span>
                </td>
                <td className="py-4 px-6">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${
                      trade.side.toLowerCase() === "buy"
                        ? "bg-pantheon-secondary-500/20 text-pantheon-secondary-500"
                        : "bg-pantheon-accent-red/20 text-pantheon-accent-red"
                    }`}
                  >
                    {trade.side.toLowerCase() === "buy" ? "LONG" : "SHORT"}
                  </span>
                </td>
                <td className="py-4 px-6 text-right text-pantheon-text-primary font-mono text-sm">
                  {formatCurrency(trade.entry_price)}
                </td>
                <td className="py-4 px-6 text-right text-pantheon-text-primary font-mono text-sm">
                  {formatCurrency(trade.entry_price * trade.quantity)}
                </td>
                <td className="py-4 px-6 text-right text-pantheon-text-primary font-mono text-sm">
                  {trade.exit_price
                    ? formatCurrency(trade.exit_price)
                    : "-"}
                </td>
                <td className="py-4 px-6 text-right text-pantheon-text-primary font-mono text-sm">
                  {trade.exit_price
                    ? formatCurrency(trade.exit_price * trade.quantity)
                    : "-"}
                </td>
                <td className="py-4 px-6 text-right text-pantheon-text-secondary text-sm">
                  {trade.quantity.toFixed(4)}
                </td>
                <td className="py-4 px-6 text-right text-pantheon-text-primary text-sm">
                  {getHoldingTime(trade.opened_at, trade.closed_at)}
                </td>
                <td className="py-4 px-6 text-right text-sm text-pantheon-text-secondary">
                  {getTimeAgo(trade.opened_at)}
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
            Showing {trades.length} trades
          </span>
          {trades.some((t) => t.pnl !== undefined) && (
            <div className="text-right">
              <div className="text-sm text-pantheon-text-secondary mb-1">
                Total Realized PnL
              </div>
              <div
                className={`text-xl font-bold font-mono ${
                  trades
                    .filter((t) => t.pnl !== undefined && t.status === "closed")
                    .reduce((sum, t) => sum + (t.pnl || 0), 0) >= 0
                    ? "text-pantheon-secondary-500"
                    : "text-pantheon-accent-red"
                }`}
              >
                {formatCurrency(
                  trades
                    .filter((t) => t.pnl !== undefined && t.status === "closed")
                    .reduce((sum, t) => sum + (t.pnl || 0), 0)
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
