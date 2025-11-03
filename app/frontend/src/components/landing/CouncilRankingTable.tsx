/**
 * Council Ranking Table Component
 *
 * Displays all system councils in a sortable table with real-time updates.
 * Shows key metrics: rank, name, strategy, PnL, win rate, trades, status.
 */

import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpDown, TrendingUp, TrendingDown } from 'lucide-react';
import type { CouncilWithStats } from '../../services/system-councils-api';

type SortField = 'rank' | 'name' | 'pnl' | 'pnl_pct' | 'trades' | 'positions';
type SortDirection = 'asc' | 'desc';

interface CouncilRankingTableProps {
  councils: CouncilWithStats[];
  highlightedCouncilId?: number | null;
}

export function CouncilRankingTable({ councils, highlightedCouncilId }: CouncilRankingTableProps) {
  const navigate = useNavigate();
  const [sortField, setSortField] = useState<SortField>('rank');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  // Sort and rank councils
  const sortedCouncils = useMemo(() => {
    // First, calculate ranks based on PnL percentage
    const withRanks = councils.map((council, index) => ({
      ...council,
      rank: index + 1,
    }));

    // Sort by total_pnl_percentage descending for ranking
    withRanks.sort((a, b) => {
      const aPnl = a.total_pnl_percentage || 0;
      const bPnl = b.total_pnl_percentage || 0;
      return bPnl - aPnl;
    });

    // Reassign ranks after sorting
    withRanks.forEach((council, index) => {
      council.rank = index + 1;
    });

    // Now apply user's sort preference
    const sorted = [...withRanks];

    sorted.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortField) {
        case 'rank':
          aValue = a.rank;
          bValue = b.rank;
          break;
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'pnl':
          aValue = a.total_pnl || 0;
          bValue = b.total_pnl || 0;
          break;
        case 'pnl_pct':
          aValue = a.total_pnl_percentage || 0;
          bValue = b.total_pnl_percentage || 0;
          break;
        case 'trades':
          aValue = a.total_trades || 0;
          bValue = b.total_trades || 0;
          break;
        case 'positions':
          aValue = (a.stats?.open_positions || 0) + (a.stats?.closed_positions || 0);
          bValue = (b.stats?.open_positions || 0) + (b.stats?.closed_positions || 0);
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [councils, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Toggle direction
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New field, default to ascending
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleRowClick = (councilId: number) => {
    navigate(`/council/${councilId}`);
  };

  const formatCurrency = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '0.00%';
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatDate = (dateStr: string | null | undefined): string => {
    if (!dateStr) return 'Never';

    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return 'Never';

      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch {
      return 'Never';
    }
  };

  const getLastActivity = (council: CouncilWithStats): string => {
    // Priority: last_executed_at > liveStatus.latest_cycle_time > Never
    const lastExecuted = council.last_executed_at || council.liveStatus?.latest_cycle_time;
    return formatDate(lastExecuted);
  };

  const SortButton = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center space-x-1 hover:text-pantheon-primary-500 transition-colors"
    >
      <span>{children}</span>
      {sortField === field && (
        <ArrowUpDown className="w-3 h-3" />
      )}
    </button>
  );

  if (councils.length === 0) {
    return (
      <div className="text-center py-12 text-pantheon-text-secondary">
        No system councils available
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-pantheon-border -mx-2 sm:mx-0">
      <table className="w-full text-xs sm:text-sm min-w-[800px]">
        <thead className="bg-pantheon-cosmic-surface border-b border-pantheon-border">
          <tr>
            <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-pantheon-text-secondary font-medium whitespace-nowrap">
              <SortButton field="rank">Rank ↕</SortButton>
            </th>
            <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-pantheon-text-secondary font-medium min-w-[180px]">
              <SortButton field="name">Council</SortButton>
            </th>
            <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-pantheon-text-secondary font-medium min-w-[150px] hidden md:table-cell">
              Strategy
            </th>
            <th className="px-2 sm:px-4 py-2 sm:py-3 text-right text-pantheon-text-secondary font-medium whitespace-nowrap">
              <SortButton field="pnl">Total PnL</SortButton>
            </th>
            <th className="px-2 sm:px-4 py-2 sm:py-3 text-right text-pantheon-text-secondary font-medium whitespace-nowrap">
              <SortButton field="pnl_pct">PnL %</SortButton>
            </th>
            <th className="px-2 sm:px-4 py-2 sm:py-3 text-center text-pantheon-text-secondary font-medium whitespace-nowrap">
              <SortButton field="trades">Trades</SortButton>
            </th>
            <th className="px-2 sm:px-4 py-2 sm:py-3 text-center text-pantheon-text-secondary font-medium whitespace-nowrap hidden sm:table-cell">
              <SortButton field="positions">Positions Added</SortButton>
            </th>
            <th className="px-2 sm:px-4 py-2 sm:py-3 text-center text-pantheon-text-secondary font-medium whitespace-nowrap hidden md:table-cell">
              Last Activity
            </th>
          </tr>
        </thead>
        <tbody className="bg-pantheon-cosmic-bg">
          {sortedCouncils.map((council) => {
            const pnl = council.total_pnl || 0;
            const pnlPct = council.total_pnl_percentage || 0;
            const isPositive = pnl >= 0;
            const isHighlighted = council.id === highlightedCouncilId;

            return (
              <tr
                key={council.id}
                onClick={() => handleRowClick(council.id)}
                className={`
                  border-b border-pantheon-border cursor-pointer transition-all
                  hover:bg-pantheon-cosmic-surface/50
                  ${isHighlighted ? 'bg-pantheon-primary-500/10 animate-pulse' : ''}
                `}
              >
                {/* Rank */}
                <td className="px-2 sm:px-4 py-3 sm:py-4">
                  <div className="flex items-center space-x-1 sm:space-x-2">
                    <span className="text-pantheon-text-primary font-bold text-xs sm:text-sm">
                      #{council.rank}
                    </span>
                    {council.rank === 1 && (
                      <span className="text-base sm:text-lg">🏆</span>
                    )}
                  </div>
                </td>

                {/* Council Name */}
                <td className="px-2 sm:px-4 py-3 sm:py-4">
                  <div>
                    <div className="font-semibold text-pantheon-text-primary text-xs sm:text-sm">
                      {council.name}
                    </div>
                    {council.description && (
                      <div className="text-[10px] sm:text-xs text-pantheon-text-secondary mt-0.5 sm:mt-1 line-clamp-1">
                        {council.description}
                      </div>
                    )}
                  </div>
                </td>

                {/* Strategy */}
                <td className="px-2 sm:px-4 py-3 sm:py-4 hidden md:table-cell">
                  <span className="text-pantheon-text-secondary text-xs sm:text-sm">
                    {council.strategy || 'N/A'}
                  </span>
                </td>

                {/* Total PnL */}
                <td className="px-2 sm:px-4 py-3 sm:py-4 text-right">
                  <div className="flex items-center justify-end space-x-0.5 sm:space-x-1">
                    {isPositive ? (
                      <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4 text-pantheon-secondary-500" />
                    ) : (
                      <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4 text-pantheon-accent-red" />
                    )}
                    <span
                      className={`font-mono font-semibold text-xs sm:text-sm ${
                        isPositive ? 'text-pantheon-secondary-500' : 'text-pantheon-accent-red'
                      }`}
                    >
                      {formatCurrency(pnl)}
                    </span>
                  </div>
                </td>

                {/* PnL % */}
                <td className="px-2 sm:px-4 py-3 sm:py-4 text-right">
                  <span
                    className={`font-mono font-semibold text-xs sm:text-sm ${
                      isPositive ? 'text-pantheon-secondary-500' : 'text-pantheon-accent-red'
                    }`}
                  >
                    {formatPercentage(pnlPct)}
                  </span>
                </td>

                {/* Total Trades */}
                <td className="px-2 sm:px-4 py-3 sm:py-4 text-center">
                  <span className="text-pantheon-text-primary font-mono text-xs sm:text-sm">
                    {council.total_trades || 0}
                  </span>
                </td>

                {/* Positions Added */}
                <td className="px-2 sm:px-4 py-3 sm:py-4 text-center hidden sm:table-cell">
                  <span className="text-pantheon-text-primary font-mono text-xs sm:text-sm">
                    {(council.stats?.open_positions || 0) + (council.stats?.closed_positions || 0)}
                  </span>
                </td>

                {/* Last Activity */}
                <td className="px-2 sm:px-4 py-3 sm:py-4 text-center hidden md:table-cell">
                  <span className="text-[10px] sm:text-xs text-pantheon-text-secondary">
                    {getLastActivity(council)}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
