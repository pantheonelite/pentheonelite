import { API_BASE_URL } from './config';

export interface CouncilAgent {
  id: number;
  agent_name: string;
  agent_type: string;
  role: string | null;
  traits: string[] | null;
  specialty: string | null;
  system_prompt: string | null;
  is_active: boolean;
}

export interface Council {
  id: number;
  name: string;
  description: string | null;
  is_default: boolean;
  is_public: boolean;
  strategy: string | null;
  initial_capital: string;
  current_capital: string | null;
  total_pnl: string | null;
  total_pnl_percentage: string | null;
  win_rate: string | null;
  total_trades: number | null;
  created_at: string | null;
}

export interface AgentDebate {
  id: number;
  agent_name: string;
  message: string;
  message_type: string;
  sentiment: string | null;
  market_symbol: string | null;
  confidence: string | null;
  debate_round: number | null;
  created_at: string | null;
}

export interface MarketOrder {
  id: number;
  symbol: string;
  order_type: string;
  side: string;
  quantity: string;
  entry_price: string;
  exit_price: string | null;
  status: string;
  opened_at: string;
  closed_at: string | null;
  pnl: string | null;
  pnl_percentage: string | null;
  notes: string | null;
}

export interface CouncilPerformance {
  timestamp: string;
  total_value: string;
  pnl: string;
  pnl_percentage: string;
  win_rate: string | null;
  total_trades: number;
  open_positions: number;
}

export interface DefaultCouncilData {
  council: Council;
  agents: CouncilAgent[];
  recent_debates: AgentDebate[];
  open_orders: MarketOrder[];
  closed_orders: MarketOrder[];
  performance_history: CouncilPerformance[];
}

class CouncilService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/council`;
  }

  async getAllCouncils(): Promise<Council[]> {
    const response = await fetch(`${this.baseUrl}/`);
    if (!response.ok) {
      throw new Error('Failed to fetch councils');
    }
    return response.json();
  }

  async getBestPerformingCouncil(): Promise<DefaultCouncilData> {
    const response = await fetch(`${this.baseUrl}/best`);
    if (!response.ok) {
      throw new Error('Failed to fetch best performing council');
    }
    return response.json();
  }

  async getDefaultCouncil(): Promise<DefaultCouncilData> {
    const response = await fetch(`${this.baseUrl}/default`);
    if (!response.ok) {
      throw new Error('Failed to fetch default council');
    }
    return response.json();
  }

  async getCouncil(councilId: number): Promise<Council> {
    const response = await fetch(`${this.baseUrl}/${councilId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch council');
    }
    return response.json();
  }

  async getCouncilDetail(councilId: number): Promise<DefaultCouncilData> {
    const response = await fetch(`${this.baseUrl}/${councilId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch council details');
    }
    const council: Council = await response.json();

    // Fetch related data
    const [agents, debates, orders, performance] = await Promise.all([
      this.getCouncilAgents(councilId),
      this.getCouncilDebates(councilId, 50),
      this.getCouncilOrders(councilId, undefined, 100),
      this.getCouncilPerformance(councilId, 100),
    ]);

    // Separate open and closed orders
    const open_orders = orders.filter(order => order.status === 'open');
    const closed_orders = orders.filter(order => order.status === 'closed').slice(0, 20);

    return {
      council,
      agents,
      recent_debates: debates,
      open_orders,
      closed_orders,
      performance_history: performance,
    };
  }

  async getCouncilAgents(councilId: number): Promise<CouncilAgent[]> {
    const response = await fetch(`${this.baseUrl}/${councilId}/agents`);
    if (!response.ok) {
      throw new Error('Failed to fetch council agents');
    }
    return response.json();
  }

  async getCouncilDebates(councilId: number, limit: number = 50): Promise<AgentDebate[]> {
    const response = await fetch(`${this.baseUrl}/${councilId}/debates?limit=${limit}`);
    if (!response.ok) {
      throw new Error('Failed to fetch council debates');
    }
    return response.json();
  }

  async getCouncilOrders(councilId: number, status?: string, limit: number = 100): Promise<MarketOrder[]> {
    const url = status
      ? `${this.baseUrl}/${councilId}/orders?status=${status}&limit=${limit}`
      : `${this.baseUrl}/${councilId}/orders?limit=${limit}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('Failed to fetch council orders');
    }
    return response.json();
  }

  async getCouncilPerformance(councilId: number, limit: number = 100): Promise<CouncilPerformance[]> {
    const response = await fetch(`${this.baseUrl}/${councilId}/performance?limit=${limit}`);
    if (!response.ok) {
      throw new Error('Failed to fetch council performance');
    }
    return response.json();
  }
}

export const councilService = new CouncilService();
