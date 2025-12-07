// Hero Section Animations
(function() {
    // Dynamic Stats Rotation - using hero tags from database
    // heroTagsData is defined in the template before this script loads
    const stats = typeof heroTagsData !== 'undefined' && heroTagsData.length > 0 
        ? heroTagsData 
        : ['No tags available']; // Fallback if no tags
    
    const statsElement = document.getElementById('dynamicStats');
    let currentStatIndex = 0;
    
    function rotateStats() {
        if (statsElement && stats.length > 0) {
            statsElement.style.opacity = '0';
            statsElement.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                currentStatIndex = (currentStatIndex + 1) % stats.length;
                statsElement.textContent = stats[currentStatIndex];
                statsElement.style.opacity = '1';
                statsElement.style.transform = 'translateY(0)';
            }, 300);
        }
    }
    
    // Rotate stats every 3 seconds
    if (statsElement && stats.length > 0) {
        // Set initial text
        statsElement.textContent = stats[0];
        setInterval(rotateStats, 3000);
    }
})();

