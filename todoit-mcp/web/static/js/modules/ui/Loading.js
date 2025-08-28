/**
 * Loading State Manager
 * Centralized loading state management with modern UI
 */
class Loading {
    constructor() {
        this.loadingOverlay = null;
        this.isVisible = false;
        this.loadingCount = 0; // Track multiple concurrent loading states
        this.init();
    }
    
    init() {
        this.createOverlay();
    }
    
    createOverlay() {
        this.loadingOverlay = document.getElementById('loading');
        if (!this.loadingOverlay) {
            this.loadingOverlay = document.createElement('div');
            this.loadingOverlay.id = 'loading';
            this.loadingOverlay.className = 'loading-overlay';
            this.loadingOverlay.innerHTML = `
                <div class="loading-spinner"></div>
            `;
            document.body.appendChild(this.loadingOverlay);
        }
    }
    
    /**
     * Show loading overlay
     * @param {string} message - Optional loading message
     */
    show(message = null) {
        this.loadingCount++;
        
        if (!this.isVisible) {
            this.isVisible = true;
            this.loadingOverlay.classList.add('active');
            
            // Update message if provided
            if (message) {
                this.setMessage(message);
            }
            
            // Prevent scrolling when loading
            document.body.style.overflow = 'hidden';
        }
    }
    
    /**
     * Hide loading overlay
     */
    hide() {
        this.loadingCount = Math.max(0, this.loadingCount - 1);
        
        if (this.loadingCount === 0 && this.isVisible) {
            this.isVisible = false;
            this.loadingOverlay.classList.remove('active');
            
            // Restore scrolling
            document.body.style.overflow = '';
        }
    }
    
    /**
     * Force hide loading (useful for error states)
     */
    forceHide() {
        this.loadingCount = 0;
        this.hide();
    }
    
    /**
     * Set loading message
     */
    setMessage(message) {
        let messageEl = this.loadingOverlay.querySelector('.loading-message');
        
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.className = 'loading-message';
            this.loadingOverlay.appendChild(messageEl);
        }
        
        messageEl.textContent = message;
    }
    
    /**
     * Show loading for a specific element
     */
    showForElement(element, message = 'Ładowanie...') {
        if (!element) return;
        
        // Create or update element loading state
        let loadingEl = element.querySelector('.element-loading');
        
        if (!loadingEl) {
            loadingEl = document.createElement('div');
            loadingEl.className = 'element-loading';
            loadingEl.innerHTML = `
                <div class="element-loading-spinner"></div>
                <div class="element-loading-message">${message}</div>
            `;
            
            // Position relative to element
            const rect = element.getBoundingClientRect();
            loadingEl.style.position = 'absolute';
            loadingEl.style.top = '0';
            loadingEl.style.left = '0';
            loadingEl.style.right = '0';
            loadingEl.style.bottom = '0';
            loadingEl.style.background = 'rgba(255, 255, 255, 0.8)';
            loadingEl.style.backdropFilter = 'blur(2px)';
            loadingEl.style.display = 'flex';
            loadingEl.style.flexDirection = 'column';
            loadingEl.style.alignItems = 'center';
            loadingEl.style.justifyContent = 'center';
            loadingEl.style.zIndex = '1000';
            loadingEl.style.borderRadius = 'inherit';
            
            // Ensure parent has relative positioning
            if (getComputedStyle(element).position === 'static') {
                element.style.position = 'relative';
            }
            
            element.appendChild(loadingEl);
        } else {
            loadingEl.querySelector('.element-loading-message').textContent = message;
            loadingEl.style.display = 'flex';
        }
    }
    
    /**
     * Hide loading for a specific element
     */
    hideForElement(element) {
        if (!element) return;
        
        const loadingEl = element.querySelector('.element-loading');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }
    
    /**
     * Wrap an async operation with loading state
     */
    async wrap(asyncFn, message = 'Ładowanie...') {
        try {
            this.show(message);
            const result = await asyncFn();
            return result;
        } finally {
            this.hide();
        }
    }
    
    /**
     * Wrap an async operation for a specific element
     */
    async wrapElement(element, asyncFn, message = 'Ładowanie...') {
        try {
            this.showForElement(element, message);
            const result = await asyncFn();
            return result;
        } finally {
            this.hideForElement(element);
        }
    }
}

// Create singleton instance
const loading = new Loading();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Loading;
} else {
    window.Loading = Loading;
    window.loading = loading;
}