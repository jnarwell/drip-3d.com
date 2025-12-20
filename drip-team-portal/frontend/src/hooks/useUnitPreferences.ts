import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';

export interface UnitPreference {
  id: number;
  quantity_type: string;
  unit_symbol: string;
  unit_name: string;
  unit_id: number;
  precision: number;
}

export interface UnitPreferenceCreate {
  quantity_type: string;
  unit_symbol: string;
  precision: number;
}

export interface BulkPreferenceUpdate {
  preferences: UnitPreferenceCreate[];
}

export function useUnitPreferences() {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  const { data: preferences, isLoading, error, refetch } = useQuery<UnitPreference[]>({
    queryKey: ['unit-preferences'],
    queryFn: async () => {
      const response = await api.get('/api/v1/me/unit-preferences');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const updatePreference = useMutation({
    mutationFn: async (data: UnitPreferenceCreate) => {
      const response = await api.put(
        `/api/v1/me/unit-preferences/${data.quantity_type}`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unit-preferences'] });
    },
  });

  const bulkUpdatePreferences = useMutation({
    mutationFn: async (data: BulkPreferenceUpdate) => {
      const response = await api.put('/api/v1/me/unit-preferences', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unit-preferences'] });
    },
  });

  const deletePreference = useMutation({
    mutationFn: async (quantityType: string) => {
      const response = await api.delete(`/api/v1/me/unit-preferences/${quantityType}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unit-preferences'] });
    },
  });

  // Helper to get preference for a specific quantity type
  const getPreference = (quantityType: string): UnitPreference | undefined => {
    return preferences?.find(p => p.quantity_type === quantityType);
  };

  // Helper to get preferred unit symbol for a quantity type
  const getPreferredUnit = (quantityType: string): string | undefined => {
    return getPreference(quantityType)?.unit_symbol;
  };

  // Helper to get precision for a quantity type
  const getPrecision = (quantityType: string): number => {
    return getPreference(quantityType)?.precision ?? 0.01;
  };

  return {
    preferences,
    isLoading,
    error,
    refetch,
    updatePreference,
    bulkUpdatePreferences,
    deletePreference,
    getPreference,
    getPreferredUnit,
    getPrecision,
  };
}
