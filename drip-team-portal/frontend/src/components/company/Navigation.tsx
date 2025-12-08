import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

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
    position: 'relative' as const,
    zIndex: 1000
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
      <Link to="/" style={{ ...logoStyle, textDecoration: 'none' }}>
        DRIP
      </Link>
      
      {/* Desktop Navigation Links */}
      {!isMobile && (
        <div style={{
          display: 'flex',
          gap: '40px',
          alignItems: 'center'
        }}>
          <Link 
            to="/" 
            style={{
              ...linkStyle,
              fontWeight: activePage === 'home' ? '700' : '500'
            }}
          >
            Home
          </Link>
          <Link 
            to="/progress" 
            style={{
              ...linkStyle,
              fontWeight: activePage === 'progress' ? '700' : '500'
            }}
          >
            Progress
          </Link>
          <Link 
            to="/team" 
            style={{
              ...linkStyle,
              fontWeight: activePage === 'team' ? '700' : '500'
            }}
          >
            Team
          </Link>
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
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          zIndex: 9999
        }}>
          <Link 
            to="/" 
            style={{
              ...mobileLinkStyle,
              fontWeight: activePage === 'home' ? '700' : '500'
            }}
            onClick={() => setMobileMenuOpen(false)}
          >
            Home
          </Link>
          <Link 
            to="/progress" 
            style={{
              ...mobileLinkStyle,
              fontWeight: activePage === 'progress' ? '700' : '500'
            }}
            onClick={() => setMobileMenuOpen(false)}
          >
            Progress
          </Link>
          <Link 
            to="/team" 
            style={{
              ...mobileLinkStyle,
              fontWeight: activePage === 'team' ? '700' : '500'
            }}
            onClick={() => setMobileMenuOpen(false)}
          >
            Team
          </Link>
        </div>
      )}
    </div>
  );
};

export default Navigation;