// Theme Toggle Functionality with Smooth Animations - Cycles through 5 themes
(function() {
    // Wait for DOM to be ready
    function initThemeToggle() {
        // Get all theme toggle buttons (there may be duplicates for mobile/desktop)
        const themeToggles = document.querySelectorAll('#themeToggle, #themeToggleNavMenu, .theme-toggle');
        if (themeToggles.length === 0) {
            // Retry if element not found yet
            setTimeout(initThemeToggle, 100);
            return;
        }
        
        const html = document.documentElement;
        const body = document.body;

        // Theme order: lightblue -> cyan -> light -> dark -> lightblue
        const themes = ['lightblue', 'cyan', 'light', 'dark'];
        const themeNames = {
            'lightblue': 'Light Blue',
            'cyan': 'Durjoy\'s Special',
            'light': 'Soft Lavender',
            'dark': 'Midnight Lavender'
        };
        
        // Check for saved theme preference or default to lightblue
        const savedTheme = localStorage.getItem('theme') || 'lightblue';
        const currentTheme = themes.includes(savedTheme) ? savedTheme : 'lightblue';
        html.setAttribute('data-theme', currentTheme);

        // Toast notification function
        function showToast(message, theme) {
            // Remove existing toast if any
            const existingToast = document.querySelector('.toast');
            if (existingToast) {
                existingToast.remove();
            }

            // Create toast element
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.setAttribute('data-theme', theme);
            
            // Create colored circle indicator
            const circle = document.createElement('div');
            circle.className = 'toast-indicator';
            
            // Create message container
            const messageContainer = document.createElement('div');
            messageContainer.className = 'toast-message';
            messageContainer.textContent = message;
            
            toast.appendChild(circle);
            toast.appendChild(messageContainer);
            document.body.appendChild(toast);

            // Trigger animation
            setTimeout(() => {
                toast.classList.add('show');
            }, 10);

            // Remove toast after animation (longer for cyan theme)
            const duration = theme === 'cyan' ? 3000 : 2000;
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => {
                    toast.remove();
                }, 300);
            }, duration);
        }

        // Theme menu functionality - get all theme menus (they're duplicates for mobile/desktop)
        const themeMenus = document.querySelectorAll('#themeMenu, #themeMenuNavMenu, .theme-menu');
        const themeMenu = themeMenus[0]; // Use first one for menu functionality
        const themeMenuItems = themeMenu ? themeMenu.querySelectorAll('.theme-menu-item') : [];
        
        // Get all theme menu items from all menus
        const allThemeMenuItems = document.querySelectorAll('.theme-menu-item');
        
        // Function to switch theme
        function switchTheme(newTheme) {
            // Add transitioning class for smooth animations
            body.classList.add('theme-transitioning');
            
            // Update theme
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Show toast notification
            showToast(`Switched to ${themeNames[newTheme]}`, newTheme);
            
            // Remove transitioning class after animation completes
            setTimeout(() => {
                body.classList.remove('theme-transitioning');
            }, 600);
        }
        
        // Use event delegation for click handler (works even if buttons are dynamically shown/hidden)
        document.addEventListener('click', function(e) {
            const clickedToggle = e.target.closest('#themeToggle, #themeToggleNavMenu, .theme-toggle');
            if (clickedToggle) {
                e.preventDefault();
                e.stopPropagation();
                const currentTheme = html.getAttribute('data-theme');
                const currentIndex = themes.indexOf(currentTheme);
                const nextIndex = (currentIndex + 1) % themes.length;
                const newTheme = themes[nextIndex];
                switchTheme(newTheme);
            }
        });
        
        // Attach hover listeners to all theme toggle buttons
        themeToggles.forEach(themeToggle => {
            // Find the associated theme menu (closest parent's theme menu)
            const wrapper = themeToggle.closest('.theme-toggle-wrapper');
            const associatedMenu = wrapper ? wrapper.querySelector('.theme-menu') : themeMenu;
            
            // Show menu on hover
            themeToggle.addEventListener('mouseenter', function() {
                if (associatedMenu) {
                    associatedMenu.classList.add('show');
                }
            });
            
            // Hide menu when mouse leaves
            themeToggle.addEventListener('mouseleave', function() {
                if (associatedMenu) {
                    // Delay to allow moving to menu
                    setTimeout(() => {
                        if (!associatedMenu.matches(':hover')) {
                            associatedMenu.classList.remove('show');
                        }
                    }, 100);
                }
            });
        });
        
        // Handle hover for all theme menus
        themeMenus.forEach(menu => {
            menu.addEventListener('mouseenter', function() {
                this.classList.add('show');
            });
            
            menu.addEventListener('mouseleave', function() {
                this.classList.remove('show');
            });
        });
        
        // Handle theme selection from menu - attach to ALL menu items from all menus
        allThemeMenuItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const newTheme = this.getAttribute('data-theme');
                if (newTheme && themes.includes(newTheme)) {
                    switchTheme(newTheme);
                    // Hide all theme menus
                    themeMenus.forEach(menu => {
                        menu.classList.remove('show');
                    });
                }
            });
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initThemeToggle);
    } else {
        initThemeToggle();
    }
})();

