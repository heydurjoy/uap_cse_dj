// Theme Toggle Functionality with Smooth Animations - Cycles through 5 themes
(function() {
    // Wait for DOM to be ready
    function initThemeToggle() {
        // Get all theme toggle buttons (there may be duplicates for mobile/desktop)
        const themeToggles = document.querySelectorAll('#themeToggle, .theme-toggle');
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

        // Theme menu functionality - get the first theme menu (they're duplicates)
        const themeMenu = document.querySelector('#themeMenu, .theme-menu');
        const themeMenuItems = themeMenu ? themeMenu.querySelectorAll('.theme-menu-item') : [];
        
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
            const clickedToggle = e.target.closest('#themeToggle, .theme-toggle');
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
            // Show menu on hover
            themeToggle.addEventListener('mouseenter', function() {
                if (themeMenu) {
                    themeMenu.classList.add('show');
                }
            });
            
            // Hide menu when mouse leaves
            themeToggle.addEventListener('mouseleave', function() {
                if (themeMenu) {
                    // Delay to allow moving to menu
                    setTimeout(() => {
                        if (!themeMenu.matches(':hover')) {
                            themeMenu.classList.remove('show');
                        }
                    }, 100);
                }
            });
        });
        
        // Handle theme selection from menu
        themeMenuItems.forEach(item => {
            item.addEventListener('click', function() {
                const newTheme = this.getAttribute('data-theme');
                switchTheme(newTheme);
                if (themeMenu) {
                    themeMenu.classList.remove('show');
                }
            });
        });
        
        if (themeMenu) {
            themeMenu.addEventListener('mouseenter', function() {
                themeMenu.classList.add('show');
            });
            
            themeMenu.addEventListener('mouseleave', function() {
                themeMenu.classList.remove('show');
            });
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initThemeToggle);
    } else {
        initThemeToggle();
    }
})();

