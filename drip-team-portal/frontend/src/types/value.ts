/**
 * Value System Types - Universal Value Nodes with Expressions
 *
 * ValueNodes are the core of the value system:
 * - LITERAL: Direct numeric value with optional unit
 * - EXPRESSION: Mathematical expression that computes to a value
 * - REFERENCE: Points to another ValueNode
 * - TABLE_LOOKUP: Future - table function result
 */

import { Unit } from './unit';

// ==================== Enums ====================

export type NodeType = 'literal' | 'expression' | 'reference' | 'table_lookup';

export type ComputationStatus = 'pending' | 'valid' | 'stale' | 'error' | 'circular';

// ==================== Core Types ====================

export interface UnitBrief {
  id: number;
  symbol: string;
  name: string;
}

export interface ValueNode {
  id: number;
  node_type: NodeType;
  description?: string;

  // For literals
  numeric_value?: number;
  unit_id?: number;
  unit?: UnitBrief;

  // For expressions
  expression_string?: string;

  // For references
  reference_node_id?: number;

  // Computed result
  computed_value?: number;
  computed_unit_id?: number;
  computed_unit?: UnitBrief;
  computation_status: ComputationStatus;
  computation_error?: string;
  last_computed?: string;

  // Metadata
  created_at: string;
  created_by?: string;
}

export interface ValueNodeBrief {
  id: number;
  node_type: NodeType;
  computed_value?: number;
  computation_status: ComputationStatus;
  expression_string?: string;
}

// ==================== Request Types ====================

export interface LiteralCreate {
  value: number;
  unit_id?: number;
  description?: string;
}

export interface ExpressionCreate {
  expression: string;
  description?: string;
}

export interface ReferenceCreate {
  reference_node_id: number;
  description?: string;
}

export interface ExpressionValidateRequest {
  expression: string;
}

// ==================== Response Types ====================

export interface RecalculateResponse {
  success: boolean;
  value?: number;
  unit_symbol?: string;
  error?: string;
  nodes_recalculated: number;
}

export interface BulkRecalculateResponse {
  total_nodes: number;
  successful: number;
  failed: number;
  errors: Array<{ node_id: number; error: string }>;
}

export interface ExpressionValidateResponse {
  valid: boolean;
  references: string[];
  error?: string;
  parsed_preview?: string;
}

export interface DependencyTreeNode {
  id: number;
  node_type: NodeType;
  status: ComputationStatus;
  value?: number;
  expression?: string;
  dependencies: DependencyTreeNode[];
  truncated: boolean;
}

// ==================== Helper Functions ====================

/**
 * Get a display string for a value node
 */
export function formatValueNode(node: ValueNode): string {
  if (node.computation_status === 'error') {
    return `Error: ${node.computation_error || 'Unknown error'}`;
  }

  if (node.computation_status === 'circular') {
    return 'Circular dependency';
  }

  if (node.computed_value === undefined || node.computed_value === null) {
    return node.computation_status === 'pending' ? 'Pending...' : 'No value';
  }

  const value = formatNumber(node.computed_value);
  const unit = node.computed_unit?.symbol || node.unit?.symbol;

  return unit ? `${value} ${unit}` : value;
}

/**
 * Format a number for display (handles precision)
 */
export function formatNumber(value: number, precision: number = 6): string {
  if (Number.isInteger(value)) {
    return value.toString();
  }

  // Use scientific notation for very large or small numbers
  if (Math.abs(value) > 1e6 || (Math.abs(value) < 1e-4 && value !== 0)) {
    return value.toExponential(precision - 1);
  }

  // Remove trailing zeros
  return parseFloat(value.toPrecision(precision)).toString();
}

/**
 * Get status color for UI
 */
export function getStatusColor(status: ComputationStatus): string {
  switch (status) {
    case 'valid':
      return 'green';
    case 'pending':
      return 'blue';
    case 'stale':
      return 'yellow';
    case 'error':
      return 'red';
    case 'circular':
      return 'red';
    default:
      return 'gray';
  }
}

/**
 * Get human-readable status text
 */
export function getStatusText(status: ComputationStatus): string {
  switch (status) {
    case 'valid':
      return 'Valid';
    case 'pending':
      return 'Pending calculation';
    case 'stale':
      return 'Needs recalculation';
    case 'error':
      return 'Calculation error';
    case 'circular':
      return 'Circular dependency';
    default:
      return 'Unknown';
  }
}

/**
 * Check if a value node needs recalculation
 */
export function needsRecalculation(node: ValueNode): boolean {
  return node.computation_status === 'stale' || node.computation_status === 'pending';
}

/**
 * Check if a value node has a valid computed value
 */
export function hasValidValue(node: ValueNode): boolean {
  return (
    node.computation_status === 'valid' &&
    node.computed_value !== undefined &&
    node.computed_value !== null
  );
}

/**
 * Get node type display name
 */
export function getNodeTypeName(type: NodeType): string {
  switch (type) {
    case 'literal':
      return 'Literal Value';
    case 'expression':
      return 'Expression';
    case 'reference':
      return 'Reference';
    case 'table_lookup':
      return 'Table Lookup';
    default:
      return 'Unknown';
  }
}

/**
 * Parse expression to extract references
 * Returns array of reference strings like ["cmp001.length", "steel.density"]
 */
export function extractReferences(expression: string): string[] {
  const pattern = /#([a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)?)/g;
  const matches = expression.matchAll(pattern);
  const refs: string[] = [];
  for (const match of matches) {
    if (!refs.includes(match[1])) {
      refs.push(match[1]);
    }
  }
  return refs;
}

/**
 * Validate expression syntax (client-side basic check)
 * Returns error message or null if valid
 */
export function validateExpressionSyntax(expression: string): string | null {
  if (!expression.trim()) {
    return 'Expression cannot be empty';
  }

  // Check for balanced parentheses
  let depth = 0;
  for (const char of expression) {
    if (char === '(') depth++;
    if (char === ')') depth--;
    if (depth < 0) return 'Unbalanced parentheses';
  }
  if (depth !== 0) return 'Unbalanced parentheses';

  // Check for invalid characters
  const validPattern = /^[#a-zA-Z0-9_.+\-*/^()\s]+$/;
  if (!validPattern.test(expression)) {
    return 'Expression contains invalid characters';
  }

  return null;
}

// ==================== Expression Builder Helpers ====================

/**
 * Available functions for expressions
 */
export const AVAILABLE_FUNCTIONS = [
  { name: 'sqrt', description: 'Square root', example: 'sqrt(x)' },
  { name: 'sin', description: 'Sine (radians)', example: 'sin(x)' },
  { name: 'cos', description: 'Cosine (radians)', example: 'cos(x)' },
  { name: 'tan', description: 'Tangent (radians)', example: 'tan(x)' },
  { name: 'log', description: 'Natural logarithm', example: 'log(x)' },
  { name: 'ln', description: 'Natural logarithm', example: 'ln(x)' },
  { name: 'exp', description: 'Exponential (e^x)', example: 'exp(x)' },
  { name: 'abs', description: 'Absolute value', example: 'abs(x)' },
] as const;

/**
 * Available constants for expressions
 */
export const AVAILABLE_CONSTANTS = [
  { name: 'pi', description: 'Pi (3.14159...)', value: Math.PI },
  { name: 'e', description: "Euler's number (2.71828...)", value: Math.E },
] as const;

/**
 * Available operators
 */
export const AVAILABLE_OPERATORS = [
  { symbol: '+', description: 'Addition' },
  { symbol: '-', description: 'Subtraction' },
  { symbol: '*', description: 'Multiplication' },
  { symbol: '/', description: 'Division' },
  { symbol: '^', description: 'Power' },
  { symbol: '**', description: 'Power (alternative)' },
] as const;
