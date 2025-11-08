import React, { useState } from 'react';
import { useAuthenticatedApi } from '../services/api';

const Reports: React.FC = () => {
  const api = useAuthenticatedApi();
  const [downloading, setDownloading] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });

  const downloadReport = async (format: 'pdf' | 'excel') => {
    setDownloading(format);
    try {
      const response = await api.get('/api/v1/reports/validation-report', {
        params: {
          format,
          start_date: dateRange.start,
          end_date: dateRange.end,
        },
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `drip_validation_report_${dateRange.start}_${dateRange.end}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading report:', error);
    } finally {
      setDownloading(null);
    }
  };

  const reportTypes = [
    {
      title: 'Validation Report (PDF)',
      description: 'Comprehensive validation report with component status, test results, and physics validation',
      icon: '📄',
      format: 'pdf' as const,
    },
    {
      title: 'Test Campaign Data (Excel)',
      description: 'Detailed Excel workbook with all components, tests, results, and physics data',
      icon: '📊',
      format: 'excel' as const,
    },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Reports</h1>

      {/* Date Range Selector */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Report Date Range</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="start-date" className="block text-sm font-medium text-gray-700">
              Start Date
            </label>
            <input
              type="date"
              id="start-date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label htmlFor="end-date" className="block text-sm font-medium text-gray-700">
              End Date
            </label>
            <input
              type="date"
              id="end-date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Available Reports */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reportTypes.map((report) => (
          <div key={report.format} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-start space-x-4">
              <span className="text-4xl">{report.icon}</span>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900">{report.title}</h3>
                <p className="mt-1 text-sm text-gray-600">{report.description}</p>
                <button
                  onClick={() => downloadReport(report.format)}
                  disabled={downloading !== null}
                  className="mt-4 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400"
                >
                  {downloading === report.format ? 'Generating...' : 'Download Report'}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Stats */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Report Contents</h2>
        <div className="prose prose-sm text-gray-600">
          <h3>Validation Report includes:</h3>
          <ul>
            <li>Executive summary with key metrics</li>
            <li>Component verification status by category</li>
            <li>Test campaign progress and results</li>
            <li>Physics validation with DRIP numbers</li>
            <li>Risk assessment and mitigation strategies</li>
            <li>Recent system activity</li>
          </ul>
          
          <h3>Excel Workbook includes:</h3>
          <ul>
            <li>Complete component registry with all details</li>
            <li>Full test list with prerequisites and status</li>
            <li>All test results with measurements</li>
            <li>Physics validation data and calculations</li>
            <li>Summary statistics sheet</li>
          </ul>
        </div>
      </div>

      {/* Export Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              Reports are generated in real-time based on current data. Large date ranges may take longer to process.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;