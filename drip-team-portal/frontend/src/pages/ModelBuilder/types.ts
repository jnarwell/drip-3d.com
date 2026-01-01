import { z } from 'zod';

// Input/Output variable definition
export interface ModelVariable {
  id: string; // Temporary ID for UI tracking
  name: string;
  unit: string;
  description?: string;
}

// Model data throughout the wizard
export interface ModelBuilderData {
  // Step 1: Basic Info
  name: string;
  description: string;
  category: string;

  // Step 2: Variables
  inputs: ModelVariable[];
  outputs: ModelVariable[];

  // Step 3: Equations
  equations: Record<string, string>; // outputName -> equation string
}

// Validation schemas for each step
export const stepOneSchema = z.object({
  name: z.string().min(1, 'Model name is required'),
  description: z.string().optional(),
  category: z.string().min(1, 'Category is required'),
});

export const variableSchema = z.object({
  name: z.string().min(1, 'Variable name is required'),
  unit: z.string().min(1, 'Unit is required'),
  description: z.string().optional(),
});

// API Request/Response types
export interface ValidateModelRequest {
  inputs: Array<{ name: string; unit: string; description?: string }>;
  outputs: Array<{ name: string; unit: string; description?: string }>;
  equations: Record<string, string>;
}

export interface ValidateModelResponse {
  valid: boolean;
  errors: string[];
  dimensional_analysis: {
    [outputName: string]: {
      valid: boolean;
      expected_dimension: string;
      computed_dimension: string;
      message?: string;
    };
  };
}

export interface CreateModelRequest {
  name: string;
  description?: string;
  category: string;
  inputs: Array<{ name: string; unit: string; description?: string }>;
  outputs: Array<{ name: string; unit: string; description?: string }>;
  equations: Record<string, string>;
}

export interface CreateModelResponse {
  id: string;
  name: string;
  current_version: {
    id: string;
    version: number;
    equation_latex?: string;
  };
}

// Categories for physics models
export const MODEL_CATEGORIES = [
  { value: 'thermal', label: 'Thermal' },
  { value: 'mechanical', label: 'Mechanical' },
  { value: 'acoustic', label: 'Acoustic' },
  { value: 'electrical', label: 'Electrical' },
  { value: 'fluid', label: 'Fluid Dynamics' },
  { value: 'structural', label: 'Structural' },
  { value: 'electromagnetic', label: 'Electromagnetic' },
  { value: 'optical', label: 'Optical' },
  { value: 'multiphysics', label: 'Multi-Physics' },
  { value: 'other', label: 'Other' },
] as const;

// Initial state for wizard
export const initialModelData: ModelBuilderData = {
  name: '',
  description: '',
  category: '',
  inputs: [],
  outputs: [],
  equations: {},
};
