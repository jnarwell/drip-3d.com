import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthenticatedApi } from '../services/api';

type CallbackStatus = 'processing' | 'success' | 'error';

const OAuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const api = useAuthenticatedApi();

  const [status, setStatus] = useState<CallbackStatus>('processing');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      // Check for OAuth errors from Google
      if (error) {
        setStatus('error');
        setErrorMessage(errorDescription || error);
        return;
      }

      // Validate required parameters
      if (!code) {
        setStatus('error');
        setErrorMessage('Missing authorization code from Google');
        return;
      }

      try {
        // Exchange the code for tokens via our backend
        await api.post('/api/v1/google-oauth/callback', {
          code,
          state,
          redirect_uri: `${window.location.origin}/oauth/google/callback`,
        });

        setStatus('success');

        // Redirect to documents page after short delay
        setTimeout(() => {
          navigate('/resources/documents', {
            state: { googleConnected: true }
          });
        }, 1500);

      } catch (err: unknown) {
        setStatus('error');
        if (err && typeof err === 'object' && 'response' in err) {
          const axiosError = err as { response?: { data?: { detail?: string } } };
          setErrorMessage(axiosError.response?.data?.detail || 'Failed to connect Google account');
        } else {
          setErrorMessage('Failed to connect Google account');
        }
      }
    };

    handleCallback();
  }, [searchParams, api, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8 text-center">
        {status === 'processing' && (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Connecting Google Drive...
            </h2>
            <p className="text-gray-600">
              Please wait while we complete the connection.
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Google Drive Connected!
            </h2>
            <p className="text-gray-600">
              Redirecting to Documents...
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Connection Failed
            </h2>
            <p className="text-red-600 mb-4">
              {errorMessage}
            </p>
            <div className="space-x-3">
              <button
                onClick={() => navigate('/resources/documents')}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Go Back
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
              >
                Try Again
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default OAuthCallback;
