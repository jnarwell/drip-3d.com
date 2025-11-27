import React from 'react';

const ProgressPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      <header className="bg-gray-900 text-white">
        <div className="container mx-auto px-4 py-6">
          <nav className="flex justify-between items-center">
            <h1 className="text-2xl font-bold">DRIP</h1>
            <ul className="flex space-x-6">
              <li><a href="/" className="hover:text-gray-300">Home</a></li>
              <li><a href="/progress" className="hover:text-gray-300">Progress</a></li>
              <li><a href="/team" className="hover:text-gray-300">Team</a></li>
              <li><a href="https://team.drip-3d.com" className="hover:text-gray-300">Portal</a></li>
            </ul>
          </nav>
        </div>
      </header>
      
      <main className="container mx-auto px-4 py-12">
        <h2 className="text-4xl font-bold mb-8">Project Progress</h2>
        <p className="text-gray-600 mb-8">Real-time progress tracking powered by Linear integration coming soon.</p>
        
        <div className="bg-gray-100 p-8 rounded-lg">
          <h3 className="text-2xl font-semibold mb-4">Current Phase: Development</h3>
          <div className="space-y-4">
            <div className="bg-white p-4 rounded shadow">
              <h4 className="font-semibold">Acoustic System Design</h4>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{width: '75%'}}></div>
              </div>
              <p className="text-sm text-gray-600 mt-1">75% Complete</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ProgressPage;