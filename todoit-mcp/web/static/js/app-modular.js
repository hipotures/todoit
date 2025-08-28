/**
 * TODOIT - Modular Application
 * Modern, modular architecture with improved UX
 */
class TodoApp {
    constructor() {
        this.currentView = 'lists';
        this.currentListKey = null;
        
        // Initialize modules
        this.api = window.api;
        this.toast = window.toast;
        this.loading = window.loading;
        // this.themeManager = window.themeManager;
        
        this.init();
    }
    
    async init() {
        try {
            await this.loading.wrap(async () => {
                this.setupEventListeners();
                await this.loadInitialData();
            }, 'Inicjalizacja aplikacji...');
        } catch (error) {
            this.toast.error('Błąd inicjalizacji aplikacji: ' + error.message);
        }
    }
    
    setupEventListeners() {
        // Header actions
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshCurrentView());
        }
        
        const configBtn = document.getElementById('config-btn');
        if (configBtn) {
            configBtn.addEventListener('click', () => this.showConfigModal());
        }
        
        // Navigation
        const backBtn = document.getElementById('back-to-lists');
        if (backBtn) {
            backBtn.addEventListener('click', () => this.showListsView());
        }
    }
    
    async loadInitialData() {
        // Load lists view by default
        await this.showListsView();
    }
    
    async showListsView() {
        this.currentView = 'lists';
        this.currentListKey = null;
        
        // Update UI
        document.getElementById('lists-view').style.display = 'block';
        document.getElementById('list-details-view').style.display = 'none';
        
        // Update breadcrumb
        const breadcrumb = document.getElementById('breadcrumb');
        if (breadcrumb) {
            breadcrumb.innerHTML = '<span class="breadcrumb-item active">📋 Wszystkie listy</span>';
        }
        
        // Load lists data
        try {
            const data = await this.api.getLists();
            this.renderListsTable(data);
            this.toast.success('Listy załadowane pomyślnie');
        } catch (error) {
            this.toast.error('Błąd ładowania list: ' + error.message);
        }
    }
    
    async showListDetailsView(listKey) {
        this.currentView = 'list-details';
        this.currentListKey = listKey;
        
        // Update UI
        document.getElementById('lists-view').style.display = 'none';
        document.getElementById('list-details-view').style.display = 'block';
        
        try {
            await this.loading.wrap(async () => {
                const [listData, itemsData] = await Promise.all([
                    this.api.getList(listKey),
                    this.api.getListItems(listKey)
                ]);
                
                // Update breadcrumb
                const breadcrumb = document.getElementById('breadcrumb');
                if (breadcrumb) {
                    breadcrumb.innerHTML = `
                        <span class="breadcrumb-item" onclick="app.showListsView()">📋 Wszystkie listy</span>
                        <span class="breadcrumb-separator"> › </span>
                        <span class="breadcrumb-item active">${listData.list_key}</span>
                    `;
                }
                
                // Update list info
                document.getElementById('list-title').textContent = listData.list_key;
                
                // Render items table
                this.renderItemsTable(itemsData);
                
                this.toast.success('Szczegóły listy załadowane');
            }, 'Ładowanie szczegółów listy...');
        } catch (error) {
            this.toast.error('Błąd ładowania szczegółów listy: ' + error.message);
            this.showListsView();
        }
    }
    
    renderListsTable(data) {
        // Simplified table rendering - in real implementation this would be more complex
        const tableContainer = document.getElementById('lists-table');
        if (!tableContainer) return;
        
        const lists = data.data || data.lists || [];
        tableContainer.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <p>Znaleziono ${lists.length} list.</p>
                    <div class="lists-grid">
                        ${lists.map(list => `
                            <div class="list-card card" onclick="app.showListDetailsView('${list.list_key}')">
                                <div class="card-body">
                                    <h3>${list.list_key}</h3>
                                    <p class="text-muted">${list.total_items || 0} itemów</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }
    
    renderItemsTable(data) {
        const tableContainer = document.getElementById('items-table');
        if (!tableContainer) return;
        
        const items = data.data || data.items || data || [];
        tableContainer.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <p>Znaleziono ${items.length || 0} itemów.</p>
                    <div class="items-list">
                        ${items.map(item => `
                            <div class="item-row">
                                <div class="item-key">${item.item_key}</div>
                                <div class="item-content">${item.content}</div>
                                <div class="status-badge status-${item.status}">${item.status}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }
    
    async refreshCurrentView() {
        if (this.currentView === 'lists') {
            await this.showListsView();
        } else if (this.currentView === 'list-details' && this.currentListKey) {
            await this.showListDetailsView(this.currentListKey);
        }
    }
    
    showConfigModal() {
        // TODO: Implement config modal
        this.toast.info('Konfiguracja będzie dostępna wkrótce');
    }
}

// Initialize app when all modules are loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for all modules to be ready
    const checkModules = () => {
        if (window.api && window.toast && window.loading) {
            window.app = new TodoApp();
        } else {
            setTimeout(checkModules, 50);
        }
    };
    
    checkModules();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TodoApp;
} else {
    window.TodoApp = TodoApp;
}