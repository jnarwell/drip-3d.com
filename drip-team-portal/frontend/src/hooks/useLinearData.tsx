import { useState, useEffect } from 'react';

interface LinearPhase {
  phase: number;
  title: string;
  description: string;
  targetDate: string;
  progress: number;
  projects: LinearProject[];
}

interface LinearProject {
  id: string;
  name: string;
  description: string;
  status: string;
  progress: number;
  targetDate: string;
  health: string;
  lead: {
    id: string;
    name: string;
    email: string;
  } | null;
  teamMembers: string[];
  memberCount: number;
}

interface LinearTeamMember {
  id: string;
  linearId: string;
  name: string;
  email: string;
  avatarUrl: string;
  isAdmin: boolean;
  activeProjects: string[];
  leadProjects: ProjectAssignment[];
  memberProjects: ProjectAssignment[];
}

interface ProjectAssignment {
  projectName: string;
  projectId: string;
  phase: number;
  progress: number;
  health: string;
}

interface UseLinearProgressReturn {
  phases: LinearPhase[];
  loading: boolean;
  error: Error | null;
  lastUpdated: string | null;
  refetch: () => Promise<void>;
}

interface UseLinearTeamReturn {
  members: LinearTeamMember[];
  loading: boolean;
  error: Error | null;
  lastUpdated: string | null;
  refetch: () => Promise<void>;
}

interface UseLinearMemberProjectsReturn {
  leadProjects: ProjectAssignment[];
  memberProjects: ProjectAssignment[];
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useLinearProgress(): UseLinearProgressReturn {
  const [phases, setPhases] = useState<LinearPhase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchData = async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);

      const url = new URL('/api/v1/linear/progress', API_BASE_URL);
      if (forceRefresh) {
        url.searchParams.append('force_refresh', 'true');
      }

      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error(`Failed to fetch progress data: ${response.statusText}`);
      }

      const data = await response.json();
      setPhases(data.phases || []);
      setLastUpdated(data.lastUpdated || null);
    } catch (err) {
      setError(err as Error);
      console.error('Error fetching Linear progress data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const refetch = () => fetchData(true);

  return { phases, loading, error, lastUpdated, refetch };
}

export function useLinearTeam(): UseLinearTeamReturn {
  const [members, setMembers] = useState<LinearTeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchData = async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);

      const url = new URL('/api/v1/linear-enhanced/team-members', API_BASE_URL);
      if (forceRefresh) {
        url.searchParams.append('force_refresh', 'true');
      }

      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error(`Failed to fetch team data: ${response.statusText}`);
      }

      const data = await response.json();
      setMembers(data.members || []);
      setLastUpdated(data.lastUpdated || null);
    } catch (err) {
      setError(err as Error);
      console.error('Error fetching Linear team data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const refetch = () => fetchData(true);

  return { members, loading, error, lastUpdated, refetch };
}

export function useLinearMemberProjects(memberId: string): UseLinearMemberProjectsReturn {
  const [leadProjects, setLeadProjects] = useState<ProjectAssignment[]>([]);
  const [memberProjects, setMemberProjects] = useState<ProjectAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = async () => {
    if (!memberId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const url = new URL(`/api/v1/linear-enhanced/member/${memberId}/projects`, API_BASE_URL);
      const response = await fetch(url.toString());
      
      if (!response.ok) {
        throw new Error(`Failed to fetch member projects: ${response.statusText}`);
      }

      const data = await response.json();
      setLeadProjects(data.leadProjects || []);
      setMemberProjects(data.memberProjects || []);
    } catch (err) {
      setError(err as Error);
      console.error('Error fetching member projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [memberId]);

  const refetch = () => fetchData();

  return { leadProjects, memberProjects, loading, error, refetch };
}

// Helper function to refresh all Linear data
export async function refreshAllLinearData(): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/linear-enhanced/refresh-all`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Failed to refresh data: ${response.statusText}`);
    }

    // Return void - individual hooks will refetch their data
  } catch (err) {
    console.error('Error refreshing all Linear data:', err);
    throw err;
  }
}