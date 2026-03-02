/**
 * HTMX Navigation Enhancement Module
 * 
 * Features:
 * - Progress bar animation during HTMX requests
 * - Active navigation item highlighting
 * - Toast notifications for errors and confirmations
 * - HTMX event handling (beforeRequest, afterRequest, error)
 * - Loading state management
 * - Confirm dialog handling for destructive actions
 * - Graceful degradation when JS is disabled
 * 
 * @module Navigation
 * @version 1.0.0
 */

(function() {
    'use strict';

    // ==========================================================================
    // Configuration
    // ==========================================================================
    
    const CONFIG = {
        // Progress bar settings
        progressBar: {
            height: '3px',
            color: '#0053e2', // wm-blue-100
            colorError: '#ea1100', // wm-red-100
            animationDuration: 200
        },
        // Toast notification settings
        toast: {
            duration: 5000,
            maxVisible: 5,
            position: 'top-right'
        },
        // Navigation settings
        nav: {
            activeClass: 'bg-wm-blue-110',
            selector: 'nav a[href]'
        },
        // HTMX indicator settings
        indicator: {
            showDelay: 50, // ms before showing indicator
            hideDelay: 100 // ms before hiding indicator
        }
    };

    // ==========================================================================
    // State Management
    // ==========================================================================
    
    const state = {
        requestCount: 0,
        activeToasts: [],
        progressBar: null,
        isNavigating: false
    };

    // ==========================================================================
    // Progress Bar
    // ==========================================================================
    
    /**
     * Creates and manages the top progress bar
     */
    const ProgressBar = {
        element: null,
        
        /**
         * Initialize the progress bar
         */
        init() {
            // Check if already exists
            this.element = document.getElementById('htmx-progress-bar');
            if (this.element) return;

            // Create progress bar element
            this.element = document.createElement('div');
            this.element.id = 'htmx-progress-bar';
            this.element.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                height: ${CONFIG.progressBar.height};
                background: ${CONFIG.progressBar.color};
                width: 0%;
                z-index: 9999;
                transition: width ${CONFIG.progressBar.animationDuration}ms ease-out;
                box-shadow: 0 0 10px ${CONFIG.progressBar.color};
            `;
            
            document.body.appendChild(this.element);
        },

        /**
         * Start the progress bar animation
         */
        start() {
            if (!this.element) this.init();
            
            // Reset and start animation
            this.element.style.transition = 'none';
            this.element.style.width = '0%';
            this.element.style.background = CONFIG.progressBar.color;
            
            // Force reflow
            this.element.offsetHeight;
            
            // Animate to 70% (will complete on finish)
            requestAnimationFrame(() => {
                this.element.style.transition = `width ${CONFIG.progressBar.animationDuration * 3}ms ease-out`;
                this.element.style.width = '70%';
            });
        },

        /**
         * Complete the progress bar animation
         */
        finish() {
            if (!this.element) return;
            
            // Complete to 100%
            this.element.style.transition = `width ${CONFIG.progressBar.animationDuration}ms ease-out`;
            this.element.style.width = '100%';
            
            // Hide after completion
            setTimeout(() => {
                this.element.style.transition = 'opacity 200ms ease-out';
                this.element.style.opacity = '0';
                
                setTimeout(() => {
                    this.element.style.width = '0%';
                    this.element.style.opacity = '1';
                }, 200);
            }, CONFIG.progressBar.animationDuration);
        },

        /**
         * Show error state on progress bar
         */
        error() {
            if (!this.element) return;
            
            this.element.style.background = CONFIG.progressBar.colorError;
            this.element.style.width = '100%';
            this.element.style.boxShadow = `0 0 10px ${CONFIG.progressBar.colorError}`;
            
            setTimeout(() => {
                this.element.style.transition = 'opacity 200ms ease-out';
                this.element.style.opacity = '0';
                
                setTimeout(() => {
                    this.element.style.width = '0%';
                    this.element.style.opacity = '1';
                    this.element.style.background = CONFIG.progressBar.color;
                    this.element.style.boxShadow = `0 0 10px ${CONFIG.progressBar.color}`;
                }, 200);
            }, 500);
        }
    };

    // ==========================================================================
    // Toast Notifications
    // ==========================================================================
    
    /**
     * Creates and manages toast notifications
     */
    const Toast = {
        container: null,
        
        /**
         * Initialize toast container
         */
        init() {
            this.container = document.getElementById('toast-container');
            if (this.container) return;

            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.setAttribute('aria-live', 'polite');
            this.container.setAttribute('aria-atomic', 'true');
            
            const position = CONFIG.toast.position;
            const positionStyles = {
                'top-right': 'top: 1rem; right: 1rem;',
                'top-left': 'top: 1rem; left: 1rem;',
                'bottom-right': 'bottom: 1rem; right: 1rem;',
                'bottom-left': 'bottom: 1rem; left: 1rem;'
            };
            
            this.container.style.cssText = `
                position: fixed;
                ${positionStyles[position]}
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
                max-width: 400px;
                pointer-events: none;
            `;
            
            document.body.appendChild(this.container);
        },

        /**
         * Show a toast notification
         * @param {string} message - Toast message
         * @param {string} type - Toast type: success, error, warning, info
         * @param {number} duration - Duration in ms (optional)
         */
        show(message, type = 'info', duration = CONFIG.toast.duration) {
            if (!this.container) this.init();
            
            // Limit visible toasts
            while (state.activeToasts.length >= CONFIG.toast.maxVisible) {
                const oldest = state.activeToasts.shift();
                if (oldest) oldest.remove();
            }
            
            // Create toast element
            const toast = document.createElement('div');
            toast.setAttribute('role', 'alert');
            toast.style.pointerEvents = 'auto';
            
            // Styles based on type
            const styles = {
                success: {
                    bg: 'bg-green-50',
                    border: 'border-green-400',
                    text: 'text-green-800',
                    icon: 'text-green-400',
                    iconPath: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
                },
                error: {
                    bg: 'bg-red-50',
                    border: 'border-red-400',
                    text: 'text-red-800',
                    icon: 'text-red-400',
                    iconPath: 'M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z'
                },
                warning: {
                    bg: 'bg-yellow-50',
                    border: 'border-yellow-400',
                    text: 'text-yellow-800',
                    icon: 'text-yellow-400',
                    iconPath: 'M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z'
                },
                info: {
                    bg: 'bg-blue-50',
                    border: 'border-blue-400',
                    text: 'text-blue-800',
                    icon: 'text-blue-400',
                    iconPath: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
                }
            };
            
            const style = styles[type] || styles.info;
            
            toast.className = `
                ${style.bg} border-l-4 ${style.border} ${style.text}
                p-4 rounded shadow-lg flex items-start gap-3
                transform transition-all duration-300 ease-out
                translate-x-full opacity-0
            `;
            
            toast.innerHTML = `
                <svg class="w-5 h-5 ${style.icon} flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${style.iconPath}"/>
                </svg>
                <div class="flex-1">
                    <p class="text-sm font-medium">${this.escapeHtml(message)}</p>
                </div>
                <button type="button" class="text-gray-400 hover:text-gray-600 flex-shrink-0" aria-label="Close">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            `;
            
            // Add close handler
            const closeBtn = toast.querySelector('button');
            closeBtn.addEventListener('click', () => this.dismiss(toast));
            
            // Add to container and track
            this.container.appendChild(toast);
            state.activeToasts.push(toast);
            
            // Animate in
            requestAnimationFrame(() => {
                toast.classList.remove('translate-x-full', 'opacity-0');
            });
            
            // Auto-dismiss
            if (duration > 0) {
                setTimeout(() => this.dismiss(toast), duration);
            }
            
            return toast;
        },

        /**
         * Dismiss a toast notification
         * @param {HTMLElement} toast - Toast element to dismiss
         */
        dismiss(toast) {
            toast.classList.add('translate-x-full', 'opacity-0');
            
            setTimeout(() => {
                toast.remove();
                const index = state.activeToasts.indexOf(toast);
                if (index > -1) state.activeToasts.splice(index, 1);
            }, 300);
        },

        /**
         * Escape HTML to prevent XSS
         * @param {string} text - Text to escape
         * @returns {string} Escaped text
         */
        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        // Convenience methods
        success(message, duration) { return this.show(message, 'success', duration); },
        error(message, duration) { return this.show(message, 'error', duration); },
        warning(message, duration) { return this.show(message, 'warning', duration); },
        info(message, duration) { return this.show(message, 'info', duration); }
    };

    // ==========================================================================
    // Navigation Highlighting
    // ==========================================================================
    
    /**
     * Manages active navigation state
     */
    const Navigation = {
        /**
         * Initialize navigation highlighting
         */
        init() {
            this.highlightCurrentPage();
            
            // Update on popstate (back/forward buttons)
            window.addEventListener('popstate', () => this.highlightCurrentPage());
        },

        /**
         * Highlight the current page in navigation
         */
        highlightCurrentPage() {
            const currentPath = window.location.pathname;
            const navLinks = document.querySelectorAll(CONFIG.nav.selector);
            
            navLinks.forEach(link => {
                const href = link.getAttribute('href');
                if (!href) return;
                
                // Remove existing active classes
                link.classList.remove('bg-wm-blue-110');
                link.classList.remove('text-white');
                link.removeAttribute('aria-current');
                
                // Check if this link matches current path
                const isActive = href === currentPath || 
                                (href !== '/' && currentPath.startsWith(href));
                
                if (isActive) {
                    link.classList.add('bg-wm-blue-110');
                    link.classList.add('text-white');
                    link.setAttribute('aria-current', 'page');
                }
            });
        },

        /**
         * Update navigation after HTMX navigation
         * @param {string} path - New path
         */
        update(path) {
            // Update URL without triggering navigation
            window.history.pushState({}, '', path);
            this.highlightCurrentPage();
        }
    };

    // ==========================================================================
    // Confirm Dialog
    // ==========================================================================
    
    /**
     * Handles custom confirm dialogs for destructive actions
     */
    const ConfirmDialog = {
        /**
         * Show a confirmation dialog
         * @param {string} message - Confirmation message
         * @param {Function} onConfirm - Callback when confirmed
         * @param {Function} onCancel - Callback when cancelled (optional)
         */
        show(message, onConfirm, onCancel) {
            // Create modal
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 z-[10001] flex items-center justify-center p-4';
            modal.innerHTML = `
                <div class="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity" aria-hidden="true"></div>
                <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6 transform transition-all">
                    <div class="flex items-start gap-4">
                        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                            <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                            </svg>
                        </div>
                        <div class="flex-1">
                            <h3 class="text-lg font-semibold text-gray-900">Confirm Action</h3>
                            <p class="text-sm text-gray-500 mt-1">${Toast.escapeHtml(message)}</p>
                            <div class="flex justify-end gap-3 mt-6">
                                <button type="button" class="cancel-btn px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                                    Cancel
                                </button>
                                <button type="button" class="confirm-btn px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                                    Confirm
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Focus trap
            const confirmBtn = modal.querySelector('.confirm-btn');
            const cancelBtn = modal.querySelector('.cancel-btn');
            confirmBtn.focus();
            
            // Event handlers
            const close = () => modal.remove();
            
            confirmBtn.addEventListener('click', () => {
                close();
                if (onConfirm) onConfirm();
            });
            
            cancelBtn.addEventListener('click', () => {
                close();
                if (onCancel) onCancel();
            });
            
            // Close on backdrop click
            modal.querySelector('.fixed.inset-0').addEventListener('click', () => {
                close();
                if (onCancel) onCancel();
            });
            
            // Keyboard handling
            modal.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    close();
                    if (onCancel) onCancel();
                }
            });
        }
    };

    // ==========================================================================
    // HTMX Event Handlers
    // ==========================================================================
    
    /**
     * Initialize HTMX event listeners
     */
    function initHtmxEvents() {
        if (typeof htmx === 'undefined') {
            console.warn('HTMX not loaded - navigation enhancements disabled');
            return;
        }

        // Before request starts
        document.body.addEventListener('htmx:beforeRequest', (event) => {
            state.requestCount++;
            
            // Show progress bar on first request
            if (state.requestCount === 1) {
                ProgressBar.start();
            }
            
            // Show loading indicator for this element
            const el = event.detail.elt;
            el.classList.add('htmx-requesting');
        });

        // After request completes
        document.body.addEventListener('htmx:afterRequest', (event) => {
            state.requestCount = Math.max(0, state.requestCount - 1);
            
            // Complete progress bar when all requests done
            if (state.requestCount === 0) {
                ProgressBar.finish();
            }
            
            // Remove loading indicator
            const el = event.detail.elt;
            el.classList.remove('htmx-requesting');
            
            // Update navigation on successful navigation
            if (event.detail.successful && event.detail.xhr) {
                const url = event.detail.xhr.responseURL || window.location.href;
                const path = new URL(url).pathname;
                Navigation.update(path);
            }
        });

        // Request error
        document.body.addEventListener('htmx:responseError', (event) => {
            state.requestCount = Math.max(0, state.requestCount - 1);
            ProgressBar.error();
            
            const xhr = event.detail.xhr;
            let message = 'An error occurred while processing your request.';
            
            if (xhr.status === 404) {
                message = 'The requested resource was not found.';
            } else if (xhr.status === 403) {
                message = 'You do not have permission to perform this action.';
            } else if (xhr.status === 500) {
                message = 'A server error occurred. Please try again later.';
            } else if (xhr.status === 0) {
                message = 'Network error. Please check your connection.';
            }
            
            Toast.error(message);
            
            const el = event.detail.elt;
            el.classList.remove('htmx-requesting');
        });

        // Network error
        document.body.addEventListener('htmx:sendError', (event) => {
            state.requestCount = Math.max(0, state.requestCount - 1);
            ProgressBar.error();
            Toast.error('Network error. Please check your connection and try again.');
            
            const el = event.detail.elt;
            el.classList.remove('htmx-requesting');
        });

        // Timeout
        document.body.addEventListener('htmx:timeout', (event) => {
            state.requestCount = Math.max(0, state.requestCount - 1);
            ProgressBar.error();
            Toast.error('Request timed out. Please try again.');
            
            const el = event.detail.elt;
            el.classList.remove('htmx-requesting');
        });

        // Confirm prompt
        document.body.addEventListener('htmx:confirm', (event) => {
            if (event.detail.elt.hasAttribute('hx-confirm')) {
                event.preventDefault();
                
                const message = event.detail.elt.getAttribute('hx-confirm');
                ConfirmDialog.show(
                    message,
                    () => event.detail.issueRequest(true),
                    () => {
                        // Cancelled
                        const el = event.detail.elt;
                        el.classList.remove('htmx-requesting');
                    }
                );
            }
        });

        // After swap (content updated)
        document.body.addEventListener('htmx:afterSwap', (event) => {
            // Re-initialize any dynamic content
            if (event.detail.target) {
                // Update page title if provided in response headers or meta
                const title = event.detail.target.querySelector('title');
                if (title) {
                    document.title = title.textContent;
                }
            }
        });

        // Before swap - handle navigation
        document.body.addEventListener('htmx:beforeSwap', (event) => {
            // Check if this is a full page navigation
            if (event.detail.target === document.body || 
                event.detail.target.closest('main') === document.querySelector('main')) {
                // Scroll to top for page navigations
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    }

    // ==========================================================================
    // Accessibility Enhancements
    // ==========================================================================
    
    /**
     * Initialize accessibility features
     */
    function initAccessibility() {
        // Announce page changes to screen readers
        const announcer = document.createElement('div');
        announcer.id = 'page-announcer';
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'sr-only';
        document.body.appendChild(announcer);

        // Announce navigation
        document.body.addEventListener('htmx:afterSwap', (event) => {
            if (event.detail.target === document.querySelector('main')) {
                const title = document.title || 'Page updated';
                announcer.textContent = `Navigated to ${title}`;
            }
        });
    }

    // ==========================================================================
    // No-JS Fallback Handling
    // ==========================================================================
    
    /**
     * Ensure forms work without JavaScript
     */
    function initNoJsFallback() {
        // Add .no-js class when JS is disabled (removed when JS loads)
        document.documentElement.classList.remove('no-js');
        
        // Ensure links with hx-boost have proper href
        document.querySelectorAll('[hx-boost="true"] a[href]').forEach(link => {
            // Already has href, good for fallback
            if (!link.getAttribute('href')) {
                console.warn('Link missing href for no-js fallback:', link);
            }
        });
    }

    // ==========================================================================
    // Initialization
    // ==========================================================================
    
    /**
     * Initialize the navigation module
     */
    function init() {
        // Initialize components
        ProgressBar.init();
        Navigation.init();
        initHtmxEvents();
        initAccessibility();
        initNoJsFallback();
        
        // Expose utilities globally for template use
        window.NavigationUtils = {
            Toast,
            ProgressBar,
            Navigation,
            ConfirmDialog
        };
        
        console.log('HTMX Navigation Enhancement initialized');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
