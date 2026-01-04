// Mobile Menu Toggle Functionality
(function() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    const navLinks = navMenu.querySelectorAll('.nav-link');
    let scrollPosition = 0;

    // Function to lock body scroll (but allow menu to scroll)
    function lockBodyScroll() {
        scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
        document.body.style.overflow = 'hidden';
        document.body.style.position = 'fixed';
        document.body.style.top = `-${scrollPosition}px`;
        document.body.style.width = '100%';
        // Ensure menu can still scroll
        if (navMenu) {
            navMenu.style.overflowY = 'scroll';
        }
    }

    // Function to unlock body scroll
    function unlockBodyScroll() {
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        window.scrollTo(0, scrollPosition);
    }

    // Ensure menu can scroll independently - no interference with touch events

    // Toggle menu on hamburger click
    hamburger.addEventListener('click', function() {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
        if (navMenu.classList.contains('active')) {
            lockBodyScroll();
        } else {
            unlockBodyScroll();
        }
    });

    // Close menu when clicking on a nav link (but not dropdown toggles)
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Don't close menu if clicking on a dropdown toggle
            if (!link.classList.contains('dropdown-toggle')) {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
                unlockBodyScroll();
            }
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
        const isClickInsideNav = navMenu.contains(event.target);
        const isClickOnHamburger = hamburger.contains(event.target);
        
        if (!isClickInsideNav && !isClickOnHamburger && navMenu.classList.contains('active')) {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
            unlockBodyScroll();
        }
    });

    // Close menu on window resize if it becomes desktop view
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 768) {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
            unlockBodyScroll();
        }
    });
})();

