import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { PropertyType, PropertyDefinition } from '../types';
import PropertyCreator from './PropertyCreator';
import PropertyEditor from './PropertyEditor';

interface AddPropertyDropdownProps {
  componentId: string;
}

type ViewState = 'closed' | 'types' | 'properties' | 'creator' | 'editor';

interface ContextMenuState {
  visible: boolean;
  x: number;
  y: number;
  propertyDef: PropertyDefinition | null;
}

const AddPropertyDropdown: React.FC<AddPropertyDropdownProps> = ({ componentId }) => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  const [viewState, setViewState] = useState<ViewState>('closed');
  const [selectedType, setSelectedType] = useState<PropertyType | null>(null);
  const [editingDef, setEditingDef] = useState<PropertyDefinition | null>(null);
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    visible: false,
    x: 0,
    y: 0,
    propertyDef: null,
  });
  const dropdownRef = useRef<HTMLDivElement>(null);
  const contextMenuRef = useRef<HTMLDivElement>(null);

  const { data: propertyDefinitions } = useQuery<PropertyDefinition[]>({
    queryKey: ['property-definitions', selectedType],
    queryFn: async () => {
      const params = selectedType ? `?property_type=${selectedType}` : '';
      const response = await api.get(`/api/v1/property-definitions${params}`);
      return response.data;
    },
    enabled: viewState === 'properties' && selectedType !== null,
  });

  const addProperty = useMutation({
    mutationFn: async (propertyDefId: number) => {
      await api.post(`/api/v1/components/${componentId}/properties`, {
        property_definition_id: propertyDefId,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['component-properties', componentId] });
      setViewState('closed');
      setSelectedType(null);
    },
  });

  const deletePropertyDef = useMutation({
    mutationFn: async (defId: number) => {
      await api.delete(`/api/v1/property-definitions/${defId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['property-definitions'] });
      setContextMenu({ visible: false, x: 0, y: 0, propertyDef: null });
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to delete property definition');
    },
  });

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Close context menu if clicking outside
      if (contextMenuRef.current && !contextMenuRef.current.contains(event.target as Node)) {
        setContextMenu({ visible: false, x: 0, y: 0, propertyDef: null });
      }
      // Close dropdown if clicking outside
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setViewState('closed');
        setSelectedType(null);
        setEditingDef(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const propertyTypes = Object.values(PropertyType);

  const getPropertyTypeLabel = (type: PropertyType) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  const handleBack = () => {
    if (viewState === 'properties') {
      setViewState('types');
      setSelectedType(null);
    } else if (viewState === 'creator' || viewState === 'editor') {
      setViewState('properties');
      setEditingDef(null);
    }
  };

  const handleTypeSelect = (type: PropertyType) => {
    setSelectedType(type);
    setViewState('properties');
  };

  const handlePropertySelect = (propertyDef: PropertyDefinition) => {
    addProperty.mutate(propertyDef.id);
  };

  const handleCreateNew = () => {
    setViewState('creator');
  };

  const handleContextMenu = (e: React.MouseEvent, propertyDef: PropertyDefinition) => {
    // Only show context menu for custom properties
    if (!propertyDef.is_custom) return;

    e.preventDefault();
    e.stopPropagation();

    // Get dropdown container position for relative positioning
    const dropdownRect = dropdownRef.current?.getBoundingClientRect();
    const x = e.clientX - (dropdownRect?.left || 0);
    const y = e.clientY - (dropdownRect?.top || 0);

    setContextMenu({
      visible: true,
      x,
      y,
      propertyDef,
    });
  };

  const handleRename = () => {
    if (contextMenu.propertyDef) {
      setEditingDef(contextMenu.propertyDef);
      setViewState('editor');
      setContextMenu({ visible: false, x: 0, y: 0, propertyDef: null });
    }
  };

  const handleEdit = () => {
    if (contextMenu.propertyDef) {
      setEditingDef(contextMenu.propertyDef);
      setViewState('editor');
      setContextMenu({ visible: false, x: 0, y: 0, propertyDef: null });
    }
  };

  const handleDelete = () => {
    if (contextMenu.propertyDef) {
      if (confirm(`Delete "${contextMenu.propertyDef.name}"? This cannot be undone.`)) {
        deletePropertyDef.mutate(contextMenu.propertyDef.id);
      } else {
        setContextMenu({ visible: false, x: 0, y: 0, propertyDef: null });
      }
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setViewState(viewState === 'closed' ? 'types' : 'closed')}
        className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors flex items-center gap-2"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Add Property
      </button>

      {viewState !== 'closed' && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            {viewState !== 'types' && (
              <button
                onClick={handleBack}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
                aria-label="Go back"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            <h3 className="text-sm font-semibold text-gray-900">
              {viewState === 'types' && 'Select Property Type'}
              {viewState === 'properties' && `${getPropertyTypeLabel(selectedType!)} Properties`}
              {viewState === 'creator' && 'Create Custom Property'}
              {viewState === 'editor' && 'Edit Property'}
            </h3>
            {viewState === 'types' && <div className="w-5" />}
          </div>

          {/* Content */}
          <div className="max-h-96 overflow-y-auto">
            {viewState === 'types' && (
              <div className="py-2">
                {propertyTypes.map((type) => (
                  <button
                    key={type}
                    onClick={() => handleTypeSelect(type)}
                    className="w-full px-4 py-2 text-left hover:bg-gray-50 transition-colors flex items-center justify-between"
                  >
                    <span className="text-sm text-gray-700">{getPropertyTypeLabel(type)}</span>
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                ))}
              </div>
            )}

            {viewState === 'properties' && (
              <div className="py-2">
                {propertyDefinitions?.map((propertyDef) => (
                  <button
                    key={propertyDef.id}
                    onClick={() => handlePropertySelect(propertyDef)}
                    onContextMenu={(e) => handleContextMenu(e, propertyDef)}
                    className="w-full px-4 py-2 text-left hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">{propertyDef.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">{propertyDef.unit}</span>
                        {propertyDef.is_custom && (
                          <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">custom</span>
                        )}
                      </div>
                    </div>
                    {propertyDef.description && (
                      <p className="text-xs text-gray-500 mt-1">{propertyDef.description}</p>
                    )}
                  </button>
                ))}
                <button
                  onClick={handleCreateNew}
                  className="w-full px-4 py-2 text-left hover:bg-gray-50 transition-colors border-t border-gray-200"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-indigo-600">...</span>
                    <span className="text-sm text-indigo-600">Create custom property</span>
                  </div>
                </button>
              </div>
            )}

            {viewState === 'creator' && (
              <PropertyCreator
                propertyType={selectedType!}
                componentId={componentId}
                onSuccess={() => {
                  setViewState('closed');
                  setSelectedType(null);
                }}
                onCancel={handleBack}
              />
            )}

            {viewState === 'editor' && editingDef && (
              <PropertyEditor
                propertyDef={editingDef}
                onSuccess={() => {
                  setViewState('properties');
                  setEditingDef(null);
                }}
                onCancel={handleBack}
              />
            )}
          </div>

          {/* Context Menu */}
          {contextMenu.visible && contextMenu.propertyDef && (
            <div
              ref={contextMenuRef}
              className="absolute bg-white rounded-lg shadow-xl border border-gray-200 py-1 z-[60] min-w-36"
              style={{ left: contextMenu.x, top: contextMenu.y }}
            >
              <button
                onClick={handleRename}
                className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Rename
              </button>
              <button
                onClick={handleEdit}
                className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
                Edit
              </button>
              <div className="border-t border-gray-100 my-1" />
              <button
                onClick={handleDelete}
                className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AddPropertyDropdown;
