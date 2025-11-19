import React, { useState, useEffect, useMemo } from 'react';
import { getConstants, createConstant, updateConstant, deleteConstant } from '../../services/api';
import { formatUnitWithSubscripts } from '../../utils/formatters';
import { formatUnitWithSubscriptsJSX } from '../../utils/formattersJSX';

interface SystemConstant {
  id: number;
  symbol: string;
  name: string;
  value: number;
  unit: string | null;
  description: string | null;
  category: string;
  is_editable: boolean;
  created_at: string;
  created_by: string | null;
}

const Constants: React.FC = () => {
  const [constants, setConstants] = useState<SystemConstant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortConfig, setSortConfig] = useState<{
    key: keyof SystemConstant;
    direction: 'asc' | 'desc';
  }>({ key: 'symbol', direction: 'asc' });
  
  // CRUD state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editingConstant, setEditingConstant] = useState<SystemConstant | null>(null);
  const [deletingConstant, setDeletingConstant] = useState<SystemConstant | null>(null);
  const [saving, setSaving] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState({
    symbol: '',
    name: '',
    value: 0,
    unit: '',
    description: '',
    category: ''
  });
  
  // Symbol/Unit helper state
  const [showSymbolHelper, setShowSymbolHelper] = useState(false);
  const [showUnitHelper, setShowUnitHelper] = useState(false);
  const [showCommandMenu, setShowCommandMenu] = useState(false);
  const [symbolInputMode, setSymbolInputMode] = useState<'normal' | 'subscript' | 'superscript'>('normal');
  const [unitInputMode, setUnitInputMode] = useState<'normal' | 'subscript' | 'superscript'>('normal');
  const [activeField, setActiveField] = useState<'symbol' | 'unit' | null>(null);

  // Greek alphabet and mathematical symbols
  const greekLetters = [
    { name: 'Alpha', lower: 'α', upper: 'Α' },
    { name: 'Beta', lower: 'β', upper: 'Β' },
    { name: 'Gamma', lower: 'γ', upper: 'Γ' },
    { name: 'Delta', lower: 'δ', upper: 'Δ' },
    { name: 'Epsilon', lower: 'ε', upper: 'Ε' },
    { name: 'Zeta', lower: 'ζ', upper: 'Ζ' },
    { name: 'Eta', lower: 'η', upper: 'Η' },
    { name: 'Theta', lower: 'θ', upper: 'Θ' },
    { name: 'Iota', lower: 'ι', upper: 'Ι' },
    { name: 'Kappa', lower: 'κ', upper: 'Κ' },
    { name: 'Lambda', lower: 'λ', upper: 'Λ' },
    { name: 'Mu', lower: 'μ', upper: 'Μ' },
    { name: 'Nu', lower: 'ν', upper: 'Ν' },
    { name: 'Xi', lower: 'ξ', upper: 'Ξ' },
    { name: 'Omicron', lower: 'ο', upper: 'Ο' },
    { name: 'Pi', lower: 'π', upper: 'Π' },
    { name: 'Rho', lower: 'ρ', upper: 'Ρ' },
    { name: 'Sigma', lower: 'σ', upper: 'Σ' },
    { name: 'Tau', lower: 'τ', upper: 'Τ' },
    { name: 'Upsilon', lower: 'υ', upper: 'Υ' },
    { name: 'Phi', lower: 'φ', upper: 'Φ' },
    { name: 'Chi', lower: 'χ', upper: 'Χ' },
    { name: 'Psi', lower: 'ψ', upper: 'Ψ' },
    { name: 'Omega', lower: 'ω', upper: 'Ω' }
  ];

  const mathSymbols = {
    subscripts: ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉', '₊', '₋', '₌', '₍', '₎'],
    superscripts: ['⁰', '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹', '⁺', '⁻', '⁼', '⁽', '⁾'],
    operators: ['×', '·', '÷', '±', '∞', '∝', '∑', '∏', '∫', '∂', '∇', '√']
  };

  // Comprehensive character mapping for subscript/superscript conversion
  const subscriptMap: { [key: string]: string } = {
    // Numbers
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    // Operators and punctuation
    '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
    // Lowercase letters (using actual Unicode subscripts where available)
    'a': 'ₐ', 'b': 'ᵦ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ₑ', 'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ', 
    'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ', 'p': 'ₚ', 'q': 'ᵩ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 
    'u': 'ᵤ', 'v': 'ᵥ', 'w': 'ᵨ', 'x': 'ₓ', 'y': 'ᵧ', 'z': 'ᵤ',
    // Uppercase letters (map to lowercase subscripts since Unicode has limited uppercase subscripts)
    'A': 'ₐ', 'B': 'ᵦ', 'C': 'ᶜ', 'D': 'ᵈ', 'E': 'ₑ', 'F': 'ᶠ', 'G': 'ᵍ', 'H': 'ₕ', 'I': 'ᵢ', 'J': 'ⱼ',
    'K': 'ₖ', 'L': 'ₗ', 'M': 'ₘ', 'N': 'ₙ', 'O': 'ₒ', 'P': 'ₚ', 'Q': 'ᵩ', 'R': 'ᵣ', 'S': 'ₛ', 'T': 'ₜ',
    'U': 'ᵤ', 'V': 'ᵥ', 'W': 'ᵨ', 'X': 'ₓ', 'Y': 'ᵧ', 'Z': 'ᵤ',
    // Special characters and punctuation
    '.': '·', ',': '‚', '!': '₍!₎', '?': '₍?₎', ':': '₍:₎', ';': '₍;₎', 
    '"': '₍"₎', "'": '₍'₎', '[': '₍[₎', ']': '₍]₎', '{': '₍{₎', '}': '₍}₎',
    '<': '₍<₎', '>': '₍>₎', '|': '₍|₎', '\\': '₍\\₎', '/': '₍/₎', '@': '₍@₎',
    '#': '₍#₎', '$': '₍$₎', '%': '₍%₎', '&': '₍&₎', '*': '₍*₎', '^': '₍^₎',
    '_': '₍_₎', '~': '₍~₎', '`': '₍`₎', ' ': ' '
  };
  
  const superscriptMap: { [key: string]: string } = {
    // Numbers
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    // Operators and punctuation  
    '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾', '*': '˟', '/': '╱', '.': '·', ',': '˒',
    // Lowercase letters (comprehensive Unicode superscripts)
    'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ', 'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ʰ', 'i': 'ⁱ', 'j': 'ʲ', 
    'k': 'ᵏ', 'l': 'ˡ', 'm': 'ᵐ', 'n': 'ⁿ', 'o': 'ᵒ', 'p': 'ᵖ', 'q': 'ᵠ', 'r': 'ʳ', 's': 'ˢ', 't': 'ᵗ', 
    'u': 'ᵘ', 'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ',
    // Uppercase letters (comprehensive Unicode superscripts)
    'A': 'ᴬ', 'B': 'ᴮ', 'C': 'ᶜ', 'D': 'ᴰ', 'E': 'ᴱ', 'F': 'ᶠ', 'G': 'ᴳ', 'H': 'ᴴ', 'I': 'ᴵ', 'J': 'ᴶ',
    'K': 'ᴷ', 'L': 'ᴸ', 'M': 'ᴹ', 'N': 'ᴺ', 'O': 'ᴼ', 'P': 'ᴾ', 'Q': 'ᵠ', 'R': 'ᴿ', 'S': 'ˢ', 'T': 'ᵀ',
    'U': 'ᵁ', 'V': 'ⱽ', 'W': 'ᵂ', 'X': 'ˣ', 'Y': 'ʸ', 'Z': 'ᶻ',
    // Special characters and punctuation
    '"': '⁽"⁾', "'": '⁽'⁾', '[': '⁽[⁾', ']': '⁽]⁾', '{': '⁽{⁾', '}': '⁽}⁾',
    '<': '⁽<⁾', '>': '⁽>⁾', '|': '⁽|⁾', '\\': '⁽\\⁾', '@': '⁽@⁾',
    '#': '⁽#⁾', '$': '⁽$⁾', '%': '⁽%⁾', '&': '⁽&⁾', '_': '⁽_⁾', '~': '⁽~⁾',
    '`': '⁽`⁾', '!': '⁽!⁾', '?': '⁽?⁾', ':': '⁽:⁾', ';': '⁽;⁾', ' ': ' '
  };

  // Fallback function for characters without Unicode equivalents
  const getSubscriptFallback = (char: string): string => {
    return String.fromCharCode(0x2080 + char.charCodeAt(0) - 48) || char + '₍ₛᵤᵦ₎';
  };

  const getSuperscriptFallback = (char: string): string => {
    return String.fromCharCode(0x2070 + char.charCodeAt(0) - 48) || char + '⁽ˢᵘᵖ⁾';
  };

  useEffect(() => {
    fetchConstants();
  }, []);

  // Keyboard shortcut handlers
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+, for subscript mode
      if (e.ctrlKey && e.key === ',') {
        e.preventDefault();
        if (activeField) {
          if (activeField === 'symbol') {
            setSymbolInputMode(prev => prev === 'subscript' ? 'normal' : 'subscript');
          } else if (activeField === 'unit') {
            setUnitInputMode(prev => prev === 'subscript' ? 'normal' : 'subscript');
          }
        }
      }
      // Ctrl+. for superscript mode
      else if (e.ctrlKey && e.key === '.') {
        e.preventDefault();
        if (activeField) {
          if (activeField === 'symbol') {
            setSymbolInputMode(prev => prev === 'superscript' ? 'normal' : 'superscript');
          } else if (activeField === 'unit') {
            setUnitInputMode(prev => prev === 'superscript' ? 'normal' : 'superscript');
          }
        }
      }
      // Ctrl+Space for command menu
      else if (e.ctrlKey && e.key === ' ') {
        e.preventDefault();
        setShowCommandMenu(true);
      }
      // Escape to close command menu
      else if (e.key === 'Escape') {
        setShowCommandMenu(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [activeField]);

  const fetchConstants = async () => {
    try {
      setLoading(true);
      const data = await getConstants();
      setConstants(data);
      setError(null);
    } catch (err) {
      setError('Failed to load constants');
      console.error('Error fetching constants:', err);
    } finally {
      setLoading(false);
    }
  };

  // Get unique categories
  const categories = useMemo(() => {
    const uniqueCategories = [...new Set(constants.map(c => c.category))];
    return ['all', ...uniqueCategories.sort()];
  }, [constants]);

  // Filter and sort constants
  const filteredAndSortedConstants = useMemo(() => {
    let filtered = constants;

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(c => c.category === selectedCategory);
    }

    // Search filter
    if (searchTerm) {
      const lowerSearch = searchTerm.toLowerCase();
      filtered = filtered.filter(
        c =>
          c.symbol.toLowerCase().includes(lowerSearch) ||
          c.name.toLowerCase().includes(lowerSearch) ||
          (c.description && c.description.toLowerCase().includes(lowerSearch))
      );
    }

    // Sort
    return [...filtered].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [constants, selectedCategory, searchTerm, sortConfig]);

  const handleSort = (key: keyof SystemConstant) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const formatScientificNotation = (value: number): string => {
    const absValue = Math.abs(value);
    if (absValue === 0) return '0';
    if (absValue >= 1e6 || absValue <= 1e-4) {
      return value.toExponential(4);
    }
    return value.toPrecision(6);
  };

  const resetForm = () => {
    setFormData({
      symbol: '',
      name: '',
      value: 0,
      unit: '',
      description: '',
      category: ''
    });
    setShowSymbolHelper(false);
    setShowUnitHelper(false);
    setShowCommandMenu(false);
    setSymbolInputMode('normal');
    setUnitInputMode('normal');
    setActiveField(null);
  };

  const convertText = (text: string, mode: 'normal' | 'subscript' | 'superscript'): string => {
    if (mode === 'normal') return text;
    
    if (mode === 'subscript') {
      return text.split('').map(char => {
        // First try the direct mapping
        if (subscriptMap[char]) return subscriptMap[char];
        // For any character not in the map, try to convert it
        return char; // Keep original character if no conversion available
      }).join('');
    } else {
      return text.split('').map(char => {
        // First try the direct mapping
        if (superscriptMap[char]) return superscriptMap[char];
        // For any character not in the map, try to convert it
        return char; // Keep original character if no conversion available
      }).join('');
    }
  };

  const handleSymbolInput = (newValue: string) => {
    if (symbolInputMode === 'normal') {
      setFormData({ ...formData, symbol: newValue });
    } else {
      // Find the new characters added and convert them
      const oldValue = formData.symbol;
      if (newValue.length > oldValue.length) {
        const newChars = newValue.slice(oldValue.length);
        const converted = convertText(newChars, symbolInputMode);
        setFormData({ ...formData, symbol: oldValue + converted });
      } else {
        setFormData({ ...formData, symbol: newValue });
      }
    }
  };

  const handleUnitInput = (newValue: string) => {
    if (unitInputMode === 'normal') {
      setFormData({ ...formData, unit: newValue });
    } else {
      // Find the new characters added and convert them
      const oldValue = formData.unit;
      if (newValue.length > oldValue.length) {
        const newChars = newValue.slice(oldValue.length);
        const converted = convertText(newChars, unitInputMode);
        setFormData({ ...formData, unit: oldValue + converted });
      } else {
        setFormData({ ...formData, unit: newValue });
      }
    }
  };

  const insertSymbolChar = (char: string) => {
    setFormData({ ...formData, symbol: formData.symbol + char });
  };

  const insertUnitChar = (char: string) => {
    setFormData({ ...formData, unit: formData.unit + char });
  };

  const handleAddConstant = () => {
    resetForm();
    setShowAddModal(true);
  };

  const handleEditConstant = (constant: SystemConstant) => {
    setFormData({
      symbol: constant.symbol,
      name: constant.name,
      value: constant.value,
      unit: constant.unit || '',
      description: constant.description || '',
      category: constant.category
    });
    setEditingConstant(constant);
    setShowEditModal(true);
  };

  const handleDeleteConstant = (constant: SystemConstant) => {
    setDeletingConstant(constant);
    setShowDeleteModal(true);
  };

  const submitAdd = async () => {
    try {
      setSaving(true);
      await createConstant({
        symbol: formData.symbol,
        name: formData.name,
        value: formData.value,
        unit: formData.unit || undefined,
        description: formData.description || undefined,
        category: formData.category
      });
      setShowAddModal(false);
      resetForm();
      fetchConstants();
    } catch (err) {
      setError('Failed to create constant');
      console.error('Error creating constant:', err);
    } finally {
      setSaving(false);
    }
  };

  const submitEdit = async () => {
    if (!editingConstant) return;
    
    try {
      setSaving(true);
      await updateConstant(editingConstant.id, {
        name: formData.name,
        value: formData.value,
        unit: formData.unit || undefined,
        description: formData.description || undefined
      });
      setShowEditModal(false);
      setEditingConstant(null);
      resetForm();
      fetchConstants();
    } catch (err) {
      setError('Failed to update constant');
      console.error('Error updating constant:', err);
    } finally {
      setSaving(false);
    }
  };

  const submitDelete = async () => {
    if (!deletingConstant) return;
    
    try {
      setSaving(true);
      await deleteConstant(deletingConstant.id);
      setShowDeleteModal(false);
      setDeletingConstant(null);
      fetchConstants();
    } catch (err) {
      setError('Failed to delete constant');
      console.error('Error deleting constant:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-red-600">
          <h3 className="text-lg font-semibold mb-2">Error</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">System Constants</h2>
          <button
            onClick={handleAddConstant}
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Add New Constant
          </button>
        </div>
        
        {/* Filters */}
        <div className="mb-6 space-y-4 sm:space-y-0 sm:flex sm:gap-4">
          <div className="flex-1">
            <label htmlFor="search" className="sr-only">
              Search constants
            </label>
            <input
              type="text"
              id="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by symbol, name, or description..."
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div className="sm:w-48">
            <label htmlFor="category" className="sr-only">
              Filter by category
            </label>
            <select
              id="category"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category === 'all' ? 'All Categories' : category}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('symbol')}
                >
                  <div className="flex items-center">
                    Symbol
                    {sortConfig.key === 'symbol' && (
                      <svg
                        className={`ml-2 h-4 w-4 transform ${
                          sortConfig.direction === 'desc' ? 'rotate-180' : ''
                        }`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                      </svg>
                    )}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('name')}
                >
                  <div className="flex items-center">
                    Name
                    {sortConfig.key === 'name' && (
                      <svg
                        className={`ml-2 h-4 w-4 transform ${
                          sortConfig.direction === 'desc' ? 'rotate-180' : ''
                        }`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                      </svg>
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Unit
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('category')}
                >
                  <div className="flex items-center">
                    Category
                    {sortConfig.key === 'category' && (
                      <svg
                        className={`ml-2 h-4 w-4 transform ${
                          sortConfig.direction === 'desc' ? 'rotate-180' : ''
                        }`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                      </svg>
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedConstants.map((constant) => (
                <tr key={constant.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {formatUnitWithSubscriptsJSX(constant.symbol)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {constant.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
                    {formatScientificNotation(constant.value)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {constant.unit ? formatUnitWithSubscriptsJSX(constant.unit) : '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                      {constant.category}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {constant.description || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex space-x-2">
                      {constant.is_editable && (
                        <>
                          <button
                            onClick={() => handleEditConstant(constant)}
                            className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteConstant(constant)}
                            className="text-red-600 hover:text-red-900 text-sm font-medium"
                          >
                            Delete
                          </button>
                        </>
                      )}
                      {!constant.is_editable && (
                        <span className="text-gray-400 text-sm">System defined</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredAndSortedConstants.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No constants found matching your criteria.
            </div>
          )}
        </div>
      </div>

      {/* Add Constant Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Constant</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Symbol</label>
                <div className="relative">
                  <input
                    type="text"
                    value={formData.symbol}
                    onChange={(e) => handleSymbolInput(e.target.value)}
                    onFocus={() => setActiveField('symbol')}
                    onBlur={() => setActiveField(null)}
                    className={`mt-1 block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                      symbolInputMode === 'subscript' ? 'bg-blue-50 border-blue-300' : 
                      symbolInputMode === 'superscript' ? 'bg-green-50 border-green-300' : ''
                    }`}
                    placeholder={
                      symbolInputMode === 'subscript' ? 'Type normally - will convert to subscript (Ctrl+, to toggle)' :
                      symbolInputMode === 'superscript' ? 'Type normally - will convert to superscript (Ctrl+. to toggle)' :
                      'Enter symbol (Ctrl+, for subscript, Ctrl+. for superscript)'
                    }
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowSymbolHelper(!showSymbolHelper)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                  >
                    <span className="text-sm">αβ</span>
                  </button>
                </div>
                {showSymbolHelper && (
                  <div className="mt-2 p-3 border border-gray-200 rounded-md bg-gray-50 max-h-48 overflow-y-auto">
                    <div className="space-y-3">
                      <div>
                        <h4 className="text-xs font-medium text-gray-700 mb-2">Greek Letters</h4>
                        <div className="grid grid-cols-6 gap-1">
                          {greekLetters.map((letter) => (
                            <div key={letter.name} className="space-x-1">
                              <button
                                type="button"
                                onClick={() => insertSymbolChar(letter.lower)}
                                className="text-sm px-1 py-1 hover:bg-gray-200 rounded"
                                title={`${letter.name} (lowercase)`}
                              >
                                {letter.lower}
                              </button>
                              <button
                                type="button"
                                onClick={() => insertSymbolChar(letter.upper)}
                                className="text-sm px-1 py-1 hover:bg-gray-200 rounded"
                                title={`${letter.name} (uppercase)`}
                              >
                                {letter.upper}
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="text-xs font-medium text-gray-700 mb-2">Math Symbols</h4>
                        <div className="flex flex-wrap gap-1">
                          {mathSymbols.operators.map((char) => (
                            <button
                              key={char}
                              type="button"
                              onClick={() => insertSymbolChar(char)}
                              className="text-sm px-2 py-1 hover:bg-gray-200 rounded"
                            >
                              {char}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Value</label>
                <input
                  type="number"
                  step="any"
                  value={formData.value}
                  onChange={(e) => setFormData({ ...formData, value: parseFloat(e.target.value) || 0 })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Unit</label>
                <div className="relative">
                  <input
                    type="text"
                    value={formData.unit}
                    onChange={(e) => handleUnitInput(e.target.value)}
                    onFocus={() => setActiveField('unit')}
                    onBlur={() => setActiveField(null)}
                    className={`mt-1 block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                      unitInputMode === 'subscript' ? 'bg-blue-50 border-blue-300' : 
                      unitInputMode === 'superscript' ? 'bg-green-50 border-green-300' : ''
                    }`}
                    placeholder={
                      unitInputMode === 'subscript' ? 'Type normally - will convert to subscript (Ctrl+, to toggle)' :
                      unitInputMode === 'superscript' ? 'Type normally - will convert to superscript (Ctrl+. to toggle)' :
                      'Enter unit (Ctrl+, for subscript, Ctrl+. for superscript)'
                    }
                  />
                  <button
                    type="button"
                    onClick={() => setShowUnitHelper(!showUnitHelper)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                  >
                    <span className="text-sm">×₂</span>
                  </button>
                </div>
                {showUnitHelper && (
                  <div className="mt-2 p-3 border border-gray-200 rounded-md bg-gray-50 max-h-48 overflow-y-auto">
                    <div className="space-y-3">
                      <div>
                        <h4 className="text-xs font-medium text-gray-700 mb-2">Common Unit Prefixes</h4>
                        <div className="flex flex-wrap gap-1">
                          {['m', 'k', 'M', 'G', 'T', 'μ', 'n', 'p'].map((prefix) => (
                            <button
                              key={prefix}
                              type="button"
                              onClick={() => insertUnitChar(prefix)}
                              className="text-sm px-2 py-1 hover:bg-gray-200 rounded"
                            >
                              {prefix}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="text-xs font-medium text-gray-700 mb-2">Math Symbols</h4>
                        <div className="flex flex-wrap gap-1">
                          {['×', '·', '/', '⁻¹', '²', '³'].map((char) => (
                            <button
                              key={char}
                              type="button"
                              onClick={() => insertUnitChar(char)}
                              className="text-sm px-2 py-1 hover:bg-gray-200 rounded"
                            >
                              {char}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Category</label>
                <input
                  type="text"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={submitAdd}
                disabled={saving || !formData.symbol || !formData.name || !formData.category}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Constant Modal */}
      {showEditModal && editingConstant && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Edit Constant: {editingConstant.symbol}</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Value</label>
                <input
                  type="number"
                  step="any"
                  value={formData.value}
                  onChange={(e) => setFormData({ ...formData, value: parseFloat(e.target.value) || 0 })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Unit</label>
                <div className="relative">
                  <input
                    type="text"
                    value={formData.unit}
                    onChange={(e) => handleUnitInput(e.target.value)}
                    onFocus={() => setActiveField('unit')}
                    onBlur={() => setActiveField(null)}
                    className={`mt-1 block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                      unitInputMode === 'subscript' ? 'bg-blue-50 border-blue-300' : 
                      unitInputMode === 'superscript' ? 'bg-green-50 border-green-300' : ''
                    }`}
                    placeholder={
                      unitInputMode === 'subscript' ? 'Type normally - will convert to subscript (Ctrl+, to toggle)' :
                      unitInputMode === 'superscript' ? 'Type normally - will convert to superscript (Ctrl+. to toggle)' :
                      'Enter unit (Ctrl+, for subscript, Ctrl+. for superscript)'
                    }
                  />
                  <button
                    type="button"
                    onClick={() => setShowUnitHelper(!showUnitHelper)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                  >
                    <span className="text-sm">×₂</span>
                  </button>
                </div>
                {showUnitHelper && (
                  <div className="mt-2 p-3 border border-gray-200 rounded-md bg-gray-50 max-h-48 overflow-y-auto">
                    <div className="space-y-3">
                      <div>
                        <h4 className="text-xs font-medium text-gray-700 mb-2">Common Unit Prefixes</h4>
                        <div className="flex flex-wrap gap-1">
                          {['m', 'k', 'M', 'G', 'T', 'μ', 'n', 'p'].map((prefix) => (
                            <button
                              key={prefix}
                              type="button"
                              onClick={() => insertUnitChar(prefix)}
                              className="text-sm px-2 py-1 hover:bg-gray-200 rounded"
                            >
                              {prefix}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="text-xs font-medium text-gray-700 mb-2">Math Symbols</h4>
                        <div className="flex flex-wrap gap-1">
                          {['×', '·', '/', '⁻¹', '²', '³'].map((char) => (
                            <button
                              key={char}
                              type="button"
                              onClick={() => insertUnitChar(char)}
                              className="text-sm px-2 py-1 hover:bg-gray-200 rounded"
                            >
                              {char}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={submitEdit}
                disabled={saving || !formData.name}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Updating...' : 'Update'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deletingConstant && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Delete Constant</h3>
            <p className="text-sm text-gray-500 mb-6">
              Are you sure you want to delete the constant <strong>{deletingConstant.symbol}</strong> ({deletingConstant.name})? 
              This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={submitDelete}
                disabled={saving}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Command Menu */}
      {showCommandMenu && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Keyboard Shortcuts</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">Toggle Subscript Mode</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">Ctrl + ,</kbd>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">Toggle Superscript Mode</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">Ctrl + .</kbd>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">Open Command Menu</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">Ctrl + Space</kbd>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">Close Menu/Panel</span>
                <kbd className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">Escape</kbd>
              </div>
            </div>
            <div className="mt-6 text-xs text-gray-500">
              <p><strong>Current Mode:</strong></p>
              <p>Symbol: <span className={`px-2 py-1 rounded text-xs ${
                symbolInputMode === 'subscript' ? 'bg-blue-100 text-blue-800' :
                symbolInputMode === 'superscript' ? 'bg-green-100 text-green-800' :
                'bg-gray-100 text-gray-800'
              }`}>{symbolInputMode}</span></p>
              <p>Unit: <span className={`px-2 py-1 rounded text-xs ${
                unitInputMode === 'subscript' ? 'bg-blue-100 text-blue-800' :
                unitInputMode === 'superscript' ? 'bg-green-100 text-green-800' :
                'bg-gray-100 text-gray-800'
              }`}>{unitInputMode}</span></p>
            </div>
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowCommandMenu(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Constants;