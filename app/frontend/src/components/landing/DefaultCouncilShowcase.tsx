import { useEffect, useState } from 'react';
import { AgentCard, PnLChart } from '../pantheon';
import { Card } from '../ui/card';
import { councilService, type DefaultCouncilData } from '../../services/councilService';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Skeleton } from '../ui/skeleton';

export function DefaultCouncilShowcase() {
  const [data, setData] = useState<DefaultCouncilData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const councilData = await councilService.getBestPerformingCouncil();
        setData(councilData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load council data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <section className="py-20 px-6 bg-pantheon-cosmic-bg">
        <div className="max-w-7xl mx-auto">
          <Skeleton className="h-12 w-3/4 mx-auto mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-64" />
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="py-20 px-6 bg-pantheon-cosmic-bg">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-pantheon-accent-red">
            {error || 'Failed to load council data'}
          </p>
        </div>
      </section>
    );
  }

  const { council, agents, recent_debates, open_orders, closed_orders, performance_history } = data;

  // Prepare chart data from performance history
  const chartLabels = performance_history.slice(-15).map((p) => {
    const date = new Date(p.timestamp);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  });

  const chartDatasets = [
    {
      label: council.name,
      data: performance_history.slice(-15).map((p) => parseFloat(p.pnl_percentage)),
      color: 'rgb(16, 185, 129)', // Emerald green
    },
  ];

  // Format currency
  const formatCurrency = (value: string | null | undefined) => {
    if (!value) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(parseFloat(value));
  };

  // Format percentage
  const formatPercentage = (value: string | null | undefined) => {
    if (!value) return '0.00%';
    const num = parseFloat(value);
    return `${num > 0 ? '+' : ''}${num.toFixed(2)}%`;
  };

  // Get sentiment color
  const getSentimentColor = (sentiment: string | null) => {
    if (!sentiment) return 'text-pantheon-text-secondary';
    switch (sentiment.toLowerCase()) {
      case 'bullish':
        return 'text-pantheon-secondary-500';
      case 'bearish':
        return 'text-pantheon-accent-red';
      default:
        return 'text-pantheon-accent-blue';
    }
  };

  return (
    <section id="live-council" className="py-20 px-6 bg-pantheon-cosmic-bg">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block px-4 py-2 bg-pantheon-primary-500/20 border border-pantheon-primary-500 rounded-full mb-4">
            <span className="text-pantheon-primary-500 font-semibold uppercase tracking-wider text-sm">
              🏆 Top Performing Council
            </span>
          </div>
          <h2 className="text-3xl md:text-4xl font-mythic font-bold text-pantheon-text-primary mb-4">
            {council.name}
          </h2>
          <p className="text-lg text-pantheon-text-secondary max-w-3xl mx-auto">
            {council.description}
          </p>
        </div>

        {/* Performance metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-6 text-center">
            <div className="text-sm text-pantheon-text-secondary mb-2">Total PnL</div>
            <div
              className={`text-2xl font-bold ${
                parseFloat(council.total_pnl || '0') >= 0
                  ? 'text-pantheon-secondary-500'
                  : 'text-pantheon-accent-red'
              }`}
            >
              {formatCurrency(council.total_pnl)}
            </div>
            <div className="text-sm text-pantheon-text-secondary mt-1">
              {formatPercentage(council.total_pnl_percentage)}
            </div>
          </Card>

          <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-6 text-center">
            <div className="text-sm text-pantheon-text-secondary mb-2">Win Rate</div>
            <div className="text-2xl font-bold text-pantheon-text-primary">
              {council.win_rate ? `${parseFloat(council.win_rate).toFixed(0)}%` : '0%'}
            </div>
            <div className="text-sm text-pantheon-text-secondary mt-1">
              {council.total_trades || 0} trades
            </div>
          </Card>

          <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-6 text-center">
            <div className="text-sm text-pantheon-text-secondary mb-2">Portfolio Value</div>
            <div className="text-2xl font-bold text-pantheon-text-primary">
              {formatCurrency(council.current_capital)}
            </div>
            <div className="text-sm text-pantheon-text-secondary mt-1">
              From {formatCurrency(council.initial_capital)}
            </div>
          </Card>

          <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-6 text-center">
            <div className="text-sm text-pantheon-text-secondary mb-2">Open Positions</div>
            <div className="text-2xl font-bold text-pantheon-primary-500">
              {open_orders.length}
            </div>
            <div className="text-sm text-pantheon-text-secondary mt-1">
              {closed_orders.length} closed
            </div>
          </Card>
        </div>

        {/* Performance chart */}
        <div className="mb-12">
          <PnLChart
            labels={chartLabels}
            datasets={chartDatasets}
            title="15-Day Performance History"
          />
        </div>

        {/* Council agents */}
        <div className="mb-12">
          <h3 className="text-2xl font-mythic font-semibold text-pantheon-text-primary text-center mb-8">
            Council Members
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {agents.map((agent) => (
              <AgentCard
                key={agent.id}
                name={agent.agent_name}
                traits={agent.traits || []}
              />
            ))}
          </div>
        </div>

        {/* Debates and Orders tabs */}
        <Tabs defaultValue="debates" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-pantheon-cosmic-surface border border-pantheon-border">
            <TabsTrigger value="debates">Agent Debates</TabsTrigger>
            <TabsTrigger value="orders">Market Orders</TabsTrigger>
          </TabsList>

          <TabsContent value="debates" className="mt-6">
            <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-6">
              <div className="space-y-4 max-h-[600px] overflow-y-auto">
                {recent_debates.length === 0 ? (
                  <p className="text-pantheon-text-secondary text-center py-8">
                    No debates available yet
                  </p>
                ) : (
                  recent_debates.map((debate) => (
                    <div
                      key={debate.id}
                      className={`p-4 rounded-lg border ${
                        debate.message_type === 'consensus'
                          ? 'bg-pantheon-primary-500/10 border-pantheon-primary-500'
                          : 'bg-pantheon-cosmic-bg border-pantheon-border'
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
                            <span className={`text-xs font-medium ${getSentimentColor(debate.sentiment)}`}>
                              {debate.sentiment.toUpperCase()}
                            </span>
                          )}
                        </div>
                        {debate.confidence && (
                          <span className="text-xs text-pantheon-text-secondary">
                            {parseFloat(debate.confidence).toFixed(0)}% confidence
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
          </TabsContent>

          <TabsContent value="orders" className="mt-6">
            <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-6">
              <div className="space-y-6">
                {/* Open Orders */}
                {open_orders.length > 0 && (
                  <div>
                    <h4 className="text-lg font-semibold text-pantheon-text-primary mb-4">
                      Open Positions ({open_orders.length})
                    </h4>
                    <div className="space-y-3">
                      {open_orders.map((order) => (
                        <div
                          key={order.id}
                          className="p-4 bg-pantheon-cosmic-bg border border-pantheon-primary-500 rounded-lg"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="flex items-center space-x-3">
                                <span className="text-lg font-bold text-pantheon-text-primary">
                                  {order.symbol}
                                </span>
                                <span className="px-2 py-1 bg-pantheon-secondary-500/20 text-pantheon-secondary-500 rounded text-xs font-semibold uppercase">
                                  {order.side}
                                </span>
                              </div>
                              <div className="text-sm text-pantheon-text-secondary mt-1">
                                Entry: {formatCurrency(order.entry_price)} × {parseFloat(order.quantity)} units
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm text-pantheon-text-secondary">
                                {new Date(order.opened_at).toLocaleDateString()}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Closed Orders */}
                {closed_orders.length > 0 && (
                  <div>
                    <h4 className="text-lg font-semibold text-pantheon-text-primary mb-4">
                      Recent Closed Trades ({closed_orders.length})
                    </h4>
                    <div className="space-y-3">
                      {closed_orders.map((order) => {
                        const pnl = parseFloat(order.pnl || '0');
                        const pnlPct = parseFloat(order.pnl_percentage || '0');
                        return (
                          <div
                            key={order.id}
                            className="p-4 bg-pantheon-cosmic-bg border border-pantheon-border rounded-lg"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="flex items-center space-x-3">
                                  <span className="text-lg font-bold text-pantheon-text-primary">
                                    {order.symbol}
                                  </span>
                                  <span className="text-sm text-pantheon-text-secondary uppercase">
                                    {order.side}
                                  </span>
                                </div>
                                <div className="text-sm text-pantheon-text-secondary mt-1">
                                  {formatCurrency(order.entry_price)} → {formatCurrency(order.exit_price || '0')}
                                </div>
                              </div>
                              <div className="text-right">
                                <div
                                  className={`text-lg font-bold font-mono ${
                                    pnl >= 0 ? 'text-pantheon-secondary-500' : 'text-pantheon-accent-red'
                                  }`}
                                >
                                  {formatCurrency(order.pnl)}
                                </div>
                                <div className="text-sm text-pantheon-text-secondary">
                                  {pnl >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {open_orders.length === 0 && closed_orders.length === 0 && (
                  <p className="text-pantheon-text-secondary text-center py-8">
                    No orders available yet
                  </p>
                )}
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
}
