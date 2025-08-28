/**
 * TODOIT Web Interface - New Hierarchical Architecture
 * Two-level view: Lists → List Details with Items
 */

class TodoAppNew {
    constructor() {
        this.currentView = 'lists';
        this.currentListKey = null;
        this.listsTable = null;
        this.itemsTable = null;
        this.currentPage = 0;
        this.pageSize = 20;
        this.searchTerm = '';
        this.showFavoritesOnly = false;
        this.selectedTag = '';
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.showListsView();
        this.hideLoading();
    }

    setupEventListeners() {
        // Helper to safely bind events
        const bind = (id, evt, handler) => {
            const el = document.getElementById(id);
            if (el && el.addEventListener) el.addEventListener(evt, handler);
        };

        // Global error guard (throttled) – ignore benign ResizeObserver noise
        if (!window.__todoit_error_guard_installed__) {
            window.__todoit_error_guard_installed__ = true;
            let lastErrTs = 0;
            window.addEventListener('error', (e) => {
                const message = (e && e.message) || '';
                if (message && message.includes('ResizeObserver loop')) return; // ignore
                const now = Date.now();
                if (now - lastErrTs < 1500) return; // throttle
                lastErrTs = now;
                try {
                    const cont = document.getElementById('toast-container') || document.body;
                    const msg = document.createElement('div');
                    msg.style.cssText = 'position:fixed;bottom:12px;right:12px;background:#fee;border:1px solid #f99;color:#900;padding:8px 10px;border-radius:6px;z-index:9999;font:12px/1.3 system-ui';
                    msg.textContent = 'Błąd JS: ' + (message || 'nieznany');
                    cont.appendChild(msg);
                    setTimeout(() => msg.remove(), 4000);
                } catch (_) {}
            });
        }

        // Navigation
        bind('back-to-lists', 'click', () => this.showListsView());

        // Lists view controls
        bind('lists-search', 'input', (e) => { this.searchTerm = e.target.value; this.loadListsData(); });

        bind('lists-favorites-toggle', 'click', () => {
            this.showFavoritesOnly = !this.showFavoritesOnly;
            const btn = document.getElementById('lists-favorites-toggle');
            if (this.showFavoritesOnly) {
                btn.classList.add('active');
                btn.textContent = '⭐ Tylko ulubione';
            } else {
                btn.classList.remove('active');
                btn.textContent = '⭐ Ulubione';
            }
            this.saveFilters(); // Zapisz filtry
            this.loadListsData();
        });

        // Tag filter
        bind('lists-tag-filter', 'change', (e) => {
            this.selectedTag = e.target.value;
            this.currentPage = 0; // Reset to first page
            this.saveFilters(); // Zapisz filtry
            this.loadListsData();
        });

        // Edit properties button
        bind('edit-properties', 'click', () => { if (this.currentListKey) this.showPropertiesModal(this.currentListKey); });

        // Items view controls
        bind('items-search', 'input', (e) => { if (this.itemsTable) this.itemsTable.setFilter('content', 'like', e.target.value); });

        bind('items-status-filter', 'change', (e) => {
            if (!this.itemsTable) return;
            if (e.target.value === '') this.itemsTable.removeFilter('status');
            else this.itemsTable.setFilter('status', '=', e.target.value);
        });

        // Config modal (keep existing functionality)
        const configModal = document.getElementById('config-modal');
        bind('config-btn', 'click', () => { if (configModal) configModal.style.display = 'block'; });
        if (configModal) {
            configModal.querySelectorAll('.close-btn').forEach(btn => btn.addEventListener('click', () => { configModal.style.display = 'none'; }));
            window.addEventListener('click', (e) => { if (e.target === configModal) configModal.style.display = 'none'; });
        }
    }

    async showListsView() {
        this.currentView = 'lists';
        this.currentListKey = null;
        
        // Update UI
        document.getElementById('lists-view').style.display = 'block';
        document.getElementById('list-details-view').style.display = 'none';
        
        // Update breadcrumb
        const breadcrumb = document.getElementById('breadcrumb');
        breadcrumb.innerHTML = '<span class="breadcrumb-item active">📋 Wszystkie listy</span>';
        
        await this.initListsTable();
        await this.loadTagsData();
        this.restoreFilters(); // Przywróć zapisane filtry
        await this.loadListsData();
    }

    async showListDetailsView(listKey) {
        this.currentView = 'list-details';
        this.currentListKey = listKey;
        
        // Update UI
        document.getElementById('lists-view').style.display = 'none';
        document.getElementById('list-details-view').style.display = 'block';
        
        try {
            // Load list details
            const response = await fetch(`/api/lists/${listKey}`);
            const result = await response.json();
            
            if (result.success) {
                const list = result.list;
                
                // Update breadcrumb
                const breadcrumb = document.getElementById('breadcrumb');
                breadcrumb.innerHTML = `
                    <span class="breadcrumb-item" id="back-to-lists-breadcrumb">📋 Wszystkie listy</span>
                    <span class="breadcrumb-separator"> → </span>
                    <span class="breadcrumb-item active">📄 ${list.title}</span>
                `;
                
                // Add click handler for breadcrumb
                document.getElementById('back-to-lists-breadcrumb').addEventListener('click', () => {
                    this.showListsView();
                });
                
                // Update list header
                document.getElementById('list-title').textContent = list.title;
                document.getElementById('list-description').textContent = list.description || '';
                
                // Load and display all properties
                try {
                    const propsResponse = await fetch(`/api/lists/${listKey}/properties`);
                    const propsResult = await propsResponse.json();
                    
                    const propertiesEl = document.getElementById('list-properties');
                    propertiesEl.innerHTML = '';
                    
                    if (propsResult.success && propsResult.properties && Object.keys(propsResult.properties).length > 0) {
                        Object.entries(propsResult.properties).forEach(([key, value]) => {
                            const tag = document.createElement('span');
                            tag.className = `property-tag ${key === 'is_favorite' ? 'favorite' : ''}`;
                            tag.textContent = `${key}=${value}`;
                            propertiesEl.appendChild(tag);
                        });
                    } else {
                        propertiesEl.innerHTML = '<span style="color: #999; font-style: italic;">brak properties</span>';
                    }
                } catch (error) {
                    const propertiesEl = document.getElementById('list-properties');
                    propertiesEl.innerHTML = '<span style="color: #999;">błąd ładowania properties</span>';
                }
                
                await this.initItemsTable();
                await this.loadItemsData();
                
            } else {
                this.showToast('Błąd podczas ładowania szczegółów listy', 'error');
                this.showListsView();
            }
        } catch (error) {
            this.showToast('Błąd połączenia', 'error');
            this.showListsView();
        }
    }

    async initListsTable() {
        if (this.listsTable) {
            this.listsTable.destroy();
        }

        
        // Check if Tabulator is available
        if (typeof Tabulator === 'undefined') {
            this.createFallbackTable();
            return;
        }
        
        this.listsTable = new Tabulator("#lists-table", {
            height: "auto",
            layout: "fitData",
            autoResize: true,
            responsiveLayout: "hide",
            responsiveLayoutCollapseStartOpen: false,
            placeholder: "Brak list do wyświetlenia",
            selectable: true,
            initialSort: [
                {column: "list_key", dir: "asc"}
            ],
            columns: [
                {
                    title: "⭐",
                    field: "is_favorite",
                    hozAlign: "center",
                    formatter: (cell) => cell.getValue() ? "⭐" : "☆",
                    cellClick: (e, cell) => {
                        this.toggleFavorite(cell.getRow().getData().list_key);
                    }
                },
                {
                    title: "🔑 Klucz",
                    field: "list_key",
                    formatter: (cell) => {
                        return `<code style="font-size: 0.85em; color: #666;">${cell.getValue()}</code>`;
                    }
                },
                {
                    title: "📋 Lista",
                    field: "title",
                    formatter: (cell, formatterParams, onRendered) => {
                        const data = cell.getRow().getData();
                        return `<strong style="cursor: pointer;">${data.title}</strong>` + 
                               (data.description ? `<br><small style="color: #666;">${data.description}</small>` : '');
                    },
                    cellClick: (e, cell) => {
                        const listKey = cell.getRow().getData().list_key;
                        this.showListDetailsView(listKey);
                    }
                },
                {
                    title: "📊 Postęp",
                    field: "completion_percentage",
                    formatter: (cell) => {
                        const percentage = cell.getValue();
                        return `<div style="display: flex; align-items: center; gap: 8px;">
                            <div class="progress-bar" style="flex: 1; height: 12px;">
                                <div class="progress-fill" style="width: ${percentage}%; height: 100%;"></div>
                            </div>
                            <small style="white-space: nowrap;">${percentage}%</small>
                        </div>`;
                    }
                },
                {
                    title: "📈 Statusy",
                    field: "status_counts",
                    formatter: (cell, formatterParams, onRendered) => {
                        const data = cell.getRow().getData();
                        return `
                            <div class="status-counts">
                                ${data.pending_items > 0 ? `<span class="status-count pending"><span class="dot"></span>${data.pending_items}</span>` : ''}
                                ${data.in_progress_items > 0 ? `<span class="status-count in-progress"><span class="dot"></span>${data.in_progress_items}</span>` : ''}
                                ${data.completed_items > 0 ? `<span class="status-count completed"><span class="dot"></span>${data.completed_items}</span>` : ''}
                                ${data.failed_items > 0 ? `<span class="status-count failed"><span class="dot"></span>${data.failed_items}</span>` : ''}
                            </div>
                        `;
                    }
                },
                {
                    title: "🔢 Itemy",
                    field: "total_items",
                    hozAlign: "center"
                },
                {
                    title: "📅 Ostatnia aktywność",
                    field: "updated_at",
                    formatter: (cell) => {
                        return this.formatDate(cell.getValue());
                    }
                },
                {
                    title: "⚙️ Properties",
                    field: "properties_count",
                    resizable: true,
                    hozAlign: "center",
                    formatter: (cell) => {
                        return '<span class="expand-props">⚙️</span>';
                    },
                    cellClick: (e, cell) => {
                        e.stopPropagation(); // Prevent row click
                        this.toggleListProperties(cell.getRow());
                    }
                }
            ],
            rowClick: (e, row) => {
                e.stopPropagation();
                const listKey = row.getData().list_key;
                this.showListDetailsView(listKey);
            },
            rowSelected: (row) => {
                const listKey = row.getData().list_key;
                this.showListDetailsView(listKey);
            },
            rowDblClick: (e, row) => {
                // Double-click to open list properties modal
                const listKey = row.getData().list_key;
                this.showPropertiesModal(listKey);
            },
            locale: "pl"
        });
        
        // Removed aggressive resize redraw to prevent jitter/loops.
    }

    async initItemsTable() {
        if (this.itemsTable) {
            this.itemsTable.destroy();
        }

        // Graceful fallback when Tabulator is unavailable or fails to init
        if (typeof Tabulator === 'undefined') {
            this.itemsTable = null;
            const el = document.getElementById('items-table');
            if (el) {
                el.innerHTML = '<div class="fallback" style="padding: 12px; color: #555;">Tabulator niedostępny – wyświetlam prostą listę…</div>';
            }
            return;
        }

        try {
        this.itemsTable = new Tabulator("#items-table", {
            height: "calc(100vh - 320px)",
            layout: "fitData",
            autoResize: false, // avoid ResizeObserver loops causing redraw jitter
            responsiveLayout: "hide",
            responsiveLayoutCollapseStartOpen: false,
            placeholder: "Brak itemów do wyświetlenia",
            columns: [
                {
                    title: "🔽",
                    field: "expand",
                    width: 50,
                    maxWidth: 50,
                    resizable: false,
                    responsive: 0,
                    hozAlign: "center",
                    formatter: (cell) => {
                        const data = cell.getRow().getData();
                        const hasSubitems = data.subitems_count > 0;
                        if (hasSubitems) {
                            return '<span class="expand-icon">▶️</span>';
                        }
                        return '';
                    },
                    cellClick: (e, cell) => {
                        this.toggleSubitems(cell.getRow());
                    }
                },
                {
                    title: "",
                    field: "expand_props_toggle",
                    width: 30,
                    hozAlign: "center",
                    formatter: (cell) => {
                        const itemData = cell.getData();
                        const count = Number(itemData.properties_count || 0);
                        const color = count > 0 ? '#17a2b8' : '#999';
                        const title = count > 0 ? `Properties: ${count}` : 'Brak properties (kliknij, aby dodać)';
                        return `<span class="item-expand-arrow" data-item="${itemData.item_key}" style="color: ${color}; cursor: pointer;" title="${title}">▶</span>`;
                    },
                    cellClick: (e, cell) => {
                        const arrow = e.target.closest('.item-expand-arrow');
                        if (arrow) {
                            e.stopPropagation();
                            this.toggleItemProperties(cell.getRow());
                        }
                    }
                },
                {
                    title: "📝 Klucz",
                    field: "item_key",
                    resizable: true,
                    editor: "input"
                },
                {
                    title: "📄 Treść",
                    field: "content",
                    resizable: true,
                    editor: "textarea"
                },
                {
                    title: "📊 Status",
                    field: "status",
                    resizable: true,
                    editor: "list",
                    editorParams: {
                        values: {
                            "pending": "Oczekujące",
                            "in_progress": "W trakcie",
                            "completed": "Ukończone",
                            "failed": "Nieudane"
                        }
                    },
                    formatter: (cell) => this.formatStatus(cell.getValue())
                },
                {
                    title: "🔸 Subitemy",
                    field: "subitems_count",
                    resizable: true,
                    hozAlign: "center",
                    formatter: (cell) => {
                        const count = cell.getValue();
                        return count > 0 ? count : '';
                    }
                }
            ],
            cellEdited: (cell) => {
                this.handleItemCellEdit(cell);
            },
            rowDblClick: (e, row) => {
                // Double-click to open properties modal
                const data = row.getData();
                this.showItemPropertiesModal(this.currentListKey, data.item_key);
            },
            locale: "pl"
        });
        
        // No window resize handler here; fixed height prevents jitter
        } catch (e) {
            console.error('Failed to initialize Tabulator for items:', e);
            this.itemsTable = null;
            const el = document.getElementById('items-table');
            if (el) {
                el.innerHTML = '<div class="fallback" style="padding: 12px; color: #b00;">Błąd inicjalizacji tabeli – wyświetlam prostą listę…</div>';
            }
        }
    }

    toggleSubitems(parentRow) {
        const data = parentRow.getData();
        const rowElement = parentRow.getElement();
        const expandIcon = rowElement.querySelector('.expand-icon');
        const existingNested = rowElement.querySelector('.nested-table');
        
        if (existingNested) {
            // Close subitems
            existingNested.remove();
            expandIcon.textContent = '▶️';
        } else {
            // Open subitems
            expandIcon.textContent = '🔽';
            this.createSubitemTable(parentRow, data.subitems);
        }
    }

    toggleProperties(parentRow) {
        try {
            const data = parentRow.getData();
            const rowElement = parentRow.getElement();
            const existingNested = rowElement.querySelector('.properties-display');
            
            if (existingNested) {
                // Close properties
                existingNested.remove();
            } else {
                // Open properties
                this.createPropertiesDisplay(parentRow, data.properties || {});
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    }

    createSubitemTable(parentRow, subitems) {
        const parentData = parentRow.getData();
        
        // Create container for nested table
        const holderEl = document.createElement("div");
        
        // Add parent item properties header
        const parentPropsEl = document.createElement("div");
        parentPropsEl.className = "parent-item-header";
        parentPropsEl.style.padding = "5px 10px";
        parentPropsEl.style.backgroundColor = "#e9ecef";
        parentPropsEl.style.borderBottom = "1px solid #dee2e6";
        parentPropsEl.style.fontSize = "12px";
        parentPropsEl.style.color = "#495057";
        
        const propsCount = parentData.properties_count || 0;
        parentPropsEl.innerHTML = `
            <strong>${parentData.item_key}</strong> - Properties: 
            ${propsCount > 0 ? 
                `<span class="props-link" onclick="app.showItemPropertiesModal('${this.currentListKey}', '${parentData.item_key}')" style="color: #007bff; cursor: pointer; text-decoration: underline;">${propsCount} właściwości</span>` : 
                '<span style="color: #6c757d;">brak properties</span>'
            }
        `;
        
        const tableEl = document.createElement("div");
        
        holderEl.className = "nested-table";
        holderEl.style.padding = "0 20px 10px 50px";
        holderEl.style.backgroundColor = "#f8f9fa";
        holderEl.style.borderLeft = "3px solid #007bff";
        
        holderEl.appendChild(parentPropsEl);
        holderEl.appendChild(tableEl);
        parentRow.getElement().appendChild(holderEl);

        // Create nested Tabulator table
        const subTable = new Tabulator(tableEl, {
            layout: "fitData",
            autoResize: true,
            data: subitems,
            height: Math.min(250, subitems.length * 40 + 50),
            columns: [
                {
                    title: "",
                    field: "expand_toggle",
                    width: 30,
                    hozAlign: "center",
                    formatter: (cell) => {
                        const subitemData = cell.getData();
                        const hasProperties = subitemData.properties && Object.keys(subitemData.properties).length > 0;
                        const color = hasProperties ? '#17a2b8' : '#999';
                        const title = hasProperties ? 'Kliknij aby pokazać properties' : 'Brak properties (kliknij, aby dodać)';
                        return `<span class="subitem-expand-arrow" data-subitem="${subitemData.item_key}" style="color: ${color}; cursor: pointer;" title="${title}">▶</span>`;
                    },
                    cellClick: (e, cell) => {
                        const arrow = e.target.closest('.subitem-expand-arrow');
                        if (arrow) {
                            e.stopPropagation();
                            this.toggleSubitemProperties(cell.getRow(), parentData);
                        }
                    }
                },
                {
                    title: "🔸 Klucz",
                    field: "item_key",
                    resizable: true,
                    editor: "input"
                },
                {
                    title: "📄 Treść",
                    field: "content",
                    resizable: true,
                    editor: "textarea"
                },
                {
                    title: "📊 Status",
                    field: "status",
                    resizable: true,
                    editor: "list",
                    editorParams: {
                        values: {
                            "pending": "Oczekujące",
                            "in_progress": "W trakcie",
                            "completed": "Ukończone",
                            "failed": "Nieudane"
                        }
                    },
                    formatter: (cell) => this.formatStatus(cell.getValue())
                }
            ],
            cellEdited: (cell) => {
                this.handleSubitemEdit(parentRow.getData(), cell);
            }
        });

        // Arrow colors are now set correctly in the formatter based on properties_count
    }

    createPropertiesDisplay(parentRow, properties) {
        try {
            const parentData = parentRow.getData();
            
            // Create container for properties display
            const holderEl = document.createElement("div");
            holderEl.className = "properties-display";
            holderEl.style.padding = "10px 20px 10px 50px";
            holderEl.style.backgroundColor = "#f8f9fa";
            holderEl.style.borderLeft = "3px solid #28a745";
            holderEl.style.borderTop = "1px solid #dee2e6";
            
            const propertiesHtml = Object.keys(properties || {}).length > 0 ? 
                Object.entries(properties).map(([key, value]) => 
                    `<div style="margin: 5px 0; display: flex; justify-content: space-between;">
                        <strong>${key}:</strong> 
                        <span>${value}</span>
                    </div>`
                ).join('') : 
                '<div style="color: #6c757d; font-style: italic;">Brak properties</div>';
            
            holderEl.innerHTML = `
                <div style="margin-bottom: 10px; font-weight: bold; color: #495057;">
                    ⚙️ Properties dla ${parentData.item_key}
                    <button onclick="app.showItemPropertiesModal('${this.currentListKey}', '${parentData.item_key}')" 
                            style="float: right; padding: 2px 8px; font-size: 12px; border: 1px solid #007bff; background: white; color: #007bff; border-radius: 3px; cursor: pointer;">
                        ✏️ Edytuj
                    </button>
                </div>
                <div style="background: white; padding: 10px; border-radius: 4px; border: 1px solid #dee2e6;">
                    ${propertiesHtml}
                </div>
            `;
            
            parentRow.getElement().appendChild(holderEl);
            
        } catch (error) {
        }
    }

    createFallbackTable() {
        const container = document.getElementById('lists-table');
        container.innerHTML = `
            <div style="padding: 20px; border: 1px solid #ddd; background: white;">
                <h3>Lista TODO (fallback)</h3>
                <p>Tabulator nie załadował się, ładuję dane bezpośrednio...</p>
                <div id="fallback-lists"></div>
            </div>
        `;
        
        // Load data directly
        this.loadFallbackData();
    }
    
    async loadFallbackData() {
        try {
            const response = await fetch('/api/lists?limit=10');
            const result = await response.json();
            
            if (result.success && result.data) {
                const container = document.getElementById('fallback-lists');
                const html = result.data.map(list => 
                    `<div style="border: 1px solid #ccc; margin: 5px; padding: 10px; cursor: pointer;" 
                          onclick="app.showListDetailsView('${list.list_key}')">
                        <strong>${list.title}</strong> (${list.total_items} items)
                     </div>`
                ).join('');
                container.innerHTML = html;
            }
        } catch (error) {
        }
    }

    async loadListsData() {
        this.showLoading();
        try {
            const params = new URLSearchParams({
                limit: this.pageSize,
                offset: this.currentPage * this.pageSize,
                search: this.searchTerm,
                favorites_only: this.showFavoritesOnly,
                tag: this.selectedTag
            });

            const response = await fetch(`/api/lists?${params}`);
            const result = await response.json();
            
            if (result.success) {
                this.listsTable.setData(result.data);
                this.updateListsPagination(result.pagination);
            } else {
                this.showToast('Błąd podczas ładowania list', 'error');
            }
        } catch (error) {
            this.showToast('Błąd połączenia', 'error');
        }
        this.hideLoading();
    }

    async loadTagsData() {
        try {
            const response = await fetch('/api/tags');
            const result = await response.json();
            
            if (result.success) {
                const tagSelect = document.getElementById('lists-tag-filter');
                
                // Clear existing options except first one
                tagSelect.innerHTML = '<option value="">🏷️ Wszystkie tagi</option>';
                
                // Add tag options
                result.tags.forEach(tag => {
                    const option = document.createElement('option');
                    option.value = tag;
                    option.textContent = `🏷️ ${tag}`;
                    tagSelect.appendChild(option);
                });
            }
        } catch (error) {
        }
    }

    async loadItemsData() {
        if (!this.currentListKey) return;
        
        this.showLoading();
        try {
            const response = await fetch(`/api/lists/${this.currentListKey}/items`);
            const result = await response.json();
            
            if (result.success) {
                const items = Array.isArray(result.data) ? result.data : [];
                if (this.itemsTable) {
                    this.itemsTable.setData(items);
                    this.updateItemsPagination(result.pagination);
                    // Verify rows actually rendered & visible; if not, use fallback view
                    setTimeout(() => {
                        try {
                            const container = document.getElementById('items-table');
                            const hasRows = container && container.querySelectorAll('.tabulator-row').length > 0;
                            const rect = container ? container.getBoundingClientRect() : { height: 0 };
                            const visible = rect.height > 30; // table has some height
                            if ((!hasRows || !visible) && items.length > 0) {
                                console.warn('Tabulator rows not visible; switching to fallback list.');
                                this.itemsTable = null;
                                this.renderItemsFallback(items, result.pagination);
                            }
                        } catch { /* ignore */ }
                    }, 120);
                } else {
                    // Render simple fallback list when Tabulator is not available
                    this.renderItemsFallback(items, result.pagination);
                }
                // Update property arrows after data is loaded (DISABLED TO FIX JUMPING)
                // await this.updatePropertyArrows();
                
            } else {
                this.showToast('Błąd podczas ładowania itemów', 'error');
            }
        } catch (error) {
            this.showToast('Błąd połączenia', 'error');
        }
        this.hideLoading();
    }

    renderItemsFallback(items, pagination) {
        const container = document.getElementById('items-table');
        if (!container) return;
        if (!Array.isArray(items)) {
            container.innerHTML = '<div style="padding: 12px; color: #b00;">Błąd danych itemów</div>';
            return;
        }

        const rows = items.map(it => {
            const badge = this.formatStatus(it.status);
            const subs = it.subitems_count ? `<span style="color:#555;"> • subitems: ${it.subitems_count}</span>` : '';
            return `<div style="padding:8px 10px; border-bottom:1px solid #eee;">
                        <code style="color:#666;">${it.item_key}</code> — ${it.content || ''}
                        <span style="margin-left:8px;">${badge}</span>${subs}
                    </div>`;
        }).join('');

        container.innerHTML = `
            <div style="background:#fff; border:1px solid #e5e7eb; border-radius:6px; overflow:hidden;">
                <div style="padding:8px 10px; font-weight:600; background:#f9fafb; border-bottom:1px solid #e5e7eb;">Items</div>
                <div>${rows || '<div style="padding:12px; color:#777;">Brak itemów</div>'}</div>
            </div>`;

        // Simple pagination info
        this.updateItemsPagination(pagination);
    }

    updateListsPagination(pagination) {
        const container = document.getElementById('lists-pagination');
        if (!pagination) {
            container.style.display = 'none';
            return;
        }
        
        container.style.display = 'flex';
        const currentPage = Math.floor(pagination.offset / pagination.limit) + 1;
        const totalPages = Math.ceil(pagination.total / pagination.limit);
        
        container.innerHTML = `
            <div class="pagination-info">
                Strona ${currentPage} z ${totalPages} (${pagination.total} list)
            </div>
            <div class="pagination-controls">
                <button class="pagination-btn" ${currentPage <= 1 ? 'disabled' : ''} onclick="app.goToListsPage(${currentPage - 2})">‹</button>
                ${this.generatePageButtons(currentPage, totalPages, 'app.goToListsPage')}
                <button class="pagination-btn" ${!pagination.has_more ? 'disabled' : ''} onclick="app.goToListsPage(${currentPage})">›</button>
            </div>
        `;
    }

    updateItemsPagination(pagination) {
        const container = document.getElementById('items-pagination');
        if (!pagination) {
            container.style.display = 'none';
            return;
        }
        
        container.style.display = 'flex';
        const currentPage = Math.floor(pagination.offset / pagination.limit) + 1;
        const totalPages = Math.ceil(pagination.total / pagination.limit);
        
        container.innerHTML = `
            <div class="pagination-info">
                Strona ${currentPage} z ${totalPages} (${pagination.total} itemów)
            </div>
            <div class="pagination-controls">
                <button class="pagination-btn" ${currentPage <= 1 ? 'disabled' : ''} onclick="app.goToItemsPage(${currentPage - 2})">‹</button>
                ${this.generatePageButtons(currentPage, totalPages, 'app.goToItemsPage')}
                <button class="pagination-btn" ${!pagination.has_more ? 'disabled' : ''} onclick="app.goToItemsPage(${currentPage})">›</button>
            </div>
        `;
    }

    generatePageButtons(currentPage, totalPages, clickHandler) {
        let buttons = '';
        const maxButtons = 5;
        let start = Math.max(1, currentPage - Math.floor(maxButtons / 2));
        let end = Math.min(totalPages, start + maxButtons - 1);
        
        if (end - start < maxButtons - 1) {
            start = Math.max(1, end - maxButtons + 1);
        }
        
        for (let i = start; i <= end; i++) {
            buttons += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="${clickHandler}(${i - 1})">${i}</button>`;
        }
        
        return buttons;
    }

    goToListsPage(page) {
        this.currentPage = page;
        this.loadListsData();
    }

    goToItemsPage(page) {
        // Items pagination would go here when implemented
        // For now, Tabulator handles it client-side
    }

    async toggleFavorite(listKey) {
        try {
            const response = await fetch(`/api/lists/${listKey}/favorite`, {
                method: 'POST'
            });

            const result = await response.json();
            if (result.success) {
                this.showToast(result.message, 'success');
                await this.loadListsData(); // Refresh data
            } else {
                this.showToast('Błąd podczas zmiany ulubionych', 'error');
            }
        } catch (error) {
            this.showToast('Błąd połączenia', 'error');
        }
    }

    async handleItemCellEdit(cell) {
        const data = cell.getRow().getData();
        const field = cell.getField();
        const value = cell.getValue();

        try {
            const updateData = {};
            updateData[field] = value;

            const response = await fetch(`/api/items/${this.currentListKey}/${data.item_key}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
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
            updateData[field] = value;

            const response = await fetch(`/api/subitems/${this.currentListKey}/${parentData.item_key}/${subitemData.item_key}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
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
            this.showToast('Błąd połączenia', 'error');
            cell.restoreOldValue();
        }
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
            const date = new Date(dateString);
            const now = new Date();
            const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
            
            if (diffDays === 0) return 'dziś';
            if (diffDays === 1) return 'wczoraj';
            if (diffDays < 7) return `${diffDays} dni temu`;
            
            return date.toLocaleDateString('pl-PL', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
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

    async showPropertiesModal(listKey) {
        try {
            // Get current properties
            const response = await fetch(`/api/lists/${listKey}/properties`);
            const result = await response.json();
            
            if (!result.success) {
                this.showToast('Błąd podczas pobierania properties', 'error');
                return;
            }
            
            const properties = result.properties || {};
            
            // Create modal HTML
            const modalHTML = `
                <div id="properties-modal" class="modal" style="display: block;">
                    <div class="modal-content" style="max-width: 550px; width: 95%;">
                        <div class="modal-header">
                            <h2>⚙️ Properties - ${listKey}</h2>
                            <button class="close-btn">✖️</button>
                        </div>
                        <div class="modal-body">
                            <div id="properties-list" class="properties-form">
                                ${Object.entries(properties).map(([key, value]) => `
                                    <div class="property-row">
                                        <input type="text" class="property-key" value="${key}" placeholder="klucz" />
                                        <input type="text" class="property-value" value="${value}" placeholder="wartość" />
                                        <button class="btn btn-danger delete-property" data-key="${key}">🗑️</button>
                                    </div>
                                `).join('')}
                                <div class="property-row new-property">
                                    <input type="text" class="property-key" placeholder="nowy klucz" />
                                    <input type="text" class="property-value" placeholder="wartość" />
                                    <button class="btn btn-primary add-property">➕</button>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button id="save-properties" class="btn btn-primary">✅ Zapisz</button>
                            <button class="close-btn btn btn-secondary">❌ Anuluj</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            const existingModal = document.getElementById('properties-modal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Add modal to DOM
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            // Setup modal event handlers
            this.setupPropertiesModal(listKey);
            
        } catch (error) {
            this.showToast('Błąd połączenia', 'error');
        }
    }

    setupPropertiesModal(listKey) {
        const modal = document.getElementById('properties-modal');
        
        // Close button handlers
        modal.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                modal.remove();
            });
        });
        
        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        // Add property button
        modal.querySelector('.add-property').addEventListener('click', () => {
            const newRow = modal.querySelector('.new-property');
            const key = newRow.querySelector('.property-key').value.trim();
            const value = newRow.querySelector('.property-value').value.trim();
            
            if (key) {
                const propertiesList = modal.querySelector('#properties-list');
                const propertyRow = document.createElement('div');
                propertyRow.className = 'property-row';
                propertyRow.innerHTML = `
                    <input type="text" class="property-key" value="${key}" placeholder="klucz" />
                    <input type="text" class="property-value" value="${value}" placeholder="wartość" />
                    <button class="btn btn-danger delete-property" data-key="${key}">🗑️</button>
                `;
                propertiesList.insertBefore(propertyRow, newRow);
                
                // Setup delete button
                propertyRow.querySelector('.delete-property').addEventListener('click', () => {
                    propertyRow.remove();
                });
                
                // Clear new property inputs
                newRow.querySelector('.property-key').value = '';
                newRow.querySelector('.property-value').value = '';
            }
        });
        
        // Delete property buttons
        modal.querySelectorAll('.delete-property').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.parentElement.remove();
            });
        });
        
        // Save properties button
        modal.querySelector('#save-properties').addEventListener('click', async () => {
            await this.saveProperties(listKey);
            modal.remove();
        });
    }

    async saveProperties(listKey) {
        const modal = document.getElementById('properties-modal');
        const propertyRows = modal.querySelectorAll('.property-row:not(.new-property)');
        
        try {
            this.showLoading();
            
            // Get all current properties to compare and delete removed ones
            const currentResponse = await fetch(`/api/lists/${listKey}/properties`);
            const currentResult = await currentResponse.json();
            const currentProps = currentResult.success ? currentResult.properties : {};
            
            // Collect new properties from form
            const newProps = {};
            propertyRows.forEach(row => {
                const key = row.querySelector('.property-key').value.trim();
                const value = row.querySelector('.property-value').value.trim();
                if (key) {
                    newProps[key] = value;
                }
            });
            
            // Delete removed properties
            for (const key of Object.keys(currentProps)) {
                if (!(key in newProps)) {
                    await fetch(`/api/lists/${listKey}/properties/${key}`, {
                        method: 'DELETE'
                    });
                }
            }
            
            // Set/update properties
            for (const [key, value] of Object.entries(newProps)) {
                await fetch(`/api/lists/${listKey}/properties`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key, value })
                });
            }
            
            this.showToast('Properties zaktualizowane', 'success');
            await this.loadListsData(); // Refresh lists view
            
            // Refresh list details if we're in that view
            if (this.currentView === 'list-details' && this.currentListKey === listKey) {
                await this.showListDetailsView(listKey);
            }
            
        } catch (error) {
            this.showToast('Błąd podczas zapisywania', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async showItemPropertiesModal(listKey, itemKey) {
        try {
            // Get current properties
            const response = await fetch(`/api/lists/${listKey}/items/${itemKey}/properties`);
            const result = await response.json();
            
            if (!result.success) {
                this.showToast('Błąd podczas pobierania properties itemu', 'error');
                return;
            }
            
            const properties = result.properties || {};
            
            // Create modal HTML
            const modalHTML = `
                <div id="item-properties-modal" class="modal" style="display: block;">
                    <div class="modal-content" style="max-width: 550px; width: 95%;">
                        <div class="modal-header">
                            <h2>⚙️ Properties - ${itemKey}</h2>
                            <button class="close-btn">✖️</button>
                        </div>
                        <div class="modal-body">
                            <div id="item-properties-list" class="properties-form">
                                ${Object.entries(properties).map(([key, value]) => `
                                    <div class="property-row">
                                        <input type="text" class="property-key" value="${key}" placeholder="klucz" />
                                        <input type="text" class="property-value" value="${value}" placeholder="wartość" />
                                        <button class="btn btn-danger delete-property" data-key="${key}">🗑️</button>
                                    </div>
                                `).join('')}
                                <div class="property-row new-property">
                                    <input type="text" class="property-key" placeholder="nowy klucz" />
                                    <input type="text" class="property-value" placeholder="wartość" />
                                    <button class="btn btn-primary add-property">➕</button>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button id="save-item-properties" class="btn btn-primary">✅ Zapisz</button>
                            <button class="close-btn btn btn-secondary">❌ Anuluj</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            const existingModal = document.getElementById('item-properties-modal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Add modal to DOM
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            // Setup modal event handlers
            this.setupItemPropertiesModal(listKey, itemKey);
            
        } catch (error) {
            this.showToast('Błąd połączenia', 'error');
        }
    }

    setupItemPropertiesModal(listKey, itemKey) {
        const modal = document.getElementById('item-properties-modal');
        
        // Close button handlers
        modal.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                modal.remove();
            });
        });
        
        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        // Add property button
        modal.querySelector('.add-property').addEventListener('click', () => {
            const newRow = modal.querySelector('.new-property');
            const key = newRow.querySelector('.property-key').value.trim();
            const value = newRow.querySelector('.property-value').value.trim();
            
            if (key) {
                const propertiesList = modal.querySelector('#item-properties-list');
                const propertyRow = document.createElement('div');
                propertyRow.className = 'property-row';
                propertyRow.innerHTML = `
                    <input type="text" class="property-key" value="${key}" placeholder="klucz" />
                    <input type="text" class="property-value" value="${value}" placeholder="wartość" />
                    <button class="btn btn-danger delete-property" data-key="${key}">🗑️</button>
                `;
                propertiesList.insertBefore(propertyRow, newRow);
                
                // Setup delete button
                propertyRow.querySelector('.delete-property').addEventListener('click', () => {
                    propertyRow.remove();
                });
                
                // Clear new property inputs
                newRow.querySelector('.property-key').value = '';
                newRow.querySelector('.property-value').value = '';
            }
        });
        
        // Delete property buttons
        modal.querySelectorAll('.delete-property').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.parentElement.remove();
            });
        });
        
        // Save properties button
        modal.querySelector('#save-item-properties').addEventListener('click', async () => {
            await this.saveItemProperties(listKey, itemKey);
            modal.remove();
        });
    }

    async saveItemProperties(listKey, itemKey) {
        const modal = document.getElementById('item-properties-modal');
        const propertyRows = modal.querySelectorAll('.property-row:not(.new-property)');
        
        try {
            this.showLoading();
            
            // Collect new properties from form
            const newProps = {};
            propertyRows.forEach(row => {
                const key = row.querySelector('.property-key').value.trim();
                const value = row.querySelector('.property-value').value.trim();
                if (key) {
                    newProps[key] = value;
                }
            });
            
            // Set/update properties
            for (const [key, value] of Object.entries(newProps)) {
                await fetch(`/api/lists/${listKey}/items/${itemKey}/properties`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key, value })
                });
            }
            
            this.showToast('Properties itemu zaktualizowane', 'success');
            // await this.loadItemsData(); // DISABLED TO PREVENT JUMPING/LOOP
            
        } catch (error) {
            this.showToast('Błąd podczas zapisywania', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async showSubitemPropertiesModal(listKey, itemKey, subitemKey) {
        try {
            // Get current properties
            const response = await fetch(`/api/lists/${listKey}/items/${itemKey}/subitems/${subitemKey}/properties`);
            const result = await response.json();
            
            if (!result.success) {
                this.showToast('Błąd podczas pobierania properties subitemu', 'error');
                return;
            }
            
            const properties = result.properties || {};
            
            // Create modal HTML
            const modalHTML = `
                <div id="subitem-properties-modal" class="modal" style="display: block;">
                    <div class="modal-content" style="max-width: 550px; width: 95%;">
                        <div class="modal-header">
                            <h2>⚙️ Properties - ${subitemKey}</h2>
                            <button class="close-btn">✖️</button>
                        </div>
                        <div class="modal-body">
                            <div id="subitem-properties-list" class="properties-form">
                                ${Object.entries(properties).map(([key, value]) => `
                                    <div class="property-row">
                                        <input type="text" class="property-key" value="${key}" placeholder="klucz" />
                                        <input type="text" class="property-value" value="${value}" placeholder="wartość" />
                                        <button class="btn btn-danger delete-property" data-key="${key}">🗑️</button>
                                    </div>
                                `).join('')}
                                <div class="property-row new-property">
                                    <input type="text" class="property-key" placeholder="nowy klucz" />
                                    <input type="text" class="property-value" placeholder="wartość" />
                                    <button class="btn btn-primary add-property">➕</button>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button id="save-subitem-properties" class="btn btn-primary">✅ Zapisz</button>
                            <button class="close-btn btn btn-secondary">❌ Anuluj</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            const existingModal = document.getElementById('subitem-properties-modal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Add modal to DOM
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            // Setup modal event handlers
            this.setupSubitemPropertiesModal(listKey, itemKey, subitemKey);
            
        } catch (error) {
            this.showToast('Błąd połączenia', 'error');
        }
    }

    setupSubitemPropertiesModal(listKey, itemKey, subitemKey) {
        const modal = document.getElementById('subitem-properties-modal');
        
        // Close button handlers
        modal.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                modal.remove();
            });
        });
        
        // Click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        // Add property button
        modal.querySelector('.add-property').addEventListener('click', () => {
            const newRow = modal.querySelector('.new-property');
            const key = newRow.querySelector('.property-key').value.trim();
            const value = newRow.querySelector('.property-value').value.trim();
            
            if (key) {
                const propertiesList = modal.querySelector('#subitem-properties-list');
                const propertyRow = document.createElement('div');
                propertyRow.className = 'property-row';
                propertyRow.innerHTML = `
                    <input type="text" class="property-key" value="${key}" placeholder="klucz" />
                    <input type="text" class="property-value" value="${value}" placeholder="wartość" />
                    <button class="btn btn-danger delete-property" data-key="${key}">🗑️</button>
                `;
                propertiesList.insertBefore(propertyRow, newRow);
                
                // Setup delete button
                propertyRow.querySelector('.delete-property').addEventListener('click', () => {
                    propertyRow.remove();
                });
                
                // Clear new property inputs
                newRow.querySelector('.property-key').value = '';
                newRow.querySelector('.property-value').value = '';
            }
        });
        
        // Delete property buttons
        modal.querySelectorAll('.delete-property').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.parentElement.remove();
            });
        });
        
        // Save properties button
        modal.querySelector('#save-subitem-properties').addEventListener('click', async () => {
            await this.saveSubitemProperties(listKey, itemKey, subitemKey);
            modal.remove();
        });
    }

    async saveSubitemProperties(listKey, itemKey, subitemKey) {
        const modal = document.getElementById('subitem-properties-modal');
        const propertyRows = modal.querySelectorAll('.property-row:not(.new-property)');
        
        try {
            this.showLoading();
            
            // Collect new properties from form
            const newProps = {};
            propertyRows.forEach(row => {
                const key = row.querySelector('.property-key').value.trim();
                const value = row.querySelector('.property-value').value.trim();
                if (key) {
                    newProps[key] = value;
                }
            });
            
            // Set/update properties
            for (const [key, value] of Object.entries(newProps)) {
                await fetch(`/api/lists/${listKey}/items/${itemKey}/subitems/${subitemKey}/properties`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key, value })
                });
            }
            
            this.showToast('Properties subitemu zaktualizowane', 'success');
            // await this.loadItemsData(); // DISABLED TO PREVENT JUMPING/LOOP
            
        } catch (error) {
            this.showToast('Błąd podczas zapisywania', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    container.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    saveFilters() {
        const filters = {
            selectedTag: this.selectedTag,
            showFavoritesOnly: this.showFavoritesOnly,
            searchTerm: this.searchTerm
        };
        localStorage.setItem('todoFilters', JSON.stringify(filters));
    }

    restoreFilters() {
        try {
            const saved = localStorage.getItem('todoFilters');
            if (saved) {
                const filters = JSON.parse(saved);
                
                // Przywróć wartości
                this.selectedTag = filters.selectedTag || '';
                this.showFavoritesOnly = filters.showFavoritesOnly || false;
                this.searchTerm = filters.searchTerm || '';
                
                // Ustaw elementy UI
                document.getElementById('lists-tag-filter').value = this.selectedTag;
                document.getElementById('lists-search').value = this.searchTerm;
                
                const btn = document.getElementById('lists-favorites-toggle');
                if (this.showFavoritesOnly) {
                    btn.classList.add('active');
                    btn.textContent = '⭐ Tylko ulubione';
                } else {
                    btn.classList.remove('active');
                    btn.textContent = '⭐ Ulubione';
                }
            }
        } catch (error) {
        }
    }

    toggleListProperties(parentRow) {
        try {
            const data = parentRow.getData();
            const rowElement = parentRow.getElement();
            const existingNested = rowElement.querySelector('.list-properties-display');
            
            if (existingNested) {
                // Close properties
                existingNested.remove();
            } else {
                // Open properties - load from API
                this.loadAndShowListProperties(parentRow, data.list_key);
            }
        } catch (error) {
        }
    }

    async loadAndShowListProperties(parentRow, listKey) {
        try {
            const response = await fetch(`/api/lists/${listKey}/properties`);
            const result = await response.json();
            
            if (result.success) {
                this.createListPropertiesDisplay(parentRow, result.properties || {}, listKey);
            } else {
                this.createListPropertiesDisplay(parentRow, {}, listKey);
            }
        } catch (error) {
            this.createListPropertiesDisplay(parentRow, {}, listKey);
        }
    }

    createListPropertiesDisplay(parentRow, properties, listKey) {
        try {
            // Create container for properties display
            const holderEl = document.createElement("div");
            holderEl.className = "list-properties-display";
            holderEl.style.padding = "10px 20px 10px 50px";
            holderEl.style.backgroundColor = "#f8f9fa";
            holderEl.style.borderLeft = "3px solid #007bff";
            holderEl.style.borderTop = "1px solid #dee2e6";
            
            const propertiesHtml = Object.keys(properties || {}).length > 0 ? 
                Object.entries(properties).map(([key, value]) => 
                    `<div style="margin: 5px 0; display: flex; justify-content: space-between;">
                        <strong>${key}:</strong> 
                        <span>${value}</span>
                    </div>`
                ).join('') : 
                '<div style="color: #6c757d; font-style: italic;">Brak properties</div>';
            
            holderEl.innerHTML = `
                <div style="margin-bottom: 10px; font-weight: bold; color: #495057;">
                    ⚙️ Properties dla listy: ${listKey}
                    <button onclick="app.showListPropertiesModal('${listKey}')" 
                            style="float: right; padding: 2px 8px; font-size: 12px; border: 1px solid #007bff; background: white; color: #007bff; border-radius: 3px; cursor: pointer;">
                        ✏️ Edytuj
                    </button>
                </div>
                <div style="background: white; padding: 10px; border-radius: 4px; border: 1px solid #dee2e6;">
                    ${propertiesHtml}
                </div>
            `;
            
            parentRow.getElement().appendChild(holderEl);
            
        } catch (error) {
        }
    }

    toggleSubitemProperties(subitemRow, parentData) {
        try {
            const subitemData = subitemRow.getData();
            const rowElement = subitemRow.getElement();
            const existingProps = rowElement.nextElementSibling;
            const arrow = rowElement.querySelector('.subitem-expand-arrow');
            
            if (existingProps && existingProps.classList.contains('subitem-properties-row')) {
                // Close properties
                existingProps.remove();
                if (arrow) arrow.innerHTML = '▶';
                return;
            }
            
            // Open properties - load from API (arrow status already checked during init)
            this.loadAndShowSubitemProperties(subitemRow, this.currentListKey, parentData.item_key, subitemData.item_key);
            if (arrow) arrow.innerHTML = '▼';
            
        } catch (error) {
        }
    }


    async loadAndShowSubitemProperties(subitemRow, listKey, parentItemKey, subitemKey) {
        try {
            const response = await fetch(`/api/lists/${listKey}/items/${parentItemKey}/subitems/${subitemKey}/properties`);
            const result = await response.json();
            
            if (result.success) {
                this.createSubitemPropertiesRow(subitemRow, result.properties || {}, listKey, parentItemKey, subitemKey);
            } else {
                this.createSubitemPropertiesRow(subitemRow, {}, listKey, parentItemKey, subitemKey);
            }
        } catch (error) {
            this.createSubitemPropertiesRow(subitemRow, {}, listKey, parentItemKey, subitemKey);
        }
    }

    createSubitemPropertiesRow(subitemRow, properties, listKey, parentItemKey, subitemKey) {
        try {
            // Create properties row (div to work inside Tabulator's DOM)
            const propertiesRow = document.createElement("div");
            propertiesRow.className = "subitem-properties-row";
            propertiesRow.style.backgroundColor = "#fff3cd";
            propertiesRow.style.padding = '8px 10px';
            propertiesRow.style.borderLeft = '3px solid #ffc107';
            propertiesRow.style.borderRight = '1px solid #eee';
            propertiesRow.style.borderBottom = '1px solid #eee';
            
            let propertiesHtml = '';
            
            if (Object.keys(properties || {}).length > 0) {
                // Show properties with delete buttons
                const propsArray = Object.entries(properties);
                propertiesHtml = propsArray.map(([key, value], index) => {
                    const isLast = index === propsArray.length - 1;
                    return `<div style="margin: 2px 0; display: flex; align-items: center;" class="property-item">
                        <span style="color: #856404;">⚙️</span> 
                        <strong style="margin-left: 3px;">${key}:</strong> 
                        <span class="property-value" data-key="${key}" data-listkey="${listKey}" data-itemkey="${parentItemKey}" data-subitemkey="${subitemKey}" style="cursor: pointer; padding: 2px; border: 1px solid transparent; margin-left: 5px; flex: 1;" title="Kliknij aby edytować">${value}</span>
                        <button class="delete-property-btn" data-key="${key}" style="margin-left: 8px; font-size: 12px; color: #dc3545; background: none; border: none; cursor: pointer;" title="Usuń property">🗑️</button>
                        ${isLast ? `<button class="add-property-btn" data-listkey="${listKey}" data-itemkey="${parentItemKey}" data-subitemkey="${subitemKey}" style="margin-left: 15px; font-size: 12px; color: #28a745; background: none; border: none; cursor: pointer;" title="Dodaj property">➕</button>` : ''}
                    </div>`;
                }).join('');
            } else {
                // No properties - just add button
                propertiesHtml = `<div style="color: #856404; font-style: italic; display: flex; align-items: center; justify-content: space-between;">
                    <span><span style="color: #856404;">⚙️</span> <span style="margin-left: 5px;">Brak properties</span></span>
                    <button class="add-property-btn" data-listkey="${listKey}" data-itemkey="${parentItemKey}" data-subitemkey="${subitemKey}" style="font-size: 12px; color: #28a745; background: none; border: none; cursor: pointer;" title="Dodaj property">➕ Dodaj</button>
                </div>`;
            }
            
            propertiesRow.innerHTML = `${propertiesHtml}`;
            
            // Insert after current row
            subitemRow.getElement().parentNode.insertBefore(propertiesRow, subitemRow.getElement().nextSibling);
            
            // Add event listeners for property editing
            this.addSubitemPropertyEventListeners(propertiesRow);
            
        } catch (error) {
        }
    }

    addSubitemPropertyEventListeners(propertiesRow) {
        // Property value click to edit
        propertiesRow.querySelectorAll('.property-value').forEach(span => {
            span.addEventListener('click', (e) => {
                this.editPropertyValue(e.target);
            });
        });

        // Delete property buttons
        propertiesRow.querySelectorAll('.delete-property-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.deleteSubitemProperty(e.target);
            });
        });

        // Add property buttons
        propertiesRow.querySelectorAll('.add-property-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.addSubitemProperty(e.target);
            });
        });
    }

    editPropertyValue(span) {
        const currentValue = span.textContent;
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentValue;
        input.style.cssText = 'padding: 2px; border: 1px solid #007bff; width: 200px;';
        
        const saveEdit = async () => {
            const newValue = input.value.trim();
            if (newValue && newValue !== currentValue) {
                try {
                    const response = await fetch(`/api/lists/${span.dataset.listkey}/items/${span.dataset.itemkey}/subitems/${span.dataset.subitemkey}/properties`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            key: span.dataset.key,
                            value: newValue
                        })
                    });
                    
                    if (response.ok) {
                        span.textContent = newValue;
                        span.style.backgroundColor = '#d4edda';
                        setTimeout(() => { span.style.backgroundColor = ''; }, 1000);
                    } else {
                        alert('Błąd podczas zapisywania property');
                    }
                } catch (error) {
                    alert('Błąd podczas zapisywania property');
                }
            }
            span.style.display = '';
            input.remove();
        };

        input.addEventListener('blur', saveEdit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') saveEdit();
            if (e.key === 'Escape') {
                span.style.display = '';
                input.remove();
            }
        });

        span.style.display = 'none';
        span.parentNode.insertBefore(input, span);
        input.focus();
        input.select();
    }

    async deleteSubitemProperty(btn) {
        const key = btn.dataset.key;
        if (!confirm(`Czy na pewno usunąć property '${key}'?`)) return;

        try {
            const span = btn.parentNode.querySelector('.property-value');
            const response = await fetch(`/api/lists/${span.dataset.listkey}/items/${span.dataset.itemkey}/subitems/${span.dataset.subitemkey}/properties/${encodeURIComponent(key)}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                btn.parentNode.remove();
            } else {
                alert('Błąd podczas usuwania property');
            }
        } catch (error) {
            alert('Błąd podczas usuwania property');
        }
    }

    addSubitemProperty(btn) {
        const keyInput = prompt('Podaj nazwę nowej property:');
        if (!keyInput?.trim()) return;
        
        const valueInput = prompt('Podaj wartość property:');
        if (valueInput === null) return;

        this.saveNewSubitemProperty(btn.dataset.listkey, btn.dataset.itemkey, btn.dataset.subitemkey, keyInput.trim(), valueInput);
    }

    async saveNewSubitemProperty(listKey, itemKey, subitemKey, key, value) {
        try {
            const response = await fetch(`/api/lists/${listKey}/items/${itemKey}/subitems/${subitemKey}/properties`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    key: key,
                    value: value
                })
            });
            
            if (response.ok) {
                // Refresh the properties display by reloading the current properties row
                const existingProps = document.querySelector('.subitem-properties-row');
                if (existingProps) {
                    // Find the subitem row that owns this properties row
                    const subitemRowElement = existingProps.previousElementSibling;
                    existingProps.remove();
                    
                    // Reopen with updated data
                    const mockSubitemRow = { getElement: () => subitemRowElement };
                    this.loadAndShowSubitemProperties(mockSubitemRow, listKey, itemKey, subitemKey);
                } else {
                    alert('Property została dodana, ale nie można odświeżyć widoku. Odśwież stronę.');
                }
            } else {
                alert('Błąd podczas dodawania property');
            }
        } catch (error) {
            alert('Błąd podczas dodawania property');
        }
    }


    toggleItemProperties(itemRow) {
        try {
            const itemData = itemRow.getData();
            const rowElement = itemRow.getElement();
            const existingProps = rowElement.nextElementSibling;
            const arrow = rowElement.querySelector('.item-expand-arrow');
            
            if (existingProps && existingProps.classList.contains('item-properties-row')) {
                // Close properties
                existingProps.remove();
                if (arrow) arrow.innerHTML = '▶';
                return;
            }
            
            // Open properties - load from API
            this.loadAndShowItemProperties(itemRow, this.currentListKey, itemData.item_key);
            if (arrow) arrow.innerHTML = '▼';
            
        } catch (error) {
        }
    }

    async loadAndShowItemProperties(itemRow, listKey, itemKey) {
        try {
            const response = await fetch(`/api/lists/${listKey}/items/${itemKey}/properties`);
            const result = await response.json();
            
            if (result.success) {
                this.createItemPropertiesRow(itemRow, result.properties || {}, listKey, itemKey);
            } else {
                this.createItemPropertiesRow(itemRow, {}, listKey, itemKey);
            }
        } catch (error) {
            this.createItemPropertiesRow(itemRow, {}, listKey, itemKey);
        }
    }

    createItemPropertiesRow(itemRow, properties, listKey, itemKey) {
        try {
            // Create properties row (div for Tabulator structure)
            const propertiesRow = document.createElement("div");
            propertiesRow.className = "item-properties-row";
            propertiesRow.style.backgroundColor = "#d1ecf1";
            propertiesRow.style.padding = '8px 10px';
            propertiesRow.style.borderLeft = '3px solid #17a2b8';
            propertiesRow.style.borderRight = '1px solid #eee';
            propertiesRow.style.borderBottom = '1px solid #eee';
            
            let propertiesHtml = '';
            
            if (Object.keys(properties || {}).length > 0) {
                // Show properties with delete buttons
                const propsArray = Object.entries(properties);
                propertiesHtml = propsArray.map(([key, value], index) => {
                    const isLast = index === propsArray.length - 1;
                    return `<div style="margin: 2px 0; display: flex; align-items: center;" class="property-item">
                        <span style="color: #0c5460;">⚙️</span> 
                        <strong style="margin-left: 3px;">${key}:</strong> 
                        <span class="property-value" data-key="${key}" data-listkey="${listKey}" data-itemkey="${itemKey}" style="cursor: pointer; padding: 2px; border: 1px solid transparent; margin-left: 5px; flex: 1;" title="Kliknij aby edytować">${value}</span>
                        <button class="delete-item-property-btn" data-key="${key}" style="margin-left: 8px; font-size: 12px; color: #dc3545; background: none; border: none; cursor: pointer;" title="Usuń property">🗑️</button>
                        ${isLast ? `<button class="add-item-property-btn" data-listkey="${listKey}" data-itemkey="${itemKey}" style="margin-left: 15px; font-size: 12px; color: #28a745; background: none; border: none; cursor: pointer;" title="Dodaj property">➕</button>` : ''}
                    </div>`;
                }).join('');
            } else {
                // No properties - just add button
                propertiesHtml = `<div style="color: #0c5460; font-style: italic; display: flex; align-items: center; justify-content: space-between;">
                    <span><span style="color: #0c5460;">⚙️</span> <span style="margin-left: 5px;">Brak properties</span></span>
                    <button class="add-item-property-btn" data-listkey="${listKey}" data-itemkey="${itemKey}" style="font-size: 12px; color: #28a745; background: none; border: none; cursor: pointer;" title="Dodaj property">➕ Dodaj</button>
                </div>`;
            }
            
            propertiesRow.innerHTML = `${propertiesHtml}`;
            
            // Insert after current row
            const itemElement = itemRow.getElement();
            
            itemElement.parentNode.insertBefore(propertiesRow, itemElement.nextSibling);
            
            // Add event listeners for property editing
            this.addItemPropertyEventListeners(propertiesRow);
            
        } catch (error) {
        }
    }

    addItemPropertyEventListeners(propertiesRow) {
        // Property value click to edit
        propertiesRow.querySelectorAll('.property-value').forEach(span => {
            span.addEventListener('click', (e) => {
                this.editItemPropertyValue(e.target);
            });
        });

        // Delete property buttons
        propertiesRow.querySelectorAll('.delete-item-property-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.deleteItemProperty(e.target);
            });
        });

        // Add property buttons
        propertiesRow.querySelectorAll('.add-item-property-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.addItemProperty(e.target);
            });
        });
    }

    editItemPropertyValue(span) {
        // Same logic as subitem properties but for items
        const currentValue = span.textContent;
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentValue;
        input.style.cssText = 'padding: 2px; border: 1px solid #007bff; width: 200px;';
        
        const saveEdit = async () => {
            const newValue = input.value.trim();
            if (newValue && newValue !== currentValue) {
                try {
                    const response = await fetch(`/api/lists/${span.dataset.listkey}/items/${span.dataset.itemkey}/properties`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            key: span.dataset.key,
                            value: newValue
                        })
                    });
                    
                    if (response.ok) {
                        span.textContent = newValue;
                        span.style.backgroundColor = '#d4edda';
                        setTimeout(() => { span.style.backgroundColor = ''; }, 1000);
                    } else {
                        alert('Błąd podczas zapisywania property');
                    }
                } catch (error) {
                    alert('Błąd podczas zapisywania property');
                }
            }
            span.style.display = '';
            input.remove();
        };

        input.addEventListener('blur', saveEdit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') saveEdit();
            if (e.key === 'Escape') {
                span.style.display = '';
                input.remove();
            }
        });

        span.style.display = 'none';
        span.parentNode.insertBefore(input, span);
        input.focus();
        input.select();
    }

    async deleteItemProperty(btn) {
        const key = btn.dataset.key;
        if (!confirm(`Czy na pewno usunąć property '${key}'?`)) return;

        try {
            const span = btn.parentNode.querySelector('.property-value');
            const response = await fetch(`/api/lists/${span.dataset.listkey}/items/${span.dataset.itemkey}/properties/${encodeURIComponent(key)}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                btn.parentNode.remove();
            } else {
                alert('Błąd podczas usuwania property');
            }
        } catch (error) {
            alert('Błąd podczas usuwania property');
        }
    }

    addItemProperty(btn) {
        const keyInput = prompt('Podaj nazwę nowej property:');
        if (!keyInput?.trim()) return;
        
        const valueInput = prompt('Podaj wartość property:');
        if (valueInput === null) return;

        this.saveNewItemProperty(btn.dataset.listkey, btn.dataset.itemkey, keyInput.trim(), valueInput);
    }

    async saveNewItemProperty(listKey, itemKey, key, value) {
        try {
            const response = await fetch(`/api/lists/${listKey}/items/${itemKey}/properties`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    key: key,
                    value: value
                })
            });
            
            if (response.ok) {
                // Refresh the properties display
                const existingProps = document.querySelector('.item-properties-row');
                if (existingProps) {
                    const itemRowElement = existingProps.previousElementSibling;
                    existingProps.remove();
                    
                    const mockItemRow = { getElement: () => itemRowElement };
                    this.loadAndShowItemProperties(mockItemRow, listKey, itemKey);
                } else {
                    alert('Property została dodana, ale nie można odświeżyć widoku. Odśwież stronę.');
                }
            } else {
                alert('Błąd podczas dodawania property');
            }
        } catch (error) {
            alert('Błąd podczas dodawania property');
        }
    }

    // Update property arrows to show correct colors based on actual properties (DISABLED)
    async updatePropertyArrows() {
        // COMPLETELY DISABLED TO PREVENT LOOPS
        return;
    }

    // Fallback method for individual property checking (DISABLED)
    async updatePropertyArrowsFallback() {
        // COMPLETELY DISABLED TO PREVENT LOOPS
        return;
    }


}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.app = new TodoAppNew();
    } catch (error) {
    }
});
