/**
 * Global Activity Feed Component
 *
 * Displays recent debates and trades across all system councils.
 * Features real-time updates via WebSocket and polling.
 */

import { useEffect, useState, useRef } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Card } from '../ui/card';
import { Skeleton } from '../ui/skeleton';
import { MessageSquare, TrendingUp, Filter } from 'lucide-react';
import type { DebateMessage, TradeRecord } from '../../services/system-councils-api';
import { systemCouncilsService } from '../../services/system-councils-api';
import { useCouncilWebSocketContext } from '../../contexts/CouncilWebSocketProvider';
import { toast } from 'sonner';

interface EnrichedDebate extends DebateMessage {
  councilId: number;
  councilName: string;
}

interface EnrichedTrade extends TradeRecord {
  councilId: number;
  councilName: string;
}

export function GlobalActivityFeed() {
  const [debates, setDebates] = useState<EnrichedDebate[]>([]);
  const [trades, setTrades] = useState<EnrichedTrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCouncil, setSelectedCouncil] = useState<number | null>(null);
  const [councilNames, setCouncilNames] = useState<Map<number, string>>(new Map());

  const debatesEndRef = useRef<HTMLDivElement>(null);
  const tradesEndRef = useRef<HTMLDivElement>(null);

  // WebSocket for real-time updates
  const { isConnected, addTradeListener, removeTradeListener, addConsensusListener, removeConsensusListener } = useCouncilWebSocketContext();

  // Register WebSocket listeners
  useEffect(() => {
    const listenerId = 'global-activity-feed';

    // Trade listener
    const handleTrade = (tradeEvent: any) => {
      // Add new trade to the list
      const newTrade: EnrichedTrade = {
        id: Date.now(), // Temporary ID
        symbol: tradeEvent.symbol,
        order_type: 'market',
        side: tradeEvent.side,
        quantity: tradeEvent.quantity,
        entry_price: tradeEvent.price,
        exit_price: null,
        pnl: null,
        pnl_percentage: null,
        status: 'open',
        opened_at: tradeEvent.timestamp,
        closed_at: null,
        councilId: tradeEvent.council_id,
        councilName: tradeEvent.council_name,
      };

      setTrades(prev => [newTrade, ...prev].slice(0, 50));

      // Show toast for significant trades
      const tradeValue = tradeEvent.quantity * tradeEvent.price;
      if (tradeValue > 1000) {
        toast.success(`${tradeEvent.council_name} executed ${tradeEvent.side} order`, {
          description: `${tradeEvent.quantity} ${tradeEvent.symbol} @ $${tradeEvent.price.toFixed(2)}`,
        });
      }

      // Auto-scroll
      setTimeout(() => {
        tradesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    };

    // Consensus listener
    const handleConsensus = (consensusEvent: any) => {
      // Add consensus as a debate message
      const newDebate: EnrichedDebate = {
        id: Date.now(),
        agent_name: 'Council',
        message: `Reached consensus: ${consensusEvent.decision} on ${consensusEvent.symbol}`,
        message_type: 'consensus',
        sentiment: consensusEvent.decision.toLowerCase().includes('buy') ? 'bullish' :
                   consensusEvent.decision.toLowerCase().includes('sell') ? 'bearish' : null,
        market_symbol: consensusEvent.symbol,
        confidence: consensusEvent.confidence,
        debate_round: null,
        created_at: consensusEvent.timestamp,
        councilId: consensusEvent.council_id,
        councilName: consensusEvent.council_name,
      };

      setDebates(prev => [newDebate, ...prev].slice(0, 50));

      // Auto-scroll
      setTimeout(() => {
        debatesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    };

    // Register listeners
    addTradeListener(listenerId, handleTrade);
    addConsensusListener(listenerId, handleConsensus);

    // Cleanup on unmount
    return () => {
      removeTradeListener(listenerId);
      removeConsensusListener(listenerId);
    };
  }, [addTradeListener, removeTradeListener, addConsensusListener, removeConsensusListener]);

  // Fetch initial activity
  useEffect(() => {
    const fetchActivity = async () => {
      try {
        const activity = await systemCouncilsService.getGlobalActivity(50);
        setDebates(activity.debates as EnrichedDebate[]);
        setTrades(activity.trades as EnrichedTrade[]);
        setCouncilNames(activity.councils);
      } catch (error) {
        console.error('Failed to fetch global activity:', error);
        toast.error('Failed to load activity feed');
      } finally {
        setLoading(false);
      }
    };

    fetchActivity();

    // Refresh every 15 seconds
    const interval = setInterval(fetchActivity, 15000);
    return () => clearInterval(interval);
  }, []);

  // Filter by selected council
  const filteredDebates = selectedCouncil
    ? debates.filter(d => d.councilId === selectedCouncil)
    : debates;

  const filteredTrades = selectedCouncil
    ? trades.filter(t => t.councilId === selectedCouncil)
    : trades;

  const getSentimentColor = (sentiment: string | null): string => {
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

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMs / 3600000);
    if (diffHours < 24) return `${diffHours}h ago`;

    return date.toLocaleString();
  };

  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  if (loading) {
    return (
      <section className="py-20 px-6 bg-pantheon-cosmic-bg">
        <div className="max-w-7xl mx-auto">
          <Skeleton className="h-8 w-64 mb-6" />
          <Skeleton className="h-96 w-full" />
        </div>
      </section>
    );
  }

  return (
    <section className="py-20 px-6 bg-pantheon-cosmic-bg">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-mythic font-bold text-pantheon-text-primary mb-2">
              Global Activity Feed
            </h2>
            <p className="text-pantheon-text-secondary">
              Real-time debates and trades from all system councils
            </p>
          </div>

          {/* Connection status */}
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-pantheon-secondary-500 animate-pulse' : 'bg-pantheon-accent-red'}`} />
            <span className="text-sm text-pantheon-text-secondary">
              {isConnected ? 'Live' : 'Reconnecting...'}
            </span>
          </div>
        </div>

        {/* Council Filter */}
        {councilNames.size > 0 && (
          <div className="mb-6">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-pantheon-text-secondary" />
              <select
                value={selectedCouncil || ''}
                onChange={(e) => setSelectedCouncil(e.target.value ? Number(e.target.value) : null)}
                className="bg-pantheon-cosmic-surface border border-pantheon-border rounded-lg px-4 py-2 text-pantheon-text-primary focus:outline-none focus:ring-2 focus:ring-pantheon-primary-500"
              >
                <option value="">All Councils</option>
                {Array.from(councilNames.entries()).map(([id, name]) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Tabs */}
        <Tabs defaultValue="debates" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-pantheon-cosmic-surface border border-pantheon-border">
            <TabsTrigger value="debates" className="flex items-center space-x-2">
              <MessageSquare className="w-4 h-4" />
              <span>Recent Debates ({filteredDebates.length})</span>
            </TabsTrigger>
            <TabsTrigger value="trades" className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4" />
              <span>Recent Trades ({filteredTrades.length})</span>
            </TabsTrigger>
          </TabsList>

          {/* Debates Tab */}
          <TabsContent value="debates" className="mt-6">
            <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-6">
              <div className="space-y-4 max-h-[600px] overflow-y-auto">
                {filteredDebates.length === 0 ? (
                  <p className="text-pantheon-text-secondary text-center py-8">
                    No debates available yet
                  </p>
                ) : (
                  filteredDebates.map((debate) => (
                    <div
                      key={debate.id}
                      className={`p-4 rounded-lg border transition-all ${
                        debate.message_type === 'consensus'
                          ? 'bg-pantheon-primary-500/10 border-pantheon-primary-500'
                          : 'bg-pantheon-cosmic-bg border-pantheon-border'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-3 flex-wrap">
                          <span className="font-semibold text-pantheon-primary-500">
                            {debate.agent_name}
                          </span>
                          <span className="text-xs text-pantheon-text-secondary">
                            @ {debate.councilName}
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
                        <div className="flex items-center space-x-3">
                          {debate.confidence !== null && (
                            <span className="text-xs text-pantheon-text-secondary">
                              {(debate.confidence * 100).toFixed(0)}% confidence
                            </span>
                          )}
                          <span className="text-xs text-pantheon-text-secondary whitespace-nowrap">
                            {formatTimestamp(debate.created_at)}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-pantheon-text-secondary leading-relaxed">
                        {debate.message}
                      </p>
                    </div>
                  ))
                )}
                <div ref={debatesEndRef} />
              </div>
            </Card>
          </TabsContent>

          {/* Trades Tab */}
          <TabsContent value="trades" className="mt-6">
            <Card className="bg-pantheon-cosmic-surface border-pantheon-border p-6">
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {filteredTrades.length === 0 ? (
                  <p className="text-pantheon-text-secondary text-center py-8">
                    No trades available yet
                  </p>
                ) : (
                  filteredTrades.map((trade) => {
                    const isBuy = trade.side.toLowerCase() === 'buy';
                    const pnl = trade.pnl || 0;
                    const isProfitable = pnl > 0;

                    return (
                      <div
                        key={trade.id}
                        className="p-4 bg-pantheon-cosmic-bg border border-pantheon-border rounded-lg hover:border-pantheon-primary-500 transition-all"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            {/* Symbol and Side */}
                            <div>
                              <div className="flex items-center space-x-2">
                                <span className="text-lg font-bold text-pantheon-text-primary">
                                  {trade.symbol}
                                </span>
                                <span className={`px-2 py-1 rounded text-xs font-semibold uppercase ${
                                  isBuy
                                    ? 'bg-pantheon-secondary-500/20 text-pantheon-secondary-500'
                                    : 'bg-pantheon-accent-red/20 text-pantheon-accent-red'
                                }`}>
                                  {trade.side}
                                </span>
                                <span className={`text-xs px-2 py-1 rounded ${
                                  trade.status === 'open'
                                    ? 'bg-pantheon-primary-500/20 text-pantheon-primary-500'
                                    : 'bg-pantheon-cosmic-surface text-pantheon-text-secondary'
                                }`}>
                                  {trade.status}
                                </span>
                              </div>
                              <div className="text-sm text-pantheon-text-secondary mt-1">
                                {trade.quantity} @ {formatPrice(trade.entry_price)}
                                {trade.exit_price && ` → ${formatPrice(trade.exit_price)}`}
                              </div>
                              <div className="text-xs text-pantheon-text-secondary mt-1">
                                {trade.councilName}
                              </div>
                            </div>
                          </div>

                          {/* PnL or Timestamp */}
                          <div className="text-right">
                            {trade.pnl !== null ? (
                              <div>
                                <div className={`text-lg font-bold font-mono ${
                                  isProfitable ? 'text-pantheon-secondary-500' : 'text-pantheon-accent-red'
                                }`}>
                                  {formatPrice(pnl)}
                                </div>
                                {trade.pnl_percentage !== null && (
                                  <div className="text-sm text-pantheon-text-secondary">
                                    {trade.pnl_percentage > 0 ? '+' : ''}{trade.pnl_percentage.toFixed(2)}%
                                  </div>
                                )}
                              </div>
                            ) : (
                              <div className="text-sm text-pantheon-text-secondary">
                                {formatTimestamp(trade.opened_at)}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={tradesEndRef} />
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
}
