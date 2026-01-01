import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';

export interface TimeEntry {
  id: number;
  user_id: string;
  user_email?: string;
  user_name?: string;
  started_at: string;
  stopped_at: string | null;
  duration_seconds: number | null;
  linear_issue_id: string | null;
  linear_issue_title: string | null;
  resource_id: number | null;
  resource_title?: string | null;
  description: string | null;
  is_uncategorized: boolean;
  component_id: number | null;
  component_name?: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface TimeEntryFilters {
  start_date?: string;
  end_date?: string;
  user_id?: string;
  component_id?: number;
  limit?: number;
}

export interface TimeSummaryGroup {
  key: string;
  total_seconds: number;
  entry_count: number;
}

export interface TimeSummary {
  groups: TimeSummaryGroup[];
}

export interface StartTimerPayload {
  linear_issue_id?: string;
  component_id?: number;
}

export interface StopTimerPayload {
  linear_issue_id?: string;
  linear_issue_title?: string;
  resource_id?: number;
  description?: string;
  is_uncategorized?: boolean;
  component_id?: number;
}

export function useActiveTimer() {
  const api = useAuthenticatedApi();

  return useQuery<TimeEntry | null>({
    queryKey: ['time', 'active'],
    queryFn: async () => {
      const response = await api.get('/api/v1/time/active');
      // Backend returns entry directly or null
      return response.data || null;
    },
    refetchInterval: 30000, // Poll every 30 seconds
  });
}

export function useTimeEntries(filters: TimeEntryFilters = {}) {
  const api = useAuthenticatedApi();

  return useQuery<{ entries: TimeEntry[]; total: number }>({
    queryKey: ['time', 'entries', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.user_id) params.append('user_id', filters.user_id);
      if (filters.component_id) params.append('component_id', String(filters.component_id));
      if (filters.limit) params.append('limit', String(filters.limit));

      const response = await api.get(`/api/v1/time/entries?${params.toString()}`);
      return response.data;
    },
  });
}

export function useTimeSummary(filters: { start_date?: string; end_date?: string; group_by?: string } = {}) {
  const api = useAuthenticatedApi();

  return useQuery<TimeSummary>({
    queryKey: ['time', 'summary', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.group_by) params.append('group_by', filters.group_by);

      const response = await api.get(`/api/v1/time/summary?${params.toString()}`);
      return response.data;
    },
  });
}

export function useAllActiveTimers() {
  const api = useAuthenticatedApi();

  return useQuery<{ active_timers: TimeEntry[]; count: number }>({
    queryKey: ['time', 'all-active'],
    queryFn: async () => {
      const response = await api.get('/api/v1/time/team/active');
      return response.data;
    },
    refetchInterval: 30000,
  });
}

export function useStartTimer() {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: StartTimerPayload = {}) => {
      const response = await api.post('/api/v1/time/start', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['time', 'active'] });
      queryClient.invalidateQueries({ queryKey: ['time', 'entries'] });
      queryClient.invalidateQueries({ queryKey: ['time', 'all-active'] });
    },
  });
}

export function useStopTimer() {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: StopTimerPayload = {}) => {
      const response = await api.post('/api/v1/time/stop', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['time', 'active'] });
      queryClient.invalidateQueries({ queryKey: ['time', 'entries'] });
      queryClient.invalidateQueries({ queryKey: ['time', 'summary'] });
      queryClient.invalidateQueries({ queryKey: ['time', 'all-active'] });
    },
  });
}

export function useDeleteTimeEntry() {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (entryId: number) => {
      const response = await api.delete(`/api/v1/time/entries/${entryId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['time', 'entries'] });
      queryClient.invalidateQueries({ queryKey: ['time', 'summary'] });
    },
  });
}

export function useUpdateTimeEntry() {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ entryId, payload }: { entryId: number; payload: Partial<StopTimerPayload> }) => {
      const response = await api.patch(`/api/v1/time/entries/${entryId}`, payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['time', 'entries'] });
      queryClient.invalidateQueries({ queryKey: ['time', 'summary'] });
    },
  });
}
