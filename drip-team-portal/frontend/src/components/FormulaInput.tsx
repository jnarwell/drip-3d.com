import React, { useState, useRef, useEffect } from 'react';
import { useAuthenticatedApi } from '../services/api';

interface FormulaInputProps {
  value: string;
  onChange: (value: string) => void;
  onFormulaDetected?: (isFormula: boolean) => void;
  placeholder?: string;
  componentId?: string;
  className?: string;
  disabled?: boolean;
}

export const FormulaInput: React.FC<FormulaInputProps> = ({
  value,
  onChange,
  onFormulaDetected,
  placeholder = "Enter value or formula (e.g., cmp1.width * cmp1.height)",
  componentId,
  className = "",
  disabled = false
}) => {
  const [suggestion, setSuggestion] = useState('');
  const [variables, setVariables] = useState<string[]>([]);
  const [isLoadingVariables, setIsLoadingVariables] = useState(false);
  const [hasUserTyped, setHasUserTyped] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const api = useAuthenticatedApi();

  // Fetch available variables on mount
  useEffect(() => {
    const fetchVariables = async () => {
      setIsLoadingVariables(true);
      try {
        // Exclude current component from suggestions
        const params = componentId ? { exclude_component: componentId } : {};
        console.log('FormulaInput: Fetching variables with params:', params);
        const response = await api.get('/api/v1/variables/search', { params });
        console.log('FormulaInput: Received variables:', response.data.variables?.length || 0, 'total');
        const varList = response.data.variables?.map((v: any) => v.id) || [];
        console.log('FormulaInput: Variable IDs:', varList);
        setVariables(varList);
      } catch (error) {
        console.error('Failed to fetch variables:', error);
      }
      setIsLoadingVariables(false);
    };

    fetchVariables();
  }, [componentId]);

  // Detect if input is a formula
  useEffect(() => {
    const isFormula = /\b(cmp\d+|[a-z]+)\.[a-zA-Z]+/.test(value) || 
                     /[\+\-\*\/\(\)]/.test(value) ||
                     /^[0-9\.\s]+[\+\-\*\/]/.test(value);
    onFormulaDetected?.(isFormula);
  }, [value, onFormulaDetected]);

  const findSuggestion = (input: string, cursorPos: number): string => {
    const beforeCursor = input.substring(0, cursorPos);
    
    // Find the current word/variable being typed (including # prefix)
    const matches = beforeCursor.match(/#?([a-zA-Z0-9]+\.?[a-zA-Z0-9]*)$/); 
    if (!matches) {
      console.log('FormulaInput: No matches for pattern in:', beforeCursor);
      return '';
    }
    
    const partial = matches[1];
    console.log('FormulaInput: Looking for suggestions for partial:', partial);
    if (!partial) return '';

    // Find matching variables
    const varMatches = variables.filter(v => 
      v.toLowerCase().startsWith(partial.toLowerCase())
    );
    
    console.log('FormulaInput: Found', varMatches.length, 'matches:', varMatches);

    if (varMatches.length > 0) {
      // Return the completion part only
      const suggestion = varMatches[0].substring(partial.length);
      console.log('FormulaInput: Suggesting:', suggestion);
      return suggestion;
    }

    return '';
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    const cursorPos = e.target.selectionStart || 0;
    
    onChange(newValue);
    setHasUserTyped(true);
    
    // Update suggestion
    const newSuggestion = findSuggestion(newValue, cursorPos);
    setSuggestion(newSuggestion);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Tab' && suggestion) {
      e.preventDefault();
      
      const cursorPos = inputRef.current?.selectionStart || 0;
      const beforeCursor = value.substring(0, cursorPos);
      const afterCursor = value.substring(cursorPos);
      
      // Insert the suggestion
      const newValue = beforeCursor + suggestion + afterCursor;
      onChange(newValue);
      setSuggestion('');
      
      // Move cursor after the completed text
      setTimeout(() => {
        const newPos = cursorPos + suggestion.length;
        inputRef.current?.setSelectionRange(newPos, newPos);
        inputRef.current?.focus();
      }, 0);
    }
  };

  // Get the position for the suggestion overlay
  const getSuggestionStyle = () => {
    if (!suggestion || !inputRef.current) return {};
    
    const input = inputRef.current;
    const cursorPos = input.selectionStart || 0;
    const beforeCursor = value.substring(0, cursorPos);
    
    // Create a temporary span to measure text width
    const span = document.createElement('span');
    span.style.font = getComputedStyle(input).font;
    span.style.visibility = 'hidden';
    span.style.position = 'absolute';
    span.textContent = beforeCursor;
    document.body.appendChild(span);
    const textWidth = span.offsetWidth;
    document.body.removeChild(span);
    
    return {
      left: `${textWidth + 12}px`
    };
  };

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className={className}
      />
      
      {suggestion && (
        <div 
          className="absolute top-0 flex items-center h-full pointer-events-none"
          style={getSuggestionStyle()}
        >
          <span className="text-gray-400">
            {suggestion}
            <span className="ml-2 text-xs bg-gray-200 text-gray-600 px-1 rounded">Tab</span>
          </span>
        </div>
      )}
      
      {!hasUserTyped && (/\b(cmp\d+|[a-z]+)\.[a-zA-Z]+/.test(value) || /[\+\-\*\/\(\)]/.test(value)) && (
        <div className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500">
          Formula detected
        </div>
      )}
    </div>
  );
};

export default FormulaInput;