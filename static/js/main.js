// Main JavaScript file for Ceramica HR Management System
// Handles common functionality across all pages

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // Initialize current time display
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);

    // Form validation enhancements
    setupFormValidation();

    // Search functionality
    setupSearchHandlers();

    // Print functionality
    setupPrintHandlers();

    // Data table enhancements
    setupDataTableEnhancements();

    console.log('Ceramica HR System initialized successfully');
});

/**
 * Updates the current time display if element exists
 */
function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        const options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            locale: 'fr-MA'
        };
        timeElement.textContent = now.toLocaleDateString('fr-MA', options);
    }
}

/**
 * Enhanced form validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Real-time validation feedback
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (input.checkValidity()) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
            }
        });
    });
}

/**
 * Search functionality enhancements
 */
function setupSearchHandlers() {
    const searchInputs = document.querySelectorAll('input[type="search"], input[name="search"]');
    
    searchInputs.forEach(function(input) {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const searchTerm = input.value;
            
            // Debounce search to avoid too many requests
            searchTimeout = setTimeout(function() {
                if (searchTerm.length >= 2 || searchTerm.length === 0) {
                    // Auto-submit search form or trigger search function
                    const form = input.closest('form');
                    if (form && searchTerm.length >= 2) {
                        // Show loading indicator
                        showLoadingState(form);
                    }
                }
            }, 500);
        });
    });
}

/**
 * Print functionality setup
 */
function setupPrintHandlers() {
    const printButtons = document.querySelectorAll('[onclick*="print"], .btn-print');
    
    printButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Add print-specific classes
            document.body.classList.add('print-mode');
            
            // Print after a short delay to allow CSS to load
            setTimeout(function() {
                window.print();
                document.body.classList.remove('print-mode');
            }, 100);
        });
    });
}

/**
 * Data table enhancements
 */
function setupDataTableEnhancements() {
    const tables = document.querySelectorAll('.table');
    
    tables.forEach(function(table) {
        // Add row hover effects
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(function(row) {
            row.addEventListener('mouseenter', function() {
                row.style.backgroundColor = 'var(--bs-light)';
            });
            
            row.addEventListener('mouseleave', function() {
                row.style.backgroundColor = '';
            });
        });

        // Add click-to-select functionality for data rows
        rows.forEach(function(row, index) {
            row.addEventListener('click', function(e) {
                // Skip if clicking on action buttons
                if (e.target.closest('.btn') || e.target.closest('a')) {
                    return;
                }
                
                // Toggle row selection
                row.classList.toggle('table-active');
            });
        });
    });
}

/**
 * Show loading state for forms
 */
function showLoadingState(element) {
    const submitButton = element.querySelector('button[type="submit"]');
    if (submitButton) {
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Chargement...';
        submitButton.disabled = true;
        
        // Re-enable after 3 seconds (fallback)
        setTimeout(function() {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }, 3000);
    }
}

/**
 * Confirmation dialogs for delete actions
 */
function confirmDelete(message = 'Êtes-vous sûr de vouloir supprimer cet élément ?') {
    return confirm(message);
}

/**
 * Show success toast notification
 */
function showSuccessToast(message) {
    showToast(message, 'success');
}

/**
 * Show error toast notification
 */
function showErrorToast(message) {
    showToast(message, 'danger');
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);

    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 4000 });
    toast.show();

    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

/**
 * Format currency for Morocco (MAD)
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-MA', {
        style: 'currency',
        currency: 'MAD'
    }).format(amount);
}

/**
 * Format date for Morocco
 */
function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    const formatOptions = { ...defaultOptions, ...options };
    
    return new Intl.DateTimeFormat('fr-MA', formatOptions).format(new Date(date));
}

/**
 * Validate CIN (Moroccan National ID)
 */
function validateCIN(cin) {
    // Basic CIN validation for Morocco
    const cinPattern = /^[A-Z]{1,2}\d{6}$/;
    return cinPattern.test(cin.toUpperCase());
}

/**
 * Validate phone number (Morocco format)
 */
function validatePhoneNumber(phone) {
    // Morocco phone number patterns
    const mobilePattern = /^(\+212|0)[6-7]\d{8}$/;
    const landlinePattern = /^(\+212|0)[5]\d{8}$/;
    
    return mobilePattern.test(phone) || landlinePattern.test(phone);
}

/**
 * Auto-resize textareas
 */
function autoResizeTextareas() {
    const textareas = document.querySelectorAll('textarea');
    
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
}

/**
 * Initialize employee avatar placeholders
 */
function initializeAvatars() {
    const avatars = document.querySelectorAll('.employee-avatar');
    
    avatars.forEach(function(avatar) {
        const name = avatar.dataset.name;
        if (name && !avatar.innerHTML) {
            const initials = name.split(' ').map(n => n[0]).join('').substr(0, 2);
            avatar.textContent = initials.toUpperCase();
        }
    });
}

/**
 * Keyboard shortcuts
 */
document.addEventListener('keydown', function(e) {
    // Ctrl+S to save forms
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        const form = document.querySelector('form');
        if (form) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.click();
            }
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(function(modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
});

// Export functions for global use
window.HRSystem = {
    showSuccessToast,
    showErrorToast,
    confirmDelete,
    formatCurrency,
    formatDate,
    validateCIN,
    validatePhoneNumber,
    showLoadingState
};

// Initialize additional features when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    autoResizeTextareas();
    initializeAvatars();
    
    // Add fade-in animation to main content
    const main = document.querySelector('main');
    if (main) {
        main.classList.add('fade-in');
    }
});
