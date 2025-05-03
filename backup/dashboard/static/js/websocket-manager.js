/**
 * WebSocket Manager - Handles connections and events for real-time updates
 */
class WebSocketManager {
    /**
     * Initialize a new WebSocket Manager
     */
    constructor() {
        this.connections = {};
        this.eventHandlers = {};
        this.reconnectTimeouts = {};
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // Start with 2 seconds
        
        // Default handlers
        this.defaultHandlers = {
            onOpen: () => console.log('WebSocket connected'),
            onClose: () => console.log('WebSocket disconnected'),
            onError: (e) => console.error('WebSocket error:', e),
            onMessage: (data) => console.log('WebSocket message:', data)
        };
    }
    
    /**
     * Create and establish a WebSocket connection
     * 
     * @param {string} id - Unique identifier for this connection
     * @param {string} url - WebSocket URL to connect to
     * @param {Object} handlers - Event handlers for this connection
     * @param {boolean} autoReconnect - Whether to automatically reconnect on disconnect
     * @returns {WebSocket} The WebSocket instance
     */
    connect(id, url, handlers = {}, autoReconnect = true) {
        // Close existing connection if any
        if (this.connections[id]) {
            this.disconnect(id);
        }
        
        // Initialize reconnect count
        this.reconnectAttempts = 0;
        
        // Create WebSocket
        const fullUrl = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + 
                        window.location.host + url;
        
        const ws = new WebSocket(fullUrl);
        
        // Store handlers
        this.eventHandlers[id] = {
            onOpen: handlers.onOpen || this.defaultHandlers.onOpen,
            onClose: handlers.onClose || this.defaultHandlers.onClose,
            onError: handlers.onError || this.defaultHandlers.onError,
            onMessage: handlers.onMessage || this.defaultHandlers.onMessage,
            autoReconnect
        };
        
        // Set up event listeners
        ws.onopen = (e) => {
            // Reset reconnect attempts on successful connection
            this.reconnectAttempts = 0;
            this.eventHandlers[id].onOpen(e);
        };
        
        ws.onclose = (e) => {
            this.eventHandlers[id].onClose(e);
            
            // Handle auto-reconnect if enabled
            if (autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
                
                console.log(`WebSocket ${id} closed. Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                
                this.reconnectTimeouts[id] = setTimeout(() => {
                    this.connect(id, url, handlers, autoReconnect);
                }, delay);
            }
        };
        
        ws.onerror = (e) => {
            this.eventHandlers[id].onError(e);
        };
        
        ws.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                this.eventHandlers[id].onMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
                this.eventHandlers[id].onError(error);
            }
        };
        
        // Store the connection
        this.connections[id] = ws;
        
        return ws;
    }
    
    /**
     * Disconnect a WebSocket connection
     * 
     * @param {string} id - Identifier of the connection to disconnect
     */
    disconnect(id) {
        if (this.connections[id]) {
            // Clear any pending reconnect timeouts
            if (this.reconnectTimeouts[id]) {
                clearTimeout(this.reconnectTimeouts[id]);
                delete this.reconnectTimeouts[id];
            }
            
            // Close the connection
            this.connections[id].close();
            delete this.connections[id];
            delete this.eventHandlers[id];
            
            console.log(`WebSocket ${id} disconnected`);
        }
    }
    
    /**
     * Disconnect all WebSocket connections
     */
    disconnectAll() {
        for (const id in this.connections) {
            this.disconnect(id);
        }
    }
    
    /**
     * Check if a connection is active
     * 
     * @param {string} id - Identifier of the connection to check
     * @returns {boolean} Whether the connection is active
     */
    isConnected(id) {
        return !!(this.connections[id] && this.connections[id].readyState === WebSocket.OPEN);
    }
    
    /**
     * Send data through a WebSocket connection
     * 
     * @param {string} id - Identifier of the connection to send through
     * @param {Object|string} data - Data to send
     * @returns {boolean} Whether the data was sent successfully
     */
    send(id, data) {
        if (!this.isConnected(id)) {
            console.error(`Cannot send message: WebSocket ${id} is not connected`);
            return false;
        }
        
        try {
            const message = typeof data === 'string' ? data : JSON.stringify(data);
            this.connections[id].send(message);
            return true;
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
            return false;
        }
    }
}

// Create a global instance
window.websocketManager = new WebSocketManager();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.websocketManager) {
        window.websocketManager.disconnectAll();
    }
});