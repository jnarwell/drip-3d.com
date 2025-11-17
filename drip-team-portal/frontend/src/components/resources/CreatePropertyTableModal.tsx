import React, { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import { PropertyTableTemplate, CreatePropertyTableData, ImportMethod, SourceType, DocumentAnalysisResult } from '../../types/resources';

interface CreatePropertyTableModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const CreatePropertyTableModal: React.FC<CreatePropertyTableModalProps> = ({ isOpen, onClose }) => {
  const queryClient = useQueryClient();
  const [step, setStep] = useState<'method' | 'details' | 'data'>('method');
  const [importMethod, setImportMethod] = useState<ImportMethod | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<PropertyTableTemplate | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [documentAnalysis, setDocumentAnalysis] = useState<DocumentAnalysisResult[] | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState<Partial<CreatePropertyTableData>>({
    name: '',
    description: '',
    source_citation: '',
    source_authority: '',
    source_type: SourceType.OTHER,
    tags: [],
    is_public: false,
    data: []
  });

  // Fetch available templates
  const { data: templates } = useQuery<PropertyTableTemplate[]>({
    queryKey: ['property-table-templates'],
    queryFn: async () => {
      const response = await api.get('/api/v1/property-table-templates/');
      return response.data;
    },
    enabled: isOpen
  });

  // Create property table mutation
  const createTableMutation = useMutation({
    mutationFn: async (data: CreatePropertyTableData) => {
      const response = await api.post('/api/v1/enhanced/property-tables/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['property-tables'] });
      onClose();
      resetForm();
    }
  });

  const resetForm = () => {
    setStep('method');
    setImportMethod(null);
    setSelectedTemplate(null);
    setUploadedFile(null);
    setDocumentAnalysis(null);
    setFormData({
      name: '',
      description: '',
      source_citation: '',
      source_authority: '',
      source_type: SourceType.OTHER,
      tags: [],
      is_public: false,
      data: []
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
      
      // Auto-fill form with first table found
      if (response.data && response.data.length > 0) {
        const firstTable = response.data[0];
        setFormData(prev => ({
          ...prev,
          name: firstTable.table_name,
          source_citation: firstTable.source_info || ''
        }));
      }
    } catch (error) {
      console.error('Error analyzing document:', error);
      alert('Failed to analyze document. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCreateTable = () => {
    if (!importMethod) return;

    const tableData: CreatePropertyTableData = {
      ...formData as CreatePropertyTableData,
      import_method: importMethod,
      template_id: selectedTemplate?.id,
      source_document_path: uploadedFile?.name,
      extracted_via_ocr: importMethod === ImportMethod.DOCUMENT_IMPORT && documentAnalysis?.[0]?.extraction_method === 'ocr'
    };

    createTableMutation.mutate(tableData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Create Property Table</h3>
        </div>

        <div className="p-6 overflow-y-auto max-h-[70vh]">
          {step === 'method' && (
            <div className="space-y-6">
              <h4 className="text-sm font-medium text-gray-900">How would you like to create your table?</h4>
              
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {/* Document Import */}
                <button
                  onClick={() => {
                    setImportMethod(ImportMethod.DOCUMENT_IMPORT);
                    setStep('details');
                  }}
                  className="relative rounded-lg border border-gray-300 bg-white p-6 shadow-sm hover:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <svg className="h-10 w-10 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div className="flex-1 text-left">
                      <p className="text-base font-medium text-gray-900">Import from Document</p>
                      <p className="mt-1 text-sm text-gray-500">Upload a PDF or Excel file to extract table data</p>
                      <p className="mt-2 text-xs text-green-600 font-medium">🟢 Auto-verified when successful</p>
                    </div>
                  </div>
                </button>

                {/* Manual Entry */}
                <button
                  onClick={() => {
                    setImportMethod(ImportMethod.MANUAL_ENTRY);
                    setStep('details');
                  }}
                  className="relative rounded-lg border border-gray-300 bg-white p-6 shadow-sm hover:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <svg className="h-10 w-10 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </div>
                    <div className="flex-1 text-left">
                      <p className="text-base font-medium text-gray-900">Manual Entry</p>
                      <p className="mt-1 text-sm text-gray-500">Create a table and enter data manually</p>
                      <p className="mt-2 text-xs text-yellow-600 font-medium">🟡 Cited if source provided</p>
                    </div>
                  </div>
                </button>

                {/* From Template */}
                <button
                  onClick={() => {
                    setImportMethod(ImportMethod.MANUAL_ENTRY);
                    setStep('details');
                  }}
                  className="relative rounded-lg border border-gray-300 bg-white p-6 shadow-sm hover:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <svg className="h-10 w-10 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
                      </svg>
                    </div>
                    <div className="flex-1 text-left">
                      <p className="text-base font-medium text-gray-900">Use Template</p>
                      <p className="mt-1 text-sm text-gray-500">Start from an existing table structure</p>
                      <p className="mt-2 text-xs text-gray-500">
                        {templates && templates.length > 0 ? `${templates.length} templates available` : 'No templates yet'}
                      </p>
                    </div>
                  </div>
                </button>

                {/* API Import (future) */}
                <button
                  disabled
                  className="relative rounded-lg border border-gray-200 bg-gray-50 p-6 shadow-sm cursor-not-allowed opacity-60"
                >
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <svg className="h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div className="flex-1 text-left">
                      <p className="text-base font-medium text-gray-900">API Import</p>
                      <p className="mt-1 text-sm text-gray-500">Connect to external data sources</p>
                      <p className="mt-2 text-xs text-gray-400">Coming soon</p>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          )}

          {step === 'details' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-gray-900">Table Details</h4>
                <button
                  onClick={() => setStep('method')}
                  className="text-sm text-indigo-600 hover:text-indigo-500"
                >
                  ← Back
                </button>
              </div>

              {/* Document upload for import method */}
              {importMethod === ImportMethod.DOCUMENT_IMPORT && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Upload Document</label>
                    <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                      <div className="space-y-1 text-center">
                        <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                          <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <div className="flex text-sm text-gray-600">
                          <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                            <span>Upload a file</span>
                            <input
                              id="file-upload"
                              name="file-upload"
                              type="file"
                              className="sr-only"
                              accept=".pdf,.xlsx,.xls,.csv"
                              onChange={(e) => {
                                const file = e.target.files?.[0];
                                if (file) handleFileUpload(file);
                              }}
                            />
                          </label>
                          <p className="pl-1">or drag and drop</p>
                        </div>
                        <p className="text-xs text-gray-500">PDF, Excel up to 10MB</p>
                      </div>
                    </div>
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

                  {documentAnalysis && documentAnalysis.length > 0 && (
                    <div className="bg-green-50 border border-green-200 rounded-md p-4">
                      <h5 className="text-sm font-medium text-green-800 mb-2">Document analyzed successfully!</h5>
                      <p className="text-sm text-green-600">Found {documentAnalysis.length} table(s) in the document</p>
                      <div className="mt-2 text-xs text-green-600">
                        <p>• {documentAnalysis[0].total_rows} data rows detected</p>
                        <p>• Confidence: {Math.round(documentAnalysis[0].confidence_score * 100)}%</p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Template selection */}
              {templates && templates.length > 0 && importMethod === ImportMethod.MANUAL_ENTRY && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Select Template (Optional)</label>
                  <select
                    value={selectedTemplate?.id || ''}
                    onChange={(e) => {
                      const template = templates.find(t => t.id === parseInt(e.target.value));
                      setSelectedTemplate(template || null);
                    }}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                  >
                    <option value="">No template - create custom structure</option>
                    {templates.map((template) => (
                      <option key={template.id} value={template.id}>
                        {template.name} ({template.usage_count} uses)
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Basic info */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Table Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="e.g., Water Properties at Saturation"
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Describe the table contents and applicable conditions..."
                />
              </div>

              {/* Source information */}
              <div className="space-y-4 border-t pt-4">
                <h5 className="text-sm font-medium text-gray-900">Source Information</h5>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="source_type" className="block text-sm font-medium text-gray-700">
                      Source Type
                    </label>
                    <select
                      id="source_type"
                      value={formData.source_type}
                      onChange={(e) => setFormData({ ...formData, source_type: e.target.value as SourceType })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    >
                      <option value={SourceType.STANDARD}>Standard (ISO, ASTM, etc.)</option>
                      <option value={SourceType.HANDBOOK}>Engineering Handbook</option>
                      <option value={SourceType.PAPER}>Research Paper</option>
                      <option value={SourceType.REPORT}>Technical Report</option>
                      <option value={SourceType.EXPERIMENTAL}>Experimental Data</option>
                      <option value={SourceType.OTHER}>Other</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="source_authority" className="block text-sm font-medium text-gray-700">
                      Authority/Publisher
                    </label>
                    <input
                      type="text"
                      id="source_authority"
                      value={formData.source_authority}
                      onChange={(e) => setFormData({ ...formData, source_authority: e.target.value })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      placeholder="e.g., IAPWS, NIST"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="source_citation" className="block text-sm font-medium text-gray-700">
                    Full Citation
                  </label>
                  <input
                    type="text"
                    id="source_citation"
                    value={formData.source_citation}
                    onChange={(e) => setFormData({ ...formData, source_citation: e.target.value })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="e.g., IAPWS-95 Formulation for Thermodynamic Properties of Water"
                  />
                  {importMethod === ImportMethod.MANUAL_ENTRY && (
                    <p className="mt-1 text-xs text-gray-500">
                      Providing a citation will mark this table as 🟡 Cited
                    </p>
                  )}
                </div>
              </div>

              {/* Tags */}
              <div>
                <label htmlFor="tags" className="block text-sm font-medium text-gray-700">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  id="tags"
                  value={formData.tags?.join(', ')}
                  onChange={(e) => setFormData({ 
                    ...formData, 
                    tags: e.target.value.split(',').map(t => t.trim()).filter(t => t) 
                  })}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="e.g., water, steam, thermodynamic"
                />
              </div>

              <div className="flex items-center">
                <input
                  id="is_public"
                  type="checkbox"
                  checked={formData.is_public}
                  onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="is_public" className="ml-2 block text-sm text-gray-900">
                  Make this table public
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setStep('method')}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (importMethod === ImportMethod.MANUAL_ENTRY) {
                      setStep('data');
                    } else {
                      handleCreateTable();
                    }
                  }}
                  disabled={!formData.name || createTableMutation.isPending}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
                >
                  {importMethod === ImportMethod.MANUAL_ENTRY ? 'Next' : 'Create Table'}
                </button>
              </div>
            </div>
          )}

          {step === 'data' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-gray-900">Enter Table Data</h4>
                <button
                  onClick={() => setStep('details')}
                  className="text-sm text-indigo-600 hover:text-indigo-500"
                >
                  ← Back
                </button>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <p className="text-sm text-yellow-800">
                  Manual data entry coming soon. For now, tables will be created empty and you can add data later.
                </p>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setStep('details')}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={handleCreateTable}
                  disabled={!formData.name || createTableMutation.isPending}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
                >
                  {createTableMutation.isPending ? 'Creating...' : 'Create Table'}
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

export default CreatePropertyTableModal;