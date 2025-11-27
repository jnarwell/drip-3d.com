import React from 'react';

const TeamPage: React.FC = () => {
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
        <h2 className="text-4xl font-bold mb-8">Our Team</h2>
        <p className="text-gray-600 mb-8">Meet the engineers and scientists building the future of manufacturing.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div className="bg-gray-100 p-6 rounded-lg">
            <h3 className="text-xl font-semibold">Team Member</h3>
            <p className="text-gray-600">Role</p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default TeamPage;