import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuthenticatedApi } from '../../services/api';
import { PhysicsModel } from './types';

interface StepBindInputsProps {
  model: PhysicsModel;
  bindings: Record<string, string>;
  onChange: (bindings: Record<string, string>) => void;
  onValidationChange?: (allValid: boolean) => void;
}

type ValidationStatus = 'valid' | 'invalid' | 'pending' | 'empty';

interface PropertySuggestion {
  name: string;
  unit: string;
  has_value: boolean;
}

// Module-level cache shared across instances (same pattern as ExpressionInput)
const entityPropertiesCache = new Map<string, PropertySuggestion[]>();
const entityExistsCache = new Map<string, boolean>();
const CACHE_TTL_MS = 60000;
const cacheTimestamps = new Map<string, number>();

function getCached<T>(cache: Map<string, T>, key: string): T | null {
  const ts = cacheTimestamps.get(key);
  if (ts && Date.now() - ts < CACHE_TTL_MS) {
    return cache.get(key) ?? null;
  }
  return null;
}

function setCached<T>(cache: Map<string, T>, key: string, value: T): void {
  cache.set(key, value);
  cacheTimestamps.set(key, Date.now());
}

// Classify a binding value string into its type
function classifyBinding(value: string): 'empty' | 'literal' | 'reference' | 'expression' | 'lookup' {
  const trimmed = value.trim();
  if (!trimmed) return 'empty';

  // LOOKUP(...) pattern
  if (/^LOOKUP\s*\(/i.test(trimmed)) return 'lookup';

  // Pure reference: #ENTITY.property (no spaces, no operators outside the reference)
  if (/^#[a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z][a-zA-Z0-9_]*$/.test(trimmed)) return 'reference';

  // Pure numeric literal
  if (/^-?[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?$/.test(trimmed)) return 'literal';

  // Expression: contains operators, multiple references, or mixed content
  return 'expression';
}

export default function StepBindInputs({ model, bindings, onChange, onValidationChange }: StepBindInputsProps) {
  const api = useAuthenticatedApi();
  const inputs = model.inputs || [];

  const [validationStatus, setValidationStatus] = useState<Record<string, ValidationStatus>>({});
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Debounce timers per field
  const debounceTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  // Stable ref to hold the latest validateBinding without adding it to useEffect deps.
  // This breaks the infinite render loop caused by useAuthenticatedApi() creating a new
  // axios instance on every render, which makes validateBinding change every render, which
  // triggers the useEffect, which sets pending state, which re-renders, which repeats.
  const validateBindingRef = useRef<(name: string, value: string) => Promise<void>>(async () => {});

  const handleInputChange = (name: string, value: string) => {
    onChange({ ...bindings, [name]: value });
  };

  // Validate a single binding and update status.
  // Note: validateBinding is recreated when api changes (every render due to useAuthenticatedApi).
  // We sync it to validateBindingRef so the debounce useEffect can call it without depending on it.
  const validateBinding = useCallback(async (inputName: string, value: string) => {
    const kind = classifyBinding(value);

    if (kind === 'empty') {
      setValidationStatus(prev => ({ ...prev, [inputName]: 'empty' }));
      setValidationErrors(prev => ({ ...prev, [inputName]: '' }));
      return;
    }

    if (kind === 'literal') {
      setValidationStatus(prev => ({ ...prev, [inputName]: 'valid' }));
      setValidationErrors(prev => ({ ...prev, [inputName]: '' }));
      return;
    }

    if (kind === 'lookup') {
      // Accept LOOKUP expressions without deep validation
      setValidationStatus(prev => ({ ...prev, [inputName]: 'valid' }));
      setValidationErrors(prev => ({ ...prev, [inputName]: '' }));
      return;
    }

    // For references and expressions, validate the # references
    const refPattern = /#([a-zA-Z][a-zA-Z0-9_]*)\.([a-zA-Z][a-zA-Z0-9_]*)/g;
    const refs: Array<{ entity: string; property: string }> = [];
    let match;
    while ((match = refPattern.exec(value)) !== null) {
      refs.push({ entity: match[1], property: match[2] });
    }

    if (refs.length === 0 && kind === 'expression') {
      // Expression without references - just validate syntax via API
      setValidationStatus(prev => ({ ...prev, [inputName]: 'pending' }));
      try {
        const resp = await api.post('/api/v1/values/validate-expression', { expression: value });
        if (resp.data.valid) {
          setValidationStatus(prev => ({ ...prev, [inputName]: 'valid' }));
          setValidationErrors(prev => ({ ...prev, [inputName]: '' }));
        } else {
          setValidationStatus(prev => ({ ...prev, [inputName]: 'invalid' }));
          setValidationErrors(prev => ({
            ...prev,
            [inputName]: resp.data.error || 'Invalid expression syntax',
          }));
        }
      } catch {
        // Network error - accept with warning
        setValidationStatus(prev => ({ ...prev, [inputName]: 'valid' }));
        setValidationErrors(prev => ({ ...prev, [inputName]: '' }));
      }
      return;
    }

    // Validate each # reference
    setValidationStatus(prev => ({ ...prev, [inputName]: 'pending' }));

    for (const ref of refs) {
      const entityKey = ref.entity.toUpperCase();

      // Check entity existence (cached)
      let entityExists = getCached(entityExistsCache, entityKey);
      if (entityExists === null) {
        try {
          const resp = await api.get(`/api/v1/search/entities?q=${encodeURIComponent(ref.entity)}&limit=5`);
          const entities: Array<{ code: string; name: string }> = resp.data;
          // Match by exact code or generated code (case-insensitive)
          const found = entities.some(
            e => e.code.toUpperCase() === entityKey || e.name.toUpperCase() === ref.entity.toUpperCase()
          );
          entityExists = found;
          setCached(entityExistsCache, entityKey, found);
        } catch {
          // Network error - skip validation
          continue;
        }
      }

      if (!entityExists) {
        setValidationStatus(prev => ({ ...prev, [inputName]: 'invalid' }));
        setValidationErrors(prev => ({
          ...prev,
          [inputName]: `Component or material "${ref.entity}" not found`,
        }));
        return;
      }

      // Check property existence (cached)
      const propKey = `${entityKey}:${ref.property.toLowerCase()}`;
      let properties = getCached(entityPropertiesCache, entityKey);
      if (properties === null) {
        try {
          const resp = await api.get(
            `/api/v1/search/entities/${encodeURIComponent(ref.entity)}/properties?q=`
          );
          properties = resp.data as PropertySuggestion[];
          setCached(entityPropertiesCache, entityKey, properties);
        } catch {
          // Network error - skip property check
          continue;
        }
      }

      const propExists = properties.some(
        p => p.name.toLowerCase() === ref.property.toLowerCase()
      );

      if (!propExists) {
        setValidationStatus(prev => ({ ...prev, [inputName]: 'invalid' }));
        setValidationErrors(prev => ({
          ...prev,
          [inputName]: `Property "${ref.property}" not found on "${ref.entity}"`,
        }));
        return;
      }
    }

    // All references validated
    setValidationStatus(prev => ({ ...prev, [inputName]: 'valid' }));
    setValidationErrors(prev => ({ ...prev, [inputName]: '' }));
  }, [api]);

  // Keep the ref in sync with the latest validateBinding on every render.
  // This allows the debounce effect below to call the latest version without listing
  // validateBinding as a dependency (which would cause the infinite loop).
  validateBindingRef.current = validateBinding;

  // Debounced validation trigger per field.
  // IMPORTANT: validateBinding is intentionally NOT in this dependency array.
  // It is accessed via validateBindingRef.current to avoid the infinite render loop.
  // The ref is always up-to-date because validateBindingRef.current = validateBinding
  // runs on every render before effects fire.
  useEffect(() => {
    inputs.forEach(input => {
      const value = bindings[input.name] || '';

      // Clear existing timer
      if (debounceTimers.current[input.name]) {
        clearTimeout(debounceTimers.current[input.name]);
      }

      // Set pending immediately for non-empty values
      if (value.trim()) {
        setValidationStatus(prev => ({ ...prev, [input.name]: 'pending' }));
      } else {
        setValidationStatus(prev => ({ ...prev, [input.name]: 'empty' }));
        setValidationErrors(prev => ({ ...prev, [input.name]: '' }));
      }

      // Debounce the actual validation - use ref to avoid stale closure
      debounceTimers.current[input.name] = setTimeout(() => {
        validateBindingRef.current(input.name, value);
      }, 500);
    });

    // Cleanup on unmount
    return () => {
      Object.values(debounceTimers.current).forEach(clearTimeout);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bindings, inputs]);

  // Notify parent when validation state changes
  useEffect(() => {
    if (!onValidationChange) return;

    const requiredInputs = inputs.filter(i => i.required !== false && !i.optional);
    const allValid = requiredInputs.every(i => {
      const status = validationStatus[i.name];
      return status === 'valid';
    });

    onValidationChange(allValid);
  }, [validationStatus, inputs, onValidationChange]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Bind Inputs</h2>
        <p className="text-sm text-gray-600">
          Provide values for each input. You can enter literal values or reference expressions.
        </p>
      </div>

      <div className="space-y-4">
        {inputs.map(input => {
          const value = bindings[input.name] || '';
          const isRequired = input.required !== false && !input.optional;
          const status = validationStatus[input.name] || 'empty';
          const errorMsg = validationErrors[input.name] || '';

          const inputBorderClass =
            status === 'invalid'
              ? 'border-red-400 focus:ring-red-400'
              : status === 'valid'
              ? 'border-green-400 focus:ring-green-400'
              : 'border-gray-300 focus:ring-indigo-500';

          return (
            <div key={input.name} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <label className="block text-sm font-medium text-gray-900">
                    {input.name}
                    {isRequired && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  {input.description && (
                    <p className="text-xs text-gray-500 mt-0.5">{input.description}</p>
                  )}
                </div>
                <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded">
                  {input.unit}
                </span>
              </div>

              <input
                type="text"
                value={value}
                onChange={(e) => handleInputChange(input.name, e.target.value)}
                placeholder={`Enter value or expression (e.g., 100, #COMP.prop)`}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:border-transparent text-sm font-mono ${inputBorderClass}`}
              />

              {/* Validation feedback */}
              {status === 'pending' && value.trim() && (
                <p className="mt-1 text-xs text-gray-400">Checking...</p>
              )}
              {status === 'valid' && value.trim() && (
                <p className="mt-1 text-xs text-green-600">Valid</p>
              )}
              {status === 'invalid' && errorMsg && (
                <p className="mt-1 text-xs text-red-600">{errorMsg}</p>
              )}

              <div className="mt-2 text-xs text-gray-500">
                Examples: <code className="bg-gray-200 px-1 rounded">25.5</code>,{' '}
                <code className="bg-gray-200 px-1 rounded">#FRAME.height</code>,{' '}
                <code className="bg-gray-200 px-1 rounded">LOOKUP("steam", "h", T=373)</code>
              </div>
            </div>
          );
        })}
      </div>

      {inputs.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          This model has no inputs to bind.
        </div>
      )}
    </div>
  );
}
