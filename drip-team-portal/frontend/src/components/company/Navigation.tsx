import React, { useState, useEffect } from 'react';

interface NavigationProps {
  activePage?: 'home' | 'progress' | 'team';
}

const Navigation: React.FC<NavigationProps> = ({ activePage }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Check window size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Close mobile menu when clicking outside
  useEffect(() => {
    if (mobileMenuOpen) {
      const handleClick = () => setMobileMenuOpen(false);
      document.addEventListener('click', handleClick);
      return () => document.removeEventListener('click', handleClick);
    }
  }, [mobileMenuOpen]);

  const navStyle = {
    backgroundColor: '#354857',
    paddingLeft: '24px',
    paddingRight: '38px',
    paddingTop: '12px',
    paddingBottom: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    position: 'relative' as const
  };

  const logoStyle = {
    color: '#ffffff',
    fontSize: '32px',
    fontWeight: 'bold',
    letterSpacing: '1px'
  };

  const linkStyle = {
    color: '#ffffff',
    textDecoration: 'none',
    fontSize: '16px',
    fontWeight: '500'
  };

  const mobileLinkStyle = {
    ...linkStyle,
    display: 'block',
    padding: '15px 24px',
    borderTop: '1px solid rgba(255,255,255,0.1)'
  };

  return (
    <div style={navStyle}>
      {/* DRIP Logo */}
      <a href="/" style={{ ...logoStyle, textDecoration: 'none' }}>
        DRIP
      </a>
      
      {/* Desktop Navigation Links */}
      {!isMobile && (
        <div style={{
          display: 'flex',
          gap: '40px',
          alignItems: 'center'
        }}>
          <a 
            href="/" 
            style={{
              ...linkStyle,
              fontWeight: activePage === 'home' ? '700' : '500'
            }}
          >
            Home
          </a>
          <a 
            href="/progress" 
            style={{
              ...linkStyle,
              fontWeight: activePage === 'progress' ? '700' : '500'
            }}
          >
            Progress
          </a>
          <a 
            href="/team" 
            style={{
              ...linkStyle,
              fontWeight: activePage === 'team' ? '700' : '500'
            }}
          >
            Team
          </a>
        </div>
      )}

      {/* Mobile Menu Button */}
      {isMobile && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setMobileMenuOpen(!mobileMenuOpen);
          }}
          style={{
            background: 'none',
            border: 'none',
            color: '#ffffff',
            fontSize: '24px',
            cursor: 'pointer',
            padding: '5px'
          }}
        >
          ☰
        </button>
      )}

      {/* Mobile Menu Dropdown */}
      {isMobile && mobileMenuOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          backgroundColor: '#354857',
          boxShadow: '0 2px 5px rgba(0,0,0,0.2)'
        }}>
          <a 
            href="/" 
            style={{
              ...mobileLinkStyle,
              fontWeight: activePage === 'home' ? '700' : '500'
            }}
          >
            Home
          </a>
          <a 
            href="/progress" 
            style={{
              ...mobileLinkStyle,
              fontWeight: activePage === 'progress' ? '700' : '500'
            }}
          >
            Progress
          </a>
          <a 
            href="/team" 
            style={{
              ...mobileLinkStyle,
              fontWeight: activePage === 'team' ? '700' : '500'
            }}
          >
            Team
          </a>
        </div>
      )}
    </div>
  );
};

export default Navigation;