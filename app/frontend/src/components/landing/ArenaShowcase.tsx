import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LeaderboardTable } from '../pantheon';
import { Card } from '../ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Skeleton } from '../ui/skeleton';
import { systemCouncilsService, DebateMessage } from '../../services/system-councils-api';
import { toast } from 'sonner';

interface LeaderboardEntry {
  rank: number;
  name: string;
  pnl: number;
  winRate: number;
  trades: number;
  councilId: number;
  description: string;
}

interface AggregateStats {
  totalTrades: number;
  totalCouncils: number;
  profitableCouncils: number;
  avgPnl: number;
  topWinRate: number;
}

export function ArenaShowcase() {
  const navigate = useNavigate();
  const [selectedEntry, setSelectedEntry] = useState<LeaderboardEntry | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [recentDebates, setRecentDebates] = useState<DebateMessage[]>([]);
  const [aggregateStats, setAggregateStats] = useState<AggregateStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArenaData = async () => {
      try {
        const councils = await systemCouncilsService.getAllCouncilsWithStats();

        // Sort by PnL percentage descending
        const sortedCouncils = councils.sort((a, b) => {
          const aPnl = a.total_pnl_percentage || 0;
          const bPnl = b.total_pnl_percentage || 0;
          return bPnl - aPnl;
        });

        const entries: LeaderboardEntry[] = sortedCouncils.map((council, index) => ({
          rank: index + 1,
          name: council.name,
          pnl: council.total_pnl_percentage || 0,
          winRate: council.win_rate || 0,
          trades: council.total_trades || 0,
          councilId: council.id,
          description: council.description || '',
        }));

        setLeaderboard(entries);

        // Calculate aggregate statistics
        const stats: AggregateStats = {
          totalCouncils: councils.length,
          totalTrades: councils.reduce((sum, c) => sum + (c.total_trades || 0), 0),
          profitableCouncils: councils.filter(c => (c.total_pnl_percentage || 0) > 0).length,
          avgPnl: councils.reduce((sum, c) => sum + (c.total_pnl_percentage || 0), 0) / Math.max(councils.length, 1),
          topWinRate: Math.max(...councils.map(c => c.win_rate || 0)),
        };
        setAggregateStats(stats);

        // Fetch recent debates from top council
        if (sortedCouncils.length > 0) {
          const topCouncil = sortedCouncils[0];
          try {
            const debates = await systemCouncilsService.getCouncilDebates(topCouncil.id, 10);
            setRecentDebates(debates);
          } catch (debateErr) {
            console.warn('Failed to fetch debates for top council:', debateErr);
          }
        }

        setError(null);
      } catch (err) {
        console.error('Failed to fetch councils for arena:', err);
        setError(err instanceof Error ? err.message : 'Failed to load councils');
        toast.error('Failed to load council leaderboard');
      } finally {
        setLoading(false);
      }
    };

    fetchArenaData();
  }, []);

  if (loading) {
    return (
      <section id="arena" className="py-20 px-6 bg-pantheon-cosmic-surface">
        <div className="max-w-7xl mx-auto">
          <Skeleton className="h-12 w-2/3 mx-auto mb-8" />
          <Skeleton className="h-96 mb-8" />
        </div>
      </section>
    );
  }

  if (error || leaderboard.length === 0) {
    return (
      <section id="arena" className="py-20 px-6 bg-pantheon-cosmic-surface">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-pantheon-accent-red">
            {error || 'No councils available'}
          </p>
        </div>
      </section>
    );
  }

  const avgPnl = leaderboard.slice(0, 3).reduce((sum, entry) => sum + entry.pnl, 0) / 3;

  return (
    <section id="arena" className="py-20 px-6 bg-pantheon-cosmic-surface">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-mythic font-bold text-pantheon-text-primary mb-4">
            Pantheon Arena: Watch Councils Compete
          </h2>
          <p className="text-lg text-pantheon-text-secondary max-w-2xl mx-auto">
            Real-time performance of agent councils yielding superior PnL on crypto markets
          </p>
        </div>

        {/* Leaderboard */}
        <div className="mb-12">
          <LeaderboardTable
            data={leaderboard}
            onRowClick={(entry) => {
              // Navigate to council detail page
              navigate(`/council/${entry.councilId}`);
            }}
          />
          <p className="mt-4 text-center text-pantheon-secondary-500 font-semibold">
            Top councils average <span className="text-2xl">{avgPnl.toFixed(1)}%</span> returns—build yours
          </p>
        </div>

        {/* Real-time Insights Grid */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* Live Debates from Top Council */}
          <Card className="bg-pantheon-cosmic-bg border-pantheon-border p-6">
            <h3 className="text-xl font-mythic font-semibold text-pantheon-text-primary mb-4">
              Live Debate Preview
              {leaderboard.length > 0 && (
                <span className="ml-2 text-sm font-normal text-pantheon-text-secondary">
                  from {leaderboard[0].name}
                </span>
              )}
            </h3>
            <div className="space-y-3">
              {recentDebates.length > 0 ? (
                recentDebates.slice(0, 4).map((debate) => (
                  <div
                    key={debate.id}
                    className={`p-3 rounded-lg border ${
                      debate.sentiment === 'bullish'
                        ? 'border-pantheon-secondary-500 bg-pantheon-secondary-500/10'
                        : debate.sentiment === 'bearish'
                        ? 'border-pantheon-accent-red bg-pantheon-accent-red/10'
                        : 'border-pantheon-border bg-pantheon-cosmic-surface'
                    }`}
                  >
                    <div className="flex flex-col">
                      <span className="font-semibold text-pantheon-primary-500 text-sm">
                        {debate.agent_name}
                      </span>
                      <span className="mt-1 text-pantheon-text-secondary text-sm">
                        {debate.message}
                      </span>
                      {debate.confidence && (
                        <span className="mt-1 text-xs text-pantheon-text-secondary">
                          Confidence: {(debate.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-pantheon-text-secondary text-sm">
                  No recent debates available. Councils are currently analyzing markets...
                </p>
              )}
            </div>
          </Card>

          {/* Aggregate Performance Statistics */}
          <Card className="bg-pantheon-cosmic-bg border-pantheon-border p-6">
            <h3 className="text-xl font-mythic font-semibold text-pantheon-text-primary mb-4">
              Platform Performance
            </h3>
            {aggregateStats ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-pantheon-cosmic-surface border border-pantheon-border rounded-lg p-3">
                    <div className="text-2xl font-bold text-pantheon-secondary-500">
                      {aggregateStats.totalCouncils}
                    </div>
                    <div className="text-xs text-pantheon-text-secondary mt-1">
                      Active Councils
                    </div>
                  </div>
                  <div className="bg-pantheon-cosmic-surface border border-pantheon-border rounded-lg p-3">
                    <div className="text-2xl font-bold text-pantheon-text-primary">
                      {aggregateStats.totalTrades}
                    </div>
                    <div className="text-xs text-pantheon-text-secondary mt-1">
                      Total Trades
                    </div>
                  </div>
                  <div className="bg-pantheon-cosmic-surface border border-pantheon-border rounded-lg p-3">
                    <div className={`text-2xl font-bold ${aggregateStats.avgPnl >= 0 ? 'text-pantheon-secondary-500' : 'text-pantheon-accent-red'}`}>
                      {aggregateStats.avgPnl >= 0 ? '+' : ''}{aggregateStats.avgPnl.toFixed(1)}%
                    </div>
                    <div className="text-xs text-pantheon-text-secondary mt-1">
                      Average PnL
                    </div>
                  </div>
                  <div className="bg-pantheon-cosmic-surface border border-pantheon-border rounded-lg p-3">
                    <div className="text-2xl font-bold text-pantheon-primary-500">
                      {aggregateStats.topWinRate.toFixed(0)}%
                    </div>
                    <div className="text-xs text-pantheon-text-secondary mt-1">
                      Best Win Rate
                    </div>
                  </div>
                </div>
                <div className="bg-pantheon-cosmic-surface border border-pantheon-border rounded-lg p-4 mt-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-pantheon-text-secondary">
                      Profitable Councils
                    </span>
                    <span className="text-lg font-bold text-pantheon-secondary-500">
                      {aggregateStats.profitableCouncils} / {aggregateStats.totalCouncils}
                    </span>
                  </div>
                  <div className="w-full bg-pantheon-cosmic-bg rounded-full h-3 overflow-hidden mt-2">
                    <div
                      className="bg-gradient-to-r from-pantheon-secondary-500 to-pantheon-primary-500 h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${(aggregateStats.profitableCouncils / Math.max(aggregateStats.totalCouncils, 1)) * 100}%`
                      }}
                    />
                  </div>
                </div>
                <p className="text-sm text-pantheon-text-secondary mt-4">
                  <span className="text-pantheon-secondary-500 font-bold">
                    {((aggregateStats.profitableCouncils / Math.max(aggregateStats.totalCouncils, 1)) * 100).toFixed(0)}%
                  </span>{' '}
                  of councils are profitable through collaborative agent decision-making
                </p>
              </div>
            ) : (
              <p className="text-pantheon-text-secondary">Loading statistics...</p>
            )}
          </Card>
        </div>
      </div>

      {/* Detail modal */}
      <Dialog open={!!selectedEntry} onOpenChange={() => setSelectedEntry(null)}>
        <DialogContent className="bg-pantheon-cosmic-surface border-pantheon-border">
          <DialogHeader>
            <DialogTitle className="text-2xl font-mythic text-pantheon-text-primary">
              {selectedEntry?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 text-pantheon-text-secondary">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm uppercase tracking-wider">Rank</span>
                <p className="text-2xl font-bold text-pantheon-primary-500">
                  #{selectedEntry?.rank}
                </p>
              </div>
              <div>
                <span className="text-sm uppercase tracking-wider">PnL</span>
                <p className="text-2xl font-bold text-pantheon-secondary-500">
                  +{selectedEntry?.pnl}%
                </p>
              </div>
              <div>
                <span className="text-sm uppercase tracking-wider">Win Rate</span>
                <p className="text-2xl font-bold text-pantheon-text-primary">
                  {selectedEntry?.winRate}%
                </p>
              </div>
              <div>
                <span className="text-sm uppercase tracking-wider">Trades</span>
                <p className="text-2xl font-bold text-pantheon-text-primary">
                  {selectedEntry?.trades}
                </p>
              </div>
            </div>
            <p className="text-sm">
              {selectedEntry?.description || 'This council combines multiple legendary agents for superior market insights.'}
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </section>
  );
}
