import React from 'react';

/**
 * Formats units with proper subscripts and superscripts using JSX
 * Returns React elements with <sub> and <sup> tags
 */
export function formatUnitWithSubscriptsJSX(unit: string | null | undefined): React.ReactNode {
  if (!unit) return '';
  
  // Parse the unit string and convert to JSX with proper subscripts/superscripts
  const parts: React.ReactNode[] = [];
  let remaining = unit;
  
  // Special replacements for Greek letters
  const greekReplacements: Record<string, string> = {
    'sigma': 'σ',
    'phi': 'φ',
    'rho': 'ρ',
    'mu': 'μ',
    'epsilon': 'ε',
  };
  
  // Replace Greek letters first
  for (const [pattern, replacement] of Object.entries(greekReplacements)) {
    remaining = remaining.replace(pattern, replacement);
  }
  
  // Handle special cases with full word subscripts
  const specialPatterns = [
    { pattern: /R_specific_air/g, replacement: () => <>R<sub>specific,air</sub></> },
    { pattern: /T_stp|T_STP/g, replacement: () => <>T<sub>STP</sub></> },
    { pattern: /P_stp|P_STP/g, replacement: () => <>P<sub>STP</sub></> },
    { pattern: /rho_water/g, replacement: () => <>ρ<sub>water</sub></> },
    { pattern: /mu_water/g, replacement: () => <>μ<sub>water</sub></> },
    { pattern: /mu_0/g, replacement: () => <>μ<sub>0</sub></> },
    { pattern: /epsilon_0/g, replacement: () => <>ε<sub>0</sub></> },
    { pattern: /h_planck/g, replacement: () => <>h</> },
    { pattern: /k_B/g, replacement: () => <>k<sub>B</sub></> },
    { pattern: /N_A/g, replacement: () => <>N<sub>A</sub></> },
    { pattern: /T_0/g, replacement: () => <>T<sub>0</sub></> },
  ];
  
  // Check if the entire string matches a special pattern
  for (const { pattern, replacement } of specialPatterns) {
    if (pattern.test(unit)) {
      return replacement();
    }
  }
  
  // Handle general patterns with regex
  let currentIndex = 0;
  
  // Pattern for underscore subscripts (letters or numbers)
  const subscriptPattern = /_([A-Za-z0-9]+)/g;
  let match;
  
  while ((match = subscriptPattern.exec(remaining)) !== null) {
    // Add text before the match
    if (match.index > currentIndex) {
      parts.push(remaining.substring(currentIndex, match.index));
    }
    
    // Add the subscript
    parts.push(<sub key={`sub-${match.index}`}>{match[1]}</sub>);
    
    currentIndex = match.index + match[0].length;
  }
  
  // Add any remaining text
  if (currentIndex < remaining.length) {
    let finalPart = remaining.substring(currentIndex);
    
    // Handle superscripts in the remaining text
    finalPart = finalPart.replace(/\^(-?\d+)/g, (match, exp) => {
      const supChars: Record<string, string> = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '-': '⁻',
      };
      return exp.split('').map((c: string) => supChars[c] || c).join('');
    });
    
    // Handle common superscript patterns
    finalPart = finalPart
      .replace(/([a-zA-Z])2\b/g, '$1²')
      .replace(/([a-zA-Z])3\b/g, '$1³')
      .replace(/m²/g, 'm²')
      .replace(/m³/g, 'm³');
    
    // Handle common molecule patterns
    finalPart = finalPart
      .replace(/H2O/g, 'H₂O')
      .replace(/CO2/g, 'CO₂')
      .replace(/SO2/g, 'SO₂')
      .replace(/NO2/g, 'NO₂')
      .replace(/O2/g, 'O₂')
      .replace(/N2/g, 'N₂')
      .replace(/H2/g, 'H₂');
    
    parts.push(finalPart);
  }
  
  // If no parts were created, return the original string with basic replacements
  if (parts.length === 0) {
    return remaining
      .replace(/\^(-?\d+)/g, (match, exp) => {
        const supChars: Record<string, string> = {
          '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
          '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
          '-': '⁻',
        };
        return exp.split('').map((c: string) => supChars[c] || c).join('');
      })
      .replace(/([a-zA-Z])2\b/g, '$1²')
      .replace(/([a-zA-Z])3\b/g, '$1³');
  }
  
  return <>{parts}</>;
}