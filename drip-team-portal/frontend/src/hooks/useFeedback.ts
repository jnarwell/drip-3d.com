import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';

export interface FeedbackSubmission {
  id: number;
  user_id: string;
  type: 'bug' | 'feature' | 'question';
  urgency: 'need_now' | 'nice_to_have';
  description: string;
  page_url: string;
  browser_info: { userAgent: string; viewportWidth: number; viewportHeight: number };
  status: 'new' | 'reviewed' | 'in_progress' | 'resolved' | 'wont_fix';
  resolution_notes: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeedbackFilters {
  status?: string;
  type?: string;
  urgency?: string;
  limit?: number;
  offset?: number;
}

export interface FeedbackCreatePayload {
  type: string;
  urgency: string;
  description: string;
  page_url: string;
  browser_info: { userAgent: string; viewportWidth: number; viewportHeight: number };
}

export interface FeedbackUpdatePayload {
  status?: string;
  resolution_notes?: string;
}

// List all feedback submissions with optional filters
export function useFeedbackList(filters: FeedbackFilters = {}) {
  const api = useAuthenticatedApi();

  return useQuery<{ feedback: FeedbackSubmission[]; total: number }>({
    queryKey: ['feedback', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.type) params.append('type', filters.type);
      if (filters.urgency) params.append('urgency', filters.urgency);
      if (filters.limit) params.append('limit', String(filters.limit));
      if (filters.offset) params.append('offset', String(filters.offset));

      const response = await api.get(`/api/v1/feedback?${params.toString()}`);
      return response.data;
    },
  });
}

// Get single feedback submission by ID
export function useFeedbackDetail(id: number) {
  const api = useAuthenticatedApi();

  return useQuery<FeedbackSubmission>({
    queryKey: ['feedback', id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/feedback/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

// Create new feedback submission
export function useCreateFeedback() {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: FeedbackCreatePayload) => {
      const response = await api.post('/api/v1/feedback', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feedback'] });
    },
  });
}

// Update feedback submission (status, resolution notes)
export function useUpdateFeedback() {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, updates }: { id: number; updates: FeedbackUpdatePayload }) => {
      const response = await api.patch(`/api/v1/feedback/${id}`, updates);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feedback'] });
    },
  });
}

// Export feedback as CSV
export function useExportFeedback(filters: FeedbackFilters = {}) {
  const api = useAuthenticatedApi();

  const exportFeedback = async () => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.type) params.append('type', filters.type);
    if (filters.urgency) params.append('urgency', filters.urgency);

    const response = await api.get(`/api/v1/feedback/export?${params.toString()}`, {
      responseType: 'blob',
    });

    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `feedback_export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return exportFeedback;
}
