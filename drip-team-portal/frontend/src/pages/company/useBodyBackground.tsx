import { useEffect } from 'react';

export const useBodyBackground = (color: string) => {
  useEffect(() => {
    // Store the original background color
    const originalColor = document.body.style.backgroundColor;
    
    // Set the new background color
    document.body.style.backgroundColor = color;
    
    // Cleanup function to restore original color
    return () => {
      document.body.style.backgroundColor = originalColor;
    };
  }, [color]);
};