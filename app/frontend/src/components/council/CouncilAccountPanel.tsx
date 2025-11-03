import { Card } from "../ui/card";

interface CouncilAccount {
  council_id: number;
  total_account_value: number;
  available_balance: number;
  used_balance: number;
  total_margin_used: number;
  total_unrealized_profit: number;
  total_realized_pnl: number;
  net_pnl: number;
  total_fees: number;
  trading_mode: "paper" | "real";
  trading_type: "futures" | "spot";
  initial_capital: number;
}

interface Props {
  account: CouncilAccount;
}

export function CouncilAccountPanel({ account }: Props) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const getTradingModeBadge = () => {
    if (account.trading_mode === "paper") {
      return (
        <span className="px-2 py-1 rounded text-xs font-semibold bg-pantheon-accent-blue/20 text-pantheon-accent-blue">
          📝 Paper Trading
        </span>
      );
    }
    return (
      <span className="px-2 py-1 rounded text-xs font-semibold bg-pantheon-accent-orange/20 text-pantheon-accent-orange">
        💰 Live Trading
      </span>
    );
  };

  const getTradingTypeBadge = () => {
    if (account.trading_type === "futures") {
      return (
        <span className="px-2 py-1 rounded text-xs font-semibold bg-pantheon-primary-500/20 text-pantheon-primary-500">
          📊 Futures
        </span>
      );
    }
    return (
      <span className="px-2 py-1 rounded text-xs font-semibold bg-pantheon-secondary-500/20 text-pantheon-secondary-500">
        💵 Spot
      </span>
    );
  };

  const pnlColor = account.total_unrealized_profit >= 0
    ? "text-pantheon-secondary-500"
    : "text-pantheon-accent-red";

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      {/* Card 1: Account Value */}
      <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-4">
        <div className="flex flex-col h-full">
          <div className="text-sm text-pantheon-text-secondary mb-2">
            Total Account Value
          </div>
          <div className="text-3xl font-bold text-pantheon-text-primary mb-2">
            {formatCurrency(account.total_account_value)}
          </div>
          <div className="flex gap-2 mt-auto">
            {getTradingModeBadge()}
            {getTradingTypeBadge()}
          </div>
        </div>
      </Card>

      {/* Card 2: Available Balance */}
      <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-4">
        <div className="flex flex-col h-full">
          <div className="text-sm text-pantheon-text-secondary mb-2">
            Available Cash
          </div>
          <div className="text-3xl font-bold text-pantheon-text-primary mb-2">
            {formatCurrency(account.available_balance)}
          </div>
          {account.trading_type === "futures" && (
            <div className="text-xs text-pantheon-text-secondary mt-auto">
              Margin Used: {formatCurrency(account.total_margin_used)}
            </div>
          )}
        </div>
      </Card>

      {/* Card 3: P&L Summary */}
      <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-4">
        <div className="flex flex-col h-full">
          <div className="text-sm text-pantheon-text-secondary mb-2">
            Total P&L
          </div>
          <div className={`text-3xl font-bold font-mono mb-2 ${pnlColor}`}>
            {formatCurrency(account.total_unrealized_profit)}
          </div>
          <div className="flex justify-between items-center text-xs text-pantheon-text-secondary mt-auto">
            <span>Net Realized: {formatCurrency(account.net_pnl)}</span>
            <span>Fees: {formatCurrency(account.total_fees)}</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
