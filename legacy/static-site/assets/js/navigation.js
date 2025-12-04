// Navigation functionality

domReady(() => {
    const header = document.querySelector('.site-header');
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mainNav = document.querySelector('.main-nav');
    const navLinks = document.querySelectorAll('.main-nav a');
    
    // Mobile menu toggle
    if (mobileMenuToggle && mainNav) {
        mobileMenuToggle.addEventListener('click', () => {
            mainNav.classList.toggle('main-nav--open');
            mobileMenuToggle.classList.toggle('active');
            
            // Update aria-label for accessibility
            const isOpen = mainNav.classList.contains('main-nav--open');
            mobileMenuToggle.setAttribute('aria-label', isOpen ? 'Close menu' : 'Open menu');
            
            // Prevent body scroll when menu is open
            document.body.style.overflow = isOpen ? 'hidden' : '';
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!mainNav.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                mainNav.classList.remove('main-nav--open');
                mobileMenuToggle.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
        
        // Close mobile menu when clicking a link
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                mainNav.classList.remove('main-nav--open');
                mobileMenuToggle.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
    }
    
    // Header scroll behavior
    let lastScroll = 0;
    const scrollThreshold = 100;
    
    const handleScroll = () => {
        const currentScroll = window.pageYOffset;
        
        // Add/remove scrolled class
        if (currentScroll > scrollThreshold) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        
        // Hide/show header on scroll
        if (currentScroll > lastScroll && currentScroll > scrollThreshold) {
            // Scrolling down
            header.classList.add('header--hidden');
        } else {
            // Scrolling up
            header.classList.remove('header--hidden');
        }
        
        lastScroll = currentScroll;
    };
    
    // Throttle scroll event for performance
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        if (scrollTimeout) {
            window.cancelAnimationFrame(scrollTimeout);
        }
        scrollTimeout = window.requestAnimationFrame(handleScroll);
    });
    
    // Set active navigation item based on current page
    const currentPath = window.location.pathname;
    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
});

// Add corresponding CSS for header states
const headerStyles = `
<style>
.site-header {
    transition: transform 0.3s ease, background-color 0.3s ease;
}

.site-header.scrolled {
    background-color: rgba(44, 62, 80, 0.98);
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.site-header.header--hidden {
    transform: translateY(-100%);
}

.mobile-menu-toggle {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    transition: transform 0.3s ease;
}

.mobile-menu-toggle.active {
    transform: rotate(90deg);
}

@media (max-width: 768px) {
    .main-nav {
        position: fixed;
        top: 0;
        right: -100%;
        width: 80%;
        max-width: 300px;
        height: 100vh;
        background-color: var(--steel-dark);
        transition: right 0.3s ease;
        z-index: calc(var(--z-sticky) + 1);
        overflow-y: auto;
    }
    
    .main-nav--open {
        right: 0;
        box-shadow: -5px 0 20px rgba(0,0,0,0.3);
    }
    
    .main-nav ul {
        flex-direction: column;
        padding: var(--space-xl);
        gap: var(--space-lg);
        margin-top: var(--space-3xl);
    }
    
    .main-nav a {
        font-size: var(--text-lg);
        display: block;
        padding: var(--space-sm) 0;
    }
}
</style>`;

// Inject header-specific styles
if (!document.querySelector('#navigation-styles')) {
    const styleTag = document.createElement('div');
    styleTag.id = 'navigation-styles';
    styleTag.innerHTML = headerStyles;
    document.head.appendChild(styleTag.firstElementChild);
}