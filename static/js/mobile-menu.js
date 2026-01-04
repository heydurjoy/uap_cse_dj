// Mobile Menu Toggle Functionality
(function() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    const navLinks = navMenu.querySelectorAll('.nav-link');
    let scrollPosition = 0;

    // Function to lock body scroll
    function lockBodyScroll() {
        scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
        document.body.style.overflow = 'hidden';
        document.body.style.position = 'fixed';
        document.body.style.top = `-${scrollPosition}px`;
        document.body.style.width = '100%';
    }

    // Function to unlock body scroll
    function unlockBodyScroll() {
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        window.scrollTo(0, scrollPosition);
    }

    // Prevent scroll propagation from nav-menu to body
    if (navMenu) {
        navMenu.addEventListener('wheel', function(e) {
            const menu = e.currentTarget;
            const isScrollingDown = e.deltaY > 0;
            const isScrollingUp = e.deltaY < 0;
            const isAtTop = menu.scrollTop === 0;
            const isAtBottom = menu.scrollTop + menu.clientHeight >= menu.scrollHeight - 1;

            // Prevent scroll propagation if we're at the boundaries
            if ((isScrollingUp && isAtTop) || (isScrollingDown && isAtBottom)) {
                e.preventDefault();
                e.stopPropagation();
            }
        }, { passive: false });

        // Prevent touch scroll propagation at boundaries only
        let touchStartY = 0;
        navMenu.addEventListener('touchstart', function(e) {
            touchStartY = e.touches[0].clientY;
        }, { passive: true });

        navMenu.addEventListener('touchmove', function(e) {
            const menu = e.currentTarget;
            const touchY = e.touches[0].clientY;
            const scrollDelta = touchY - touchStartY;
            const isScrollingDown = scrollDelta < 0;
            const isScrollingUp = scrollDelta > 0;
            const isAtTop = menu.scrollTop <= 0;
            const isAtBottom = menu.scrollTop + menu.clientHeight >= menu.scrollHeight - 1;

            // Only prevent propagation if trying to scroll past boundaries
            if ((isScrollingUp && isAtTop) || (isScrollingDown && isAtBottom)) {
                e.stopPropagation();
            }
            // Otherwise, allow normal scrolling within the menu
        }, { passive: true });
    }

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

