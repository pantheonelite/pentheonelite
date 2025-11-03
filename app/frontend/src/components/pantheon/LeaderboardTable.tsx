import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';

interface LeaderboardEntry {
  rank: number;
  name: string;
  pnl: number;
  winRate: number;
  trades: number;
  councilId?: number;
}

interface LeaderboardTableProps {
  data: LeaderboardEntry[];
  onRowClick?: (entry: LeaderboardEntry) => void;
}

export function LeaderboardTable({ data, onRowClick }: LeaderboardTableProps) {
  const getRankBadge = (rank: number) => {
    if (rank === 1)
      return '🥇';
    if (rank === 2)
      return '🥈';
    if (rank === 3)
      return '🥉';
    return rank;
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-pantheon-secondary-500';
    if (pnl < 0) return 'text-pantheon-accent-red';
    return 'text-pantheon-text-secondary';
  };

  return (
    <div className="w-full overflow-x-auto rounded-lg border border-pantheon-border bg-pantheon-cosmic-surface">
      <Table>
        <TableHeader>
          <TableRow className="border-b border-pantheon-border hover:bg-transparent">
            <TableHead className="text-pantheon-text-primary font-semibold uppercase text-xs tracking-wider">
              Rank
            </TableHead>
            <TableHead className="text-pantheon-text-primary font-semibold uppercase text-xs tracking-wider">
              Council Name
            </TableHead>
            <TableHead className="text-pantheon-text-primary font-semibold uppercase text-xs tracking-wider text-right">
              PnL %
            </TableHead>
            <TableHead className="text-pantheon-text-primary font-semibold uppercase text-xs tracking-wider text-right">
              Win Rate
            </TableHead>
            <TableHead className="text-pantheon-text-primary font-semibold uppercase text-xs tracking-wider text-right">
              Trades
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((entry) => (
            <TableRow
              key={entry.rank}
              className="border-b border-pantheon-border hover:bg-pantheon-primary-500/10 transition-colors cursor-pointer"
              onClick={() => onRowClick?.(entry)}
            >
              <TableCell className="font-medium text-pantheon-text-primary">
                <span className="text-lg">{getRankBadge(entry.rank)}</span>
              </TableCell>
              <TableCell className="text-pantheon-text-primary font-medium">
                {entry.name}
              </TableCell>
              <TableCell className={`text-right font-mono font-semibold ${getPnLColor(entry.pnl)}`}>
                {entry.pnl > 0 ? '+' : ''}
                {entry.pnl.toFixed(2)}%
              </TableCell>
              <TableCell className="text-right font-mono text-pantheon-text-secondary">
                {entry.winRate.toFixed(0)}%
              </TableCell>
              <TableCell className="text-right font-mono text-pantheon-text-secondary">
                {entry.trades}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
