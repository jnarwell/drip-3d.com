/**
 * Formats units with proper subscripts and superscripts
 * Converts patterns like H_2O to H₂O, m^2 to m², etc.
 */
export function formatUnitWithSubscripts(unit: string | null | undefined): string {
  if (!unit) return '';
  
  // Subscript mappings for numbers
  const subscripts: Record<string, string> = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
  };
  
  // Subscript mappings for letters (limited Unicode support)
  const letterSubscripts: Record<string, string> = {
    'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ', 'k': 'ₖ', 'l': 'ₗ', 
    'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ', 'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 
    'u': 'ᵤ', 'v': 'ᵥ', 'x': 'ₓ',
    'A': 'ₐ', 'B': 'в', // Limited uppercase support
  };
  
  // Superscript mappings
  const superscripts: Record<string, string> = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    '-': '⁻', '+': '⁺', '(': '⁽', ')': '⁾',
  };
  
  let formatted = unit;
  
  // Special replacements for Greek letters and complete transformations
  const specialReplacements: Record<string, string> = {
    'rho_water': 'ρwater',
    'mu_water': 'μwater',
    'mu_0': 'μ₀',
    'epsilon_0': 'ε₀',
    'sigma': 'σ',
    'phi': 'φ',
  };
  
  // Apply special replacements first
  for (const [pattern, replacement] of Object.entries(specialReplacements)) {
    if (formatted === pattern) {
      formatted = replacement;
    }
  }
  
  // Handle single letter subscripts (e.g., N_A -> Nₐ, k_B -> kв)
  formatted = formatted.replace(/_([A-Za-z])(?![A-Za-z])/g, (match, letter) => {
    return letterSubscripts[letter] || `_${letter}`;
  });
  
  // Handle numeric subscripts (e.g., H_2O -> H₂O, T_0 -> T₀)
  formatted = formatted.replace(/_([0-9]+)/g, (match, digits) => {
    return digits.split('').map((d: string) => subscripts[d] || d).join('');
  });
  
  // For complex subscripts that can't be rendered cleanly with Unicode, simplify
  formatted = formatted
    .replace('R_specific_air', 'R (air)')
    .replace('T_stp', 'T_STP')
    .replace('P_stp', 'P_STP')
    .replace('h_planck', 'h');
  
  // Handle superscripts for exponents (e.g., m^2 -> m², m^-1 -> m⁻¹)
  formatted = formatted.replace(/\^([-+]?[0-9]+)/g, (match, exp) => {
    return exp.split('').map((c: string) => superscripts[c] || c).join('');
  });
  
  // Handle common patterns
  formatted = formatted
    // Convert s^2 patterns (without caret) to superscripts
    .replace(/([a-zA-Z])2\b/g, '$1²')
    .replace(/([a-zA-Z])3\b/g, '$1³')
    // Convert H2O patterns to subscripts
    .replace(/H2O/g, 'H₂O')
    .replace(/CO2/g, 'CO₂')
    .replace(/SO2/g, 'SO₂')
    .replace(/NO2/g, 'NO₂')
    .replace(/O2/g, 'O₂')
    .replace(/N2/g, 'N₂')
    .replace(/H2/g, 'H₂')
    // Handle inH2O -> inH₂O
    .replace(/H2O/g, 'H₂O')
    .replace(/inH₂O/g, 'inH₂O');
  
  return formatted;
}

/**
 * Formats a value with its unit, applying subscript/superscript formatting
 */
export function formatValueWithFormattedUnit(
  value: number | string,
  unit: string | null | undefined,
  decimals: number = 2
): string {
  const formattedUnit = formatUnitWithSubscripts(unit);
  const formattedValue = typeof value === 'number' ? value.toFixed(decimals) : value;
  return formattedUnit ? `${formattedValue} ${formattedUnit}` : formattedValue;
}