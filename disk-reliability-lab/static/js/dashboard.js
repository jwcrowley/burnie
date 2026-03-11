/**
 * Disk Reliability Lab - Dashboard JavaScript
 * Common functionality for all dashboard pages
 */

// ============================================================================
// Theme Management
// ============================================================================

(function() {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
    const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');

    // Initialize theme
    function initTheme() {
        // Check localStorage or system preference
        if (localStorage.getItem('color-theme') === 'dark' ||
            (!('color-theme' in localStorage) &&
             window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
            themeToggleLightIcon.classList.remove('hidden');
        } else {
            document.documentElement.classList.remove('dark');
            themeToggleDarkIcon.classList.remove('hidden');
        }
    }

    // Toggle theme
    function toggleTheme() {
        themeToggleDarkIcon.classList.toggle('hidden');
        themeToggleLightIcon.classList.toggle('hidden');

        if (localStorage.getItem('color-theme')) {
            if (localStorage.getItem('color-theme') === 'light') {
                document.documentElement.classList.add('dark');
                localStorage.setItem('color-theme', 'dark');
            } else {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('color-theme', 'light');
            }
        } else {
            if (document.documentElement.classList.contains('dark')) {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('color-theme', 'light');
            } else {
                document.documentElement.classList.add('dark');
                localStorage.setItem('color-theme', 'dark');
            }
        }

        // Trigger chart updates if Chart.js is loaded
        if (typeof Chart !== 'undefined') {
            const isDark = document.documentElement.classList.contains('dark');
            Chart.defaults.color = isDark ? '#9ca3af' : '#6b7280';
            Chart.defaults.borderColor = isDark ? '#374151' : '#e5e7eb';
        }
    }

    // Initialize on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initTheme();
            if (themeToggleBtn) {
                themeToggleBtn.addEventListener('click', toggleTheme);
            }
        });
    } else {
        initTheme();
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', toggleTheme);
        }
    }
})();

// ============================================================================
// Mobile Menu
// ============================================================================

(function() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
})();

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Format bytes to human readable format
 */
function formatBytes(bytes, decimals = 1) {
    if (!bytes || bytes === 0) return '-';

    const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const value = bytes / Math.pow(k, i);

    return value.toFixed(decimals) + ' ' + units[i];
}

/**
 * Format date to readable string
 */
function formatDate(dateString) {
    if (!dateString) return '-';

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

    return date.toLocaleDateString();
}

/**
 * Format duration in seconds to readable string
 */
function formatDuration(seconds) {
    if (!seconds) return '-';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

/**
 * Debounce function for search inputs
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Get score color class based on value
 */
function getScoreColor(score) {
    if (score >= 90) return 'score-high';
    if (score >= 70) return 'score-medium';
    if (score >= 50) return 'score-low';
    return 'score-critical';
}

/**
 * Get status color class
 */
function getStatusColor(status) {
    const colors = {
        'passed': 'status-passed',
        'failed': 'status-failed',
        'testing': 'status-testing',
        'pending': 'status-pending',
        'running': 'status-testing'
    };
    return colors[status] || 'status-unknown';
}

// ============================================================================
// Chart.js Helpers
// ============================================================================

/**
 * Create default chart options for the current theme
 */
function getDefaultChartOptions() {
    const isDark = document.documentElement.classList.contains('dark');
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: isDark ? '#9ca3af' : '#6b7280'
                }
            }
        },
        scales: {
            x: {
                ticks: {
                    color: isDark ? '#9ca3af' : '#6b7280'
                },
                grid: {
                    color: isDark ? '#374151' : '#e5e7eb'
                }
            },
            y: {
                ticks: {
                    color: isDark ? '#9ca3af' : '#6b7280'
                },
                grid: {
                    color: isDark ? '#374151' : '#e5e7eb'
                }
            }
        }
    };
}

/**
 * Update chart colors when theme changes
 */
function updateChartTheme(chart) {
    if (!chart) return;

    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#9ca3af' : '#6b7280';
    const gridColor = isDark ? '#374151' : '#e5e7eb';

    // Update options
    chart.options.plugins.legend.labels.color = textColor;
    if (chart.options.scales.x) {
        chart.options.scales.x.ticks.color = textColor;
        chart.options.scales.x.grid.color = gridColor;
    }
    if (chart.options.scales.y) {
        chart.options.scales.y.ticks.color = textColor;
        chart.options.scales.y.grid.color = gridColor;
    }

    chart.update('none'); // Update without animation
}

// ============================================================================
// HTMX Event Handlers
// ============================================================================

document.body.addEventListener('htmx:afterRequest', function(evt) {
    // Hide loading indicators
    const loadingIndicators = document.querySelectorAll('.htmx-indicator');
    loadingIndicators.forEach(indicator => {
        indicator.style.display = 'none';
    });
});

document.body.addEventListener('htmx:beforeRequest', function(evt) {
    // Show loading indicators for the target
    const target = evt.detail.target;
    if (target) {
        const indicator = target.querySelector('.htmx-indicator');
        if (indicator) {
            indicator.style.display = 'inline';
        }
    }
});

// ============================================================================
// Auto-refresh functionality
// ============================================================================

/**
 * Setup auto-refresh for a container
 */
function setupAutoRefresh(containerId, url, intervalSeconds) {
    const container = document.getElementById(containerId);
    if (!container) return;

    setInterval(() => {
        // Only refresh if the page is visible
        if (!document.hidden) {
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    container.innerHTML = html;
                })
                .catch(error => {
                    console.error('Auto-refresh error:', error);
                });
        }
    }, intervalSeconds * 1000);
}

// ============================================================================
// Keyboard shortcuts
// ============================================================================

document.addEventListener('keydown', function(evt) {
    // Ctrl/Cmd + K for search focus
    if ((evt.ctrlKey || evt.metaKey) && evt.key === 'k') {
        evt.preventDefault();
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="Search"], input[placeholder*="serial"]');
        if (searchInput) {
            searchInput.focus();
        }
    }

    // Escape to close modals
    if (evt.key === 'Escape') {
        const modals = document.querySelectorAll('[id$="-modal"]');
        modals.forEach(modal => {
            if (!modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
            }
        });
    }
});

// ============================================================================
// Page visibility handling
// ============================================================================

document.addEventListener('visibilitychange', function() {
    // Pause/resume auto-refresh based on visibility
    if (document.hidden) {
        document.body.dataset.paused = 'true';
    } else {
        document.body.dataset.paused = 'false';
        // Trigger a refresh for important containers
        const statsContainer = document.getElementById('stats-overview');
        if (statsContainer && typeof htmx !== 'undefined') {
            htmx.trigger(statsContainer, 'refresh');
        }
    }
});

// ============================================================================
// Initialize on page load
// ============================================================================

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

function init() {
    // Initialize any charts on the page
    if (typeof initializeCharts === 'function') {
        initializeCharts();
    }

    // Setup any auto-refresh containers
    // Call setupAutoRefresh for specific containers as needed
}

// ============================================================================
// Export utilities
// ============================================================================

/**
 * Export data as CSV file
 */
function exportAsCSV(data, filename) {
    const csv = dataToCSV(data);
    downloadFile(csv, filename, 'text/csv');
}

/**
 * Convert JSON data to CSV string
 */
function dataToCSV(data) {
    if (!data || data.length === 0) return '';

    const headers = Object.keys(data[0]);
    const csvRows = [];

    // Add headers
    csvRows.push(headers.join(','));

    // Add data rows
    for (const row of data) {
        const values = headers.map(header => {
            const value = row[header];
            // Escape quotes and wrap in quotes if contains comma
            const escaped = String(value || '').replace(/"/g, '""');
            return `"${escaped}"`;
        });
        csvRows.push(values.join(','));
    }

    return csvRows.join('\n');
}

/**
 * Download file with given content
 */
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

console.log('Disk Reliability Lab Dashboard initialized');
