import React, { useState, useEffect, useRef } from 'react';

interface Variable {
  id: string;
  display_name: string;
  value: number | string | null;
  unit: string;
  type: 'component_property' | 'system_constant' | 'material_property';
  source: string;
  description?: string;
}

interface VariablePickerProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  componentId?: string;
  disabled?: boolean;
  className?: string;
}

export const VariablePicker: React.FC<VariablePickerProps> = ({
  value,
  onChange,
  placeholder = "Enter value or #variable",
  componentId,
  disabled = false,
  className = ""
}) => {
  const [showPicker, setShowPicker] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [variables, setVariables] = useState<Variable[]>([]);
  const [loading, setLoading] = useState(false);
  const [cursorPosition, setCursorPosition] = useState(0);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [suggestion, setSuggestion] = useState<string>('');
  const inputRef = useRef<HTMLInputElement>(null);
  const pickerRef = useRef<HTMLDivElement>(null);

  // Track cursor position and detect # character
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    const cursorPos = e.target.selectionStart || 0;
    
    onChange(newValue);
    setCursorPosition(cursorPos);
    
    // Check if user typed # to trigger variable picker
    if (newValue[cursorPos - 1] === '#' || newValue.includes('#')) {
      triggerVariablePicker();
    } else if (showPicker && !newValue.includes('#')) {
      setShowPicker(false);
    }
  };

  const triggerVariablePicker = async () => {
    setShowPicker(true);
    setLoading(true);
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 
        (window.location.hostname.includes('railway.app') 
          ? 'https://backend-production-aa29.up.railway.app' 
          : 'http://localhost:8000');
      
      const response = await fetch(
        `${apiUrl}/api/v1/variables/search`,
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
        setVariables(data.variables || []);
      } else {
        console.error('Failed to fetch variables');
      }
    } catch (error) {
      console.error('Error fetching variables:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVariableSelect = (variable: Variable) => {
    // Replace the # character and any search term with the variable reference
    const beforeCursor = value.substring(0, cursorPosition);
    const afterCursor = value.substring(cursorPosition);
    
    // Find the last # in the before cursor text
    const hashIndex = beforeCursor.lastIndexOf('#');
    if (hashIndex !== -1) {
      const newValue = value.substring(0, hashIndex) + `#${variable.id}` + afterCursor;
      onChange(newValue);
    } else {
      // If no # found, just append the variable
      onChange(value + `#${variable.id}`);
    }
    
    setShowPicker(false);
    setSearchTerm('');
    
    // Focus back to input
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  };

  // Filter variables based on search term
  const filteredVariables = variables.filter(variable => 
    searchTerm === '' || 
    variable.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    variable.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Close picker when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(event.target as Node)) {
        setShowPicker(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const getVariableTypeIcon = (type: string) => {
    switch (type) {
      case 'component_property':
        return <div className="w-3 h-3 bg-blue-500 rounded-full" title="Component Property" />;
      case 'system_constant':
        return <div className="w-3 h-3 bg-green-500 rounded-full" title="System Constant" />;
      case 'material_property':
        return <div className="w-3 h-3 bg-purple-500 rounded-full" title="Material Property" />;
      default:
        return <div className="w-3 h-3 bg-gray-400 rounded-full" title="Variable" />;
    }
  };

  const formatValue = (val: number | string | null) => {
    if (val === null || val === undefined) return 'No value';
    if (typeof val === 'string') return val;
    if (typeof val === 'number') {
      return val.toLocaleString(undefined, { maximumFractionDigits: 4 });
    }
    return String(val);
  };

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={handleInputChange}
          placeholder={placeholder}
          disabled={disabled}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-10"
          onFocus={() => {
            // If input contains #, show picker
            if (value.includes('#')) {
              triggerVariablePicker();
            }
          }}
        />
        
        {/* Hash icon to indicate variable support */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-3">
          <svg 
            className="w-4 h-4 text-gray-400 cursor-pointer hover:text-blue-500" 
            onClick={triggerVariablePicker}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
          </svg>
        </div>
      </div>

      {/* Variable Picker Dropdown */}
      {showPicker && (
        <div 
          ref={pickerRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-80 overflow-hidden"
        >
          {/* Search header */}
          <div className="p-3 border-b border-gray-200">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search variables..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div className="mt-2 flex items-center gap-4 text-xs text-gray-600">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full" />
                <span>Component</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span>Constants</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-purple-500 rounded-full" />
                <span>Materials</span>
              </div>
            </div>
          </div>

          {/* Variables list */}
          <div className="max-h-60 overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center text-gray-500">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
                <div className="mt-2">Loading variables...</div>
              </div>
            ) : filteredVariables.length > 0 ? (
              <div className="py-1">
                {filteredVariables.map((variable) => (
                  <button
                    key={variable.id}
                    onClick={() => handleVariableSelect(variable)}
                    className="w-full px-3 py-2 text-left hover:bg-gray-100 focus:outline-none focus:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {getVariableTypeIcon(variable.type)}
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm text-gray-900 truncate">
                            {variable.display_name}
                          </div>
                          <div className="text-xs text-gray-500 font-mono">
                            #{variable.id}
                          </div>
                        </div>
                      </div>
                      <div className="text-right text-sm text-gray-600 ml-2">
                        <div className="font-medium">
                          {formatValue(variable.value)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {variable.unit}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-gray-500">
                {searchTerm ? `No variables found for "${searchTerm}"` : 'No variables available'}
              </div>
            )}
          </div>

          {/* Footer with instructions */}
          <div className="border-t border-gray-200 p-2 bg-gray-50">
            <div className="text-xs text-gray-600 text-center">
              Type <span className="font-mono bg-gray-200 px-1 rounded">#</span> to insert variables • 
              Variables update automatically in formulas
            </div>
          </div>
        </div>
      )}
    </div>
  );
};