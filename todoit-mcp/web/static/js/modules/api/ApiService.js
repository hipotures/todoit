/**
 * API Service Layer
 * Centralized API communication with caching and error handling
 */
class ApiService {
    constructor() {
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
        this.baseURL = '/api';
    }
    
    /**
     * Generic API request method with error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const requestOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, requestOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (!data.success && data.success !== undefined) {
                throw new Error(data.error || 'API request failed');
            }
            
            return data;
        } catch (error) {
            console.error(`API Request failed for ${endpoint}:`, error);
            throw error;
        }
    }
    
    /**
     * GET request with optional caching
     */
    async get(endpoint, useCache = true) {
        const cacheKey = `GET:${endpoint}`;
        
        if (useCache && this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
            this.cache.delete(cacheKey);
        }
        
        const data = await this.request(endpoint, { method: 'GET' });
        
        if (useCache) {
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });
        }
        
        return data;
    }
    
    /**
     * POST request
     */
    async post(endpoint, data = {}) {
        this.invalidateCache();
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    /**
     * PUT request
     */
    async put(endpoint, data = {}) {
        this.invalidateCache();
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    
    /**
     * DELETE request
     */
    async delete(endpoint) {
        this.invalidateCache();
        return this.request(endpoint, { method: 'DELETE' });
    }
    
    /**
     * Clear cache for specific patterns or all
     */
    invalidateCache(pattern = null) {
        if (!pattern) {
            this.cache.clear();
            return;
        }
        
        const regex = new RegExp(pattern);
        for (const key of this.cache.keys()) {
            if (regex.test(key)) {
                this.cache.delete(key);
            }
        }
    }
    
    // === LISTS API ===
    async getLists(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/lists?${queryString}` : '/lists';
        return this.get(endpoint);
    }
    
    async getList(listKey) {
        return this.get(`/lists/${listKey}`);
    }
    
    async getListItems(listKey, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/lists/${listKey}/items?${queryString}` : `/lists/${listKey}/items`;
        return this.get(endpoint);
    }
    
    // === PROPERTIES API ===
    async getListProperties(listKey) {
        return this.get(`/lists/${listKey}/properties`);
    }
    
    async setListProperty(listKey, propertyKey, propertyValue) {
        return this.post(`/lists/${listKey}/properties`, {
            key: propertyKey,
            value: propertyValue
        });
    }
    
    async deleteListProperty(listKey, propertyKey) {
        return this.delete(`/lists/${listKey}/properties/${encodeURIComponent(propertyKey)}`);
    }
    
    async getItemProperties(listKey, itemKey) {
        return this.get(`/lists/${listKey}/items/${itemKey}/properties`);
    }
    
    async setItemProperty(listKey, itemKey, propertyKey, propertyValue) {
        return this.post(`/lists/${listKey}/items/${itemKey}/properties`, {
            key: propertyKey,
            value: propertyValue
        });
    }
    
    async deleteItemProperty(listKey, itemKey, propertyKey) {
        return this.delete(`/lists/${listKey}/items/${itemKey}/properties/${encodeURIComponent(propertyKey)}`);
    }
    
    async getSubitemProperties(listKey, itemKey, subitemKey) {
        return this.get(`/lists/${listKey}/items/${itemKey}/subitems/${subitemKey}/properties`);
    }
    
    async setSubitemProperty(listKey, itemKey, subitemKey, propertyKey, propertyValue) {
        return this.post(`/lists/${listKey}/items/${itemKey}/subitems/${subitemKey}/properties`, {
            key: propertyKey,
            value: propertyValue
        });
    }
    
    async deleteSubitemProperty(listKey, itemKey, subitemKey, propertyKey) {
        return this.delete(`/lists/${listKey}/items/${itemKey}/subitems/${subitemKey}/properties/${encodeURIComponent(propertyKey)}`);
    }
    
    // === ITEMS API ===
    async updateItem(listKey, itemKey, data) {
        return this.put(`/items/${listKey}/${itemKey}`, data);
    }
    
    async updateSubitem(listKey, itemKey, subitemKey, data) {
        return this.put(`/subitems/${listKey}/${itemKey}/${subitemKey}`, data);
    }
    
    async toggleFavorite(listKey) {
        return this.post(`/lists/${listKey}/favorite`);
    }
    
    // === CONFIGURATION API ===
    async getConfig() {
        return this.get('/config');
    }
    
    async updateConfig(config) {
        return this.post('/config', config);
    }
    
    // === TAGS API ===
    async getTags() {
        return this.get('/tags');
    }
    
    // === HEALTH CHECK ===
    async healthCheck() {
        return this.get('/health', false); // Don't cache health checks
    }
}

// Create singleton instance
const apiService = new ApiService();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiService;
} else {
    window.ApiService = ApiService;
    window.api = apiService;
}