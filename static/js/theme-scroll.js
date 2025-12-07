// Auto Theme Switch on Scroll - Only on themes page
(function() {
    // Check if we're on the themes page
    if (!document.querySelector('.theme-section[data-theme-trigger]')) {
        return; // Exit if not on themes page
    }

    const html = document.documentElement;
    const body = document.body;
    let isManualToggle = false;
    let scrollTimeout;

    // Get all theme sections
    const themeSections = document.querySelectorAll('.theme-section[data-theme-trigger]');
    
    if (themeSections.length === 0) return;

    // Intersection Observer to detect when sections come into view
    const observerOptions = {
        root: null,
        rootMargin: '-20% 0px -20% 0px', // Trigger when section is 20% from top and bottom
        threshold: 0.3
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !isManualToggle) {
                const theme = entry.target.getAttribute('data-theme-trigger');
                if (theme && html.getAttribute('data-theme') !== theme) {
                    // Add transitioning class for smooth animations
                    body.classList.add('theme-transitioning');
                    
                    // Update theme
                    html.setAttribute('data-theme', theme);
                    localStorage.setItem('theme', theme);
                    
                    // Remove transitioning class after animation completes
                    setTimeout(() => {
                        body.classList.remove('theme-transitioning');
                    }, 600);
                }
            }
        });
    }, observerOptions);

    // Observe all theme sections
    themeSections.forEach(section => {
        observer.observe(section);
    });

    // Detect manual theme toggle to temporarily disable auto-switch
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            isManualToggle = true;
            
            // Re-enable auto-switch after a delay
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                isManualToggle = false;
            }, 2000); // Wait 2 seconds after manual toggle
        });
    }

    // Also disable auto-switch when user is actively scrolling
    let scrollActive = false;
    window.addEventListener('scroll', function() {
        scrollActive = true;
        clearTimeout(scrollTimeout);
        
        scrollTimeout = setTimeout(() => {
            scrollActive = false;
        }, 150);
    });
})();

