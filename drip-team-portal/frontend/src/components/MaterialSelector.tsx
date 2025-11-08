import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';

interface Material {
  id: number;
  name: string;
  category: string;
  subcategory?: string;
  uns_number?: string;
  astm_grade?: string;
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

  const { data: materials, isLoading } = useQuery<Material[]>({
    queryKey: ['materials', selectedCategory, searchTerm],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (selectedCategory) params.append('category', selectedCategory);
      if (searchTerm) params.append('search', searchTerm);
      
      const response = await api.get(`/api/v1/materials?${params}`);
      return response.data;
    },
    enabled: isOpen,
  });

  const { data: componentMaterials } = useQuery({
    queryKey: ['component-materials', componentId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/components/${componentId}/materials`);
      return response.data;
    },
  });

  const setMaterial = useMutation({
    mutationFn: async (materialId: number) => {
      const response = await api.post(`/api/v1/components/${componentId}/material`, {
        material_id: materialId,
      });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['component-properties', componentId] });
      queryClient.invalidateQueries({ queryKey: ['component-materials', componentId] });
      
      const selectedMaterial = materials?.find(m => m.id === data.material_id);
      if (selectedMaterial && onMaterialSet) {
        onMaterialSet(selectedMaterial, data.properties_added);
      }
      
      setIsOpen(false);
    },
  });

  const removeMaterial = useMutation({
    mutationFn: async () => {
      // First get the current material to know which one to remove
      const currentMaterialId = componentMaterials?.[0]?.material.id;
      if (!currentMaterialId) return;
      
      // Remove the material and its auto-generated properties
      const response = await api.delete(`/api/v1/components/${componentId}/material/${currentMaterialId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['component-properties', componentId] });
      queryClient.invalidateQueries({ queryKey: ['component-materials', componentId] });
    },
  });

  const currentMaterial = componentMaterials?.[0]?.material;

  const categories = ['Metal', 'Ceramic', 'Polymer', 'Composite'];

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      Metal: '🔩',
      Ceramic: '🏺',
      Polymer: '🧪',
      Composite: '🔲',
    };
    return icons[category] || '📦';
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
                <span>{getCategoryIcon(currentMaterial.category)}</span>
                <span className="font-medium text-gray-900">{currentMaterial.name}</span>
              </div>
              {currentMaterial.astm_grade && (
                <span className="text-xs text-gray-600 ml-7">ASTM: {currentMaterial.astm_grade}</span>
              )}
              {currentMaterial.uns_number && (
                <span className="text-xs text-gray-600 ml-2">UNS: {currentMaterial.uns_number}</span>
              )}
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
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
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
              
              {/* Search and filters */}
              <div className="mt-4 space-y-3">
                <input
                  type="text"
                  placeholder="Search materials..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                
                <div className="flex gap-2">
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
                      {getCategoryIcon(cat)} {cat}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Materials list */}
            <div className="overflow-y-auto max-h-[50vh]">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="divide-y">
                  {/* None option */}
                  {currentMaterial && (
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
                  
                  {materials?.map((material) => (
                    <button
                      key={material.id}
                      onClick={() => setMaterial.mutate(material.id)}
                      className="w-full p-4 text-left hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span>{getCategoryIcon(material.category)}</span>
                            <h3 className="font-medium text-gray-900">{material.name}</h3>
                          </div>
                          <div className="mt-1 text-sm text-gray-600">
                            {material.subcategory && <span className="mr-3">{material.subcategory}</span>}
                            {material.astm_grade && <span className="mr-3">ASTM: {material.astm_grade}</span>}
                            {material.uns_number && <span>UNS: {material.uns_number}</span>}
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