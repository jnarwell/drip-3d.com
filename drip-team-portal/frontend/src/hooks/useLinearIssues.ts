import { useQuery } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';

export interface LinearIssue {
  id: string;
  identifier: string; // e.g., "DRP-156"
  title: string;
  state: string;
  priority: number;
  project_id?: string;
  project_name?: string;
  assignee_id?: string;
  assignee_name?: string;
  updated_at: string;
}

export interface UseLinearIssuesOptions {
  state?: 'active' | 'completed' | 'all';
  search?: string;
  limit?: number;
}

export function useLinearIssues(options: UseLinearIssuesOptions = {}) {
  const api = useAuthenticatedApi();

  return useQuery<{ issues: LinearIssue[] }>({
    queryKey: ['linear', 'issues', options],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (options.state) params.append('state', options.state);
      if (options.search) params.append('search', options.search);
      if (options.limit) params.append('limit', String(options.limit));

      const response = await api.get(`/api/v1/linear-enhanced/issues?${params.toString()}`);
      return response.data;
    },
    staleTime: 60000, // Cache for 1 minute
  });
}
