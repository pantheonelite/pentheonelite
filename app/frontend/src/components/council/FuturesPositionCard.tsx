import { Card } from "../ui/card";

interface FuturesPosition {
  id: number;
  symbol: string;
  side: "long" | "short" | "both";
  entry_price: number;
  current_price: number;
  quantity: number;
  leverage: number;
  unrealized_pnl: number;
  unrealized_pnl_percentage: number;
  opened_at: string;
  liquidation_price?: number;
  margin_used?: number;
  notional?: number;
}

interface Props {
  position: FuturesPosition;
  onClose?: (positionId: number) => void;
}

export function FuturesPositionCard({ position, onClose }: Props) {
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
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / 3600000);
    const diffMins = Math.floor((diffMs % 3600000) / 60000);

    if (diffHours < 1) {
      return `${diffMins}M`;
    } else if (diffHours < 24) {
      return `${diffHours}H ${diffMins}M`;
    } else {
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}D ${diffHours % 24}H`;
    }
  };

  const getTimeDisplay = (dateString: string) => {
    const date = new Date(dateString);
    const hours = date.getHours().toString().padStart(2, "0");
    const mins = date.getMinutes().toString().padStart(2, "0");
    const secs = date.getSeconds().toString().padStart(2, "0");
    return `${hours}:${mins}:${secs}`;
  };

  const getLiquidationDistance = () => {
    if (!position.liquidation_price || position.liquidation_price === 0) return null;

    const distance = position.side === "long"
      ? ((position.liquidation_price - position.current_price) / position.current_price) * 100
      : ((position.current_price - position.liquidation_price) / position.current_price) * 100;

    return distance;
  };

  const liquidationDistance = getLiquidationDistance();
  const pnlColor = position.unrealized_pnl >= 0
    ? "text-pantheon-secondary-500"
    : "text-pantheon-accent-red";

  const sideColor = position.side === "long" || position.side === "both"
    ? "bg-pantheon-secondary-500/20 text-pantheon-secondary-500"
    : "bg-pantheon-accent-red/20 text-pantheon-accent-red";

  return (
    <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-4 hover:bg-pantheon-cosmic-surface/80 transition-colors">
      {/* Header: Symbol and Side */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-xl font-bold text-pantheon-text-primary">
            {position.symbol}
          </span>
          <span className={`px-2 py-1 rounded-full text-xs font-semibold uppercase ${sideColor}`}>
            {position.side}
          </span>
        </div>
        {onClose && (
          <button
            onClick={() => onClose(position.id)}
            className="text-xs text-pantheon-text-secondary hover:text-pantheon-accent-red transition-colors"
          >
            Close Position
          </button>
        )}
      </div>

      {/* Entry Info */}
      <div className="grid grid-cols-2 gap-4 mb-3">
        <div>
          <div className="text-xs text-pantheon-text-secondary mb-1">Entry Time</div>
          <div className="text-sm font-mono text-pantheon-text-primary">
            {getTimeDisplay(position.opened_at)}
          </div>
        </div>
        <div>
          <div className="text-xs text-pantheon-text-secondary mb-1">Entry Price</div>
          <div className="text-sm font-mono text-pantheon-text-primary">
            {formatCurrency(position.entry_price)}
          </div>
        </div>
      </div>

      {/* Position Details */}
      <div className="grid grid-cols-2 gap-4 mb-3">
        <div>
          <div className="text-xs text-pantheon-text-secondary mb-1">Quantity</div>
          <div className="text-sm font-mono text-pantheon-text-primary">
            {position.quantity.toFixed(4)}
          </div>
        </div>
        <div>
          <div className="text-xs text-pantheon-text-secondary mb-1">Leverage</div>
          <div className="text-sm font-bold text-pantheon-primary-500">
            {position.leverage}X
          </div>
        </div>
      </div>

      {/* Risk Metrics */}
      {position.liquidation_price && position.liquidation_price > 0 && (
        <div className="grid grid-cols-2 gap-4 mb-3">
          <div>
            <div className="text-xs text-pantheon-text-secondary mb-1">Liquidation Price</div>
            <div className="text-sm font-mono text-pantheon-accent-orange">
              {formatCurrency(position.liquidation_price)}
            </div>
          </div>
          {liquidationDistance !== null && (
            <div>
              <div className="text-xs text-pantheon-text-secondary mb-1">Distance to Liq</div>
              <div className={`text-sm font-semibold ${
                liquidationDistance < 5 ? "text-pantheon-accent-red" :
                liquidationDistance < 15 ? "text-pantheon-accent-orange" :
                "text-pantheon-secondary-500"
              }`}>
                {liquidationDistance > 0 ? "+" : ""}{liquidationDistance.toFixed(2)}%
                {liquidationDistance < 5 && " ⚠️"}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Margin Info */}
      {position.margin_used && (
        <div className="mb-3">
          <div className="text-xs text-pantheon-text-secondary mb-1">Margin Used</div>
          <div className="text-sm font-mono text-pantheon-text-primary">
            {formatCurrency(position.margin_used)}
          </div>
        </div>
      )}

      {/* PnL Display */}
      <div className="border-t border-pantheon-border pt-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-pantheon-text-secondary mb-1">Unrealized P&L</div>
            <div className={`text-lg font-bold font-mono ${pnlColor}`}>
              {formatCurrency(position.unrealized_pnl)}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-pantheon-text-secondary mb-1">Holding Time</div>
            <div className="text-sm font-semibold text-pantheon-text-primary">
              {formatDate(position.opened_at)}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
