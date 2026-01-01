export interface ModelInput {
  name: string;
  unit: string;
  description?: string;
  required?: boolean;
  optional?: boolean;
}

export interface ModelOutput {
  name: string;
  unit: string;
  description?: string;
}

export interface PhysicsModel {
  id: number;
  name: string;
  description?: string;
  category: string;
  version_id: number;
  inputs: ModelInput[];
  outputs: ModelOutput[];
  current_version?: {
    id: number;
    version: number;
    inputs: ModelInput[];
    outputs: ModelOutput[];
  };
}

export interface CreateInstanceRequest {
  name: string;
  model_version_id: number;
  target_component_id?: number;
  bindings: Record<string, string>;
}

export interface ModelInstance {
  id: number;
  name: string;
  model_version_id: number;
  component_id?: number;
  computation_status: string;
  last_computed?: string;
  inputs?: Array<{
    input_name: string;
    literal_value?: number;
    source_value_node_id?: number;
    source_lookup?: { expression: string };
  }>;
  outputs?: Array<{
    name: string;
    computed_value: number;
    unit: string;
    status: string;
  }>;
}
