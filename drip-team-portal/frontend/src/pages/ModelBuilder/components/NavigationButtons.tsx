import React from 'react';

interface NavigationButtonsProps {
  step: number;
  totalSteps: number;
  onNext: () => void;
  onBack: () => void;
  onSave?: () => void;
  canProceed: boolean;
  isLoading?: boolean;
  isSaving?: boolean;
  isEditMode?: boolean;
}

const NavigationButtons: React.FC<NavigationButtonsProps> = ({
  step,
  totalSteps,
  onNext,
  onBack,
  onSave,
  canProceed,
  isLoading = false,
  isSaving = false,
  isEditMode = false,
}) => {
  const isFirstStep = step === 1;
  const isLastStep = step === totalSteps;

  return (
    <div className="flex justify-between pt-6 mt-6 border-t border-gray-200">
      <div>
        {!isFirstStep && (
          <button
            type="button"
            onClick={onBack}
            disabled={isLoading || isSaving}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Back
          </button>
        )}
      </div>

      <div className="flex space-x-3">
        {isLastStep ? (
          <button
            type="button"
            onClick={onSave}
            disabled={!canProceed || isSaving}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                {isEditMode ? 'Updating Model...' : 'Creating Model...'}
              </>
            ) : (
              isEditMode ? 'Update Model' : 'Create Model'
            )}
          </button>
        ) : (
          <button
            type="button"
            onClick={onNext}
            disabled={!canProceed || isLoading}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Loading...
              </>
            ) : (
              <>
                Next
                <svg
                  className="ml-2 h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};

export default NavigationButtons;
