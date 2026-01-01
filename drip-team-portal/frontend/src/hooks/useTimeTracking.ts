import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useDevAwareAuth } from '../services/auth-domain';
import { useAuthenticatedApi } from '../services/api';

export interface TimeBreak {
  id: number;
  started_at: string;
  stopped_at: string | null;
  duration_seconds: number | null;
  note: string | null;
}

export interface EditHistoryEntry {
  field: string;
  old_value: string | null;
  new_value: string | null;
  reason: string;
  edited_by: string;
  edited_at: string;
}

export interface Resource {
  id: number;
  title: string;
  resource_type: string;
  url: string | null;
}

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
  resource?: Resource | null;
  description: string | null;
  is_uncategorized: boolean;
  component_id: number | null;
  component_name?: string | null;
  created_at: string;
  updated_at: string | null;
  // Break tracking
  breaks?: TimeBreak[];
  total_break_seconds?: number;
  on_break?: boolean;
  // Edit tracking
  was_edited?: boolean;
  edit_history?: EditHistoryEntry[];
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

export function useTimeEntries(filters: TimeEntryFilters = {}, myEntriesOnly = true) {
  const api = useAuthenticatedApi();
  const { user } = useDevAwareAuth();

  // Apply current user filter by default (for /time page)
  // Set myEntriesOnly=false for team views
  const effectiveUserId = myEntriesOnly && user?.email && !filters.user_id
    ? user.email
    : filters.user_id;

  return useQuery<{ entries: TimeEntry[]; total: number }>({
    queryKey: ['time', 'entries', filters, effectiveUserId],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (effectiveUserId) params.append('user_id', effectiveUserId);
      if (filters.component_id) params.append('component_id', String(filters.component_id));
      if (filters.limit) params.append('limit', String(filters.limit));

      const response = await api.get(`/api/v1/time/entries?${params.toString()}`);
      return response.data;
    },
    enabled: !myEntriesOnly || !!user?.email,
  });
}

export function useTimeSummary(
  filters: { start_date?: string; end_date?: string; group_by?: string; user_id?: string } = {},
  myEntriesOnly = true
) {
  const api = useAuthenticatedApi();
  const { user } = useDevAwareAuth();

  // Apply current user filter by default
  const effectiveUserId = myEntriesOnly && user?.email && !filters.user_id
    ? user.email
    : filters.user_id;

  return useQuery<TimeSummary>({
    queryKey: ['time', 'summary', filters, effectiveUserId],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.group_by) params.append('group_by', filters.group_by);
      if (effectiveUserId) params.append('user_id', effectiveUserId);

      const response = await api.get(`/api/v1/time/summary?${params.toString()}`);
      return response.data;
    },
    enabled: !myEntriesOnly || !!user?.email,
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
    mutationFn: async ({ entryId, updates, edit_reason }: {
      entryId: number;
      updates: Record<string, unknown>;
      edit_reason: string
    }) => {
      const response = await api.patch(`/api/v1/time/entries/${entryId}`, {
        ...updates,
        edit_reason,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['time', 'entries'] });
      queryClient.invalidateQueries({ queryKey: ['time', 'summary'] });
    },
  });
}

// =============================================================================
// BREAK MUTATIONS
// =============================================================================

export function useStartBreak() {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { entryId: number; note?: string }) => {
      const response = await api.post(`/api/v1/time/entries/${data.entryId}/breaks`, {
        note: data.note
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['time', 'active'] });
      queryClient.invalidateQueries({ queryKey: ['time', 'entries'] });
    },
  });
}

export function useStopBreak() {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { entryId: number; breakId: number }) => {
      const response = await api.post(
        `/api/v1/time/entries/${data.entryId}/breaks/${data.breakId}/stop`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['time', 'active'] });
      queryClient.invalidateQueries({ queryKey: ['time', 'entries'] });
    },
  });
}

// =============================================================================
// MANUAL ENTRY
// =============================================================================

export interface ManualEntryBreak {
  started_at: string;
  stopped_at: string;
  note?: string;
}

export interface ManualEntryPayload {
  started_at: string;
  stopped_at: string;
  breaks?: ManualEntryBreak[];
  linear_issue_id?: string;
  linear_issue_title?: string;
  resource_id?: number;
  description?: string;
  is_uncategorized?: boolean;
  component_id?: number;
}

export function useCreateManualEntry() {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ManualEntryPayload) => {
      const response = await api.post('/api/v1/time/entries', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['time', 'entries'] });
      queryClient.invalidateQueries({ queryKey: ['time', 'summary'] });
    },
  });
}
