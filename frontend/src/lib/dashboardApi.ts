/**
 * Dashboard API Client Layer
 * Handles fetching candidate code maps and graph data from backend Neo4j integration.
 */

export interface CodeMapNode {
  id: string;
  name: string;
  group: string;
  val: number;
  description?: string | null;
  mastery_score?: number | null;
}

export interface CodeMapLink {
  source: string;
  target: string;
  label: string;
  weight: number;
}

export interface CodeMapGraphResponse {
  status: 'success' | 'empty' | 'error';
  nodes: CodeMapNode[];
  links: CodeMapLink[];
  message?: string | null;
  count_nodes: number;
  count_links: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Fetch candidate code map graph from backend Neo4j service.
 */
export async function fetchCodeMapGraph(sessionId?: string): Promise<CodeMapGraphResponse> {
  try {
    const url = new URL('/api/v1/dashboard/codemap', API_BASE_URL);
    if (sessionId) {
      url.searchParams.append('session_id', sessionId);
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      next: { revalidate: 10 }
    });

    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}: ${response.statusText}`);
    }

    const data: CodeMapGraphResponse = await response.json();
    return data;
  } catch (error: any) {
    console.error('Failed to fetch candidate code map from Neo4j API layer:', error);
    return {
      status: 'error',
      nodes: [
        { id: 'arrays_strings', name: 'Arrays & Strings', group: 'Data Structures', val: 12 },
        { id: 'two_pointers', name: 'Two Pointers', group: 'Algorithms', val: 9 },
        { id: 'binary_search', name: 'Binary Search', group: 'Algorithms', val: 9 },
        { id: 'trees_graphs', name: 'Trees & Graphs', group: 'Data Structures', val: 14 },
        { id: 'dynamic_programming', name: 'Dynamic Programming', group: 'Advanced', val: 16 }
      ],
      links: [
        { source: 'arrays_strings', target: 'two_pointers', label: 'PREREQUISITE_FOR', weight: 1 },
        { source: 'two_pointers', target: 'binary_search', label: 'EXTENDS', weight: 1 },
        { source: 'binary_search', target: 'dynamic_programming', label: 'DEPENDS_ON', weight: 1 },
        { source: 'arrays_strings', target: 'trees_graphs', label: 'FOUNDATION_FOR', weight: 1 }
      ],
      message: error?.message || 'Network error connecting to Neo4j service layer.',
      count_nodes: 5,
      count_links: 4
    };
  }
}
