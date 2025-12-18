export enum ComponentStatus {
  NOT_TESTED = "NOT_TESTED",
  IN_TESTING = "IN_TESTING",
  VERIFIED = "VERIFIED",
  FAILED = "FAILED"
}

export enum ComponentCategory {
  ACOUSTIC = "Acoustic",
  THERMAL = "Thermal",
  MECHANICAL = "Mechanical",
  ELECTRICAL = "Electrical",
  MATERIAL = "Material"
}

export enum RDPhase {
  PHASE_1 = "PHASE_1",
  PHASE_2 = "PHASE_2",
  PHASE_3 = "PHASE_3"
}

export enum TestStatus {
  NOT_STARTED = "NOT_STARTED",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  BLOCKED = "BLOCKED"
}

export enum TestResultStatus {
  PASS = "PASS",
  FAIL = "FAIL",
  PARTIAL = "PARTIAL"
}

export interface Component {
  id: number;
  component_id: string;
  name: string;
  part_number?: string;
  category: ComponentCategory;
  status: ComponentStatus;
  phase: RDPhase;
  unit_cost?: number;
  quantity: number;
  tech_specs?: Record<string, any>;
  purchase_order?: string;
  supplier?: string;
  lead_time_days?: number;
  order_date?: string;
  expected_delivery?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  updated_by?: string;
}

export interface Test {
  id: number;
  test_id: string;
  name: string;
  category?: string;
  purpose?: string;
  duration_hours?: number;
  prerequisites?: string[];
  status: TestStatus;
  executed_date?: string;
  engineer?: string;
  notes?: string;
  linear_issue_id?: string;
  linear_sync_status?: string;
  created_at: string;
  updated_at: string;
}

export interface TestResult {
  id: number;
  test_id: number;
  component_id?: number;
  result: TestResultStatus;
  steering_force?: number;
  bonding_strength?: number;
  temperature_max?: number;
  drip_number?: number;
  physics_validated: boolean;
  executed_at: string;
  executed_by: string;
  notes?: string;
}

export interface User {
  id: number;
  email: string;
  name?: string;
  is_active: boolean;
  is_admin: boolean;
  last_login?: string;
  created_at: string;
}

export enum PropertyType {
  THERMAL = "thermal",
  ELECTRICAL = "electrical",
  MECHANICAL = "mechanical",
  ACOUSTIC = "acoustic",
  MATERIAL = "material",
  DIMENSIONAL = "dimensional",
  OPTICAL = "optical",
  OTHER = "other"
}

export enum ValueType {
  SINGLE = "single",
  RANGE = "range",
  AVERAGE = "average"
}

export interface PropertyDefinition {
  id: number;
  name: string;
  property_type: PropertyType;
  unit: string;
  description?: string;
  value_type: ValueType;
  is_custom: boolean;
  created_at: string;
  created_by?: string;
}

export interface ComponentProperty {
  id: number;
  component_id: number;
  property_definition_id: number;
  property_definition: PropertyDefinition;
  single_value?: number;
  min_value?: number;
  max_value?: number;
  average_value?: number;
  tolerance?: number;
  notes?: string;
  source?: string;
  conditions?: Record<string, any>;
  updated_at: string;
  updated_by?: string;
  // Value system integration
  value_node_id?: number;
  value_node?: {
    id: number;
    node_type: 'literal' | 'expression' | 'reference' | 'table_lookup';
    expression_string?: string;
    computed_value?: number;
    computed_unit_symbol?: string;
    computation_status: 'pending' | 'valid' | 'stale' | 'error' | 'circular';
  };
}

export interface DashboardStats {
  totalComponents: number;
  componentsVerified: number;
  componentsFailed: number;
  totalTests: number;
  testsComplete: number;
  testsInProgress: number;
  physicsValidated: boolean;
  componentsByCategory: Array<{ category: string; count: number }>;
  componentsByStatus: Array<{ status: string; count: number }>;
  campaignProgress: Array<{ date: string; completed: number; planned: number }>;
  criticalPath: Array<{
    id: number;
    test_id: string;
    name: string;
    status: string;
    blocking: string[];
    blocked: boolean;
  }>;
  risks: Array<{
    category: string;
    severity: string;
    description: string;
    mitigation: string;
  }>;
}