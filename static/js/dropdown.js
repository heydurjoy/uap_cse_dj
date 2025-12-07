// Dropdown Menu Functionality with Liquid Glass Design
(function() {
    const dropdowns = document.querySelectorAll('.nav-dropdown');
    
    function isMobile() {
        return window.innerWidth < 768;
    }
    
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (toggle && menu) {
            // Desktop: hover to open
            dropdown.addEventListener('mouseenter', () => {
                if (!isMobile()) {
                    dropdown.classList.add('active');
                    menu.style.opacity = '0';
                    menu.style.transform = 'translateY(-10px)';
                    setTimeout(() => {
                        menu.style.opacity = '1';
                        menu.style.transform = 'translateY(0)';
                    }, 10);
                }
            });
            
            dropdown.addEventListener('mouseleave', () => {
                if (!isMobile()) {
                    dropdown.classList.remove('active');
                    menu.style.opacity = '0';
                    menu.style.transform = 'translateY(-10px)';
                }
            });
            
            // Mobile: click to toggle
            toggle.addEventListener('click', (e) => {
                if (isMobile()) {
                    e.preventDefault();
                    e.stopPropagation();
                    const isActive = dropdown.classList.contains('active');
                    
                    // Close all other dropdowns
                    dropdowns.forEach(otherDropdown => {
                        if (otherDropdown !== dropdown) {
                            otherDropdown.classList.remove('active');
                        }
                    });
                    
                    // Toggle current dropdown
                    dropdown.classList.toggle('active', !isActive);
                }
            });
        }
    });
    
    // Handle window resize
    window.addEventListener('resize', () => {
        if (!isMobile()) {
            // Reset mobile active states when switching to desktop
            dropdowns.forEach(dropdown => {
                dropdown.classList.remove('active');
            });
        }
    });
    
    // Close dropdowns when clicking outside (mobile only)
    document.addEventListener('click', (e) => {
        if (isMobile()) {
            const isClickInside = Array.from(dropdowns).some(dropdown => 
                dropdown.contains(e.target)
            );
            
            if (!isClickInside) {
                dropdowns.forEach(dropdown => {
                    dropdown.classList.remove('active');
                });
            }
        }
    });
})();

