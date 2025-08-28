/**
 * Theme Manager - Dark/Light Mode Toggle
 */
class ThemeManager {
    constructor() {
        this.currentTheme = this.getInitialTheme();
        this.init();
    }
    
    init() {
        this.applyTheme(this.currentTheme);
        this.setupToggleButton();
        this.setupSystemThemeListener();
    }
    
    getInitialTheme() {
        // Check localStorage first
        const savedTheme = localStorage.getItem('todoit-theme');
        if (savedTheme && ['light', 'dark', 'auto'].includes(savedTheme)) {
            return savedTheme;
        }
        
        // Default to auto (system preference)
        return 'auto';
    }
    
    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    getEffectiveTheme() {
        if (this.currentTheme === 'auto') {
            return this.getSystemTheme();
        }
        return this.currentTheme;
    }
    
    applyTheme(theme) {
        const effectiveTheme = theme === 'auto' ? this.getSystemTheme() : theme;
        
        // Remove existing theme classes
        document.documentElement.classList.remove('theme-light', 'theme-dark');
        
        // Add new theme class
        document.documentElement.classList.add(`theme-${effectiveTheme}`);
        
        // Set data-theme attribute for CSS
        document.documentElement.setAttribute('data-theme', effectiveTheme);
        
        // Update theme toggle button
        this.updateToggleButton(theme);
        
        // Save to localStorage
        localStorage.setItem('todoit-theme', theme);
        
        this.currentTheme = theme;
    }
    
    updateToggleButton(theme) {
        const button = document.getElementById('theme-toggle');
        if (!button) return;
        
        const icons = {
            'light': '☀️',
            'dark': '🌙',
            'auto': '🌗'
        };
        
        const titles = {
            'light': 'Przełącz na tryb ciemny',
            'dark': 'Przełącz na tryb automatyczny',
            'auto': 'Przełącz na tryb jasny'
        };
        
        const effectiveTheme = this.getEffectiveTheme();
        button.textContent = icons[effectiveTheme];
        button.title = titles[theme];
    }
    
    setupToggleButton() {
        const button = document.getElementById('theme-toggle');
        if (!button) return;
        
        button.addEventListener('click', () => {
            this.cycleTheme();
        });
    }
    
    cycleTheme() {
        const themes = ['light', 'dark', 'auto'];
        const currentIndex = themes.indexOf(this.currentTheme);
        const nextTheme = themes[(currentIndex + 1) % themes.length];
        
        this.applyTheme(nextTheme);
        
        // Add subtle animation feedback
        const button = document.getElementById('theme-toggle');
        if (button) {
            button.style.transform = 'scale(0.9)';
            setTimeout(() => {
                button.style.transform = 'scale(1)';
            }, 150);
        }
    }
    
    setupSystemThemeListener() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            mediaQuery.addEventListener('change', () => {
                if (this.currentTheme === 'auto') {
                    this.applyTheme('auto');
                }
            });
        }
    }
    
    // Public API
    setTheme(theme) {
        if (['light', 'dark', 'auto'].includes(theme)) {
            this.applyTheme(theme);
        }
    }
    
    getTheme() {
        return this.currentTheme;
    }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}