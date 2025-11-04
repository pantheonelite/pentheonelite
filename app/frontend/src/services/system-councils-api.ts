/**
 * API client for System Councils with real-time capabilities.
 *
 * Provides access to system council data, live status, debates, trades,
 * and performance metrics for landing page display.
 */

import { API_BASE_URL } from './config';

export interface CouncilResponse {
  id: number;
  name: string;
  description: string | null;
  strategy: string | null;
  is_system: boolean;
  is_public: boolean;
  status: string;
  initial_capital: number;
  current_capital: number | null;
  total_pnl: number | null;
  total_pnl_percentage: number | null;
  win_rate: number | null;
  total_trades: number | null;
  created_at: string;
  last_executed_at: string | null;
}

export interface LiveStatusResponse {
  council: CouncilResponse;
  open_position_count: number;
  total_open_value: number;
  latest_cycle_status: string | null;
  latest_cycle_time: string | null;
  is_running: boolean;
}

export interface DebateMessage {
  id: number;
  agent_name: string;
  message: string;
  message_type: string;
  sentiment: string | null;
  market_symbol: string | null;
  confidence: number | null;
  debate_round: number | null;
  created_at: string;
}

export interface TotalAccountValueDataPoint {
  timestamp: string;
  total_value: number;
  change_dollar: number;
  change_percentage: number;
}

export interface CouncilAccountValueSeries {
  council_id: number;
  council_name: string;
  data_points: TotalAccountValueDataPoint[];
  current_value: number;
  change_dollar: number;
  change_percentage: number;
}

export interface TotalAccountValueResponse {
  councils: CouncilAccountValueSeries[];
  total_current_value: number;
  total_change_dollar: number;
  total_change_percentage: number;
}

export interface TradeRecord {
  id: number;
  symbol: string;
  order_type: string;
  side: string;
  quantity: number;
  entry_price: number;
  exit_price: number | null;
  pnl: number | null;
  pnl_percentage: number | null;
  status: string;
  opened_at: string;
  closed_at: string | null;
}

export interface CouncilStatsResponse {
  council_id: number;
  council_name: string;
  total_agents: number;
  open_positions: number;
  closed_positions: number;
  total_trades: number;
  win_rate: number | null;
  total_pnl: number | null;
  total_pnl_percentage: number | null;
  average_trade_duration_hours: number | null;
  largest_win: number | null;
  largest_loss: number | null;
  current_streak: number;
}

export interface CouncilWithStats extends CouncilResponse {
  stats: CouncilStatsResponse | null;
  liveStatus: LiveStatusResponse | null;
}

export interface GlobalActivity {
  debates: DebateMessage[];
  trades: TradeRecord[];
  councils: Map<number, string>; // councilId -> councilName
}

class SystemCouncilsService {
  private baseUrl = `${API_BASE_URL}/api/v1/councils`;

  /**
   * Get all system councils.
   */
  async getSystemCouncils(): Promise<CouncilResponse[]> {
    const response = await fetch(`${this.baseUrl}/system`);

    if (!response.ok) {
      throw new Error(`Failed to fetch system councils: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get comprehensive council overview (replaces live-status and stats endpoints).
   *
   * @param councilId - Council ID
   * @param options - Optional includes for agents, debates, trades, portfolio
   */
  async getCouncilOverview(
    councilId: number,
    options?: {
      includeAgents?: boolean;
      includeDebates?: boolean;
      includeTrades?: boolean;
      includePortfolio?: boolean;
    }
  ): Promise<CouncilWithStats> {
    const params = new URLSearchParams();

    if (options?.includeAgents) params.append('include_agents', 'true');
    if (options?.includeDebates) params.append('include_debates', 'true');
    if (options?.includeTrades) params.append('include_trades', 'true');
    if (options?.includePortfolio) params.append('include_portfolio', 'true');

    const url = `${this.baseUrl}/${councilId}/overview${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch council overview: ${response.statusText}`);
    }

    const data = await response.json();

    // Transform overview response to match CouncilWithStats interface
    return {
      ...data,
      stats: {
        council_id: data.id,
        council_name: data.name,
        total_agents: data.agents?.length || 0,
        open_positions: data.open_positions_count,
        closed_positions: data.closed_positions_count,
        total_trades: data.total_trades,
        win_rate: data.win_rate,
        total_pnl: data.total_pnl,
        total_pnl_percentage: data.total_pnl_percentage,
        average_trade_duration_hours: null,
        largest_win: null,
        largest_loss: null,
        current_streak: 0,
      },
      liveStatus: {
        council: data,
        open_position_count: data.open_positions_count,
        total_open_value: 0,
        latest_cycle_status: data.status,
        latest_cycle_time: data.last_executed_at,
        is_running: data.status === 'active',
      },
    };
  }

  /**
   * Get recent debates for a council.
   */
  async getCouncilDebates(councilId: number, limit: number = 50): Promise<DebateMessage[]> {
    const response = await fetch(`${this.baseUrl}/${councilId}/debates?limit=${limit}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch council debates: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get recent trades for a council.
   */
  async getCouncilTrades(councilId: number, limit: number = 20): Promise<TradeRecord[]> {
    const response = await fetch(`${this.baseUrl}/${councilId}/trades?limit=${limit}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch council trades: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get all system councils with their stats and live status.
   *
   * Uses the new unified overview endpoint for better performance.
   */
  async getAllCouncilsWithStats(): Promise<CouncilWithStats[]> {
    const councils = await this.getSystemCouncils();

    // Fetch overview for all councils in parallel (no optional includes for speed)
    const councilsWithStats = await Promise.all(
      councils.map(async (council) => {
        try {
          return await this.getCouncilOverview(council.id);
        } catch (error) {
          console.error(`Failed to fetch overview for council ${council.id}:`, error);
          // Return basic council data with null stats/liveStatus on error
          return {
            ...council,
            stats: null,
            liveStatus: null,
          };
        }
      })
    );

    return councilsWithStats;
  }

  /**
   * Get global activity across all system councils.
   *
   * Uses the aggregated endpoint for better performance.
   */
  async getGlobalActivity(limit: number = 50): Promise<GlobalActivity> {
    try {
      // Try to use the aggregated endpoint first (more efficient)
      const response = await fetch(`${this.baseUrl}/system/activity?limit=${limit}`);

      if (response.ok) {
        const data = await response.json();

        // Convert councils object to Map
        const councilMap = new Map<number, string>(
          Object.entries(data.councils).map(([id, name]) => [Number(id), name as string])
        );

        // Add council info to debates and trades
        const enrichedDebates = data.debates.map((d: DebateMessage) => {
          const councilEntry = Array.from(councilMap.entries()).find(([_id, _name]) => true);
          return {
            ...d,
            councilId: councilEntry?.[0] || 0,
            councilName: councilEntry?.[1] || 'Unknown',
          };
        });

        const enrichedTrades = data.trades.map((t: TradeRecord) => {
          const councilEntry = Array.from(councilMap.entries()).find(([_id, _name]) => true);
          return {
            ...t,
            councilId: councilEntry?.[0] || 0,
            councilName: councilEntry?.[1] || 'Unknown',
          };
        });

        return {
          debates: enrichedDebates,
          trades: enrichedTrades,
          councils: councilMap,
        };
      }
    } catch (error) {
      console.warn('Aggregated endpoint failed, falling back to individual requests:', error);
    }

    // Fallback: Fetch from individual councils (legacy method)
    const councils = await this.getSystemCouncils();

    // Create council name map for quick lookup
    const councilMap = new Map<number, string>();
    councils.forEach(c => councilMap.set(c.id, c.name));

    // Fetch debates and trades from all councils in parallel
    const allDebates: (DebateMessage & { councilId: number; councilName: string })[] = [];
    const allTrades: (TradeRecord & { councilId: number; councilName: string })[] = [];

    await Promise.all(
      councils.map(async (council) => {
        try {
          const [debates, trades] = await Promise.all([
            this.getCouncilDebates(council.id, 20).catch(() => []),
            this.getCouncilTrades(council.id, 20).catch(() => []),
          ]);

          // Add council info to each item
          debates.forEach(d => allDebates.push({
            ...d,
            councilId: council.id,
            councilName: council.name,
          }));

          trades.forEach(t => allTrades.push({
            ...t,
            councilId: council.id,
            councilName: council.name,
          }));
        } catch (error) {
          console.error(`Failed to fetch activity for council ${council.id}:`, error);
        }
      })
    );

    // Sort by timestamp (most recent first)
    allDebates.sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    allTrades.sort((a, b) =>
      new Date(b.opened_at).getTime() - new Date(a.opened_at).getTime()
    );

    return {
      debates: allDebates.slice(0, limit),
      trades: allTrades.slice(0, limit),
      councils: councilMap,
    };
  }

  /**
   * Get aggregated total account value for all system councils.
   * Similar to nof1.ai's total account value chart.
   */
  async getTotalAccountValue(days: number = 72): Promise<TotalAccountValueResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/system/total-account-value?days=${days}`);
      if (!response.ok) {
        throw new Error('Failed to fetch total account value');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching total account value:', error);
      throw error;
    }
  }
}

export const systemCouncilsService = new SystemCouncilsService();
