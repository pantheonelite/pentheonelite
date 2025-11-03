/**
 * API client for unified Councils (v2).
 *
 * Councils are the new unified concept that replaces both:
 * - Flows (user-created trading strategies)
 * - Councils (pre-made templates)
 *
 * A council is a group of AI agents working together with a specific strategy.
 */

import { API_BASE_URL } from './config';

export interface CouncilV2 {
  id: number;
  user_id: number | null;
  is_system: boolean;
  is_public: boolean;
  is_template: boolean;
  name: string;
  description: string | null;
  strategy: string | null;
  tags: string[] | null;
  agents: any;  // Nodes/agents configuration
  connections: any;  // Edges/connections between agents
  workflow_config: any | null;
  visual_layout: any | null;  // Viewport for React Flow
  initial_capital: number;
  risk_settings: any | null;
  current_capital: number | null;
  total_pnl: number | null;
  total_pnl_percentage: number | null;
  win_rate: number | null;
  total_trades: number | null;
  status: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
  last_executed_at: string | null;
  view_count: number;
  fork_count: number;
  forked_from_id: number | null;
  meta_data: any | null;
}

export interface CouncilV2Summary {
  id: number;
  user_id: number | null;
  is_system: boolean;
  is_public: boolean;
  is_template: boolean;
  name: string;
  description: string | null;
  strategy: string | null;
  tags: string[] | null;
  initial_capital: number;
  total_pnl: number | null;
  total_pnl_percentage: number | null;
  win_rate: number | null;
  total_trades: number | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  view_count: number;
  fork_count: number;
  forked_from_id: number | null;
}

export interface CouncilV2CreateRequest {
  name: string;
  agents: any;
  connections: any;
  description?: string;
  strategy?: string;
  tags?: string[];
  workflow_config?: any;
  visual_layout?: any;
  initial_capital?: number;
  risk_settings?: any;
  is_public?: boolean;
  is_template?: boolean;
}

export interface CouncilV2UpdateRequest {
  name?: string;
  description?: string;
  agents?: any;
  connections?: any;
  workflow_config?: any;
  visual_layout?: any;
  strategy?: string;
  tags?: string[];
  initial_capital?: number;
  risk_settings?: any;
  is_public?: boolean;
  is_template?: boolean;
  status?: string;
}

export interface GetCouncilsOptions {
  includeSystem?: boolean;
  includeUser?: boolean;
  includePublic?: boolean;
  limit?: number;
}

export interface SearchCouncilsOptions {
  includeSystem?: boolean;
  includePublic?: boolean;
  limit?: number;
}

export interface PortfolioHoldingDetail {
  quantity: number;
  avg_cost: number;
  total_cost: number;
  current_value?: number;
  unrealized_pnl?: number;
}

export interface AgentInfo {
  id: string;
  name: string;
  type: string;
  role?: string;
  traits?: string[];
  specialty?: string;
  system_prompt?: string;
  position?: any;
}

export interface DebateMessage {
  id: number;
  agent_name: string;
  message: string;
  message_type: string;
  sentiment?: string;
  market_symbol?: string;
  confidence?: number;
  debate_round?: number;
  created_at: string;
}

export interface TradeRecord {
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

export interface CouncilOverviewResponse {
  // Core council info
  id: number;
  name: string;
  description?: string;
  strategy?: string;
  is_system: boolean;
  is_public: boolean;
  status: string;
  is_paper_trading: boolean;

  // Capital & Performance
  initial_capital: number;
  current_capital: number;
  available_capital: number;
  total_pnl: number;
  total_pnl_percentage: number;

  // Trading Statistics
  win_rate?: number;
  total_trades: number;
  open_positions_count: number;
  closed_positions_count: number;

  // Timestamps
  created_at: string;
  last_executed_at?: string;

  // Optional fields
  agents?: AgentInfo[];
  recent_debates?: DebateMessage[];
  recent_trades?: TradeRecord[];
  portfolio_holdings?: Record<string, PortfolioHoldingDetail>;
}

export interface GetCouncilOverviewOptions {
  includeAgents?: boolean;
  includeDebates?: boolean;
  includeTrades?: boolean;
  includePortfolio?: boolean;
}

class CouncilsV2Service {
  private baseUrl = `${API_BASE_URL}/api/v1/councils/`;  // Correct API path with trailing slash

  /**
   * Get all accessible councils.
   *
   * Returns:
   * - System councils (if includeSystem=true)
   * - User's own councils (if includeUser=true and authenticated)
   * - Public user councils (if includePublic=true)
   */
  async getCouncils(options?: GetCouncilsOptions): Promise<CouncilV2Summary[]> {
    const params = new URLSearchParams();

    if (options?.includeSystem !== undefined) {
      params.append('include_system', String(options.includeSystem));
    }
    if (options?.includeUser !== undefined) {
      params.append('include_user', String(options.includeUser));
    }
    if (options?.includePublic !== undefined) {
      params.append('include_public', String(options.includePublic));
    }
    if (options?.limit) {
      params.append('limit', String(options.limit));
    }

    const url = params.toString() ? `${this.baseUrl}?${params}` : this.baseUrl;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch councils: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get system councils (pre-made templates).
   */
  async getSystemCouncils(): Promise<CouncilV2Summary[]> {
    const response = await fetch(`${this.baseUrl}system`);

    if (!response.ok) {
      throw new Error(`Failed to fetch system councils: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get public user councils (sorted by popularity).
   */
  async getPublicCouncils(limit = 50, offset = 0): Promise<CouncilV2Summary[]> {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });

    const response = await fetch(`${this.baseUrl}public?${params}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch public councils: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get a specific council by ID.
   */
  async getCouncil(id: number): Promise<CouncilV2> {
    const response = await fetch(`${this.baseUrl}${id}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Council not found');
      }
      throw new Error(`Failed to fetch council: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Create a new council.
   */
  async createCouncil(data: CouncilV2CreateRequest): Promise<CouncilV2> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to create council: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Update an existing council.
   */
  async updateCouncil(id: number, data: CouncilV2UpdateRequest): Promise<CouncilV2> {
    const response = await fetch(`${this.baseUrl}${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Council not found');
      }
      throw new Error(`Failed to update council: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Delete a council.
   */
  async deleteCouncil(id: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Council not found');
      }
      throw new Error(`Failed to delete council: ${response.statusText}`);
    }
  }

  /**
   * Fork an existing council.
   *
   * Creates a copy of the council (system or public) and assigns it to the current user.
   *
   * Note: This requires authentication. Without auth, it will fail with a 500 error
   * due to foreign key constraint (user_id cannot be NULL).
   */
  async forkCouncil(id: number, newName?: string): Promise<CouncilV2> {
    const response = await fetch(`${this.baseUrl}${id}/fork`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ new_name: newName || undefined }),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Source council not found');
      }
      if (response.status === 500 && !newName) {
        throw new Error('Fork requires authentication. Please implement auth first.');
      }
      throw new Error(`Failed to fork council: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Search councils by name or description.
   */
  async searchCouncils(query: string, options?: SearchCouncilsOptions): Promise<CouncilV2Summary[]> {
    const params = new URLSearchParams({ query });

    if (options?.includeSystem !== undefined) {
      params.append('include_system', String(options.includeSystem));
    }
    if (options?.includePublic !== undefined) {
      params.append('include_public', String(options.includePublic));
    }
    if (options?.limit) {
      params.append('limit', String(options.limit));
    }

    const response = await fetch(`${this.baseUrl}search?${params}`);

    if (!response.ok) {
      throw new Error(`Failed to search councils: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get comprehensive council overview.
   * Unified endpoint that provides all council data with optional includes.
   *
   * @param councilId - Council ID to fetch
   * @param options - Optional flags to include agents, debates, trades, portfolio
   * @returns Complete council overview
   */
  async getCouncilOverview(
    councilId: number,
    options?: GetCouncilOverviewOptions
  ): Promise<CouncilOverviewResponse> {
    const params = new URLSearchParams();

    if (options?.includeAgents) {
      params.append('include_agents', 'true');
    }
    if (options?.includeDebates) {
      params.append('include_debates', 'true');
    }
    if (options?.includeTrades) {
      params.append('include_trades', 'true');
    }
    if (options?.includePortfolio) {
      params.append('include_portfolio', 'true');
    }

    const url = `${this.baseUrl}${councilId}/overview${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch council overview: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Helper: Convert old flow format to new council format.
   *
   * Useful for migrating from old flow-service.ts to councils-v2.
   */
  convertFlowToCouncil(flow: any): CouncilV2CreateRequest {
    return {
      name: flow.name,
      description: flow.description,
      agents: flow.nodes,  // nodes → agents
      connections: flow.edges,  // edges → connections
      visual_layout: flow.viewport,  // viewport → visual_layout
      workflow_config: flow.data,  // data → workflow_config
      tags: flow.tags,
      is_template: flow.is_template || false,
      is_public: false,  // Default to private
    };
  }

  /**
   * Helper: Convert council format back to old flow format.
   *
   * Useful for backward compatibility with existing UI components.
   */
  convertCouncilToFlow(council: CouncilV2): any {
    return {
      id: council.id,
      name: council.name,
      description: council.description,
      nodes: council.agents,  // agents → nodes
      edges: council.connections,  // connections → edges
      viewport: council.visual_layout,  // visual_layout → viewport
      data: council.workflow_config,  // workflow_config → data
      tags: council.tags,
      is_template: council.is_template,
      created_at: council.created_at,
      updated_at: council.updated_at,
    };
  }

  /**
   * Get trading metrics for a council.
   */
  async getTradingMetrics(councilId: number): Promise<TradingMetrics> {
    const response = await fetch(`${this.baseUrl}${councilId}/metrics`);

    if (!response.ok) {
      throw new Error(`Failed to fetch trading metrics: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get active positions for a council.
   */
  async getActivePositions(councilId: number): Promise<ActivePositionsResponse> {
    const response = await fetch(`${this.baseUrl}${councilId}/active-positions`);

    if (!response.ok) {
      throw new Error(`Failed to fetch active positions: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get recent trades for a council.
   */
  async getRecentTrades(councilId: number, limit = 25): Promise<TradeRecord[]> {
    const response = await fetch(`${this.baseUrl}${councilId}/trades?limit=${limit}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch recent trades: ${response.statusText}`);
    }

    return response.json();
  }
}

export interface HoldTimes {
  long: number;
  short: number;
  flat: number;
}

export interface TradingMetrics {
  net_realized: number;
  average_leverage: number;
  average_confidence: number;
  biggest_win: number;
  biggest_loss: number;
  hold_times: HoldTimes;
}

export interface ActivePositionData {
  id: number;
  symbol: string;
  side: "long" | "short";
  entry_price: number;
  current_price: number;
  quantity: number;
  leverage: number;
  unrealized_pnl: number;
  unrealized_pnl_percentage: number;
  opened_at: string;
  liquidation_price?: number;
}

export interface ActivePositionsResponse {
  positions: ActivePositionData[];
  total_unrealized_pnl: number;
}

export const councilsV2Service = new CouncilsV2Service();
