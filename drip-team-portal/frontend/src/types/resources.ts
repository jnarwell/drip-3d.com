// Enums
export enum TableType {
  SINGLE_VAR_LOOKUP = 'single_var_lookup',
  RANGE_BASED_LOOKUP = 'range_based_lookup',
  MULTI_VAR_LOOKUP = 'multi_var_lookup',
  REFERENCE_ONLY = 'reference_only'
}

export enum InterpolationType {
  LINEAR = 'linear',
  LOGARITHMIC = 'logarithmic',
  POLYNOMIAL = 'polynomial',
  RANGE_LOOKUP = 'range_lookup',
  NONE = 'none'
}

export enum ImportMethod {
  DOCUMENT_IMPORT = 'document_import',
  API_IMPORT = 'api_import',
  MANUAL_ENTRY = 'manual_entry',
  COPIED = 'copied'
}

export enum VerificationStatus {
  VERIFIED = 'verified',
  CITED = 'cited',
  UNVERIFIED = 'unverified'
}

export enum SourceType {
  STANDARD = 'standard',
  PAPER = 'paper',
  HANDBOOK = 'handbook',
  REPORT = 'report',
  EXPERIMENTAL = 'experimental',
  OTHER = 'other'
}

// Interfaces
export interface VariableDefinition {
  name: string;
  symbol: string;
  unit: string;
  description?: string;
}

export interface PropertyTableTemplate {
  id: number;
  name: string;
  description?: string;
  table_type: TableType;
  independent_vars: VariableDefinition[];
  dependent_vars: VariableDefinition[];
  interpolation_type: InterpolationType;
  extrapolation_allowed: boolean;
  require_monotonic: boolean;
  created_from_document: boolean;
  source_document_example?: string;
  is_public: boolean;
  workspace_id?: number;
  created_by: string;
  created_at: string;
  usage_count: number;
}

export interface PropertyTableSummary {
  id: number;
  name: string;
  description?: string;
  data_points_count: number;
  material_name?: string;
  verification_status: VerificationStatus;
  import_method: ImportMethod;
  source_authority?: string;
  source_citation?: string;
  created_by: string;
  created_at: string;
  last_updated: string;
}

export interface PropertyTable {
  id: number;
  name: string;
  description?: string;
  template_id?: number;
  material_id?: number;
  component_id?: number;
  data: Record<string, any>[];
  data_points_count: number;
  import_method: ImportMethod;
  source_document_path?: string;
  source_document_hash?: string;
  source_url?: string;
  source_citation?: string;
  source_type?: SourceType;
  source_authority?: string;
  verification_status: VerificationStatus;
  verification_method?: string;
  last_verified?: string;
  extracted_via_ocr: boolean;
  manual_corrections: number;
  data_quality?: string;
  applicable_conditions?: string;
  tags?: string[];
  last_updated: string;
  created_at: string;
  created_by: string;
  is_public: boolean;
  workspace_id?: number;
  template?: PropertyTableTemplate;
}

export interface DocumentAnalysisResult {
  table_name: string;
  table_type: TableType;
  independent_vars: VariableDefinition[];
  dependent_vars: VariableDefinition[];
  data_preview: Record<string, any>[];
  total_rows: number;
  source_info?: string;
  confidence_score: number;
  page_number?: number;
  extraction_method: string;
}

export interface CreatePropertyTableData {
  name: string;
  description?: string;
  template_id?: number;
  material_id?: number;
  component_id?: number;
  data: Record<string, any>[];
  import_method: ImportMethod;
  source_document_path?: string;
  source_url?: string;
  source_citation?: string;
  source_type?: SourceType;
  source_authority?: string;
  extracted_via_ocr?: boolean;
  data_quality?: string;
  applicable_conditions?: string;
  tags?: string[];
  is_public?: boolean;
  workspace_id?: number;
}