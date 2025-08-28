/**
 * TODOIT Web Interface - Main JavaScript Application
 * Uses Tabulator for advanced table functionality with nested tables for subitems
 */

class TodoApp {
    constructor() {
        this.table = null;
        this.data = [];
        this.config = {};
        this.showFavoritesOnly = false;
        
        this.init();
    }

    async init() {
        await this.loadConfig();
        this.setupEventListeners();
        await this.loadData();
        this.initTable();
        this.hideLoading();
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const result = await response.json();
            if (result.success) {
                this.config = result.config;
                this.applyConfigToUI();
            }
        } catch (error) {
            console.error('Failed to load config:', error);
        }
    }

    applyConfigToUI() {
        // Apply column visibility to checkboxes
        Object.keys(this.config.columns).forEach(column => {
            const checkbox = document.getElementById(`col-${column.replace('_', '-')}`);
            if (checkbox) {
                checkbox.checked = this.config.columns[column];
            }
        });
    }

    async loadData() {
        this.showLoading();
        try {
            const response = await fetch('/api/lists');
            const result = await response.json();
            if (result.success) {
                this.data = result.data;
            } else {
                this.showToast('Błąd podczas ładowania danych', 'error');
            }
        } catch (error) {
            console.error('Failed to load data:', error);
            this.showToast('Błąd połączenia z serwerem', 'error');
        }
        this.hideLoading();
    }

    initTable() {
        const columns = this.getColumns();
        
        this.table = new Tabulator("#todo-table", {
            height: "calc(100vh - 200px)",
            data: this.data,
            layout: "fitColumns",
            responsiveLayout: "hide",
            columns: columns,
            pagination: "local",
            paginationSize: this.config.itemsPerPage || 50,
            paginationSizeSelector: [25, 50, 100, 200],
            movableColumns: true,
            resizableColumns: true,
            sortOrderReverse: true,
            
            // Nested table for subitems
            rowFormatter: (row) => {
                const data = row.getData();
                if (data.subitems && data.subitems.length > 0) {
                    this.createSubitemTable(row, data.subitems);
                }
            },

            // Row styling
            rowFormatter: (row) => {
                const data = row.getData();
                
                // Create subitems table if exists
                if (data.subitems && data.subitems.length > 0) {
                    this.createSubitemTable(row, data.subitems);
                }
                
                // Style row based on status
                const element = row.getElement();
                element.classList.add(`status-${data.status}`);
                
                if (data.is_favorite) {
                    element.classList.add('favorite-item');
                }
            },

            // Cell editing
            cellEdited: (cell) => {
                this.handleCellEdit(cell);
            },

            // Localization
            langs: {
                "pl": {
                    "pagination": {
                        "page_size": "Rozmiar strony",
                        "first": "Pierwsza",
                        "last": "Ostatnia",
                        "prev": "Poprzednia",
                        "next": "Następna"
                    }
                }
            },
            locale: "pl"
        });

        // Setup table event listeners
        this.setupTableEvents();
    }

    getColumns() {
        const columns = [
            {
                title: "⭐",
                field: "is_favorite",
                width: 50,
                hozAlign: "center",
                resizable: false,
                headerSort: false,
                responsive: 0,
                formatter: (cell) => {
                    const value = cell.getValue();
                    return value ? "⭐" : "☆";
                },
                cellClick: (e, cell) => {
                    this.toggleFavorite(cell.getRow().getData().list_key);
                }
            },
            {
                title: "Lista",
                field: "list_title",
                width: 150,
                responsive: 1,
                editor: false
            },
            {
                title: "Item",
                field: "item_key",
                width: 120,
                responsive: 2,
                editor: "input"
            },
            {
                title: "Treść",
                field: "content",
                minWidth: 200,
                responsive: 0,
                editor: "textarea",
                editorParams: {
                    verticalNavigation: "editor"
                }
            },
            {
                title: "Status",
                field: "status",
                width: 120,
                responsive: 1,
                editor: "list",
                editorParams: {
                    values: {
                        "pending": "Oczekujące",
                        "in_progress": "W trakcie",
                        "completed": "Ukończone",
                        "failed": "Nieudane"
                    }
                },
                formatter: (cell) => {
                    return this.formatStatus(cell.getValue());
                }
            },
            {
                title: "Pozycja",
                field: "position",
                width: 80,
                responsive: 4,
                hozAlign: "center",
                editor: "number"
            },
            {
                title: "Utworzono",
                field: "created_at",
                width: 140,
                responsive: 5,
                formatter: (cell) => {
                    return this.formatDate(cell.getValue());
                }
            },
            {
                title: "Zaktualizowano",
                field: "updated_at",
                width: 140,
                responsive: 6,
                formatter: (cell) => {
                    return this.formatDate(cell.getValue());
                }
            }
        ];

        // Filter columns based on config
        return columns.filter(col => {
            const fieldName = col.field;
            return this.config.columns[fieldName] !== false;
        });
    }

    createSubitemTable(parentRow, subitems) {
        // Remove existing nested table if any
        const existingNested = parentRow.getElement().querySelector('.nested-table');
        if (existingNested) {
            existingNested.remove();
        }

        // Create container for nested table
        const holderEl = document.createElement("div");
        const tableEl = document.createElement("div");
        
        holderEl.className = "nested-table";
        holderEl.style.padding = "10px 20px 10px 50px";
        holderEl.style.backgroundColor = "#f8f9fa";
        holderEl.style.borderLeft = "3px solid #007bff";
        
        holderEl.appendChild(tableEl);
        parentRow.getElement().appendChild(holderEl);

        // Create nested Tabulator table
        const subTable = new Tabulator(tableEl, {
            layout: "fitColumns",
            data: subitems,
            height: Math.min(200, subitems.length * 35 + 40), // Dynamic height
            columns: [
                {
                    title: "🔸 Subitem",
                    field: "item_key",
                    width: 120,
                    editor: "input"
                },
                {
                    title: "Treść",
                    field: "content",
                    editor: "textarea",
                    editorParams: {
                        verticalNavigation: "editor"
                    }
                },
                {
                    title: "Status",
                    field: "status",
                    width: 120,
                    editor: "list",
                    editorParams: {
                        values: {
                            "pending": "Oczekujące",
                            "in_progress": "W trakcie",
                            "completed": "Ukończone",
                            "failed": "Nieudane"
                        }
                    },
                    formatter: (cell) => {
                        return this.formatStatus(cell.getValue());
                    }
                }
            ],
            cellEdited: (cell) => {
                this.handleSubitemEdit(parentRow.getData(), cell);
            },
            rowFormatter: (row) => {
                const element = row.getElement();
                element.classList.add(`status-${row.getData().status}`);
            }
        });
    }

    setupTableEvents() {
        // Double-click to expand/collapse subitems
        this.table.on("rowDblClick", (e, row) => {
            const nestedTable = row.getElement().querySelector('.nested-table');
            if (nestedTable) {
                nestedTable.style.display = nestedTable.style.display === 'none' ? 'block' : 'none';
            }
        });
    }

    async handleCellEdit(cell) {
        const data = cell.getRow().getData();
        const field = cell.getField();
        const value = cell.getValue();

        try {
            const updateData = {};
            if (field === 'content') {
                updateData.content = value;
            } else if (field === 'status') {
                updateData.status = value;
            } else if (field === 'item_key') {
                // Handle item key rename - this would need a different endpoint
                this.showToast('Zmiana klucza itemu nie jest jeszcze obsługiwana', 'warning');
                return;
            }

            const response = await fetch(`/api/items/${data.list_key}/${data.item_key}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });

            const result = await response.json();
            if (result.success) {
                this.showToast('Zaktualizowano pomyślnie', 'success');
            } else {
                this.showToast('Błąd podczas aktualizacji', 'error');
                cell.restoreOldValue();
            }
        } catch (error) {
            console.error('Failed to update item:', error);
            this.showToast('Błąd połączenia', 'error');
            cell.restoreOldValue();
        }
    }

    async handleSubitemEdit(parentData, cell) {
        const subitemData = cell.getRow().getData();
        const field = cell.getField();
        const value = cell.getValue();

        try {
            const updateData = {};
            if (field === 'content') {
                updateData.content = value;
            } else if (field === 'status') {
                updateData.status = value;
            }

            const response = await fetch(`/api/subitems/${parentData.list_key}/${parentData.item_key}/${subitemData.item_key}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });

            const result = await response.json();
            if (result.success) {
                this.showToast('Subitem zaktualizowany', 'success');
            } else {
                this.showToast('Błąd podczas aktualizacji subitemu', 'error');
                cell.restoreOldValue();
            }
        } catch (error) {
            console.error('Failed to update subitem:', error);
            this.showToast('Błąd połączenia', 'error');
            cell.restoreOldValue();
        }
    }

    async toggleFavorite(listKey) {
        try {
            const response = await fetch(`/api/lists/${listKey}/favorite`, {
                method: 'POST'
            });

            const result = await response.json();
            if (result.success) {
                this.showToast(result.message, 'success');
                await this.refreshData();
            } else {
                this.showToast('Błąd podczas zmiany ulubionych', 'error');
            }
        } catch (error) {
            console.error('Failed to toggle favorite:', error);
            this.showToast('Błąd połączenia', 'error');
        }
    }

    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('search-input');
        searchInput.addEventListener('input', (e) => {
            this.filterTable(e.target.value);
        });

        // Status filter
        const statusFilter = document.getElementById('status-filter');
        statusFilter.addEventListener('change', (e) => {
            this.filterByStatus(e.target.value);
        });

        // Favorites toggle
        const favoritesToggle = document.getElementById('favorites-toggle');
        favoritesToggle.addEventListener('click', () => {
            this.toggleFavoritesFilter();
        });

        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        refreshBtn.addEventListener('click', () => {
            this.refreshData();
        });

        // Config modal
        const configBtn = document.getElementById('config-btn');
        const configModal = document.getElementById('config-modal');
        const closeBtns = configModal.querySelectorAll('.close-btn');
        
        configBtn.addEventListener('click', () => {
            configModal.style.display = 'block';
        });

        closeBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                configModal.style.display = 'none';
            });
        });

        // Save config
        const saveConfigBtn = document.getElementById('save-config');
        saveConfigBtn.addEventListener('click', () => {
            this.saveConfig();
        });

        // Close modal on outside click
        window.addEventListener('click', (e) => {
            if (e.target === configModal) {
                configModal.style.display = 'none';
            }
        });
    }

    filterTable(searchTerm) {
        if (!this.table) return;

        if (searchTerm.trim() === '') {
            this.table.clearFilter();
        } else {
            this.table.setFilter([
                {field: "list_title", type: "like", value: searchTerm},
                {field: "item_key", type: "like", value: searchTerm},
                {field: "content", type: "like", value: searchTerm}
            ]);
        }
    }

    filterByStatus(status) {
        if (!this.table) return;

        if (status === '') {
            this.table.removeFilter("status");
        } else {
            this.table.setFilter("status", "=", status);
        }
    }

    toggleFavoritesFilter() {
        if (!this.table) return;

        this.showFavoritesOnly = !this.showFavoritesOnly;
        const btn = document.getElementById('favorites-toggle');
        
        if (this.showFavoritesOnly) {
            this.table.setFilter("is_favorite", "=", true);
            btn.classList.add('active');
            btn.textContent = '⭐ Tylko ulubione';
        } else {
            this.table.removeFilter("is_favorite");
            btn.classList.remove('active');
            btn.textContent = '⭐ Ulubione';
        }
    }

    async refreshData() {
        await this.loadData();
        if (this.table) {
            this.table.setData(this.data);
        }
    }

    saveConfig() {
        // Collect column visibility settings
        const columns = {};
        document.querySelectorAll('[id^="col-"]').forEach(checkbox => {
            const fieldName = checkbox.id.replace('col-', '').replace('-', '_');
            columns[fieldName] = checkbox.checked;
        });

        this.config.columns = columns;

        // Save to server (in production)
        fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                columns: columns
            })
        }).then(response => response.json())
        .then(result => {
            if (result.success) {
                this.showToast('Konfiguracja zapisana', 'success');
                // Rebuild table with new column configuration
                this.table.destroy();
                this.initTable();
            }
        }).catch(error => {
            console.error('Failed to save config:', error);
            this.showToast('Błąd podczas zapisywania konfiguracji', 'error');
        });

        // Close modal
        document.getElementById('config-modal').style.display = 'none';
    }

    formatStatus(status) {
        const statusMap = {
            'pending': '<span class="status-badge status-pending">Oczekujące</span>',
            'in_progress': '<span class="status-badge status-in-progress">W trakcie</span>',
            'completed': '<span class="status-badge status-completed">Ukończone</span>',
            'failed': '<span class="status-badge status-failed">Nieudane</span>'
        };
        return statusMap[status] || status;
    }

    formatDate(dateString) {
        if (!dateString) return '';
        try {
            return new Date(dateString).toLocaleDateString('pl-PL', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateString;
        }
    }

    showLoading() {
        document.getElementById('loading').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Show toast
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remove toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => container.removeChild(toast), 300);
        }, 3000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TodoApp();
});