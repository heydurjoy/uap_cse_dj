// Navbar scroll shrink functionality
document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.querySelector('.navbar');
    
    if (!navbar) return;
    
    let isScrolled = false;
    let lastScrollTop = 0;
    const scrollThreshold = 50; // Start shrinking after 50px scroll
    const scrollHysteresis = 10; // Hysteresis to prevent rapid toggling
    
    function handleScroll() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Use hysteresis to prevent rapid toggling
        if (!isScrolled && scrollTop > scrollThreshold) {
            navbar.classList.add('scrolled');
            isScrolled = true;
        } else if (isScrolled && scrollTop <= (scrollThreshold - scrollHysteresis)) {
            navbar.classList.remove('scrolled');
            isScrolled = false;
        }
        
        lastScrollTop = scrollTop;
    }
    
    // Use throttled scroll for better performance
    let ticking = false;
    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                handleScroll();
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });
    
    // Check initial scroll position after a small delay to ensure layout is stable
    setTimeout(function() {
        handleScroll();
    }, 100);
});

