// CanoBookHub Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Search functionality
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                // Auto-submit search after 500ms of no typing
                if (searchInput.value.length > 2) {
                    searchInput.form.submit();
                }
            }, 500);
        });
    }

    // Add to cart functionality
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
    addToCartButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const bookId = this.dataset.bookId;
            const originalText = this.innerHTML;
            
            // Show loading state
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
            this.disabled = true;
            
            fetch(`/add_to_cart/${bookId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.innerHTML = '<i class="fas fa-check"></i> Added!';
                    this.classList.remove('btn-primary');
                    this.classList.add('btn-success');
                    
                    // Update cart count
                    updateCartCount();
                    
                    // Show success message
                    showToast('Book added to cart successfully!', 'success');
                    
                    // Reset button after 2 seconds
                    setTimeout(() => {
                        this.innerHTML = originalText;
                        this.classList.remove('btn-success');
                        this.classList.add('btn-primary');
                        this.disabled = false;
                    }, 2000);
                } else {
                    this.innerHTML = originalText;
                    this.disabled = false;
                    showToast('Error adding book to cart', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.innerHTML = originalText;
                this.disabled = false;
                showToast('Error adding book to cart', 'error');
            });
        });
    });

    // Quantity update in cart
    const quantityInputs = document.querySelectorAll('.quantity-input');
    quantityInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const cartItemId = this.dataset.cartItemId;
            const quantity = this.value;
            
            fetch(`/update_cart_quantity/${cartItemId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ quantity: quantity })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update total price
                    location.reload();
                } else {
                    showToast('Error updating quantity', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error updating quantity', 'error');
            });
        });
    });

    // Book filtering
    const filterForm = document.querySelector('.filter-form');
    if (filterForm) {
        const filterInputs = filterForm.querySelectorAll('select, input');
        filterInputs.forEach(function(input) {
            input.addEventListener('change', function() {
                filterForm.submit();
            });
        });
    }

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.querySelector('.file-preview');
                    if (preview) {
                        preview.innerHTML = `
                            <img src="${e.target.result}" alt="Preview" class="img-fluid" style="max-height: 200px;">
                        `;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Dynamic form fields
    const dynamicForms = document.querySelectorAll('.dynamic-form');
    dynamicForms.forEach(function(form) {
        const addButton = form.querySelector('.add-field');
        const removeButton = form.querySelector('.remove-field');
        
        if (addButton) {
            addButton.addEventListener('click', function() {
                const fieldContainer = form.querySelector('.field-container');
                const fieldCount = fieldContainer.children.length;
                
                const newField = document.createElement('div');
                newField.className = 'mb-3';
                newField.innerHTML = `
                    <input type="text" class="form-control" name="field_${fieldCount}" placeholder="New field">
                `;
                fieldContainer.appendChild(newField);
            });
        }
        
        if (removeButton) {
            removeButton.addEventListener('click', function() {
                const fieldContainer = form.querySelector('.field-container');
                const lastField = fieldContainer.lastElementChild;
                if (lastField && fieldContainer.children.length > 1) {
                    lastField.remove();
                }
            });
        }
    });

    // Infinite scroll for book listings
    const bookContainer = document.querySelector('.book-container');
    if (bookContainer) {
        let page = 1;
        let loading = false;
        
        window.addEventListener('scroll', function() {
            if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 1000) {
                if (!loading) {
                    loading = true;
                    loadMoreBooks();
                }
            }
        });
        
        function loadMoreBooks() {
            page++;
            const url = new URL(window.location);
            url.searchParams.set('page', page);
            
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newBooks = doc.querySelectorAll('.book-card');
                    
                    newBooks.forEach(book => {
                        bookContainer.appendChild(book);
                    });
                    
                    loading = false;
                })
                .catch(error => {
                    console.error('Error loading more books:', error);
                    loading = false;
                });
        }
    }

    // Dashboard statistics animation
    const statNumbers = document.querySelectorAll('.stat-number');
    statNumbers.forEach(function(element) {
        const target = parseInt(element.textContent);
        const duration = 2000; // 2 seconds
        const increment = target / (duration / 16); // 60fps
        let current = 0;
        
        const timer = setInterval(function() {
            current += increment;
            if (current >= target) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
            }
        }, 16);
    });

    // Advanced search toggle
    const advancedSearchToggle = document.querySelector('.advanced-search-toggle');
    if (advancedSearchToggle) {
        advancedSearchToggle.addEventListener('click', function() {
            const advancedFields = document.querySelector('.advanced-search-fields');
            if (advancedFields) {
                advancedFields.style.display = advancedFields.style.display === 'none' ? 'block' : 'none';
            }
        });
    }

    // Book comparison
    const compareCheckboxes = document.querySelectorAll('.compare-checkbox');
    let selectedBooks = [];
    
    compareCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const bookId = this.dataset.bookId;
            
            if (this.checked) {
                if (selectedBooks.length < 3) {
                    selectedBooks.push(bookId);
                } else {
                    this.checked = false;
                    showToast('You can only compare up to 3 books', 'warning');
                }
            } else {
                selectedBooks = selectedBooks.filter(id => id !== bookId);
            }
            
            updateCompareButton();
        });
    });
    
    function updateCompareButton() {
        const compareButton = document.querySelector('.compare-button');
        if (compareButton) {
            compareButton.style.display = selectedBooks.length > 1 ? 'block' : 'none';
            compareButton.textContent = `Compare ${selectedBooks.length} Books`;
        }
    }
});

// Utility functions
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

function updateCartCount() {
    fetch('/cart/count')
        .then(response => response.json())
        .then(data => {
            const cartCount = document.querySelector('.cart-count');
            if (cartCount) {
                cartCount.textContent = data.count;
            }
        })
        .catch(error => {
            console.error('Error updating cart count:', error);
        });
}

function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

function formatPrice(price) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(price);
}

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

// Export for external use
window.CanoBookHub = {
    showToast,
    updateCartCount,
    formatPrice,
    debounce
};

// Analytics tracking (if needed)
function trackEvent(eventName, properties = {}) {
    // This can be extended to integrate with analytics services
    console.log('Event:', eventName, properties);
}

// Performance monitoring
window.addEventListener('load', function() {
    const loadTime = performance.now();
    console.log('Page loaded in', loadTime, 'ms');
});

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    // Can be extended to report errors to a logging service
});

// Service worker registration (for PWA features)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('ServiceWorker registered');
            })
            .catch(error => {
                console.log('ServiceWorker registration failed');
            });
    });
}
