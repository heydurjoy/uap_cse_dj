// Theme Toggle Functionality with Smooth Animations - Cycles through 4 themes
(function() {
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    const body = document.body;

    // Theme order: cyan -> light -> dark -> lightblue -> cyan
    const themes = ['cyan', 'light', 'dark', 'lightblue'];
    const themeNames = {
        'cyan': 'Durjoy\'s Special',
        'light': 'Soft Lavender',
        'dark': 'UAP Midnight Lavender',
        'lightblue': 'Light Blue'
    };
    
    // Check for saved theme preference or default to cyan (Beautiful Cyan)
    const savedTheme = localStorage.getItem('theme') || 'cyan';
    const currentTheme = themes.includes(savedTheme) ? savedTheme : 'cyan';
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

    themeToggle.addEventListener('click', function() {
        const currentTheme = html.getAttribute('data-theme');
        const currentIndex = themes.indexOf(currentTheme);
        const nextIndex = (currentIndex + 1) % themes.length;
        const newTheme = themes[nextIndex];
        
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
    });
})();

