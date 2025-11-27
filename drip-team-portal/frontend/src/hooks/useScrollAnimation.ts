import { useEffect } from 'react';

export function useScrollAnimation() {
  useEffect(() => {
    const observerOptions: IntersectionObserverInit = {
      threshold: 0.2,
      rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
          // Optional: stop observing after animation
          // observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    // Observe all elements with reveal classes
    const animatedElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');
    animatedElements.forEach(el => observer.observe(el));

    // Cleanup
    return () => {
      animatedElements.forEach(el => observer.unobserve(el));
      observer.disconnect();
    };
  }, []);
}

// Hook for smooth scrolling
export function useSmoothScroll() {
  useEffect(() => {
    const handleAnchorClick = (e: Event) => {
      const anchor = e.currentTarget as HTMLAnchorElement;
      const href = anchor.getAttribute('href');
      
      if (href && href.startsWith('#')) {
        e.preventDefault();
        const target = document.querySelector(href);
        
        if (target) {
          const headerOffset = 80; // Account for fixed header
          const elementPosition = target.getBoundingClientRect().top;
          const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });
        }
      }
    };

    const anchors = document.querySelectorAll('a[href^="#"]');
    anchors.forEach(anchor => {
      anchor.addEventListener('click', handleAnchorClick);
    });

    return () => {
      anchors.forEach(anchor => {
        anchor.removeEventListener('click', handleAnchorClick);
      });
    };
  }, []);
}