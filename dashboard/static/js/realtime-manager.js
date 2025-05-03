/**
 * Realtime Manager - Coordinates WebSocket connections and fallback polling
 * Provides a unified interface for real-time updates regardless of the underlying mechanism
 */
class RealtimeManager {
    /**
     * Initialize the Realtime Manager
     */
    constructor() {
        this.subscriptions = {};
        this.fallbackPollers = {};
        this.preferWebSockets = true;
        this.websocketsAvailable = FallbackPoller.isWebSocketSupported();
        
        // Map of channel types to their WebSocket paths and polling endpoints
        this.channelConfig = {
            'bot-status': {
                wsPath: '/ws/bot_status/',
                pollEndpoint: '/api/fallback/bot-status/',
            },
            'guild-activity': {
                wsPath: '/ws/guild_activity/{botId}/{guildId}/',
                pollEndpoint: '/api/fallback/guild-activity/',
            },
            'command-logs': {
                wsPath: '/ws/command_logs/{botId}/{guildId}/',
                pollEndpoint: '/api/fallback/command-logs/',
            },
            'dashboard-activity': {
                wsPath: '/ws/dashboard_activity/',
                pollEndpoint: '/api/fallback/dashboard-activity/',
            }
        };
        
        // Check for WebSocket support
        if (!this.websocketsAvailable) {
            console.warn('WebSockets are not supported in this browser. Using fallback polling instead.');
            this.preferWebSockets = false;
        }
    }
    
    /**
     * Subscribe to a specific channel for real-time updates
     * 
     * @param {string} channelType The type of channel to subscribe to
     * @param {Object} options Configuration options
     * @param {Function} options.onMessage Callback for receiving messages
     * @param {Function} options.onConnect Callback when connection is established (optional)
     * @param {Function} options.onDisconnect Callback when connection is lost (optional)
     * @param {Function} options.onError Callback for errors (optional)
     * @param {Object} options.params Additional parameters (e.g., botId, guildId) (optional)
     * @param {boolean} options.forcePolling Force using polling even if WebSockets are available (optional)
     * @returns {string} The subscription ID
     */
    subscribe(channelType, options) {
        if (!this.channelConfig[channelType]) {
            throw new Error(`Unknown channel type: ${channelType}`);
        }
        
        if (!options.onMessage || typeof options.onMessage !== 'function') {
            throw new Error('onMessage callback is required');
        }
        
        // Generate a unique subscription ID
        const subscriptionId = `${channelType}-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
        
        // Store the subscription
        this.subscriptions[subscriptionId] = {
            channelType,
            options,
            active: true
        };
        
        // Determine whether to use WebSockets or polling
        const useWebSockets = this.websocketsAvailable && this.preferWebSockets && !options.forcePolling;
        
        if (useWebSockets) {
            this._subscribeWithWebSockets(subscriptionId);
        } else {
            this._subscribeWithPolling(subscriptionId);
        }
        
        return subscriptionId;
    }
    
    /**
     * Unsubscribe from a channel
     * 
     * @param {string} subscriptionId The ID returned from subscribe()
     * @returns {boolean} Whether unsubscription was successful
     */
    unsubscribe(subscriptionId) {
        const subscription = this.subscriptions[subscriptionId];
        if (!subscription) {
            return false;
        }
        
        subscription.active = false;
        
        // Clean up WebSocket connection
        if (window.websocketManager && window.websocketManager.isConnected(subscriptionId)) {
            window.websocketManager.disconnect(subscriptionId);
        }
        
        // Clean up poller if exists
        if (this.fallbackPollers[subscriptionId]) {
            this.fallbackPollers[subscriptionId].stop();
            delete this.fallbackPollers[subscriptionId];
        }
        
        // Remove subscription
        delete this.subscriptions[subscriptionId];
        
        return true;
    }
    
    /**
     * Set whether to prefer WebSockets over polling
     * 
     * @param {boolean} prefer Whether to prefer WebSockets
     */
    setPreferWebSockets(prefer) {
        this.preferWebSockets = prefer && this.websocketsAvailable;
        
        // Restart active subscriptions with the new preference
        for (const subscriptionId in this.subscriptions) {
            const subscription = this.subscriptions[subscriptionId];
            if (subscription.active) {
                // Clean up existing connections
                if (window.websocketManager && window.websocketManager.isConnected(subscriptionId)) {
                    window.websocketManager.disconnect(subscriptionId);
                }
                
                if (this.fallbackPollers[subscriptionId]) {
                    this.fallbackPollers[subscriptionId].stop();
                    delete this.fallbackPollers[subscriptionId];
                }
                
                // Restart with new preference
                const useWebSockets = this.websocketsAvailable && this.preferWebSockets && !subscription.options.forcePolling;
                
                if (useWebSockets) {
                    this._subscribeWithWebSockets(subscriptionId);
                } else {
                    this._subscribeWithPolling(subscriptionId);
                }
            }
        }
    }
    
    /**
     * Set up a WebSocket subscription
     * 
     * @param {string} subscriptionId The subscription ID
     * @private
     */
    _subscribeWithWebSockets(subscriptionId) {
        const subscription = this.subscriptions[subscriptionId];
        const { channelType, options } = subscription;
        const config = this.channelConfig[channelType];
        
        // Build the WebSocket path with parameters
        let wsPath = config.wsPath;
        
        if (options.params) {
            // Replace placeholders in path with actual values
            if (options.params.botId) {
                wsPath = wsPath.replace('{botId}', options.params.botId);
            } else {
                wsPath = wsPath.replace('{botId}/', '');
            }
            
            if (options.params.guildId) {
                wsPath = wsPath.replace('{guildId}', options.params.guildId);
            } else {
                wsPath = wsPath.replace('{guildId}/', '');
            }
        }
        
        // Clean up any remaining placeholders
        wsPath = wsPath.replace(/{[^}]+}\//g, '');
        
        // Set up event handlers
        const handlers = {
            onOpen: (e) => {
                console.log(`WebSocket connection established for ${channelType}`);
                if (options.onConnect) {
                    options.onConnect();
                }
            },
            onClose: (e) => {
                console.log(`WebSocket connection closed for ${channelType}`);
                
                if (options.onDisconnect) {
                    options.onDisconnect();
                }
                
                // If still active, try to reconnect or fall back to polling
                if (subscription.active) {
                    if (e.code === 1006) {
                        // Abnormal closure, try polling as fallback
                        console.warn(`WebSocket connection failed for ${channelType}, falling back to polling`);
                        this._subscribeWithPolling(subscriptionId);
                    }
                }
            },
            onError: (e) => {
                console.error(`WebSocket error for ${channelType}:`, e);
                
                if (options.onError) {
                    options.onError(e);
                }
            },
            onMessage: (data) => {
                options.onMessage(data);
            }
        };
        
        // Connect using WebSocket Manager
        if (window.websocketManager) {
            window.websocketManager.connect(
                subscriptionId,
                wsPath,
                handlers,
                true // Auto-reconnect
            );
        } else {
            console.error('WebSocket Manager not found, falling back to polling');
            this._subscribeWithPolling(subscriptionId);
        }
    }
    
    /**
     * Set up a polling subscription
     * 
     * @param {string} subscriptionId The subscription ID
     * @private
     */
    _subscribeWithPolling(subscriptionId) {
        const subscription = this.subscriptions[subscriptionId];
        const { channelType, options } = subscription;
        const config = this.channelConfig[channelType];
        
        // Prepare polling parameters
        const pollParams = {};
        if (options.params) {
            if (options.params.botId) {
                pollParams.bot_id = options.params.botId;
            }
            
            if (options.params.guildId) {
                pollParams.guild_id = options.params.guildId;
            }
        }
        
        // Set up the poller
        const poller = new FallbackPoller({
            endpoint: config.pollEndpoint,
            onData: (data) => {
                // If this returns multiple results, call onMessage for each
                if (data.results && Array.isArray(data.results)) {
                    data.results.forEach(result => {
                        options.onMessage(result);
                    });
                } else {
                    options.onMessage(data);
                }
                
                // Call onConnect on first successful poll
                if (!this.fallbackPollers[subscriptionId].hasConnected) {
                    this.fallbackPollers[subscriptionId].hasConnected = true;
                    if (options.onConnect) {
                        options.onConnect();
                    }
                }
            },
            onError: (error) => {
                console.error(`Polling error for ${channelType}:`, error);
                
                if (options.onError) {
                    options.onError(error);
                }
            },
            interval: 5000, // 5 seconds
            autoStart: true,
            params: pollParams
        });
        
        // Store the poller
        this.fallbackPollers[subscriptionId] = poller;
        this.fallbackPollers[subscriptionId].hasConnected = false;
    }
    
    /**
     * Check if a subscription is active
     * 
     * @param {string} subscriptionId The subscription ID
     * @returns {boolean} Whether the subscription is active
     */
    isSubscribed(subscriptionId) {
        return !!(this.subscriptions[subscriptionId] && this.subscriptions[subscriptionId].active);
    }
    
    /**
     * Unsubscribe from all channels
     */
    unsubscribeAll() {
        for (const subscriptionId in this.subscriptions) {
            this.unsubscribe(subscriptionId);
        }
    }
}

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    window.realtimeManager = new RealtimeManager();
    
    // Clean up on page unload
    window.addEventListener('beforeunload', () => {
        if (window.realtimeManager) {
            window.realtimeManager.unsubscribeAll();
        }
    });
});