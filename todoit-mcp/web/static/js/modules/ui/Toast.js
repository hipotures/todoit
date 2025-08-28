/**
 * Toast Notification System
 * Modern toast notifications with animations
 */
class Toast {
    constructor() {
        this.container = null;
        this.toasts = new Map();
        this.autoRemoveDelay = 5000; // 5 seconds
        this.init();
    }
    
    init() {
        this.createContainer();
    }
    
    createContainer() {
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }
    
    /**
     * Show a toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, error, warning, info)
     * @param {number} duration - Auto-remove delay in ms (0 = never)
     * @returns {string} Toast ID for manual removal
     */
    show(message, type = 'info', duration = this.autoRemoveDelay) {
        const toastId = this.generateId();
        const toast = this.createToast(toastId, message, type);
        
        this.container.appendChild(toast);
        this.toasts.set(toastId, toast);
        
        // Animate in
        requestAnimationFrame(() => {
            toast.classList.add('animate-slideIn');
        });
        
        // Auto-remove
        if (duration > 0) {
            setTimeout(() => {
                this.remove(toastId);
            }, duration);
        }
        
        return toastId;
    }
    
    /**
     * Create toast element
     */
    createToast(id, message, type) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('data-toast-id', id);
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${icons[type] || icons.info}</span>
                <span class="toast-message">${message}</span>
                <button class="toast-close" aria-label="Zamknij">×</button>
            </div>
        `;
        
        // Add close button functionality
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.remove(id);
        });
        
        // Click to dismiss
        toast.addEventListener('click', (e) => {
            if (e.target !== closeBtn) {
                this.remove(id);
            }
        });
        
        return toast;
    }
    
    /**
     * Remove toast by ID
     */
    remove(toastId) {
        const toast = this.toasts.get(toastId);
        if (!toast) return;
        
        // Animate out
        toast.style.transform = 'translateX(100%)';
        toast.style.opacity = '0';
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            this.toasts.delete(toastId);
        }, 300);
    }
    
    /**
     * Remove all toasts
     */
    clear() {
        for (const toastId of this.toasts.keys()) {
            this.remove(toastId);
        }
    }
    
    /**
     * Convenience methods
     */
    success(message, duration) {
        return this.show(message, 'success', duration);
    }
    
    error(message, duration = 0) { // Errors don't auto-hide by default
        return this.show(message, 'error', duration);
    }
    
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }
    
    info(message, duration) {
        return this.show(message, 'info', duration);
    }
    
    /**
     * Generate unique ID
     */
    generateId() {
        return `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}

// Create singleton instance
const toast = new Toast();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Toast;
} else {
    window.Toast = Toast;
    window.toast = toast;
}