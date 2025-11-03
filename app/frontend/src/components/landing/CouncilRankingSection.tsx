/**
 * Council Ranking Section Component
 *
 * Wrapper component that handles data fetching, polling, and WebSocket integration
 * for the Council Ranking Table.
 */

import { useEffect, useState } from 'react';
import { Skeleton } from '../ui/skeleton';
import { CouncilRankingTable } from './CouncilRankingTable';
import { systemCouncilsService, type CouncilWithStats } from '../../services/system-councils-api';
import { useCouncilWebSocketContext } from '../../contexts/CouncilWebSocketProvider';
import { toast } from 'sonner';

export function CouncilRankingSection() {
  const [councils, setCouncils] = useState<CouncilWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [highlightedCouncilId, setHighlightedCouncilId] = useState<number | null>(null);

  // WebSocket for real-time updates
  const { isConnected, addTradeListener, removeTradeListener, addConsensusListener, removeConsensusListener } = useCouncilWebSocketContext();

  // Register WebSocket listeners
  useEffect(() => {
    const listenerId = 'council-ranking';

    // Trade listener
    const handleTrade = (tradeEvent: any) => {
      // Highlight the council that made a trade
      setHighlightedCouncilId(tradeEvent.council_id);

      // Update the council's trade count
      setCouncils(prev => prev.map(council => {
        if (council.id === tradeEvent.council_id) {
          return {
            ...council,
            total_trades: (council.total_trades || 0) + 1,
            last_executed_at: tradeEvent.timestamp,
          };
        }
        return council;
      }));

      // Clear highlight after 3 seconds
      setTimeout(() => {
        setHighlightedCouncilId(null);
      }, 3000);
    };

    // Consensus listener
    const handleConsensus = (consensusEvent: any) => {
      // Update last activity for the council
      setCouncils(prev => prev.map(council => {
        if (council.id === consensusEvent.council_id) {
          return {
            ...council,
            last_executed_at: consensusEvent.timestamp,
          };
        }
        return council;
      }));
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

  // Fetch councils data
  const fetchCouncils = async () => {
    try {
      const councilsData = await systemCouncilsService.getAllCouncilsWithStats();
      setCouncils(councilsData);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch councils:', err);
      setError(err instanceof Error ? err.message : 'Failed to load councils');
      toast.error('Failed to load system councils');
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchCouncils();
  }, []);

  // Poll every 10 seconds for council stats
  useEffect(() => {
    const interval = setInterval(() => {
      fetchCouncils();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <section className="py-8 sm:py-12 md:py-20 px-4 sm:px-6 bg-pantheon-cosmic-bg">
        <div className="max-w-7xl mx-auto">
          <Skeleton className="h-8 sm:h-12 w-full sm:w-96 mb-6 sm:mb-8" />
          <Skeleton className="h-64 sm:h-96 w-full" />
        </div>
      </section>
    );
  }

  if (error && councils.length === 0) {
    return (
      <section className="py-8 sm:py-12 md:py-20 px-4 sm:px-6 bg-pantheon-cosmic-bg">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <h2 className="text-2xl sm:text-3xl font-mythic font-bold text-pantheon-text-primary mb-3 sm:mb-4">
              Live System Councils
            </h2>
            <p className="text-sm sm:text-base text-pantheon-accent-red px-2">{error}</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section id="leaderboard" className="py-8 sm:py-12 md:py-20 px-4 sm:px-6 bg-pantheon-cosmic-bg">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-block px-3 sm:px-4 py-1.5 sm:py-2 bg-pantheon-primary-500/20 border border-pantheon-primary-500 rounded-full mb-3 sm:mb-4">
            <span className="text-pantheon-primary-500 font-semibold uppercase tracking-wider text-xs sm:text-sm flex items-center space-x-1 sm:space-x-2">
              <span className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full ${isConnected ? 'bg-pantheon-secondary-500 animate-pulse' : 'bg-pantheon-accent-red'}`} />
              <span>{isConnected ? '🔴 Live Trading' : 'Reconnecting...'}</span>
            </span>
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-mythic font-bold text-pantheon-text-primary mb-3 sm:mb-4">
            System Councils Leaderboard
          </h2>
          <p className="text-sm sm:text-base md:text-lg text-pantheon-text-secondary max-w-3xl mx-auto px-2">
            Watch AI agent councils compete in real-time cryptocurrency trading.
            Each council represents a unique strategy powered by collaborative AI agents.
          </p>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-4 mb-6 sm:mb-8">
          <div className="bg-pantheon-cosmic-surface border border-pantheon-border rounded-lg p-3 sm:p-4 text-center">
            <div className="text-xl sm:text-2xl font-bold text-pantheon-primary-500">
              {councils.length}
            </div>
            <div className="text-xs sm:text-sm text-pantheon-text-secondary mt-1">
              Active Councils
            </div>
          </div>

          <div className="bg-pantheon-cosmic-surface border border-pantheon-border rounded-lg p-3 sm:p-4 text-center">
            <div className="text-xl sm:text-2xl font-bold text-pantheon-text-primary">
              {councils.reduce((sum, c) => sum + (c.total_trades || 0), 0)}
            </div>
            <div className="text-xs sm:text-sm text-pantheon-text-secondary mt-1">
              Total Trades
            </div>
          </div>

          <div className="bg-pantheon-cosmic-surface border border-pantheon-border rounded-lg p-3 sm:p-4 text-center">
            <div className="text-xl sm:text-2xl font-bold text-pantheon-secondary-500">
              {councils.filter(c => (c.total_pnl || 0) > 0).length}
            </div>
            <div className="text-xs sm:text-sm text-pantheon-text-secondary mt-1">
              Profitable
            </div>
          </div>

          <div className="bg-pantheon-cosmic-surface border border-pantheon-border rounded-lg p-3 sm:p-4 text-center">
            <div className="text-xl sm:text-2xl font-bold text-pantheon-text-primary">
              {councils.reduce((sum, c) => sum + (c.stats?.open_positions || 0), 0)}
            </div>
            <div className="text-xs sm:text-sm text-pantheon-text-secondary mt-1">
              Open Positions
            </div>
          </div>
        </div>

        {/* Ranking Table */}
        <CouncilRankingTable
          councils={councils}
          highlightedCouncilId={highlightedCouncilId}
        />

        {/* Footer Note */}
        <div className="mt-4 sm:mt-6 text-center text-xs sm:text-sm text-pantheon-text-secondary px-2">
          <p>Rankings are updated in real-time. Click on any council to view detailed performance metrics.</p>
        </div>
      </div>
    </section>
  );
}
