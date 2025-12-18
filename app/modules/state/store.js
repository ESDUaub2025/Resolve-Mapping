/**
 * State Management Store
 * ======================
 * Immutable state management for map application.
 * Enables state-driven rendering without layer rebuilding.
 * 
 * Architecture:
 * - Single source of truth for app state
 * - Immutable updates (spread operators)
 * - Observer pattern for reactivity
 * - State persistence in localStorage
 */

const StateStore = (function() {
    'use strict';

    // Initial state structure
    const INITIAL_STATE = {
        // UI state
        language: 'en',
        sidebarCollapsed: false,
        
        // Data state
        themesLoaded: false,
        themes: {}, // {water: {id, color, data, features}, ...}
        staticLayers: {}, // {fire, preservations, predictions}
        
        // Layer visibility
        visibleLayers: new Set(), // Set of layer IDs
        
        // Active filters per theme
        filters: {
            // water: {village: 'Barouk', cropType: 'apple'},
            // energy: {energySource: 'solar'},
            // ...
        },
        
        // Feature selection
        selectedFeatureId: null,
        hoveredFeatureId: null,
        
        // Map state
        mapLoaded: false,
        mapCenter: [35.55, 33.69],
        mapZoom: 12
    };

    // Current state (mutable container for immutable state object)
    let state = { ...INITIAL_STATE, filters: {} };

    // Observers (callbacks to notify on state changes)
    const observers = [];

    /**
     * Get current state (frozen copy)
     */
    function getState() {
        return Object.freeze({ ...state });
    }

    /**
     * Update state immutably
     * @param {Object|Function} updates - Object with updates or updater function
     */
    function setState(updates) {
        const prevState = { ...state };

        // Support function updater: setState(state => ({...state, key: value}))
        if (typeof updates === 'function') {
            state = updates(prevState);
        } else {
            state = { ...prevState, ...updates };
        }

        // Notify observers
        notifyObservers(prevState, state);

        // Persist to localStorage (selective)
        persistState();
    }

    /**
     * Update nested state path immutably
     * Example: updatePath(['filters', 'water'], {village: 'Barouk'})
     */
    function updatePath(path, value) {
        setState(prevState => {
            const newState = { ...prevState };
            let current = newState;

            // Navigate to parent of target
            for (let i = 0; i < path.length - 1; i++) {
                current[path[i]] = { ...current[path[i]] };
                current = current[path[i]];
            }

            // Set value
            const lastKey = path[path.length - 1];
            if (typeof value === 'function') {
                current[lastKey] = value(current[lastKey]);
            } else {
                current[lastKey] = value;
            }

            return newState;
        });
    }

    /**
     * Subscribe to state changes
     * @param {Function} callback - Called with (prevState, newState)
     * @returns {Function} Unsubscribe function
     */
    function subscribe(callback) {
        observers.push(callback);
        
        // Return unsubscribe function
        return () => {
            const index = observers.indexOf(callback);
            if (index > -1) {
                observers.splice(index, 1);
            }
        };
    }

    /**
     * Notify all observers
     */
    function notifyObservers(prevState, newState) {
        observers.forEach(callback => {
            try {
                callback(prevState, newState);
            } catch (error) {
                console.error('Observer error:', error);
            }
        });
    }

    /**
     * Persist state to localStorage
     */
    function persistState() {
        try {
            const persistData = {
                language: state.language,
                sidebarCollapsed: state.sidebarCollapsed,
                mapCenter: state.mapCenter,
                mapZoom: state.mapZoom,
                visibleLayers: Array.from(state.visibleLayers || [])
            };
            
            localStorage.setItem('mapState', JSON.stringify(persistData));
        } catch (error) {
            console.warn('Failed to persist state:', error);
        }
    }

    /**
     * Restore state from localStorage
     */
    function restoreState() {
        try {
            const stored = localStorage.getItem('mapState');
            if (stored) {
                const parsed = JSON.parse(stored);
                
                setState({
                    language: parsed.language || 'en',
                    sidebarCollapsed: parsed.sidebarCollapsed || false,
                    mapCenter: parsed.mapCenter || INITIAL_STATE.mapCenter,
                    mapZoom: parsed.mapZoom || INITIAL_STATE.mapZoom,
                    visibleLayers: new Set(parsed.visibleLayers || [])
                });

                console.log('✓ State restored from localStorage');
            }
        } catch (error) {
            console.warn('Failed to restore state:', error);
        }
    }

    /**
     * Reset state to initial values
     */
    function resetState() {
        state = { 
            ...INITIAL_STATE,
            filters: {},
            visibleLayers: new Set()
        };
        notifyObservers({}, state);
        persistState();
    }

    /**
     * Layer visibility helpers
     */
    function toggleLayer(layerId) {
        setState(prevState => {
            const newVisible = new Set(prevState.visibleLayers);
            if (newVisible.has(layerId)) {
                newVisible.delete(layerId);
            } else {
                newVisible.add(layerId);
            }
            return { ...prevState, visibleLayers: newVisible };
        });
    }

    function showLayer(layerId) {
        setState(prevState => {
            const newVisible = new Set(prevState.visibleLayers);
            newVisible.add(layerId);
            return { ...prevState, visibleLayers: newVisible };
        });
    }

    function hideLayer(layerId) {
        setState(prevState => {
            const newVisible = new Set(prevState.visibleLayers);
            newVisible.delete(layerId);
            return { ...prevState, visibleLayers: newVisible };
        });
    }

    function isLayerVisible(layerId) {
        return state.visibleLayers.has(layerId);
    }

    /**
     * Filter helpers
     */
    function setFilter(theme, filterKey, value) {
        updatePath(['filters', theme], prevFilters => ({
            ...prevFilters,
            [filterKey]: value
        }));
    }

    function clearFilter(theme, filterKey) {
        updatePath(['filters', theme], prevFilters => {
            const newFilters = { ...prevFilters };
            delete newFilters[filterKey];
            return newFilters;
        });
    }

    function clearAllFilters(theme) {
        updatePath(['filters', theme], {});
    }

    function getFilters(theme) {
        return state.filters[theme] || {};
    }

    /**
     * Theme data helpers
     */
    function setThemeData(themeKey, data) {
        updatePath(['themes', themeKey], data);
    }

    function getThemeData(themeKey) {
        return state.themes[themeKey];
    }

    function getAllThemes() {
        return state.themes;
    }

    /**
     * Feature selection helpers
     */
    function selectFeature(featureId) {
        setState({ selectedFeatureId: featureId });
    }

    function deselectFeature() {
        setState({ selectedFeatureId: null });
    }

    function hoverFeature(featureId) {
        setState({ hoveredFeatureId: featureId });
    }

    function unhoverFeature() {
        setState({ hoveredFeatureId: null });
    }

    /**
     * Language helpers
     */
    function setLanguage(lang) {
        if (lang !== 'en' && lang !== 'ar') {
            console.warn(`Invalid language: ${lang}`);
            return;
        }
        setState({ language: lang });
    }

    function getLanguage() {
        return state.language;
    }

    function toggleLanguage() {
        const newLang = state.language === 'en' ? 'ar' : 'en';
        setLanguage(newLang);
    }

    // Public API
    return {
        // Core state management
        getState,
        setState,
        updatePath,
        subscribe,
        resetState,
        restoreState,

        // Layer visibility
        toggleLayer,
        showLayer,
        hideLayer,
        isLayerVisible,

        // Filters
        setFilter,
        clearFilter,
        clearAllFilters,
        getFilters,

        // Theme data
        setThemeData,
        getThemeData,
        getAllThemes,

        // Feature selection
        selectFeature,
        deselectFeature,
        hoverFeature,
        unhoverFeature,

        // Language
        setLanguage,
        getLanguage,
        toggleLanguage
    };
})();

// Export for use in app.js
if (typeof window !== 'undefined') {
    window.StateStore = StateStore;
}
