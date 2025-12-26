// Notification System
(function() {
    const NOTIFICATION_STORAGE_KEY = 'cleared_notifications';
    const MAX_NOTIFICATIONS = 10; // Show top 10 recent posts
    
    let clearedNotifications = [];
    let allNotifications = [];
    
    // Load cleared notifications from localStorage
    function loadClearedNotifications() {
        try {
            const stored = localStorage.getItem(NOTIFICATION_STORAGE_KEY);
            if (stored) {
                clearedNotifications = JSON.parse(stored);
            }
        } catch (e) {
            console.error('Error loading cleared notifications:', e);
            clearedNotifications = [];
        }
    }
    
    // Save cleared notifications to localStorage
    function saveClearedNotifications() {
        try {
            localStorage.setItem(NOTIFICATION_STORAGE_KEY, JSON.stringify(clearedNotifications));
        } catch (e) {
            console.error('Error saving cleared notifications:', e);
        }
    }
    
    // Fetch notifications from server
    async function fetchNotifications() {
        try {
            const response = await fetch('/office/api/notifications/');
            if (response.ok) {
                const data = await response.json();
                return data.notifications || [];
            }
        } catch (e) {
            console.error('Error fetching notifications:', e);
        }
        return [];
    }
    
    // Filter out cleared notifications
    function getUnreadNotifications(notifications) {
        return notifications.filter(notif => !clearedNotifications.includes(notif.id));
    }
    
    // Update badge count
    function updateBadge(count) {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    // Format date for display
    function formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
    
    // Get post type badge color class
    function getPostTypeClass(type) {
        const typeMap = {
            'notice': 'notif-type-notice',
            'events': 'notif-type-events',
            'seminars': 'notif-type-seminars',
            'workshop': 'notif-type-workshop',
            'others': 'notif-type-others'
        };
        return typeMap[type] || 'notif-type-others';
    }
    
    // Render notifications
    function renderNotifications(notifications) {
        const container = document.getElementById('notificationList');
        if (!container) return;
        
        if (notifications.length === 0) {
            container.innerHTML = `
                <div class="notification-empty">
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                    </svg>
                    <p>No new notifications</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = notifications.map(notif => `
            <a href="${notif.url}" class="notification-item" data-id="${notif.id}">
                <div class="notification-icon ${getPostTypeClass(notif.type)}">
                    ${notif.is_pinned ? `
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 17v5M9 10V6a3 3 0 0 1 3-3h0a3 3 0 0 1 3 3v4M5 10h14l-1 7H6l-1-7z"></path>
                        </svg>
                    ` : `
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                        </svg>
                    `}
                </div>
                <div class="notification-content">
                    <div class="notification-header">
                        <span class="notification-type ${getPostTypeClass(notif.type)}">${notif.type_display}</span>
                        <span class="notification-time">${formatDate(notif.date)}</span>
                    </div>
                    <div class="notification-title">${notif.title}</div>
                    ${notif.description ? `<div class="notification-description">${notif.description}</div>` : ''}
                </div>
            </a>
        `).join('');
    }
    
    // Clear all notifications
    function clearAllNotifications() {
        const unread = getUnreadNotifications(allNotifications);
        unread.forEach(notif => {
            if (!clearedNotifications.includes(notif.id)) {
                clearedNotifications.push(notif.id);
            }
        });
        saveClearedNotifications();
        updateNotifications();
    }
    
    // Update notifications display
    async function updateNotifications() {
        loadClearedNotifications();
        allNotifications = await fetchNotifications();
        const unread = getUnreadNotifications(allNotifications);
        renderNotifications(unread);
        updateBadge(unread.length);
    }
    
    // Initialize
    document.addEventListener('DOMContentLoaded', function() {
        const notificationBtn = document.getElementById('notificationBtn');
        const notificationModal = document.getElementById('notificationModal');
        const clearAllBtn = document.getElementById('clearAllNotifications');
        const closeModal = document.getElementById('closeNotificationModal');
        
        if (!notificationBtn || !notificationModal) return;
        
        // Toggle modal
        notificationBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (notificationModal) {
                notificationModal.classList.toggle('active');
                if (notificationModal.classList.contains('active')) {
                    updateNotifications();
                }
            }
        });
        
        // Close modal when clicking outside
        document.addEventListener('click', function(e) {
            if (!notificationModal.contains(e.target) && !notificationBtn.contains(e.target)) {
                notificationModal.classList.remove('active');
            }
        });
        
        // Clear all button
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                clearAllNotifications();
            });
        }
        
        // Close button - multiple handlers for reliability
        if (closeModal) {
            // Direct handler
            closeModal.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (notificationModal) {
                    notificationModal.classList.remove('active');
                }
            });
            
            // Also handle SVG clicks inside close button
            const closeSvg = closeModal.querySelector('svg');
            if (closeSvg) {
                closeSvg.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    if (notificationModal) {
                        notificationModal.classList.remove('active');
                    }
                });
            }
        }
        
        // Event delegation backup for close button
        document.addEventListener('click', function(e) {
            const closeBtn = e.target.closest('#closeNotificationModal') || 
                           e.target.closest('.close-notification-btn') ||
                           (e.target.closest('svg') && e.target.closest('svg').parentElement && e.target.closest('svg').parentElement.id === 'closeNotificationModal');
            if (closeBtn && notificationModal) {
                e.preventDefault();
                e.stopPropagation();
                notificationModal.classList.remove('active');
            }
        });
        
        // Initial load
        updateNotifications();
        
        // Update every 5 minutes
        setInterval(updateNotifications, 5 * 60 * 1000);
    });
})();

