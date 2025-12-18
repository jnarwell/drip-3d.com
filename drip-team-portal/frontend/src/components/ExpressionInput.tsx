import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuthenticatedApi } from '../services/api';

interface EntitySuggestion {
  code: string;
  name: string;
  type: 'component' | 'material';
  category?: string;
}

interface PropertySuggestion {
  name: string;
  unit: string;
  type?: string;
  has_value: boolean;
}

interface ExpressionInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  onCancel?: () => void;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}

/**
 * Expression input with ghost text autocomplete.
 *
 * - Type `#` to start a reference
 * - Ghost text shows the best matching entity code
 * - Tab to accept ghost text (adds `.` after entity)
 * - After `.`, ghost text shows property names
 * - Tab to accept property
 */
// Simple cache for search results (shared across all ExpressionInput instances)
const entityCache = new Map<string, EntitySuggestion[]>();
const propertyCache = new Map<string, PropertySuggestion[]>();
const CACHE_TTL = 60000; // 1 minute
const cacheTimestamps = new Map<string, number>();

const getCachedResult = <T,>(cache: Map<string, T>, key: string): T | null => {
  const timestamp = cacheTimestamps.get(key);
  if (timestamp && Date.now() - timestamp < CACHE_TTL) {
    return cache.get(key) || null;
  }
  return null;
};

const setCachedResult = <T,>(cache: Map<string, T>, key: string, value: T) => {
  cache.set(key, value);
  cacheTimestamps.set(key, Date.now());
};

const ExpressionInput: React.FC<ExpressionInputProps> = ({
  value,
  onChange,
  onSubmit,
  onCancel,
  placeholder = 'Enter value or expression (e.g., #CODE.property * 2)',
  className = '',
  autoFocus = false,
}) => {
  const api = useAuthenticatedApi();
  const inputRef = useRef<HTMLInputElement>(null);

  const [ghostText, setGhostText] = useState('');
  const [suggestionType, setSuggestionType] = useState<'entity' | 'property'>('entity');
  const [fullSuggestion, setFullSuggestion] = useState<string>(''); // Full code/property to complete

  // Find the current reference being typed (everything after the last #)
  const getCurrentReference = useCallback(() => {
    const cursorPos = inputRef.current?.selectionStart || value.length;
    const textBeforeCursor = value.slice(0, cursorPos);

    // Find the last # before cursor
    const lastHashIndex = textBeforeCursor.lastIndexOf('#');
    if (lastHashIndex === -1) return null;

    // Get the reference text (from # to cursor)
    const refText = textBeforeCursor.slice(lastHashIndex + 1);

    // Check if there's a space or operator that would end the reference
    const endMatch = refText.match(/[\s+\-*/()]/);
    if (endMatch) return null;

    return {
      text: refText,
      startIndex: lastHashIndex,
      hasDot: refText.includes('.'),
      beforeDot: refText.split('.')[0],
      afterDot: refText.includes('.') ? refText.split('.')[1] : ''
    };
  }, [value]);

  // Debounce timer refs
  const entityTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const propertyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Track the latest query to prevent race conditions
  const latestEntityQueryRef = useRef<string>('');
  const latestPropertyQueryRef = useRef<{ entityCode: string; query: string }>({ entityCode: '', query: '' });

  // Apply entity suggestions to ghost text
  const applyEntitySuggestion = useCallback((suggestions: EntitySuggestion[], requestQuery: string) => {
    if (suggestions.length > 0) {
      const match = suggestions[0];
      if (match.code.toUpperCase().startsWith(requestQuery.toUpperCase())) {
        const remaining = match.code.slice(requestQuery.length);
        setGhostText(remaining);
        setFullSuggestion(match.code);
        setSuggestionType('entity');
        return;
      }
    }
    setGhostText('');
    setFullSuggestion('');
  }, []);

  // Fetch best matching entity (with caching)
  const fetchEntitySuggestion = useCallback((query: string) => {
    // Clear previous timer
    if (entityTimerRef.current) {
      clearTimeout(entityTimerRef.current);
    }

    // Track this as the latest query
    latestEntityQueryRef.current = query;

    if (!query) {
      setGhostText('');
      setFullSuggestion('');
      return;
    }

    const cacheKey = `entity:${query.toLowerCase()}`;

    // Check cache first - apply immediately if found
    const cached = getCachedResult(entityCache, cacheKey);
    if (cached) {
      applyEntitySuggestion(cached, query);
      return;
    }

    // No debounce - fire immediately since we handle race conditions
    const requestQuery = query;

    (async () => {
      try {
        const response = await api.get(`/api/v1/search/entities?q=${encodeURIComponent(query)}&limit=1`);
        const suggestions: EntitySuggestion[] = response.data;

        // Cache the result
        setCachedResult(entityCache, cacheKey, suggestions);

        // Only apply if this is still the latest query (prevent race conditions)
        if (latestEntityQueryRef.current !== requestQuery) {
          return;
        }

        applyEntitySuggestion(suggestions, requestQuery);
      } catch (error) {
        if (latestEntityQueryRef.current === requestQuery) {
          setGhostText('');
          setFullSuggestion('');
        }
      }
    })();
  }, [api, applyEntitySuggestion]);

  // Apply property suggestions to ghost text
  const applyPropertySuggestion = useCallback((suggestions: PropertySuggestion[], requestQuery: string) => {
    if (suggestions.length > 0) {
      const match = suggestions[0];
      if (match.name.toLowerCase().startsWith(requestQuery.toLowerCase())) {
        const remaining = match.name.slice(requestQuery.length);
        setGhostText(remaining);
        setFullSuggestion(match.name);
        setSuggestionType('property');
        return;
      }
    }
    setGhostText('');
    setFullSuggestion('');
  }, []);

  // Fetch best matching property (with caching)
  const fetchPropertySuggestion = useCallback((entityCode: string, query: string) => {
    // Clear previous timer
    if (propertyTimerRef.current) {
      clearTimeout(propertyTimerRef.current);
    }

    // Track this as the latest query
    latestPropertyQueryRef.current = { entityCode, query };

    const cacheKey = `property:${entityCode.toLowerCase()}:${query.toLowerCase()}`;

    // Check cache first - apply immediately if found
    const cached = getCachedResult(propertyCache, cacheKey);
    if (cached) {
      applyPropertySuggestion(cached, query);
      return;
    }

    // No debounce - fire immediately since we handle race conditions
    const requestEntityCode = entityCode;
    const requestQuery = query;

    (async () => {
      try {
        const response = await api.get(
          `/api/v1/search/entities/${encodeURIComponent(entityCode)}/properties?q=${encodeURIComponent(query)}`
        );
        const suggestions: PropertySuggestion[] = response.data;

        // Cache the result
        setCachedResult(propertyCache, cacheKey, suggestions);

        // Only apply if this is still the latest query (prevent race conditions)
        if (latestPropertyQueryRef.current.entityCode !== requestEntityCode ||
            latestPropertyQueryRef.current.query !== requestQuery) {
          return;
        }

        applyPropertySuggestion(suggestions, requestQuery);
      } catch (error) {
        if (latestPropertyQueryRef.current.entityCode === requestEntityCode &&
            latestPropertyQueryRef.current.query === requestQuery) {
          setGhostText('');
          setFullSuggestion('');
        }
      }
    })();
  }, [api, applyPropertySuggestion]);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (entityTimerRef.current) clearTimeout(entityTimerRef.current);
      if (propertyTimerRef.current) clearTimeout(propertyTimerRef.current);
    };
  }, []);

  // Pre-fetch all entities on mount to warm up cache
  useEffect(() => {
    const prefetchEntities = async () => {
      // Skip if we already have cached data
      if (entityCache.size > 0) return;

      try {
        // Fetch all entities (increased limit for pre-fetch)
        const response = await api.get('/api/v1/search/entities?q=&limit=50');
        const allEntities: EntitySuggestion[] = response.data;

        // Cache results for each entity code prefix
        allEntities.forEach(entity => {
          const code = entity.code.toLowerCase();
          // Cache for each prefix length (f, fr, fra, fram, frame, etc.)
          for (let i = 1; i <= code.length; i++) {
            const prefix = code.slice(0, i);
            const cacheKey = `entity:${prefix}`;
            // Only cache if not already cached
            if (!entityCache.has(cacheKey)) {
              // Filter entities that match this prefix
              const matching = allEntities.filter(e =>
                e.code.toLowerCase().startsWith(prefix)
              );
              setCachedResult(entityCache, cacheKey, matching.slice(0, 1));
            }
          }
        });
      } catch (error) {
        // Ignore prefetch errors
      }
    };

    prefetchEntities();
  }, [api]);

  // Update ghost text based on current reference
  useEffect(() => {
    const ref = getCurrentReference();

    if (!ref) {
      setGhostText('');
      setFullSuggestion('');
      return;
    }

    if (ref.hasDot) {
      // After the dot - search properties
      if (ref.beforeDot) {
        fetchPropertySuggestion(ref.beforeDot, ref.afterDot);
      }
    } else {
      // Before the dot - search entities
      fetchEntitySuggestion(ref.text);
    }
  }, [value, getCurrentReference, fetchEntitySuggestion, fetchPropertySuggestion]);

  // Handle Tab to accept ghost text
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Tab' && ghostText && fullSuggestion) {
      e.preventDefault();

      const ref = getCurrentReference();
      if (!ref) return;

      const cursorPos = inputRef.current?.selectionStart || value.length;
      const beforeRef = value.slice(0, ref.startIndex);
      const afterCursor = value.slice(cursorPos);

      let newValue: string;
      let newCursorPos: number;

      if (suggestionType === 'entity') {
        // Complete entity and add dot
        newValue = `${beforeRef}#${fullSuggestion}.${afterCursor}`;
        newCursorPos = beforeRef.length + 1 + fullSuggestion.length + 1;
      } else {
        // Complete property
        newValue = `${beforeRef}#${ref.beforeDot}.${fullSuggestion}${afterCursor}`;
        newCursorPos = beforeRef.length + 1 + ref.beforeDot.length + 1 + fullSuggestion.length;
      }

      onChange(newValue);
      setGhostText('');
      setFullSuggestion('');

      // Set cursor position after React re-render
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.setSelectionRange(newCursorPos, newCursorPos);
          inputRef.current.focus();
        }
      }, 0);
      return;
    }

    if (e.key === 'Enter' && onSubmit) {
      onSubmit();
    }
    if (e.key === 'Escape' && onCancel) {
      onCancel();
    }
  };

  return (
    <div className="relative">
      <div className="relative">
        {/* Ghost text layer */}
        <div
          className="absolute inset-0 px-3 py-2 font-mono text-sm pointer-events-none whitespace-pre"
          style={{ color: 'transparent' }}
        >
          {value}
          <span className="text-gray-400">{ghostText}</span>
        </div>

        {/* Actual input */}
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm bg-transparent ${className}`}
          autoFocus={autoFocus}
          autoComplete="off"
        />
      </div>

      {/* Hint */}
      {ghostText && (
        <div className="mt-1 text-xs text-gray-400">
          Press <kbd className="px-1 py-0.5 bg-gray-100 rounded text-gray-600">Tab</kbd> to complete
        </div>
      )}
    </div>
  );
};

export default ExpressionInput;
