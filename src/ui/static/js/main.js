/**
 * Buchhaltung - Main JavaScript
 * Professional UI functionality
 */

// ============================================
// CSRF Token Handling
// ============================================
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// ============================================
// Global State
// ============================================
const state = {
    apiDataLoaded: false,
    apiRowCount: 0,
    theme: localStorage.getItem('theme') || 'light'
};

// ============================================
// Initialize on DOM Load
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initSidebar();
    checkApiStatus();
});

// ============================================
// Theme Management
// ============================================
function initTheme() {
    // Apply saved theme
    document.documentElement.setAttribute('data-bs-theme', state.theme);
    updateThemeIcon();
    
    // Theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-bs-theme', state.theme);
    localStorage.setItem('theme', state.theme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = state.theme === 'light' ? 'bi bi-moon-stars' : 'bi bi-sun';
        }
    }
}

// ============================================
// Sidebar Management
// ============================================
function initSidebar() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 992) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }
}

// ============================================
// API Status Check
// ============================================
async function checkApiStatus() {
    try {
        const response = await fetch('/api/check-api-data', {
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        const result = await response.json();
        
        state.apiDataLoaded = result.has_data;
        state.apiRowCount = result.row_count;
        
        updateApiStatus(result.has_data, result.has_data ? `${result.row_count} rows loaded` : 'No data loaded');
    } catch (error) {
        console.error('Error checking API status:', error);
        updateApiStatus(false, 'Connection error');
    }
}

function updateApiStatus(connected, text) {
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    
    if (statusDot) {
        statusDot.className = 'status-dot ' + (connected ? 'connected' : 'disconnected');
    }
    
    if (statusText) {
        statusText.textContent = text;
    }
    
    state.apiDataLoaded = connected;
}

// ============================================
// Toast Notifications
// ============================================
function showToast(type, message) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toastId = 'toast-' + Date.now();
    const iconClass = {
        'success': 'bi-check-circle-fill text-success',
        'error': 'bi-x-circle-fill text-danger',
        'warning': 'bi-exclamation-triangle-fill text-warning',
        'info': 'bi-info-circle-fill text-info'
    };
    
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    };
    
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi ${iconClass[type] || iconClass.info} me-2"></i>
                <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                <small>Just now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 4000
    });
    
    toast.show();
    
    // Remove from DOM after hidden
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

// ============================================
// Utility Functions
// ============================================
function formatCurrency(value, currency = '€') {
    return currency + value.toLocaleString('de-DE', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatNumber(value) {
    return value.toLocaleString('de-DE');
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('de-DE');
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ============================================
// Form Validation
// ============================================
function validateDateFormat(dateStr) {
    const regex = /^\d{2}\.\d{2}\.\d{4}$/;
    if (!regex.test(dateStr)) return false;
    
    const [day, month, year] = dateStr.split('.').map(Number);
    const date = new Date(year, month - 1, day);
    
    return date.getDate() === day &&
           date.getMonth() === month - 1 &&
           date.getFullYear() === year;
}

// ============================================
// Data Fetching Helpers
// ============================================
async function fetchJson(url, options = {}) {
    try {
        const csrfToken = getCSRFToken();
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// ============================================
// Loading State Helpers
// ============================================
function showLoading(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.style.display = 'block';
}

function hideLoading(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.style.display = 'none';
}

function showElement(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.style.display = 'block';
}

function hideElement(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.style.display = 'none';
}

// ============================================
// Button State Helpers
// ============================================
function setButtonLoading(button, loading, loadingText = 'Loading...') {
    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${loadingText}`;
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || button.innerHTML;
    }
}

// ============================================
// Chart Configuration
// ============================================
const chartConfig = {
    responsive: true,
    displayModeBar: false
};

const chartLayout = {
    font: {
        family: 'Inter, sans-serif'
    },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: {
        t: 40,
        b: 40,
        l: 60,
        r: 20
    }
};

// Update chart colors based on theme
function getChartColors() {
    const isDark = state.theme === 'dark';
    return {
        text: isDark ? '#E2E8F0' : '#1E293B',
        grid: isDark ? '#334155' : '#E2E8F0',
        background: isDark ? '#1E293B' : '#FFFFFF'
    };
}

// ============================================
// Export functions for global access
// ============================================
window.getCSRFToken = getCSRFToken;
window.showToast = showToast;
window.updateApiStatus = updateApiStatus;
window.checkApiStatus = checkApiStatus;
window.formatCurrency = formatCurrency;
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.formatFileSize = formatFileSize;
window.validateDateFormat = validateDateFormat;
window.fetchJson = fetchJson;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showElement = showElement;
window.hideElement = hideElement;
window.setButtonLoading = setButtonLoading;
window.chartConfig = chartConfig;
window.chartLayout = chartLayout;
window.getChartColors = getChartColors;