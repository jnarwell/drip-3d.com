import React from 'react';

interface Step {
  number: number;
  title: string;
}

interface ProgressStepperProps {
  currentStep: number;
  steps: Step[];
}

const ProgressStepper: React.FC<ProgressStepperProps> = ({ currentStep, steps }) => {
  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center">
        {steps.map((step, index) => {
          const isCompleted = step.number < currentStep;
          const isCurrent = step.number === currentStep;
          const isLast = index === steps.length - 1;

          return (
            <li key={step.number} className={`relative ${!isLast ? 'flex-1' : ''}`}>
              <div className="flex items-center">
                {/* Circle */}
                <div
                  className={`relative flex h-8 w-8 items-center justify-center rounded-full border-2 ${
                    isCompleted
                      ? 'border-indigo-600 bg-indigo-600'
                      : isCurrent
                      ? 'border-indigo-600 bg-white'
                      : 'border-gray-300 bg-white'
                  }`}
                >
                  {isCompleted ? (
                    <svg
                      className="h-5 w-5 text-white"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <span
                      className={`text-sm font-medium ${
                        isCurrent ? 'text-indigo-600' : 'text-gray-500'
                      }`}
                    >
                      {step.number}
                    </span>
                  )}
                </div>

                {/* Step title */}
                <span
                  className={`ml-3 text-sm font-medium ${
                    isCompleted || isCurrent ? 'text-indigo-600' : 'text-gray-500'
                  }`}
                >
                  {step.title}
                </span>

                {/* Connector line */}
                {!isLast && (
                  <div className="ml-4 flex-1 h-0.5 bg-gray-200">
                    <div
                      className={`h-full ${isCompleted ? 'bg-indigo-600' : 'bg-gray-200'}`}
                      style={{ width: isCompleted ? '100%' : '0%' }}
                    />
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default ProgressStepper;
