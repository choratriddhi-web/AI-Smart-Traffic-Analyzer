// AI Smart Traffic Analyzer - Main Interactive Scripts

document.addEventListener('DOMContentLoaded', () => {
    // 1. Live Clock in Topbar
    const clockElem = document.getElementById('live-system-clock');
    if (clockElem) {
        function updateClock() {
            const now = new Date();
            clockElem.textContent = now.toLocaleTimeString('en-US', { hour12: false }) + " UTC+5:30";
        }
        setInterval(updateClock, 1000);
        updateClock();
    }

    // 2. Mobile Sidebar Toggle
    const toggleBtn = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.app-sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }

    // 3. Auto-hide Bootstrap alert banners after 6 seconds
    setTimeout(() => {
        document.querySelectorAll('.alert-dismissible').forEach(alert => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        });
    }, 6000);
});
