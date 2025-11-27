import { useMemo } from 'react';

export type DomainType = 'company' | 'team';

export function useDomain(): DomainType {
  return useMemo(() => {
    const hostname = window.location.hostname;
    
    // Check if we're on the team subdomain
    if (hostname.includes('team.')) {
      return 'team';
    }
    
    // Default to company site for www.drip-3d.com, drip-3d.com, localhost, etc.
    return 'company';
  }, []);
}

export function useIsTeamDomain(): boolean {
  const domain = useDomain();
  return domain === 'team';
}

export function useIsCompanyDomain(): boolean {
  const domain = useDomain();
  return domain === 'company';
}