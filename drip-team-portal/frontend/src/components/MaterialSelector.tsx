import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';

interface Material {
  id: number;
  name: string;
  category: string;
  subcategory?: string;
  uns_number?: string;
  astm_grade?: string;
  mp_id?: string;
  data_source?: string;
  properties?: MaterialPropertyValue[];
}

interface MaterialPropertyValue {
  property_name: string;
  value?: number;
  value_min?: number;
  value_max?: number;
  unit: string;
  temperature?: number;
}

interface MPMaterial {
  mp_id: string;
  formula: string;
  common_name?: string;
  density?: number;
  formation_energy?: number;
  stability: boolean;
  band_gap?: number;
  crystal_system?: string;
  elastic_moduli?: {
    bulk_modulus: number;
    shear_modulus: number;
    youngs_modulus: number;
    poisson_ratio: number;
  };
  acoustic_properties?: {
    longitudinal_velocity: number;
    longitudinal_impedance: number;
    impedance_contrast_with_air: number;
  };
  has_standard?: boolean;
  data_source?: string;
  mechanical_properties?: {
    yield_strength?: number;
    ultimate_tensile_strength?: number;
    elongation?: number;
    brinell_hardness?: number;
  };
  thermal_properties?: {
    melting_point?: number;
    thermal_conductivity?: number;
    specific_heat?: number;
  };
  applications?: string[];
  standards?: string[];
}

interface MaterialSelectorProps {
  componentId: string;
  currentMaterialId?: number;
  onMaterialSet?: (material: Material, propertiesAdded: string[]) => void;
}

const MaterialSelector: React.FC<MaterialSelectorProps> = ({ componentId, currentMaterialId, onMaterialSet }) => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchMode, setSearchMode] = useState<'local' | 'materials-project'>('local');
  const [mpSearchResults, setMpSearchResults] = useState<MPMaterial[]>([]);
  const [isSearchingMP, setIsSearchingMP] = useState(false);
  const [mpSearchType, setMpSearchType] = useState<'formula' | 'alloy'>('alloy');

  // Debug logging
  console.log('MaterialSelector Debug:', {
    componentId,
    isOpen,
    searchMode,
    mpSearchType,
    searchTerm,
    mpSearchResults: mpSearchResults.length,
    timestamp: new Date().toISOString()
  });

  const { data: materials, isLoading } = useQuery<Material[]>({
    queryKey: ['materials', selectedCategory, searchTerm],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (selectedCategory) params.append('category', selectedCategory);
      if (searchTerm) params.append('search', searchTerm);
      
      const response = await api.get(`/api/v1/materials?${params}`);
      return response.data;
    },
    enabled: isOpen && searchMode === 'local',
  });

  const { data: componentMaterials } = useQuery({
    queryKey: ['component-materials', componentId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/components/${componentId}/materials`);
      return response.data;
    },
  });

  // Materials Project search
  useEffect(() => {
    if (searchMode === 'materials-project' && searchTerm.length > 1) {
      const delayDebounceFn = setTimeout(() => {
        searchMaterialsProject();
      }, 500);

      return () => clearTimeout(delayDebounceFn);
    } else {
      setMpSearchResults([]);
    }
  }, [searchTerm, searchMode, mpSearchType]);

  const searchMaterialsProject = async () => {
    console.log('Starting Materials Project search:', { searchTerm, mpSearchType });
    setIsSearchingMP(true);
    try {
      const searchRequest = {
        query_type: mpSearchType === 'alloy' ? 'alloy_system' : 'elements',
        alloy_system: mpSearchType === 'alloy' ? searchTerm : undefined,
        elements_include: mpSearchType === 'formula' ? [searchTerm] : undefined,
        limit: 20,
      };

      console.log('Sending MP search request:', searchRequest);
      const response = await api.post('/api/v1/materials-project/search', searchRequest);
      console.log('MP search results:', response.data);
      setMpSearchResults(response.data);
    } catch (error) {
      console.error('Error searching Materials Project:', error);
      setMpSearchResults([]);
    } finally {
      setIsSearchingMP(false);
    }
  };

  const setMaterial = useMutation({
    mutationFn: async (materialId: number) => {
      console.log('🔄 Starting material change mutation:', { componentId, materialId });
      const response = await api.put(`/api/v1/components/${componentId}/material?material_id=${materialId}`);
      console.log('✅ Material change response:', response.data);
      return response.data;
    },
    onSuccess: (data) => {
      console.log('🎉 Material change successful, invalidating queries...', data);
      
      // Add small delay to ensure backend commit is complete
      setTimeout(() => {
        console.log('🔄 Invalidating component-properties query...');
        queryClient.invalidateQueries({ queryKey: ['component-properties', componentId] });
        console.log('🔄 Invalidating component-materials query...');
        queryClient.invalidateQueries({ queryKey: ['component-materials', componentId] });
      }, 100);
      
      const selectedMaterial = materials?.find(m => m.id === data.changes?.new_material_id);
      console.log('📋 Selected material:', selectedMaterial);
      
      if (selectedMaterial && onMaterialSet) {
        console.log('📞 Calling onMaterialSet callback...');
        onMaterialSet(selectedMaterial, data.changes?.properties_added || []);
      }
      
      setIsOpen(false);
    },
    onError: (error) => {
      console.error('❌ Material change error:', error);
    },
  });

  const importAndSetMaterial = useMutation({
    mutationFn: async (mpMaterial: MPMaterial) => {
      try {
        // First import the material from Materials Project
        const importResponse = await api.post('/api/v1/materials-project/import', {
          mp_id: mpMaterial.mp_id,
          material_name: mpMaterial.common_name || mpMaterial.formula,
          category: determineCategory(mpMaterial.formula),
        });

        // Then set it as the component's material
        const setResponse = await api.put(`/api/v1/components/${componentId}/material?material_id=${importResponse.data.material_id}`);

        return {
          ...setResponse.data,
          imported_material: importResponse.data,
        };
      } catch (error: any) {
        console.error('Import error:', error.response?.data || error);
        throw error;
      }
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      queryClient.invalidateQueries({ queryKey: ['component-properties', componentId] });
      queryClient.invalidateQueries({ queryKey: ['component-materials', componentId] });
      
      setIsOpen(false);
    },
    onError: (error: any) => {
      console.error('Import failed:', error.response?.data || error);
    },
  });

  const removeMaterial = useMutation({
    mutationFn: async () => {
      const currentMaterialId = componentMaterials?.[0]?.material.id;
      if (!currentMaterialId) return;
      
      const response = await api.delete(`/api/v1/components/${componentId}/material/${currentMaterialId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['component-properties', componentId] });
      queryClient.invalidateQueries({ queryKey: ['component-materials', componentId] });
    },
  });

  const currentMaterial = componentMaterials?.[0]?.material;

  // Expanded categories to cover all material types
  const categories = [
    'Metal',
    'Ceramic', 
    'Polymer',
    'Composite',
    'Semiconductor',
    'Glass',
    'Biomaterial',
    'Nanomaterial',
    'Refractory',
    'Superalloy',
  ];

  const getCategoryIcon = (category: string) => {
    // Removed emojis for professional appearance
    return '';
  };

  const determineCategory = (formula: string): string => {
    // Simple heuristic to determine category from formula
    if (formula.includes('Si') && (formula.includes('O') || formula.includes('N'))) return 'Ceramic';
    if (formula.includes('C') && formula.length > 5) return 'Polymer';
    if (formula.includes('Al') || formula.includes('Fe') || formula.includes('Ti') || formula.includes('Cu')) return 'Metal';
    if (formula.includes('Si') && !formula.includes('O')) return 'Semiconductor';
    return 'Other';
  };

  const formatMPProperties = (material: MPMaterial): string[] => {
    const props = [];
    if (material.density != null) props.push(`Density: ${material.density.toFixed(2)} g/cm³`);
    if (material.elastic_moduli?.youngs_modulus) {
      props.push(`E: ${material.elastic_moduli.youngs_modulus?.toFixed(0) || 'N/A'} GPa`);
    }
    if (material.mechanical_properties?.yield_strength) {
      props.push(`σy: ${material.mechanical_properties.yield_strength} MPa`);
    }
    if (material.mechanical_properties?.ultimate_tensile_strength) {
      props.push(`σUTS: ${material.mechanical_properties.ultimate_tensile_strength} MPa`);
    }
    if (material.acoustic_properties?.longitudinal_impedance) {
      props.push(`Z: ${material.acoustic_properties.longitudinal_impedance ? (material.acoustic_properties.longitudinal_impedance / 1e6).toFixed(1) : 'N/A'} MRayl`);
    }
    if (material.band_gap !== undefined) {
      props.push(`Band Gap: ${material.band_gap?.toFixed(2) || 'N/A'} eV`);
    }
    if (material.thermal_properties?.melting_point) {
      props.push(`Tm: ${material.thermal_properties.melting_point}°C`);
    }
    return props;
  };

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Material</h3>
        {currentMaterial && (
          <span className="text-xs text-gray-500">
            Properties will be inherited from material database
          </span>
        )}
      </div>
      
      <div className="mt-2">
        {currentMaterial ? (
          <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900">{currentMaterial.name}</span>
              </div>
              <div className="mt-1 text-xs text-gray-600">
                {currentMaterial.astm_grade && (
                  <span className="mr-2">ASTM: {currentMaterial.astm_grade}</span>
                )}
                {currentMaterial.uns_number && (
                  <span className="mr-2">UNS: {currentMaterial.uns_number}</span>
                )}
                {currentMaterial.mp_id && (
                  <span className="mr-2">MP: {currentMaterial.mp_id}</span>
                )}
                {currentMaterial.data_source && (
                  <span>Source: {currentMaterial.data_source}</span>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setIsOpen(true)}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Change
              </button>
              <button
                onClick={() => removeMaterial.mutate()}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Remove
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setIsOpen(true)}
            className="w-full p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-gray-400 transition-colors"
          >
            <div className="flex items-center justify-center gap-2 text-gray-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Select Material</span>
            </div>
          </button>
        )}
        
        {/* Material properties preview */}
        {currentMaterial && componentMaterials?.[0]?.inherited_properties && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
            <p className="text-xs font-medium text-gray-700 mb-2">
              Inherited Material Properties:
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {componentMaterials[0].inherited_properties.slice(0, 6).map((prop: MaterialPropertyValue) => (
                <div key={prop.property_name} className="flex justify-between">
                  <span className="text-gray-600">{prop.property_name}:</span>
                  <span className="font-medium">
                    {prop.value !== undefined ? prop.value : `${prop.value_min}-${prop.value_max}`} {prop.unit}
                  </span>
                </div>
              ))}
            </div>
            {componentMaterials[0].inherited_properties.length > 6 && (
              <p className="text-xs text-gray-500 mt-2">
                +{componentMaterials[0].inherited_properties.length - 6} more properties
              </p>
            )}
          </div>
        )}
      </div>

      {/* Material Selection Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[85vh] overflow-hidden">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Select Material</h2>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              {/* Search mode toggle */}
              <div className="mt-4 flex items-center gap-4 mb-3">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="searchMode"
                    value="local"
                    checked={searchMode === 'local'}
                    onChange={(e) => {
                      console.log('Search mode changing to:', e.target.value);
                      setSearchMode(e.target.value as 'local' | 'materials-project');
                    }}
                    className="mr-2"
                  />
                  <span className="text-sm">Local Database</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="searchMode"
                    value="materials-project"
                    checked={searchMode === 'materials-project'}
                    onChange={(e) => {
                      console.log('Search mode changing to:', e.target.value);
                      setSearchMode(e.target.value as 'local' | 'materials-project');
                    }}
                    className="mr-2"
                  />
                  <span className="text-sm">Materials Project</span>
                </label>
              </div>
              
              {/* Search and filters */}
              <div className="space-y-3">
                {searchMode === 'materials-project' && (
                  <div className="flex gap-2 mb-2">
                    <button
                      onClick={() => setMpSearchType('alloy')}
                      className={`px-3 py-1 rounded text-xs ${
                        mpSearchType === 'alloy' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      Engineering Alloys
                    </button>
                    <button
                      onClick={() => setMpSearchType('formula')}
                      className={`px-3 py-1 rounded text-xs ${
                        mpSearchType === 'formula' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      Chemical Formula
                    </button>
                  </div>
                )}
                
                <input
                  type="text"
                  placeholder={
                    searchMode === 'materials-project' 
                      ? (mpSearchType === 'alloy' ? "e.g., 6061, 316, brass, Ti-6Al-4V..." : "e.g., Al, Fe, TiO2, SiC...")
                      : "Search materials..."
                  }
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                
                {searchMode === 'local' && (
                  <div className="flex gap-2 flex-wrap">
                    <button
                      onClick={() => setSelectedCategory('')}
                      className={`px-3 py-1 rounded-full text-sm ${
                        selectedCategory === '' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      All
                    </button>
                    {categories.map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setSelectedCategory(cat)}
                        className={`px-3 py-1 rounded-full text-sm ${
                          selectedCategory === cat ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                )}
                
                {searchMode === 'materials-project' && (
                  <p className="text-xs text-gray-600">
                    Search Materials Project database for scientifically-validated material properties.
                    Properties will be automatically imported when you select a material.
                  </p>
                )}
              </div>
            </div>
            
            {/* Materials list */}
            <div className="overflow-y-auto max-h-[50vh]">
              {(isLoading || isSearchingMP) ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="divide-y">
                  {/* None option */}
                  {currentMaterial && searchMode === 'local' && (
                    <button
                      onClick={() => {
                        removeMaterial.mutate();
                        setIsOpen(false);
                      }}
                      className="w-full p-4 text-left hover:bg-gray-50 transition-colors border-b-2"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium text-gray-900">None (No Material)</h3>
                          <p className="text-sm text-gray-600 mt-1">
                            Remove material selection and auto-generated properties
                          </p>
                        </div>
                      </div>
                    </button>
                  )}
                  
                  {/* Local materials */}
                  {searchMode === 'local' && materials?.map((material) => (
                    <button
                      key={material.id}
                      onClick={() => {
                        console.log('🎯 Local material clicked:', material.name, 'ID:', material.id);
                        setMaterial.mutate(material.id);
                      }}
                      className="w-full p-4 text-left hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium text-gray-900">{material.name}</h3>
                          </div>
                          <div className="mt-1 text-sm text-gray-600">
                            {material.subcategory && <span className="mr-3">{material.subcategory}</span>}
                            {material.astm_grade && <span className="mr-3">ASTM: {material.astm_grade}</span>}
                            {material.uns_number && <span className="mr-3">UNS: {material.uns_number}</span>}
                            {material.data_source && <span>Source: {material.data_source}</span>}
                          </div>
                          {material.properties && material.properties.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-2">
                              {material.properties.slice(0, 4).map((prop) => (
                                <span key={prop.property_name} className="text-xs bg-gray-100 px-2 py-1 rounded">
                                  {prop.property_name}: {prop.value || `${prop.value_min}-${prop.value_max}`} {prop.unit}
                                </span>
                              ))}
                              {material.properties.length > 4 && (
                                <span className="text-xs text-gray-500">
                                  +{material.properties.length - 4} more
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        {material.id === currentMaterialId && (
                          <span className="text-blue-600">
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                  
                  {/* Materials Project results */}
                  {searchMode === 'materials-project' && mpSearchResults.map((material) => (
                    <button
                      key={material.mp_id}
                      onClick={() => importAndSetMaterial.mutate(material)}
                      disabled={importAndSetMaterial.isPending}
                      className="w-full p-4 text-left hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <div>
                              <h3 className="font-medium text-gray-900">
                                {material.common_name || material.formula}
                              </h3>
                              {material.common_name && (
                                <p className="text-sm text-gray-600">{material.formula}</p>
                              )}
                            </div>
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                              MP: {material.mp_id}
                            </span>
                            {material.stability && (
                              <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">
                                Stable
                              </span>
                            )}
                            {material.has_standard && (
                              <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                                Standards Data
                              </span>
                            )}
                            {material.data_source && (
                              <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                                {material.data_source}
                              </span>
                            )}
                            {/* Show property completeness */}
                            {(() => {
                              let propCount = 0;
                              if (material.density) propCount++;
                              if (material.elastic_moduli?.youngs_modulus) propCount++;
                              if (material.mechanical_properties?.yield_strength) propCount++;
                              if (material.acoustic_properties) propCount++;
                              if (material.thermal_properties?.melting_point) propCount++;
                              
                              if (propCount >= 4) {
                                return (
                                  <span className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
                                    Complete Data
                                  </span>
                                );
                              }
                              return null;
                            })()}
                          </div>
                          <div className="mt-1 text-sm text-gray-600">
                            {material.crystal_system && <span className="mr-3">Crystal: {material.crystal_system}</span>}
                            {material.formation_energy && (
                              <span>Formation Energy: {material.formation_energy?.toFixed(3) || 'N/A'} eV/atom</span>
                            )}
                          </div>
                          {material.standards && material.standards.length > 0 && (
                            <div className="mt-1 text-xs text-gray-500">
                              Standards: {material.standards.slice(0, 3).join(', ')}
                              {material.standards.length > 3 && ` +${material.standards.length - 3} more`}
                            </div>
                          )}
                          {material.applications && material.applications.length > 0 && (
                            <div className="mt-1 text-xs text-gray-500 italic">
                              Used for: {material.applications.slice(0, 2).join(', ')}
                              {material.applications.length > 2 && '...'}
                            </div>
                          )}
                          <div className="mt-2 flex flex-wrap gap-2">
                            {formatMPProperties(material).map((prop, idx) => (
                              <span key={idx} className="text-xs bg-gray-100 px-2 py-1 rounded">
                                {prop}
                              </span>
                            ))}
                          </div>
                        </div>
                        {importAndSetMaterial.isPending && (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        )}
                      </div>
                    </button>
                  ))}
                  
                  {searchMode === 'materials-project' && mpSearchResults.length === 0 && searchTerm.length > 1 && !isSearchingMP && (
                    <div className="p-8 text-center text-gray-500">
                      No materials found in Materials Project matching "{searchTerm}"
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MaterialSelector;