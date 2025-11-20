export enum ReferenceType {
  COMPONENT_PROPERTY = 'component_property',
  SYSTEM_CONSTANT = 'system_constant',
  LITERAL_VALUE = 'literal_value',
  FUNCTION_CALL = 'function_call',
}

export enum FormulaStatus {
  VALID = 'valid',
  ERROR = 'error',
  CIRCULAR = 'circular',
  MISSING_DEPS = 'missing_deps',
  DISABLED = 'disabled',
}

export interface PropertyReference {
  id: number;
  formula_id: number;
  variable_name: string;
  reference_type: ReferenceType;
  target_component_id?: number;
  target_property_definition_id?: number;
  target_constant_symbol?: string;
  literal_value?: number;
  function_name?: string;
  function_args?: number[];
  description?: string;
  units_expected?: string;
  default_value?: number;
}

export interface PropertyFormula {
  id: number;
  name: string;
  description?: string;
  property_definition_id: number;
  component_id?: number;
  formula_expression: string;
  is_active: boolean;
  validation_status: FormulaStatus;
  validation_message?: string;
  calculation_order: number;
  version: number;
  created_at: string;
  updated_at: string;
  created_by: string;
  references: PropertyReference[];
  property_definition?: any;
  component?: any;
}

export interface FormulaValidationResponse {
  is_valid: boolean;
  error_message?: string;
  variables_found?: string[];
  dependencies?: number[];
}

export interface CalculationResponse {
  success: boolean;
  value?: number;
  error_message?: string;
  input_values?: Record<string, any>;
  calculation_time_ms?: number;
}