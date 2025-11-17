import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import { TableType, InterpolationType, VariableDefinition, DocumentAnalysisResult } from '../../types/resources';

interface CreatePropertyTableTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const CreatePropertyTableTemplateModal: React.FC<CreatePropertyTableTemplateModalProps> = ({ isOpen, onClose }) => {
  const queryClient = useQueryClient();
  const [step, setStep] = useState<'method' | 'upload' | 'structure' | 'details'>('method');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [documentAnalysis, setDocumentAnalysis] = useState<DocumentAnalysisResult[] | null>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<DocumentAnalysisResult | null>(null);
  
  // Form data
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    table_type: TableType.SINGLE_VAR_LOOKUP,
    independent_vars: [] as VariableDefinition[],
    dependent_vars: [] as VariableDefinition[],
    interpolation_type: InterpolationType.LINEAR,
    extrapolation_allowed: false,
    require_monotonic: false,
    is_public: false
  });

  // Create template mutation
  const createTemplateMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/api/v1/property-table-templates/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['property-table-templates'] });
      onClose();
      resetForm();
    }
  });

  const resetForm = () => {
    setStep('method');
    setUploadedFile(null);
    setDocumentAnalysis(null);
    setSelectedAnalysis(null);
    setFormData({
      name: '',
      description: '',
      table_type: TableType.SINGLE_VAR_LOOKUP,
      independent_vars: [],
      dependent_vars: [],
      interpolation_type: InterpolationType.LINEAR,
      extrapolation_allowed: false,
      require_monotonic: false,
      is_public: false
    });
  };

  const handleFileUpload = async (file: File) => {
    setUploadedFile(file);
    setIsAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/v1/property-table-templates/analyze-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setDocumentAnalysis(response.data);
      setStep('structure');
    } catch (error) {
      console.error('Error analyzing document:', error);
      alert('Failed to analyze document. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSelectStructure = (analysis: DocumentAnalysisResult) => {
    setSelectedAnalysis(analysis);
    setFormData({
      ...formData,
      name: analysis.table_name,
      table_type: analysis.table_type as TableType,
      independent_vars: analysis.independent_vars,
      dependent_vars: analysis.dependent_vars
    });
    setStep('details');
  };

  const handleManualCreate = () => {
    // Set up some example variables for manual creation
    setFormData({
      ...formData,
      independent_vars: [
        { name: 'Temperature', symbol: 'T', unit: '°C', description: 'Temperature' }
      ],
      dependent_vars: [
        { name: 'Pressure', symbol: 'P', unit: 'kPa', description: 'Pressure' }
      ]
    });
    setStep('details');
  };

  const handleCreateTemplate = () => {
    const templateData = {
      ...formData,
      // Ensure enums are sent as their string values
      table_type: formData.table_type,
      interpolation_type: formData.interpolation_type,
      created_from_document: uploadedFile !== null,
      source_document_example: uploadedFile?.name
    };

    createTemplateMutation.mutate(templateData);
  };

  const addVariable = (type: 'independent' | 'dependent') => {
    const newVar: VariableDefinition = {
      name: '',
      symbol: '',
      unit: '',
      description: ''
    };

    if (type === 'independent') {
      setFormData({
        ...formData,
        independent_vars: [...formData.independent_vars, newVar]
      });
    } else {
      setFormData({
        ...formData,
        dependent_vars: [...formData.dependent_vars, newVar]
      });
    }
  };

  const updateVariable = (type: 'independent' | 'dependent', index: number, field: keyof VariableDefinition, value: string) => {
    const vars = type === 'independent' ? [...formData.independent_vars] : [...formData.dependent_vars];
    vars[index] = { ...vars[index], [field]: value };
    
    setFormData({
      ...formData,
      [type === 'independent' ? 'independent_vars' : 'dependent_vars']: vars
    });
  };

  const removeVariable = (type: 'independent' | 'dependent', index: number) => {
    const vars = type === 'independent' ? [...formData.independent_vars] : [...formData.dependent_vars];
    vars.splice(index, 1);
    
    setFormData({
      ...formData,
      [type === 'independent' ? 'independent_vars' : 'dependent_vars']: vars
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Create Property Table Template</h3>
        </div>

        <div className="p-6 overflow-y-auto max-h-[70vh]">
          {step === 'method' && (
            <div className="space-y-6">
              <h4 className="text-sm font-medium text-gray-900">How would you like to create your template?</h4>
              
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {/* From Document */}
                <button
                  onClick={() => setStep('upload')}
                  className="relative rounded-lg border border-gray-300 bg-white p-6 shadow-sm hover:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <svg className="h-10 w-10 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div className="flex-1 text-left">
                      <p className="text-base font-medium text-gray-900">Extract from Document</p>
                      <p className="mt-1 text-sm text-gray-500">Upload a PDF or screenshot to extract table structure</p>
                    </div>
                  </div>
                </button>

                {/* Manual Creation */}
                <button
                  onClick={handleManualCreate}
                  className="relative rounded-lg border border-gray-300 bg-white p-6 shadow-sm hover:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <svg className="h-10 w-10 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </div>
                    <div className="flex-1 text-left">
                      <p className="text-base font-medium text-gray-900">Create Manually</p>
                      <p className="mt-1 text-sm text-gray-500">Define table structure from scratch</p>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          )}

          {step === 'upload' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-gray-900">Upload Document</h4>
                <button
                  onClick={() => setStep('method')}
                  className="text-sm text-indigo-600 hover:text-indigo-500"
                >
                  ← Back
                </button>
              </div>

              <div>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                      <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <div className="flex text-sm text-gray-600">
                      <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                        <span>Upload a document</span>
                        <input
                          id="file-upload"
                          name="file-upload"
                          type="file"
                          className="sr-only"
                          accept=".pdf,.xlsx,.xls,.png,.jpg,.jpeg"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) handleFileUpload(file);
                          }}
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-gray-500">PDF, Excel, or image files up to 10MB</p>
                  </div>
                </div>
                <p className="mt-2 text-sm text-gray-500">
                  Upload a document containing property tables. We'll extract the table structure and help you create a reusable template.
                </p>
              </div>

              {isAnalyzing && (
                <div className="text-center py-4">
                  <div className="inline-flex items-center">
                    <svg className="animate-spin h-5 w-5 text-indigo-600 mr-2" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Analyzing document...
                  </div>
                </div>
              )}
            </div>
          )}

          {step === 'structure' && documentAnalysis && (
            <div className="space-y-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-gray-900">Select Table Structure</h4>
                <button
                  onClick={() => setStep('upload')}
                  className="text-sm text-indigo-600 hover:text-indigo-500"
                >
                  ← Back
                </button>
              </div>

              <p className="text-sm text-gray-600">
                We found {documentAnalysis.length} table structure(s) in your document. Select one to use as a template:
              </p>

              <div className="space-y-4">
                {documentAnalysis.map((analysis, index) => (
                  <div
                    key={index}
                    className="border border-gray-300 rounded-lg p-4 hover:border-indigo-500 cursor-pointer"
                    onClick={() => handleSelectStructure(analysis)}
                  >
                    <h5 className="font-medium text-gray-900">{analysis.table_name}</h5>
                    <p className="text-sm text-gray-500 mt-1">
                      Type: {analysis.table_type} • {analysis.total_rows} rows • Confidence: {Math.round(analysis.confidence_score * 100)}%
                    </p>
                    <div className="mt-2 grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <p className="font-medium text-gray-700">Independent Variables:</p>
                        <ul className="mt-1 space-y-1">
                          {analysis.independent_vars.map((v, i) => (
                            <li key={i} className="text-gray-600">{v.symbol} - {v.name} ({v.unit})</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="font-medium text-gray-700">Dependent Variables:</p>
                        <ul className="mt-1 space-y-1">
                          {analysis.dependent_vars.slice(0, 3).map((v, i) => (
                            <li key={i} className="text-gray-600">{v.symbol} - {v.name} ({v.unit})</li>
                          ))}
                          {analysis.dependent_vars.length > 3 && (
                            <li className="text-gray-400">... and {analysis.dependent_vars.length - 3} more</li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {step === 'details' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-gray-900">Template Details</h4>
                <button
                  onClick={() => setStep(documentAnalysis ? 'structure' : 'method')}
                  className="text-sm text-indigo-600 hover:text-indigo-500"
                >
                  ← Back
                </button>
              </div>

              {/* Basic Info */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Template Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="e.g., Water Properties - Saturation Temperature"
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Describe what this template is for..."
                />
              </div>

              {/* Table Type */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="table_type" className="block text-sm font-medium text-gray-700">
                    Table Type
                  </label>
                  <select
                    id="table_type"
                    value={formData.table_type}
                    onChange={(e) => setFormData({ ...formData, table_type: e.target.value as TableType })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  >
                    <option value={TableType.SINGLE_VAR_LOOKUP}>Single Variable Lookup</option>
                    <option value={TableType.RANGE_BASED_LOOKUP}>Range-based Lookup</option>
                    <option value={TableType.MULTI_VAR_LOOKUP}>Multi-variable Lookup</option>
                    <option value={TableType.REFERENCE_ONLY}>Reference Only</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="interpolation_type" className="block text-sm font-medium text-gray-700">
                    Interpolation
                  </label>
                  <select
                    id="interpolation_type"
                    value={formData.interpolation_type}
                    onChange={(e) => setFormData({ ...formData, interpolation_type: e.target.value as InterpolationType })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  >
                    <option value={InterpolationType.LINEAR}>Linear</option>
                    <option value={InterpolationType.LOGARITHMIC}>Logarithmic</option>
                    <option value={InterpolationType.POLYNOMIAL}>Polynomial</option>
                    <option value={InterpolationType.RANGE_LOOKUP}>Range Lookup</option>
                    <option value={InterpolationType.NONE}>None</option>
                  </select>
                </div>
              </div>

              {/* Variables */}
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="text-sm font-medium text-gray-900">Independent Variables</h5>
                    <button
                      type="button"
                      onClick={() => addVariable('independent')}
                      className="text-sm text-indigo-600 hover:text-indigo-500"
                    >
                      + Add Variable
                    </button>
                  </div>
                  <div className="space-y-2">
                    {formData.independent_vars.map((varDef, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={varDef.name}
                          onChange={(e) => updateVariable('independent', index, 'name', e.target.value)}
                          placeholder="Name"
                          className="flex-1 text-sm border-gray-300 rounded-md"
                        />
                        <input
                          type="text"
                          value={varDef.symbol}
                          onChange={(e) => updateVariable('independent', index, 'symbol', e.target.value)}
                          placeholder="Symbol"
                          className="w-20 text-sm border-gray-300 rounded-md"
                        />
                        <input
                          type="text"
                          value={varDef.unit}
                          onChange={(e) => updateVariable('independent', index, 'unit', e.target.value)}
                          placeholder="Unit"
                          className="w-20 text-sm border-gray-300 rounded-md"
                        />
                        <button
                          type="button"
                          onClick={() => removeVariable('independent', index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="text-sm font-medium text-gray-900">Dependent Variables</h5>
                    <button
                      type="button"
                      onClick={() => addVariable('dependent')}
                      className="text-sm text-indigo-600 hover:text-indigo-500"
                    >
                      + Add Variable
                    </button>
                  </div>
                  <div className="space-y-2">
                    {formData.dependent_vars.map((varDef, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={varDef.name}
                          onChange={(e) => updateVariable('dependent', index, 'name', e.target.value)}
                          placeholder="Name"
                          className="flex-1 text-sm border-gray-300 rounded-md"
                        />
                        <input
                          type="text"
                          value={varDef.symbol}
                          onChange={(e) => updateVariable('dependent', index, 'symbol', e.target.value)}
                          placeholder="Symbol"
                          className="w-20 text-sm border-gray-300 rounded-md"
                        />
                        <input
                          type="text"
                          value={varDef.unit}
                          onChange={(e) => updateVariable('dependent', index, 'unit', e.target.value)}
                          placeholder="Unit"
                          className="w-20 text-sm border-gray-300 rounded-md"
                        />
                        <button
                          type="button"
                          onClick={() => removeVariable('dependent', index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Options */}
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.extrapolation_allowed}
                    onChange={(e) => setFormData({ ...formData, extrapolation_allowed: e.target.checked })}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">Allow extrapolation beyond data range</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.require_monotonic}
                    onChange={(e) => setFormData({ ...formData, require_monotonic: e.target.checked })}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">Require monotonic data</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_public}
                    onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">Make this template public</span>
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={handleCreateTemplate}
                  disabled={!formData.name || formData.independent_vars.length === 0 || formData.dependent_vars.length === 0 || createTemplateMutation.isPending}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
                >
                  {createTemplateMutation.isPending ? 'Creating...' : 'Create Template'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 text-right">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreatePropertyTableTemplateModal;