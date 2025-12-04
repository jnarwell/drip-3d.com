import { useState, useEffect, useRef, useCallback } from 'react';

export const useScrollEasterEgg = (threshold: number = 7) => {
  const [isRevealed, setIsRevealed] = useState(false);
  const [scrollAttempts, setScrollAttempts] = useState(0);
  const lastSwipeTime = useRef(0);
  const resetTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hasTriggeredBounce = useRef(false);
  const isCountingRef = useRef(false);

  // Use a ref to track the current attempt count to avoid closure issues
  const scrollAttemptsRef = useRef(0);
  
  // Track if the easter egg has been revealed to prevent multiple triggers
  const isRevealedRef = useRef(false);

  const resetAttempts = useCallback(() => {
    if (!isRevealedRef.current) {
      setScrollAttempts(0);
      scrollAttemptsRef.current = 0;
    }
  }, []);

  useEffect(() => {
    // Track when we hit the bottom boundary
    const handleScroll = () => {
      const scrollPosition = window.scrollY + window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      
      // Detect if we've hit the bottom boundary (bounce-back point)
      if (scrollPosition >= documentHeight) {
        hasTriggeredBounce.current = true;
      } else if (scrollPosition < documentHeight - 10) {
        // Reset bounce flag when we scroll away from bottom
        hasTriggeredBounce.current = false;
      }
    };

    // Listen for wheel events that happen at the bottom
    const handleWheel = (e: WheelEvent) => {
      // Prevent any action if already revealed
      if (isRevealedRef.current) return;
      
      const scrollPosition = window.scrollY + window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      const atBottom = scrollPosition >= documentHeight - 2;
      
      // Only process downward scrolls at the bottom
      if (atBottom && e.deltaY > 0 && hasTriggeredBounce.current && !isCountingRef.current) {
        const currentTime = Date.now();
        const timeSinceLastSwipe = currentTime - lastSwipeTime.current;
        
        // If more than 800ms has passed, reset the counter
        if (timeSinceLastSwipe > 520 && scrollAttemptsRef.current > 0) {
          resetAttempts();
        }
        
        // Only count if this is a new swipe (at least 600ms since last count)
        if (timeSinceLastSwipe > 450 || lastSwipeTime.current === 0) {
          isCountingRef.current = true;
          lastSwipeTime.current = currentTime;
          
          // Clear any existing reset timer
          if (resetTimer.current) {
            clearTimeout(resetTimer.current);
          }
          
          // Increment the count
          scrollAttemptsRef.current += 1;
          const newCount = scrollAttemptsRef.current;
          setScrollAttempts(newCount);
          
          // Check if we've reached the threshold
          if (newCount === 15 && !isRevealedRef.current) {
            isRevealedRef.current = true;
            setIsRevealed(true);
            // Scroll to the easter egg smoothly
            setTimeout(() => {
              const easterEggElement = document.getElementById('easter-egg-section');
              if (easterEggElement) {
                easterEggElement.scrollIntoView({ behavior: 'smooth' });
              }
            }, 100);
          }
          
          // Reset the counting flag after a delay
          setTimeout(() => {
            isCountingRef.current = false;
          }, 500);
          
          // Set a new timer to reset attempts after 800ms of inactivity
          resetTimer.current = setTimeout(resetAttempts, 550);
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('wheel', handleWheel, { passive: true });
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('wheel', handleWheel);
      if (resetTimer.current) {
        clearTimeout(resetTimer.current);
      }
    };
  }, [threshold, resetAttempts]);

  return { isRevealed, scrollAttempts };
};