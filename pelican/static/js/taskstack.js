/* jshint esversion: 6 */
document.addEventListener('DOMContentLoaded', function() {
    function updateActiveProgressBars() {
        const bars = document.querySelectorAll('.progress-bar');
        
        bars.forEach(bar => {
            const progress = parseFloat(bar.dataset.progress);
            const duration = parseFloat(bar.dataset.duration);
            const progressElement = bar.querySelector('.progress');
            
            if (progress < 100) {
                // Calculate remaining time and update progress
                const now = new Date();
                const elapsed = (progress / 100) * duration;
                const remaining = duration - elapsed;
                const width = Math.min(100, (elapsed / duration) * 100);
                
                progressElement.style.width = width + '%';
                
                // Update every second
                setTimeout(updateProgressBars, 1000);
            } else {
                progressElement.style.width = '100%';
            }
        });
    }
    
    updateProgressBars();
});
