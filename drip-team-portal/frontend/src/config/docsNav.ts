export interface DocNavItem {
  title: string;
  path?: string;
  children?: DocNavItem[];
}

export interface DocNavSection {
  title: string;
  items: DocNavItem[];
}

export const docsNav: DocNavSection[] = [
  {
    title: 'Getting Started',
    items: [
      { title: 'Overview', path: '/docs/getting-started' },
      { title: 'Navigation', path: '/docs/getting-started/navigation' },
      { title: 'Feedback', path: '/docs/getting-started/feedback' },
    ],
  },
  {
    title: 'Components',
    items: [
      { title: 'Overview', path: '/docs/components' },
      { title: 'Registry', path: '/docs/components/registry' },
      { title: 'Detail View', path: '/docs/components/detail' },
      { title: 'Properties', path: '/docs/components/properties' },
      { title: 'Materials', path: '/docs/components/materials' },
    ],
  },
  {
    title: 'Testing',
    items: [
      { title: 'Overview', path: '/docs/testing' },
      { title: 'Protocols', path: '/docs/testing/protocols' },
      { title: 'Runs', path: '/docs/testing/runs' },
      { title: 'Execution', path: '/docs/testing/execution' },
      { title: 'Results', path: '/docs/testing/results' },
    ],
  },
  {
    title: 'Models',
    items: [
      { title: 'Overview', path: '/docs/models' },
      { title: 'Creating', path: '/docs/models/creating' },
      { title: 'Equations', path: '/docs/models/equations' },
      { title: 'Versioning', path: '/docs/models/versioning' },
    ],
  },
  {
    title: 'Analysis',
    items: [
      { title: 'Overview', path: '/docs/analysis' },
      { title: 'Creating', path: '/docs/analysis/creating' },
      { title: 'Bindings', path: '/docs/analysis/bindings' },
      { title: 'Chaining', path: '/docs/analysis/chaining' },
    ],
  },
  {
    title: 'Time Tracking',
    items: [
      { title: 'Overview', path: '/docs/time' },
      { title: 'Timer', path: '/docs/time/timer' },
      { title: 'Manual Entry', path: '/docs/time/manual' },
      { title: 'Categorization', path: '/docs/time/categorization' },
      { title: 'Team View', path: '/docs/time/team-view' },
    ],
  },
  {
    title: 'Reports',
    items: [
      { title: 'Overview', path: '/docs/reports' },
      { title: 'Activity', path: '/docs/reports/activity' },
      { title: 'Charts', path: '/docs/reports/charts' },
      { title: 'Export', path: '/docs/reports/export' },
    ],
  },
  {
    title: 'Resources',
    items: [
      { title: 'Overview', path: '/docs/resources' },
      { title: 'Property Tables', path: '/docs/resources/property-tables' },
      { title: 'Constants', path: '/docs/resources/constants' },
      { title: 'Documents', path: '/docs/resources/documents' },
      { title: 'Contacts', path: '/docs/resources/contacts' },
    ],
  },
  {
    title: 'Reference',
    items: [
      { title: 'Units', path: '/docs/reference/units' },
      { title: 'Expressions', path: '/docs/reference/expressions' },
      { title: 'Keyboard Shortcuts', path: '/docs/reference/keyboard-shortcuts' },
    ],
  },
  {
    title: 'Settings',
    items: [
      { title: 'Settings', path: '/docs/settings' },
    ],
  },
];

// Helper to get the markdown file path from a route path
export function getMarkdownPath(routePath: string): string {
  // Clean the path
  let cleanPath = routePath.replace(/^\/docs\/?/, '').replace(/\/$/, '');

  if (!cleanPath) {
    // Root /docs route - try getting-started as landing page
    return '/docs/getting-started/index.md';
  }

  // Check if this looks like a section root (single segment like "components", "testing")
  // These should map to index.md files
  const segments = cleanPath.split('/');

  if (segments.length === 1) {
    // Section root like /docs/components -> /docs/components/index.md
    return `/docs/${cleanPath}/index.md`;
  }

  // Multi-segment path like /docs/components/registry -> /docs/components/registry.md
  return `/docs/${cleanPath}.md`;
}

// Flatten navigation for search/iteration
export function flattenNav(nav: DocNavSection[]): DocNavItem[] {
  const items: DocNavItem[] = [];

  for (const section of nav) {
    for (const item of section.items) {
      if (item.path) {
        items.push(item);
      }
      if (item.children) {
        for (const child of item.children) {
          if (child.path) {
            items.push(child);
          }
        }
      }
    }
  }

  return items;
}
