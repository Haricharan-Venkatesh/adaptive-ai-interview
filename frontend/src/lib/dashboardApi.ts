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
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000); // 8 second timeout

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
      next: { revalidate: 10 },
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);

    if (!response.ok) {
      if (response.status === 404) {
        return {
          status: 'empty',
          nodes: [],
          links: [],
          message: 'No candidate code map found. The graph might be empty or the language is unsupported.',
          count_nodes: 0,
          count_links: 0
        };
      }
      throw new Error(`HTTP Error ${response.status}: ${response.statusText}`);
    }

    const data: CodeMapGraphResponse = await response.json();
    return data;
  } catch (error: unknown) {
    clearTimeout(timeoutId);
    console.error('Failed to fetch candidate code map from Neo4j API layer:', error);
    
    let errorMessage = 'Network error connecting to Neo4j service layer.';
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        errorMessage = 'Request timed out. The Neo4j service took too long to respond.';
      } else {
        errorMessage = error.message;
      }
    }

    return {
      status: 'error',
      nodes: [],
      links: [],
      message: errorMessage,
      count_nodes: 0,
      count_links: 0
    };
  }
}
