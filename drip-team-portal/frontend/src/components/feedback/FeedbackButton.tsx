import React, { useState } from 'react';
import FeedbackModal from './FeedbackModal';

const FeedbackButton: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsModalOpen(true)}
        className="fixed top-3 right-3 z-40 w-10 h-10 rounded-full bg-indigo-600 text-white shadow-lg hover:bg-indigo-700 transition-colors flex items-center justify-center font-semibold text-lg"
        title="Send Feedback"
      >
        ?
      </button>

      {isModalOpen && <FeedbackModal onClose={() => setIsModalOpen(false)} />}
    </>
  );
};

export default FeedbackButton;
