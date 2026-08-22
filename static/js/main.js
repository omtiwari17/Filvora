document.addEventListener("DOMContentLoaded", () => {
    // Add navbar solid background effect on scroll
    const navbar = document.querySelector('nav');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('bg-gray-950');
                navbar.classList.remove('bg-gradient-to-b', 'from-black/80', 'to-transparent');
            } else {
                navbar.classList.remove('bg-gray-950');
                navbar.classList.add('bg-gradient-to-b', 'from-black/80', 'to-transparent');
            }
        });
    }

    // Dismiss search dropdown when clicking outside
    document.addEventListener('click', (e) => {
        const searchContainer = document.getElementById('navbar-search-container');
        const dropdown = document.getElementById('search-results-dropdown');
        if (searchContainer && dropdown && !searchContainer.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });
});
