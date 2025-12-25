// Engineering Properties API Types

// Property Source Summary (from /sources endpoint)
export interface PropertySourceSummary {
  id: string;
  name: string;
  category: string;
  description?: string;
  type: 'table' | 'equation' | 'library';
  source: string;
  inputs: PropertyInput[];
  outputs: PropertyOutput[];
  view_count: number;
  column_count?: number;
  lookup_source_id?: string;  // If set, use this source ID for LOOKUP() instead of id
}

// Input definition
export interface PropertyInput {
  name: string;
  unit: string;
  type: 'discrete' | 'continuous';
  description?: string;
  values?: (string | number)[];
  range?: [number, number];
  optional?: boolean;
}

// Output definition
export interface PropertyOutput {
  name: string;
  unit: string;
  description?: string;
}

// Detailed source info (from /sources/{id} endpoint)
export interface PropertySourceDetail extends PropertySourceSummary {
  source_url?: string;
  version: string;
  views: PropertyView[];
}

// View definition
export interface PropertyView {
  id: string;
  name: string;
  description?: string;
  layout: 'flat' | 'nested';
}

// View data (from /sources/{id}/views/{view_id} endpoint)
export interface PropertyViewData {
  metadata: {
    source_id: string;
    source_name: string;
    view_id: string;
    view_name: string;
  };
  headers: PropertyViewHeader[];
  rows: PropertyViewRow[];
}

export interface PropertyViewHeader {
  key: string;
  label: string;
  unit: string;
  subscript?: string;
  is_input?: boolean;
}

export interface PropertyViewRow {
  section?: {
    label: string;
    value: string | number;
    unit: string;
  };
  values: Record<string, string | number | null>;
}

// Lookup request/response
export interface PropertyLookupRequest {
  source_id: string;
  output: string;
  inputs: Record<string, string | number>;
}

export interface PropertyLookupResponse {
  value: number;
  source_id: string;
  output: string;
  inputs: Record<string, string | number>;
}

// Category info
export interface PropertyCategory {
  id: string;
  name: string;
  description: string;
}
