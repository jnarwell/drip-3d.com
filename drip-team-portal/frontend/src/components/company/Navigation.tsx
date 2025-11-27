import React, { useState, useEffect, useCallback } from 'react';
import { debounce } from '../../utils/drip';

interface NavigationProps {
  activePage: 'home' | 'progress' | 'team';
}

const Navigation: React.FC<NavigationProps> = ({ activePage }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [headerVisible, setHeaderVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  // Handle scroll behavior
  useEffect(() => {
    let ticking = false;

    const updateScrollState = () => {
      const currentScrollY = window.scrollY;
      
      // Add background when scrolled
      setScrolled(currentScrollY > 0);
      
      // Hide/show header based on scroll direction
      if (currentScrollY > lastScrollY && currentScrollY > 50) {
        setHeaderVisible(false);
      } else {
        setHeaderVisible(true);
      }
      
      setLastScrollY(currentScrollY);
      ticking = false;
    };

    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(updateScrollState);
        ticking = true;
      }
    };

    const debouncedScroll = debounce(handleScroll, 10);
    window.addEventListener('scroll', debouncedScroll);

    return () => {
      window.removeEventListener('scroll', debouncedScroll);
    };
  }, [lastScrollY]);

  // Handle mobile menu
  const toggleMobileMenu = useCallback(() => {
    setMobileMenuOpen(prev => {
      const newState = !prev;
      // Toggle body scroll
      if (newState) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
      return newState;
    });
  }, []);

  // Close mobile menu on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const nav = document.querySelector('.mobile-nav');
      const toggle = document.querySelector('.mobile-menu-toggle');
      
      if (mobileMenuOpen && nav && !nav.contains(target) && !toggle?.contains(target)) {
        toggleMobileMenu();
      }
    };

    if (mobileMenuOpen) {
      document.addEventListener('click', handleOutsideClick);
    }

    return () => {
      document.removeEventListener('click', handleOutsideClick);
    };
  }, [mobileMenuOpen, toggleMobileMenu]);

  // Close menu on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mobileMenuOpen) {
        toggleMobileMenu();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [mobileMenuOpen, toggleMobileMenu]);

  // Clean up body scroll on unmount
  useEffect(() => {
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  const navClasses = `site-header ${scrolled ? 'site-header--scrolled' : ''} ${headerVisible ? 'site-header--visible' : 'site-header--hidden'}`;

  return (
    <>
      <header className={navClasses}>
        <div className="container">
          <div className="site-header__inner">
            <div className="logo">
              <a href="/">DRIP</a>
            </div>
            <nav className="main-nav">
              <ul>
                <li><a href="/" className={activePage === 'home' ? 'active' : ''}>Home</a></li>
                <li><a href="/progress" className={activePage === 'progress' ? 'active' : ''}>Progress</a></li>
                <li><a href="/team" className={activePage === 'team' ? 'active' : ''}>Team</a></li>
              </ul>
            </nav>
            <button 
              className={`mobile-menu-toggle ${mobileMenuOpen ? 'mobile-menu-toggle--open' : ''}`}
              aria-label="Toggle menu"
              onClick={toggleMobileMenu}
            >
              ☰
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Navigation */}
      <nav className={`mobile-nav ${mobileMenuOpen ? 'mobile-nav--open' : ''}`}>
        <ul>
          <li><a href="/" className={activePage === 'home' ? 'active' : ''}>Home</a></li>
          <li><a href="/progress" className={activePage === 'progress' ? 'active' : ''}>Progress</a></li>
          <li><a href="/team" className={activePage === 'team' ? 'active' : ''}>Team</a></li>
        </ul>
      </nav>
    </>
  );
};

export default Navigation;