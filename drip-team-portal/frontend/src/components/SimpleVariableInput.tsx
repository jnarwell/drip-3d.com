import React, { useState, useRef, useEffect } from 'react';

interface SimpleVariableInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  componentId?: string;
  className?: string;
}

interface VariableSuggestion {
  partial: string;
  full: string;
  display: string;
}

const VARIABLE_PREFIXES = ['cmp', 'const', 'mat', 'steel', 'aluminum'];

export const SimpleVariableInput: React.FC<SimpleVariableInputProps> = ({
  value,
  onChange,
  placeholder = "Type formula (use Tab for autocomplete)",
  componentId,
  className = ""
}) => {
  const [suggestion, setSuggestion] = useState<VariableSuggestion | null>(null);
  const [variables, setVariables] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch available variables
  useEffect(() => {
    const fetchVariables = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 
          (window.location.hostname.includes('railway.app') 
            ? 'https://backend-production-aa29.up.railway.app' 
            : 'http://localhost:8000');
        
        const response = await fetch(
          `${apiUrl}/api/v1/variables/search${componentId ? `?component_id=${componentId}` : ''}`,
          {
            headers: {
              'Authorization': 'Bearer test',
              'Content-Type': 'application/json',
              'x-email': 'test@drip-3d.com'
            }
          }
        );
        
        if (response.ok) {
          const data = await response.json();
          const varList = data.variables?.map((v: any) => v.id) || [];
          setVariables(varList);
        }
      } catch (error) {
        console.error('Error fetching variables:', error);
      }
    };

    fetchVariables();
  }, [componentId]);

  const findSuggestion = (input: string, cursorPos: number): VariableSuggestion | null => {
    // Find the current word being typed
    const beforeCursor = input.substring(0, cursorPos);
    const words = beforeCursor.split(/[\s\+\-\*\/\(\)]|(?=#)/);
    const currentWord = words[words.length - 1];
    
    if (!currentWord || currentWord.length < 2) return null;

    // Check if it starts with # or a known prefix
    let searchTerm = currentWord;
    if (currentWord.startsWith('#')) {
      searchTerm = currentWord.substring(1);
    }

    // Find matching variables
    const matches = variables.filter(v => 
      v.toLowerCase().startsWith(searchTerm.toLowerCase())
    );

    if (matches.length === 0) {
      // Try to match prefixes
      const prefixMatch = VARIABLE_PREFIXES.find(prefix => 
        prefix.startsWith(searchTerm.toLowerCase())
      );
      if (prefixMatch) {
        return {
          partial: searchTerm,
          full: prefixMatch,
          display: prefixMatch
        };
      }
      return null;
    }

    // Return the first match
    const match = matches[0];
    return {
      partial: searchTerm,
      full: match,
      display: match.substring(searchTerm.length)
    };
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    const cursorPos = e.target.selectionStart || 0;
    
    onChange(newValue);
    
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
      
      // Replace the partial with the full suggestion
      const words = beforeCursor.split(/[\s\+\-\*\/\(\)]|(?=#)/);
      const lastWordStart = beforeCursor.length - (words[words.length - 1]?.length || 0);
      
      const newValue = 
        value.substring(0, lastWordStart) + 
        (beforeCursor[lastWordStart] === '#' ? '#' : '') +
        suggestion.full + 
        afterCursor;
      
      onChange(newValue);
      setSuggestion(null);
      
      // Move cursor to end of completed word
      setTimeout(() => {
        const newPos = lastWordStart + suggestion.full.length + (beforeCursor[lastWordStart] === '#' ? 1 : 0);
        inputRef.current?.setSelectionRange(newPos, newPos);
      }, 0);
    }
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
        className={`${className} pr-48`}
      />
      
      {suggestion && (
        <div className="absolute inset-y-0 right-2 flex items-center pointer-events-none">
          <span className="text-gray-400 text-sm">
            <span className="text-gray-600">{suggestion.partial}</span>
            <span className="text-gray-400">{suggestion.display}</span>
            <span className="ml-2 text-xs bg-gray-100 px-1 rounded">Tab</span>
          </span>
        </div>
      )}
    </div>
  );
};

export default SimpleVariableInput;