/**
 * Fallback Poller - Provides polling fallback for browsers without WebSocket support
 * or when WebSocket connection fails
 */
class FallbackPoller {
    /**
     * Initialize the Fallback Poller
     * 
     * @param {Object} options Configuration options
     * @param {string} options.endpoint API endpoint to poll (required)
     * @param {Function} options.onData Callback for received data (required)
     * @param {Function} options.onError Callback for errors (optional)
     * @param {number} options.interval Polling interval in milliseconds (default: 5000)
     * @param {boolean} options.autoStart Whether to start polling automatically (default: false)
     * @param {Object} options.params Additional parameters to send with the request (optional)
     */
    constructor(options = {}) {
        if (!options.endpoint) {
            throw new Error('FallbackPoller requires endpoint option');
        }
        
        if (!options.onData || typeof options.onData !== 'function') {
            throw new Error('FallbackPoller requires onData callback function');
        }
        
        this.options = {
            endpoint: options.endpoint,
            onData: options.onData,
            onError: options.onError || ((error) => console.error('Polling error:', error)),
            interval: options.interval || 5000,
            autoStart: options.autoStart || false,
            params: options.params || {}
        };
        
        this.isPolling = false;
        this.pollTimer = null;
        this.lastTimestamp = null;
        this.consecutiveErrors = 0;
        this.maxConsecutiveErrors = 5;
        this.backoffFactor = 1.5;
        
        if (this.options.autoStart) {
            this.start();
        }
    }
    
    /**
     * Check if WebSockets are supported in the current browser
     * 
     * @returns {boolean} Whether WebSockets are supported
     */
    static isWebSocketSupported() {
        return 'WebSocket' in window && window.WebSocket !== null;
    }
    
    /**
     * Start polling
     * 
     * @returns {boolean} Whether polling was started successfully
     */
    start() {
        if (this.isPolling) {
            return false;
        }
        
        this.isPolling = true;
        this.consecutiveErrors = 0;
        
        // Do an initial poll immediately
        this.poll();
        
        return true;
    }
    
    /**
     * Stop polling
     */
    stop() {
        this.isPolling = false;
        
        if (this.pollTimer) {
            clearTimeout(this.pollTimer);
            this.pollTimer = null;
        }
    }
    
    /**
     * Execute a single poll
     */
    poll() {
        if (!this.isPolling) {
            return;
        }
        
        // Build URL with parameters
        let url = this.options.endpoint;
        const params = new URLSearchParams(this.options.params);
        
        // Add last timestamp if available
        if (this.lastTimestamp) {
            params.append('since', this.lastTimestamp);
        }
        
        const queryString = params.toString();
        if (queryString) {
            url += (url.includes('?') ? '&' : '?') + queryString;
        }
        
        // Make the fetch request
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Reset consecutive errors counter on success
                this.consecutiveErrors = 0;
                
                // Update last timestamp if provided in response
                if (data.timestamp) {
                    this.lastTimestamp = data.timestamp;
                }
                
                // Call the onData callback with received data
                this.options.onData(data);
                
                // Schedule next poll with normal interval
                this.schedulePoll(this.options.interval);
            })
            .catch(error => {
                this.consecutiveErrors++;
                this.options.onError(error);
                
                // If too many consecutive errors, gradually increase polling interval
                if (this.consecutiveErrors > this.maxConsecutiveErrors) {
                    const backoffInterval = this.options.interval * Math.pow(this.backoffFactor, 
                        Math.min(this.consecutiveErrors - this.maxConsecutiveErrors, 5));
                    
                    console.warn(`Too many consecutive polling errors (${this.consecutiveErrors}). Backing off to ${backoffInterval}ms.`);
                    this.schedulePoll(backoffInterval);
                } else {
                    // Use normal interval
                    this.schedulePoll(this.options.interval);
                }
            });
    }
    
    /**
     * Schedule the next poll
     * 
     * @param {number} interval Time in milliseconds until next poll
     */
    schedulePoll(interval) {
        if (!this.isPolling) {
            return;
        }
        
        // Clear any existing timer
        if (this.pollTimer) {
            clearTimeout(this.pollTimer);
        }
        
        // Schedule next poll
        this.pollTimer = setTimeout(() => this.poll(), interval);
    }
    
    /**
     * Update polling parameters
     * 
     * @param {Object} params New parameters to use
     */
    updateParams(params) {
        this.options.params = {...this.options.params, ...params};
    }
    
    /**
     * Change the polling interval
     * 
     * @param {number} interval New interval in milliseconds
     */
    setInterval(interval) {
        if (interval <= 0) {
            throw new Error('Polling interval must be positive');
        }
        
        this.options.interval = interval;
        
        // If currently polling, restart with new interval
        if (this.isPolling) {
            this.schedulePoll(interval);
        }
    }
}

// Make globally available
window.FallbackPoller = FallbackPoller;