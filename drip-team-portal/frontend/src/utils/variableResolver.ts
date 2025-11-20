// Variable resolution utilities for the formula system

export interface VariableReference {
  id: string;
  display_name: string;
  value: number | string | null;
  unit: string;
  type: 'component_property' | 'system_constant' | 'material_property';
  source: string;
}

/**
 * Check if a string contains variable references (starts with #)
 */
export function hasVariableReferences(input: string): boolean {
  return input.includes('#');
}

/**
 * Extract all variable references from a string
 */
export function extractVariableReferences(input: string): string[] {
  const variablePattern = /#([a-zA-Z0-9_\-\.]+)/g;
  const matches = [];
  let match;
  
  while ((match = variablePattern.exec(input)) !== null) {
    matches.push(match[1]); // The captured group without the #
  }
  
  return matches;
}

/**
 * Resolve a single variable reference to its current value
 */
export async function resolveVariable(variableId: string): Promise<VariableReference | null> {
  try {
    const response = await fetch(
      `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/variables/resolve/${variableId}`,
      {
        headers: {
          'Authorization': 'Bearer test',
          'Content-Type': 'application/json',
          'x-email': 'test@drip-3d.com'
        }
      }
    );
    
    if (response.ok) {
      return await response.json();
    } else {
      console.error(`Failed to resolve variable: ${variableId}`);
      return null;
    }
  } catch (error) {
    console.error(`Error resolving variable ${variableId}:`, error);
    return null;
  }
}

/**
 * Resolve all variable references in a string and return the resolved values
 */
export async function resolveAllVariables(input: string): Promise<Map<string, VariableReference>> {
  const variableIds = extractVariableReferences(input);
  const resolvedVariables = new Map<string, VariableReference>();
  
  // Resolve all variables in parallel
  const promises = variableIds.map(async (id) => {
    const resolved = await resolveVariable(id);
    if (resolved) {
      resolvedVariables.set(id, resolved);
    }
  });
  
  await Promise.all(promises);
  return resolvedVariables;
}

/**
 * Replace variable references in a string with their resolved values
 */
export function replaceVariableReferences(
  input: string, 
  resolvedVariables: Map<string, VariableReference>
): string {
  let result = input;
  
  for (const [variableId, variable] of resolvedVariables) {
    const pattern = new RegExp(`#${variableId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`, 'g');
    const value = variable.value !== null ? String(variable.value) : '0';
    result = result.replace(pattern, value);
  }
  
  return result;
}

/**
 * Check if a value appears to be a formula (contains variable references or mathematical operators)
 */
export function isFormula(input: string): boolean {
  return hasVariableReferences(input) || 
         /[+\-*/()^]/.test(input) ||
         /\b(sin|cos|tan|log|ln|sqrt|abs|exp|pow)\s*\(/.test(input);
}

/**
 * Validate variable references in a string
 */
export async function validateVariableReferences(input: string): Promise<{
  isValid: boolean;
  invalidVariables: string[];
  resolvedVariables: Map<string, VariableReference>;
}> {
  const variableIds = extractVariableReferences(input);
  const resolvedVariables = new Map<string, VariableReference>();
  const invalidVariables: string[] = [];
  
  // Try to resolve all variables
  for (const id of variableIds) {
    const resolved = await resolveVariable(id);
    if (resolved) {
      resolvedVariables.set(id, resolved);
    } else {
      invalidVariables.push(id);
    }
  }
  
  return {
    isValid: invalidVariables.length === 0,
    invalidVariables,
    resolvedVariables
  };
}

/**
 * Format a variable reference for display
 */
export function formatVariableDisplay(variable: VariableReference): string {
  const value = variable.value !== null ? String(variable.value) : 'No value';
  const unit = variable.unit ? ` ${variable.unit}` : '';
  return `${variable.display_name}: ${value}${unit}`;
}

/**
 * Get the numeric value from a variable, handling string values
 */
export function getNumericValue(variable: VariableReference): number | null {
  if (variable.value === null || variable.value === undefined) {
    return null;
  }
  
  if (typeof variable.value === 'number') {
    return variable.value;
  }
  
  if (typeof variable.value === 'string') {
    // Try to parse numeric value from string
    const parsed = parseFloat(variable.value);
    return isNaN(parsed) ? null : parsed;
  }
  
  return null;
}