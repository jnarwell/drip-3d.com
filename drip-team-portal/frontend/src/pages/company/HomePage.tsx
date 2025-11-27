import React from 'react';

const HomePage: React.FC = () => {
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
        <section className="text-center py-20">
          <h2 className="text-5xl font-bold mb-6">DRIP Acoustic Manufacturing</h2>
          <p className="text-xl text-gray-600 mb-8">Precision metal 3D printing without contact</p>
          <p className="text-lg text-gray-500">Revolutionary acoustic deposition manufacturing system</p>
        </section>
        
        <section className="py-16">
          <h3 className="text-3xl font-bold mb-8 text-center">Company Website Coming Soon</h3>
          <p className="text-center text-gray-600">
            The full company website with Linear integration for live progress updates is being migrated.
          </p>
        </section>
      </main>
      
      <footer className="bg-gray-900 text-white py-8 mt-20">
        <div className="container mx-auto px-4 text-center">
          <p>&copy; 2025 DRIP Acoustic Manufacturing. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;