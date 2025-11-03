import { Flow } from '@/types/flow';
import { API_BASE_URL } from './config';
import { councilsV2Service, CouncilV2 } from './councils-v2-api';

// Keep legacy flag - set to true to use councils-v2 API, false for old flows API
const USE_COUNCILS_V2 = true;

export interface CreateFlowRequest {
  name: string;
  description?: string;
  nodes: any;
  edges: any;
  viewport?: any;
  data?: any;
  is_template?: boolean;
  tags?: string[];
}

export interface UpdateFlowRequest {
  name?: string;
  description?: string;
  nodes?: any;
  edges?: any;
  viewport?: any;
  data?: any;
  is_template?: boolean;
  tags?: string[];
}

/**
 * Convert CouncilV2 to Flow format (for backward compatibility).
 *
 * Handles conversion of agents (dict/object) to nodes (array) and
 * connections (dict/object) to edges (array) for ReactFlow compatibility.
 */
function councilToFlow(council: CouncilV2): Flow {
  // Convert agents dict to nodes array
  // If agents is an object with node definitions, convert to array
  // If it's already an array or empty, handle appropriately
  let nodes = [];
  if (Array.isArray(council.agents)) {
    nodes = council.agents;
  } else if (council.agents && typeof council.agents === 'object') {
    // Convert object to array (assuming it's a dict of node_id: node_data)
    nodes = Object.keys(council.agents).length > 0
      ? Object.values(council.agents)
      : [];
  }

  // Convert connections dict to edges array
  let edges = [];
  if (Array.isArray(council.connections)) {
    edges = council.connections;
  } else if (council.connections && typeof council.connections === 'object') {
    // Convert object to array (assuming it's a dict of edge definitions)
    edges = Object.keys(council.connections).length > 0
      ? Object.values(council.connections)
      : [];
  }

  return {
    id: council.id,
    name: council.name,
    description: council.description || undefined,
    nodes,
    edges,
    viewport: council.visual_layout,
    data: council.workflow_config,
    is_template: council.is_template,
    tags: council.tags || undefined,
    created_at: council.created_at || new Date().toISOString(),
    updated_at: council.updated_at || undefined,
  };
}

export const flowService = {
  // Get all flows (councils)
  async getFlows(): Promise<Flow[]> {
    if (USE_COUNCILS_V2) {
      // Use councils-v2 API - get summaries first
      const councilSummaries = await councilsV2Service.getCouncils({
        includeSystem: true,
        includeUser: true,
        includePublic: true,
      });

      // Fetch full details for each council to get agents/connections
      const councilPromises = councilSummaries.map(summary =>
        councilsV2Service.getCouncil(summary.id)
      );
      const councils = await Promise.all(councilPromises);

      return councils.map(councilToFlow);
    }

    // Fallback to old API
    const response = await fetch(`${API_BASE_URL}/api/v1/flows/`);
    if (!response.ok) {
      throw new Error('Failed to fetch flows');
    }
    return response.json();
  },

  // Get a specific flow
  async getFlow(id: number): Promise<Flow> {
    if (USE_COUNCILS_V2) {
      const council = await councilsV2Service.getCouncil(id);
      return councilToFlow(council);
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/flows/${id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch flow');
    }
    return response.json();
  },

  // Create a new flow
  async createFlow(data: CreateFlowRequest): Promise<Flow> {
    if (USE_COUNCILS_V2) {
      const council = await councilsV2Service.createCouncil({
        name: data.name,
        description: data.description,
        agents: data.nodes,
        connections: data.edges,
        visual_layout: data.viewport,
        workflow_config: data.data,
        is_template: data.is_template,
        tags: data.tags,
      });
      return councilToFlow(council);
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/flows/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error('Failed to create flow');
    }
    return response.json();
  },

  // Update an existing flow
  async updateFlow(id: number, data: UpdateFlowRequest): Promise<Flow> {
    if (USE_COUNCILS_V2) {
      const council = await councilsV2Service.updateCouncil(id, {
        name: data.name,
        description: data.description,
        agents: data.nodes,
        connections: data.edges,
        visual_layout: data.viewport,
        workflow_config: data.data,
        is_template: data.is_template,
        tags: data.tags,
      });
      return councilToFlow(council);
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/flows/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error('Failed to update flow');
    }
    return response.json();
  },

  // Delete a flow
  async deleteFlow(id: number): Promise<void> {
    if (USE_COUNCILS_V2) {
      await councilsV2Service.deleteCouncil(id);
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/flows/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete flow');
    }
  },

  // Duplicate a flow (uses fork in councils-v2)
  async duplicateFlow(id: number, newName?: string): Promise<Flow> {
    if (USE_COUNCILS_V2) {
      // Note: Fork will fail without auth (user_id constraint)
      // For now, we'll fetch and create a new council instead
      try {
        const sourceCouncil = await councilsV2Service.getCouncil(id);
        const duplicatedCouncil = await councilsV2Service.createCouncil({
          name: newName || `Copy of ${sourceCouncil.name}`,
          description: sourceCouncil.description || undefined,
          agents: sourceCouncil.agents,
          connections: sourceCouncil.connections,
          visual_layout: sourceCouncil.visual_layout,
          workflow_config: sourceCouncil.workflow_config,
          is_template: false,
          tags: sourceCouncil.tags || undefined,
        });
        return councilToFlow(duplicatedCouncil);
      } catch (error) {
        console.error('Fork/duplicate failed:', error);
        throw new Error('Failed to duplicate flow. This feature requires authentication.');
      }
    }

    const url = `${API_BASE_URL}/api/v1/flows/${id}/duplicate${newName ? `?new_name=${encodeURIComponent(newName)}` : ''}`;
    const response = await fetch(url, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error('Failed to duplicate flow');
    }
    return response.json();
  },

  // Create a default flow for new users
  async createDefaultFlow(nodes: any, edges: any, viewport?: any): Promise<Flow> {
    return this.createFlow({
      name: 'My First Council',
      description: 'Welcome to Pantheon Elite! Start building your trading council here.',
      nodes,
      edges,
      viewport,
    });
  },
};
