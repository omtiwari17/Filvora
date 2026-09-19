/**
 * Filvora v2.4 - Core Application JavaScript
 */

document.addEventListener("DOMContentLoaded", () => {
    initCsrfSync();
    initNavbar();
    initKeyboardShortcuts();
    initHorizontalRails();
    initHtmxFeedback();
    initNetworkMonitor();
});

// --- Navbar & Navigation ---
function initNavbar() {
    const navbar = document.querySelector('nav');
    if (navbar) {
        const handleScroll = () => {
            if (window.scrollY > 40) {
                navbar.classList.add('bg-gray-950/95', 'backdrop-blur-xl', 'border-b', 'border-gray-800/80', 'shadow-2xl');
                navbar.classList.remove('bg-gradient-to-b', 'from-black/90', 'to-transparent');
            } else {
                navbar.classList.remove('bg-gray-950/95', 'backdrop-blur-xl', 'border-b', 'border-gray-800/80', 'shadow-2xl');
                navbar.classList.add('bg-gradient-to-b', 'from-black/90', 'to-transparent');
            }
        };
        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll();
    }

    // Dismiss search dropdown when clicking outside
    document.addEventListener('click', (e) => {
        const searchContainer = document.getElementById('navbar-search-container');
        const dropdown = document.getElementById('search-results-dropdown');
        if (searchContainer && dropdown && !searchContainer.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });

    // Highlight active nav links based on current path
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('text-white', 'font-bold', 'bg-white/10', 'border-white/20');
            link.classList.remove('text-gray-300');
        }
    });
}

// --- Mobile Dedicated Search ---
function openMobileSearch() {
    const overlay = document.getElementById('mobile-search-overlay');
    const backdrop = document.getElementById('mobile-search-backdrop');
    const input = document.getElementById('mobile-search-input');
    if (overlay) {
        overlay.classList.remove('hidden');
        if (backdrop) backdrop.classList.remove('hidden');
        if (input) {
            setTimeout(() => {
                input.focus();
                input.select();
            }, 60);
        }
    }
}

function closeMobileSearch() {
    const overlay = document.getElementById('mobile-search-overlay');
    const backdrop = document.getElementById('mobile-search-backdrop');
    const dropdown = document.getElementById('mobile-search-results-dropdown');
    if (overlay) overlay.classList.add('hidden');
    if (backdrop) backdrop.classList.add('hidden');
    if (dropdown) dropdown.classList.add('hidden');
}

function clearMobileSearch() {
    const input = document.getElementById('mobile-search-input');
    const dropdown = document.getElementById('mobile-search-results-dropdown');
    if (input) {
        input.value = '';
        input.focus();
    }
    if (dropdown) {
        dropdown.innerHTML = '';
        dropdown.classList.add('hidden');
    }
}

// --- Keyboard Shortcuts ---
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        const active = document.activeElement;
        const isInput = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable);

        // Press '/' to search
        if (e.key === '/' && !isInput) {
            e.preventDefault();
            if (window.innerWidth < 1024) {
                openMobileSearch();
            } else {
                const searchInput = document.querySelector('#navbar-search-container input[name="q"]') || document.querySelector('input[name="q"]');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
        }

        // Press 'Escape' to dismiss search dropdown, navbar dropdowns, mobile overlay, or modal
        if (e.key === 'Escape') {
            closeAllNavbarDropdowns();
            closeMobileSearch();
            const shortcutsModal = document.getElementById('shortcuts-modal');
            if (shortcutsModal) shortcutsModal.classList.add('hidden');
        }

        // Press '?' to toggle shortcuts modal
        if (e.key === '?' && !isInput) {
            e.preventDefault();
            toggleShortcutsModal();
        }
    });
}

function toggleShortcutsModal() {
    let modal = document.getElementById('shortcuts-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'shortcuts-modal';
        modal.className = 'fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md transition-opacity';
        modal.innerHTML = `
            <div class="bg-gray-900 border border-gray-700/80 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-5">
                <div class="flex items-center justify-between border-b border-gray-800 pb-3">
                    <div class="flex items-center gap-2">
                        <span class="bg-brand-500 text-white text-xs font-black px-2 py-0.5 rounded">v2.4</span>
                        <h3 class="text-lg font-bold text-white">Keyboard Shortcuts</h3>
                    </div>
                    <button onclick="document.getElementById('shortcuts-modal').classList.add('hidden');" class="text-gray-400 hover:text-white text-xl font-bold p-1">&times;</button>
                </div>
                <div class="grid grid-cols-2 gap-3 text-sm">
                    <div class="flex items-center justify-between p-2 rounded bg-gray-950/60 border border-gray-800">
                        <span class="text-gray-300">Quick Search</span>
                        <kbd class="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs text-brand-400 font-mono font-bold">/</kbd>
                    </div>
                    <div class="flex items-center justify-between p-2 rounded bg-gray-950/60 border border-gray-800">
                        <span class="text-gray-300">Close Dialogs</span>
                        <kbd class="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 font-mono font-bold">Esc</kbd>
                    </div>
                    <div class="flex items-center justify-between p-2 rounded bg-gray-950/60 border border-gray-800">
                        <span class="text-gray-300">Play / Pause</span>
                        <kbd class="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 font-mono font-bold">Space / K</kbd>
                    </div>
                    <div class="flex items-center justify-between p-2 rounded bg-gray-950/60 border border-gray-800">
                        <span class="text-gray-300">Fullscreen</span>
                        <kbd class="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 font-mono font-bold">F</kbd>
                    </div>
                    <div class="flex items-center justify-between p-2 rounded bg-gray-950/60 border border-gray-800">
                        <span class="text-gray-300">Mute Audio</span>
                        <kbd class="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 font-mono font-bold">M</kbd>
                    </div>
                    <div class="flex items-center justify-between p-2 rounded bg-gray-950/60 border border-gray-800">
                        <span class="text-gray-300">Seek 10s</span>
                        <kbd class="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 font-mono font-bold">&larr; / &rarr;</kbd>
                    </div>
                    <div class="flex items-center justify-between p-2 rounded bg-gray-950/60 border border-gray-800">
                        <span class="text-gray-300">Bookmark Scene</span>
                        <kbd class="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs text-amber-400 font-mono font-bold">B</kbd>
                    </div>
                    <div class="flex items-center justify-between p-2 rounded bg-gray-950/60 border border-gray-800">
                        <span class="text-gray-300">Sleep Timer</span>
                        <kbd class="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs text-cyan-400 font-mono font-bold">Z</kbd>
                    </div>
                    <div class="flex items-center justify-between p-2 rounded bg-gray-950/60 border border-gray-800">
                        <span class="text-gray-300">Theater Mode</span>
                        <kbd class="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs text-purple-400 font-mono font-bold">T</kbd>
                    </div>
                    <div class="flex items-center justify-between p-2 rounded bg-gray-950/60 border border-gray-800">
                        <span class="text-gray-300">Picture-in-Pic</span>
                        <kbd class="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs text-emerald-400 font-mono font-bold">P</kbd>
                    </div>
                    <div class="flex items-center justify-between p-2 rounded bg-gray-950/60 border border-gray-800">
                        <span class="text-gray-300">Next Server</span>
                        <kbd class="px-2 py-0.5 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 font-mono font-bold">Alt + S</kbd>
                    </div>
                </div>
                <div class="text-center pt-2">
                    <p class="text-xs text-gray-400">Filvora Next-Gen Cinema Platform</p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.add('hidden');
        });
    } else {
        modal.classList.toggle('hidden');
    }
}

// --- Toast Notification System ---
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const isSuccess = type === 'success';
    
    toast.className = `toast-item flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl backdrop-blur-xl border ${
        isSuccess 
            ? 'bg-gray-900/95 border-emerald-500/40 text-white' 
            : 'bg-gray-900/95 border-brand-500/40 text-white'
    }`;
    
    toast.innerHTML = `
        <div class="w-2 h-2 rounded-full ${isSuccess ? 'bg-emerald-400' : 'bg-brand-500'} animate-ping"></div>
        <span class="text-xs sm:text-sm font-semibold">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%) scale(0.9)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- HTMX Interactive Feedback ---
function initHtmxFeedback() {
    document.body.addEventListener('htmx:afterSwap', (event) => {
        if (event.detail.target && event.detail.target.matches('button[hx-post*="/library/toggle/"]')) {
            const titleAttr = event.detail.target.getAttribute('title') || '';
            if (titleAttr.includes('Saved') || titleAttr.includes('Remove')) {
                showToast('✓ Updated your Watchlist', 'success');
            } else {
                showToast('Removed from Watchlist', 'info');
            }
        }
        if (event.detail.target && event.detail.target.classList.contains('continue-watching-card')) {
            showToast('Removed from Continue Watching', 'info');
        }
    });
}

// --- Horizontal Rails (Navigation & Grab-to-Scroll) ---
function initHorizontalRails() {
    const rails = document.querySelectorAll('.rail-container');

    rails.forEach((container) => {
        const track = container.querySelector('.rail-track');
        const prevBtn = container.querySelector('.rail-prev-btn');
        const nextBtn = container.querySelector('.rail-next-btn');

        if (!track) return;

        const updateArrows = () => {
            if (window.innerWidth < 768) return;
            const tolerance = 10;
            const maxScroll = track.scrollWidth - track.clientWidth;

            if (prevBtn) {
                if (track.scrollLeft <= tolerance) {
                    prevBtn.classList.add('opacity-0', 'pointer-events-none');
                } else {
                    prevBtn.classList.remove('opacity-0', 'pointer-events-none');
                }
            }

            if (nextBtn) {
                if (track.scrollLeft >= maxScroll - tolerance || maxScroll <= 0) {
                    nextBtn.classList.add('opacity-0', 'pointer-events-none');
                } else {
                    nextBtn.classList.remove('opacity-0', 'pointer-events-none');
                }
            }
        };

        const getScrollStep = () => Math.max(track.clientWidth * 0.75, 280);

        if (prevBtn) {
            prevBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                track.scrollBy({ left: -getScrollStep(), behavior: 'smooth' });
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                track.scrollBy({ left: getScrollStep(), behavior: 'smooth' });
            });
        }

        track.addEventListener('scroll', updateArrows, { passive: true });
        window.addEventListener('resize', updateArrows, { passive: true });

        updateArrows();
        setTimeout(updateArrows, 300);
        setTimeout(updateArrows, 1000);

        // --- Mouse Drag-To-Scroll ---
        let isDown = false;
        let startX = 0;
        let scrollStart = 0;
        let isDragging = false;
        let dragDistance = 0;

        track.addEventListener('mousedown', (e) => {
            if (e.button !== 0) return;
            isDown = true;
            isDragging = false;
            dragDistance = 0;
            startX = e.pageX - track.offsetLeft;
            scrollStart = track.scrollLeft;
        });

        const stopDrag = () => {
            if (!isDown) return;
            isDown = false;
            track.classList.remove('is-dragging');
            if (isDragging) {
                setTimeout(() => {
                    isDragging = false;
                }, 100);
            }
        };

        track.addEventListener('mouseleave', stopDrag);
        track.addEventListener('mouseup', stopDrag);

        track.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            const x = e.pageX - track.offsetLeft;
            const walk = (x - startX) * 1.5;
            dragDistance = Math.abs(walk);

            if (dragDistance > 6) {
                isDragging = true;
                track.classList.add('is-dragging');
            }

            if (isDragging) {
                e.preventDefault();
                track.scrollLeft = scrollStart - walk;
            }
        });

        track.addEventListener('click', (e) => {
            if (isDragging || dragDistance > 6) {
                e.preventDefault();
                e.stopPropagation();
            }
        }, true);
    });
}

// --- Dynamic Star Rating Hover Animation ---
function initStarRatingHover() {
    document.addEventListener('mouseover', (e) => {
        const btn = e.target.closest('.star-btn');
        if (!btn) return;
        const container = btn.closest('.star-rating-container');
        if (!container) return;
        const hoverVal = parseInt(btn.dataset.star || '0', 10);
        const stars = container.querySelectorAll('.star-btn');
        stars.forEach(s => {
            const val = parseInt(s.dataset.star || '0', 10);
            const svg = s.querySelector('svg');
            if (val <= hoverVal) {
                s.classList.add('text-yellow-400', 'scale-125');
                s.classList.remove('text-gray-600');
                if (svg) svg.classList.add('text-yellow-400');
            } else {
                s.classList.remove('text-yellow-400', 'scale-125');
                s.classList.add('text-gray-600');
                if (svg) svg.classList.remove('text-yellow-400');
            }
        });
    });

    document.addEventListener('mouseout', (e) => {
        const container = e.target.closest('.star-rating-container');
        if (!container) return;
        // Check if cursor actually left the container
        if (e.relatedTarget && container.contains(e.relatedTarget)) return;
        const currentScore = parseInt(container.dataset.score || '0', 10);
        const stars = container.querySelectorAll('.star-btn');
        stars.forEach(s => {
            const val = parseInt(s.dataset.star || '0', 10);
            const svg = s.querySelector('svg');
            s.classList.remove('scale-125');
            if (val <= currentScore) {
                s.classList.add('text-yellow-400');
                s.classList.remove('text-gray-600');
                if (svg) svg.classList.add('text-yellow-400');
            } else {
                s.classList.remove('text-yellow-400');
                s.classList.add('text-gray-600');
                if (svg) svg.classList.remove('text-yellow-400');
            }
        });
    });
}
initStarRatingHover();

// --- Responsive & Touch-Aware Dropdown Handlers (Vibe, Profile & Search) ---
function isDropdownVisible(el) {
    if (!el) return false;
    const style = window.getComputedStyle(el);
    return style.opacity === '1' && style.visibility !== 'hidden' && style.pointerEvents !== 'none';
}

function closeAllNavbarDropdowns() {
    closeVibeDropdown();
    closeProfileDropdown();
    const sDropdown = document.getElementById('search-results-dropdown');
    if (sDropdown) sDropdown.classList.add('hidden');
    const backdrop = document.getElementById('navbar-dropdown-backdrop');
    if (backdrop) backdrop.classList.add('hidden');
}

function toggleVibeDropdown(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    const wrapper = document.getElementById('vibe-dropdown-wrapper');
    const menu = document.getElementById('vibe-dropdown-menu');
    const btn = document.getElementById('vibe-dropdown-btn');
    const backdrop = document.getElementById('navbar-dropdown-backdrop');
    if (!wrapper || !menu) return;

    closeProfileDropdown();

    const currentlyVisible = wrapper.classList.contains('vibe-open') || 
                             (!wrapper.classList.contains('vibe-closed') && isDropdownVisible(menu));

    if (currentlyVisible) {
        wrapper.classList.remove('vibe-open');
        wrapper.classList.add('vibe-closed');
        if (backdrop) backdrop.classList.add('hidden');
        if (btn) btn.blur();
    } else {
        wrapper.classList.remove('vibe-closed');
        wrapper.classList.add('vibe-open');
        if (backdrop) backdrop.classList.remove('hidden');
    }
}

function closeVibeDropdown() {
    const wrapper = document.getElementById('vibe-dropdown-wrapper');
    const btn = document.getElementById('vibe-dropdown-btn');
    if (!wrapper) return;
    wrapper.classList.remove('vibe-open');
    wrapper.classList.add('vibe-closed');
    if (btn) btn.blur();
    const pWrap = document.getElementById('profile-dropdown-wrapper');
    const backdrop = document.getElementById('navbar-dropdown-backdrop');
    if (backdrop && (!pWrap || !pWrap.classList.contains('profile-open'))) {
        backdrop.classList.add('hidden');
    }
}

function toggleProfileDropdown(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    const wrapper = document.getElementById('profile-dropdown-wrapper');
    const menu = document.getElementById('profile-dropdown-menu');
    const btn = document.getElementById('profile-dropdown-btn');
    const backdrop = document.getElementById('navbar-dropdown-backdrop');
    if (!wrapper || !menu) return;

    closeVibeDropdown();

    const currentlyVisible = wrapper.classList.contains('profile-open') || 
                             (!wrapper.classList.contains('profile-closed') && isDropdownVisible(menu));

    if (currentlyVisible) {
        wrapper.classList.remove('profile-open');
        wrapper.classList.add('profile-closed');
        if (backdrop) backdrop.classList.add('hidden');
        if (btn) btn.blur();
    } else {
        wrapper.classList.remove('profile-closed');
        wrapper.classList.add('profile-open');
        if (backdrop) backdrop.classList.remove('hidden');
    }
}

function closeProfileDropdown() {
    const wrapper = document.getElementById('profile-dropdown-wrapper');
    const btn = document.getElementById('profile-dropdown-btn');
    if (!wrapper) return;
    wrapper.classList.remove('profile-open');
    wrapper.classList.add('profile-closed');
    if (btn) btn.blur();
    const vWrap = document.getElementById('vibe-dropdown-wrapper');
    const backdrop = document.getElementById('navbar-dropdown-backdrop');
    if (backdrop && (!vWrap || !vWrap.classList.contains('vibe-open'))) {
        backdrop.classList.add('hidden');
    }
}

// Reset hover state when cursor leaves the element on desktop (without closing click-opened state)
const vibeWrapperEl = document.getElementById('vibe-dropdown-wrapper');
if (vibeWrapperEl) {
    vibeWrapperEl.addEventListener('mouseleave', () => {
        if (!vibeWrapperEl.classList.contains('vibe-open')) {
            vibeWrapperEl.classList.remove('vibe-closed');
        }
    });
}

const profileWrapperEl = document.getElementById('profile-dropdown-wrapper');
if (profileWrapperEl) {
    profileWrapperEl.addEventListener('mouseleave', () => {
        if (!profileWrapperEl.classList.contains('profile-open')) {
            profileWrapperEl.classList.remove('profile-closed');
        }
    });
}

// Universal capture-phase outside-interaction listener to dismiss dropdowns immediately
// Pointerdown fires on mouse, touch, and pen before any element can swallow or stop bubbling
function handleOutsideNavbarDismiss(e) {
    const vWrap = document.getElementById('vibe-dropdown-wrapper');
    const pWrap = document.getElementById('profile-dropdown-wrapper');
    const sContainer = document.getElementById('navbar-search-container');
    const sDropdown = document.getElementById('search-results-dropdown');

    if (vWrap && !vWrap.contains(e.target)) {
        closeVibeDropdown();
    }
    if (pWrap && !pWrap.contains(e.target)) {
        closeProfileDropdown();
    }
    if (sContainer && sDropdown && !sContainer.contains(e.target)) {
        sDropdown.classList.add('hidden');
    }
}

document.addEventListener('pointerdown', handleOutsideNavbarDismiss, true);
document.addEventListener('click', handleOutsideNavbarDismiss, true);

// Dismiss dropdowns if user clicks an iframe (e.g. trailer player embed)
window.addEventListener('blur', () => {
    closeAllNavbarDropdowns();
});

// Ensure bfcache (back-forward cache) always restores fresh authenticated state when navigating back from video
window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
        window.location.reload();
    }
});

// --- Global CSRF Auto-Sync Engine ---
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function syncFormCsrfTokens() {
    const liveToken = getCookie('csrftoken');
    if (!liveToken) return;
    document.querySelectorAll('input[name="csrfmiddlewaretoken"]').forEach(input => {
        if (input.value !== liveToken) {
            input.value = liveToken;
        }
    });
}

function initCsrfSync() {
    // 1. Synchronize all CSRF inputs on initial load
    syncFormCsrfTokens();

    // 2. Intercept standard HTML form submissions on capture phase before any handler
    document.addEventListener('submit', (e) => {
        const form = e.target;
        if (!form || form.tagName !== 'FORM') return;

        const method = (form.getAttribute('method') || form.method || 'GET').toUpperCase();
        if (method !== 'POST') return;

        // Skip cross-origin submissions
        const action = form.getAttribute('action') || '';
        if (action.startsWith('http://') || action.startsWith('https://')) {
            if (!action.startsWith(window.location.origin)) return;
        }

        const liveToken = getCookie('csrftoken');
        if (liveToken) {
            let csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
            if (csrfInput) {
                csrfInput.value = liveToken;
            } else {
                csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = liveToken;
                form.appendChild(csrfInput);
            }
        }
    }, true);

    // 3. Re-sync on page visibility change or pageshow
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            syncFormCsrfTokens();
        }
    });
    window.addEventListener('pageshow', () => {
        syncFormCsrfTokens();
    });
}

// --- Ambient Network Connection Monitor ---
function initNetworkMonitor() {
    const indicator = document.getElementById('network-status-indicator');
    const badge = document.getElementById('network-status-badge');
    const dot = document.getElementById('network-status-dot');
    const text = document.getElementById('network-status-text');
    if (!indicator || !badge || !dot || !text) return;

    let hideTimeout = null;

    const showStatus = (isOnline) => {
        clearTimeout(hideTimeout);
        indicator.classList.remove('hidden');

        if (isOnline) {
            badge.className = 'px-3.5 py-1.5 rounded-full text-xs font-bold shadow-2xl backdrop-blur-xl border flex items-center gap-2 bg-emerald-950/90 border-emerald-500/40 text-emerald-300';
            dot.className = 'w-2 h-2 rounded-full bg-emerald-400';
            text.textContent = 'Connection Restored';
            // Auto hide after 3.5 seconds
            hideTimeout = setTimeout(() => {
                indicator.classList.add('hidden');
            }, 3500);
        } else {
            badge.className = 'px-3.5 py-1.5 rounded-full text-xs font-bold shadow-2xl backdrop-blur-xl border flex items-center gap-2 bg-red-950/95 border-red-500/50 text-red-300';
            dot.className = 'w-2 h-2 rounded-full bg-red-500 animate-ping';
            text.textContent = 'You are offline — Running in local mode';
        }
    };

    window.addEventListener('online', () => {
        showStatus(true);
        // If viewing an offline empty state, automatically reload to re-sync
        if (document.getElementById('offline-hero-billboard')) {
            setTimeout(() => {
                window.location.reload();
            }, 1200);
        }
    });

    window.addEventListener('offline', () => {
        showStatus(false);
    });

    // Check initial connectivity status
    if (typeof navigator.onLine !== 'undefined' && !navigator.onLine) {
        showStatus(false);
    }
}

// --- In-Card Quick Rating Popover & Star Hover Engine ---
function toggleCardRate(wrapperId) {
    const wrapper = document.getElementById(wrapperId);
    if (!wrapper) return;
    const popover = wrapper.querySelector('.quick-rate-popover');
    if (!popover) return;

    const isHidden = popover.classList.contains('hidden');

    // Dismiss any other open quick rating popovers first
    document.querySelectorAll('.quick-rate-popover:not(.hidden)').forEach(p => {
        if (p !== popover) p.classList.add('hidden');
    });

    if (isHidden) {
        popover.classList.remove('hidden');
    } else {
        popover.classList.add('hidden');
    }
}

function previewCardStars(starBtn, score) {
    const popover = starBtn.closest('.quick-rate-popover');
    if (!popover) return;
    const starBtns = popover.querySelectorAll('.star-opt');
    starBtns.forEach((btn, idx) => {
        if (idx < score) {
            btn.classList.add('text-yellow-400');
            btn.classList.remove('text-gray-500');
        } else {
            btn.classList.remove('text-yellow-400');
            btn.classList.add('text-gray-500');
        }
    });
}

function resetCardStars(popover) {
    if (!popover) return;
    const currentScore = parseInt(popover.getAttribute('data-score') || '0', 10);
    const starBtns = popover.querySelectorAll('.star-opt');
    starBtns.forEach((btn, idx) => {
        if (idx < currentScore) {
            btn.classList.add('text-yellow-400');
            btn.classList.remove('text-gray-500');
        } else {
            btn.classList.remove('text-yellow-400');
            btn.classList.add('text-gray-500');
        }
    });
}

// Global outside click / tap listener to close quick rating popovers
document.addEventListener('pointerdown', (e) => {
    if (!e.target.closest('.quick-rate-wrapper')) {
        document.querySelectorAll('.quick-rate-popover:not(.hidden)').forEach(p => p.classList.add('hidden'));
    }
}, true);

// --- Card Watch & Rating State Synchronization Engine ---
function setCardWatchButtonState(btn, isWatched) {
    if (!btn) return;
    if (isWatched) {
        btn.setAttribute('title', 'Watched (Click to unmark)');
        btn.className = 'w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center shadow-lg shadow-emerald-600/30 ring-1 ring-emerald-400/50 transition-all duration-200 transform hover:scale-110 active:scale-95 shrink-0';
        btn.innerHTML = '<svg class="w-3.5 h-3.5 sm:w-4 sm:h-4 fill-current" viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zm0 12.5c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>';
    } else {
        btn.setAttribute('title', 'Mark as Watched');
        btn.className = 'w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gray-900/90 hover:bg-emerald-950/40 hover:border-emerald-500/60 text-gray-400 hover:text-emerald-400 border border-gray-700/80 flex items-center justify-center shadow-lg transition-all duration-200 transform hover:scale-110 active:scale-95 shrink-0';
        btn.innerHTML = '<svg class="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>';
    }
}

function setCardWatchedState(id, mediaType, isWatched) {
    // 1. Mobile seen badges
    document.querySelectorAll(`.card-seen-mob-${id}, .saga-seen-mob-${id}`).forEach(el => {
        if (isWatched) el.classList.remove('hidden');
        else el.classList.add('hidden');
    });

    // 2. Desktop seen badges (uses !hidden to cleanly toggle visibility without breaking sm:block responsive hierarchy)
    document.querySelectorAll(`.card-seen-desk-${id}, .saga-seen-desk-${id}`).forEach(el => {
        if (isWatched) {
            el.classList.remove('!hidden', 'sm:hidden');
        } else {
            el.classList.add('!hidden');
        }
    });

    // 3. Card watch buttons
    document.querySelectorAll(`#card-watch-btn-${mediaType}-${id}, #card-watch-btn-movie-${id}, #card-watch-btn-tv-${id}`).forEach(btn => {
        setCardWatchButtonState(btn, isWatched);
    });

    // 4. Detail page watch button
    const detailBtn = document.getElementById(`detail-watch-btn-${id}`);
    if (detailBtn) {
        if (isWatched) {
            detailBtn.className = 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30 ring-1 ring-emerald-400/40 px-6 py-3.5 rounded-full font-bold text-sm sm:text-base flex items-center justify-center gap-2 transition shadow-lg backdrop-blur-md transform hover:scale-105 active:scale-95';
            detailBtn.innerHTML = '<svg class="h-5 w-5 fill-current" viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zm0 12.5c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg><span>Watched</span>';
        } else {
            detailBtn.className = 'bg-gray-900/90 hover:bg-gray-800 text-white border border-gray-700 px-6 py-3.5 rounded-full font-bold text-sm sm:text-base flex items-center justify-center gap-2 transition shadow-lg backdrop-blur-md transform hover:scale-105 active:scale-95';
            detailBtn.innerHTML = '<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg><span>Mark as Watched</span>';
        }
    }

    // 5. Narrative timeline segments in saga header
    document.querySelectorAll(`.saga-timeline-${id}`).forEach(seg => {
        const isCurrent = seg.getAttribute('data-is-current') === 'true';
        if (isWatched) {
            seg.classList.remove('bg-gray-600', 'bg-gray-800', 'bg-brand-500');
            seg.classList.add('bg-emerald-500', 'shadow-sm', 'shadow-emerald-500/50');
        } else {
            seg.classList.remove('bg-emerald-500', 'shadow-sm', 'shadow-emerald-500/50');
            if (isCurrent) {
                seg.classList.add('bg-brand-500', 'shadow-sm', 'shadow-brand-500/50');
            } else {
                seg.classList.add('bg-gray-800');
            }
        }
    });
}

function setCardRatingState(rateContainer, score) {
    if (!rateContainer) return;
    const popover = rateContainer.querySelector('.quick-rate-popover');
    if (popover) {
        popover.setAttribute('data-score', score);
        resetCardStars(popover);
    }
    const triggerBtn = rateContainer.querySelector('button[onclick*="toggleCardRate"]');
    if (triggerBtn) {
        if (score > 0) {
            triggerBtn.className = 'w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 border border-yellow-500/60 shadow-lg shadow-yellow-500/10 ring-1 ring-yellow-400/40 flex items-center justify-center gap-0.5 transition-all duration-200 transform hover:scale-110 active:scale-95';
            triggerBtn.title = `Your rating: ${score}/5 (Click to change)`;
            triggerBtn.innerHTML = `<svg class="w-3 h-3 sm:w-3.5 sm:h-3.5 fill-current" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg><span class="text-[9px] font-black leading-none">${score}</span>`;
        } else {
            triggerBtn.className = 'w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gray-900/90 hover:bg-yellow-950/40 hover:border-yellow-500/60 text-gray-400 hover:text-yellow-400 border border-gray-700/80 flex items-center justify-center shadow-lg transition-all duration-200 transform hover:scale-110 active:scale-95';
            triggerBtn.title = 'Rate with stars';
            triggerBtn.innerHTML = `<svg class="w-3.5 h-3.5 sm:w-4 sm:h-4 fill-current" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>`;
        }
    }
}

// Global HTMX Event Listeners for Live Watch & Rating Synchronization
document.body.addEventListener('watchChanged', (e) => {
    const data = e.detail;
    if (!data || !data.tmdb_id) return;
    setCardWatchedState(data.tmdb_id, data.media_type || 'movie', !!data.is_watched);
});

document.body.addEventListener('ratingChanged', (e) => {
    const data = e.detail;
    if (!data || !data.tmdb_id) return;
    const rateContainers = document.querySelectorAll(`#card-rate-${data.media_type || 'movie'}-${data.tmdb_id}`);
    rateContainers.forEach(container => {
        setCardRatingState(container, parseInt(data.score || 0, 10));
    });
});

document.body.addEventListener('sagaWatchedChanged', (e) => {
    const data = e.detail;
    if (!data || !data.movie_ids) return;
    const isWatched = !!data.is_all_watched;
    data.movie_ids.forEach(id => {
        setCardWatchedState(id, 'movie', isWatched);
    });
});

document.body.addEventListener('sagaRatingChanged', (e) => {
    const data = e.detail;
    if (!data || !data.movie_ids) return;
    const score = parseInt(data.score || 0, 10);
    data.movie_ids.forEach(id => {
        const rateContainers = document.querySelectorAll(`#card-rate-movie-${id}`);
        rateContainers.forEach(container => {
            setCardRatingState(container, score);
        });
    });
});

// --- Universal Card Click-to-Details Navigation ---
function navigateToCard(event, url) {
    if (!url || !event) return;
    // Disregard clicks inside buttons, links, inputs, or rating popover elements
    if (event.target.closest('button, a, input, select, textarea, .quick-rate-popover, .quick-rate-wrapper')) {
        return;
    }
    // Prevent navigation if the user was actively selecting text
    const selection = window.getSelection();
    if (selection && selection.toString().trim().length > 0) {
        return;
    }
    // Middle click or modifier keys (Ctrl/Cmd) open details in new tab
    if (event.ctrlKey || event.metaKey || event.button === 1) {
        window.open(url, '_blank');
    } else {
        window.location.href = url;
    }
}
window.navigateToCard = navigateToCard;
