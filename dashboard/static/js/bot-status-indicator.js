/**
 * Bot Status Indicator Component
 * 
 * Provides real-time status indicators for bots via WebSockets
 */
class BotStatusIndicator {
    /**
     * Initialize the Bot Status Indicator
     * 
     * @param {Object} options Configuration options
     * @param {string} options.selector CSS selector for status indicators (default: '[data-bot-status]')
     * @param {boolean} options.autoConnect Whether to connect automatically (default: true)
     */
    constructor(options = {}) {
        this.options = {
            selector: options.selector || '[data-bot-status]',
            autoConnect: options.autoConnect !== undefined ? options.autoConnect : true
        };
        
        this.indicators = {};
        this.connected = false;
        this.connectionId = 'bot-status';
        
        this.statusClasses = {
            'online': 'bg-green-500',
            'offline': 'bg-gray-500',
            'connecting': 'bg-yellow-500 animate-pulse',
            'error': 'bg-red-500',
            'unknown': 'bg-gray-300'
        };
        
        // Initialize
        this.findIndicators();
        
        if (this.options.autoConnect) {
            this.connect();
        }
    }
    
    /**
     * Find all status indicators in the DOM
     */
    findIndicators() {
        const elements = document.querySelectorAll(this.options.selector);
        
        elements.forEach(element => {
            const botId = element.getAttribute('data-bot-status');
            if (botId) {
                this.indicators[botId] = element;
                
                // Set initial status to unknown if not specified
                if (!element.hasAttribute('data-status')) {
                    this.updateIndicator(botId, 'unknown');
                }
            }
        });
    }
    
    /**
     * Connect to the WebSocket for bot status updates
     */
    connect() {
        if (!window.websocketManager) {
            console.error('WebSocket Manager not found');
            return false;
        }
        
        if (window.websocketManager.isConnected(this.connectionId)) {
            return true;
        }
        
        try {
            // Set indicators to connecting state
            Object.keys(this.indicators).forEach(botId => {
                this.updateIndicator(botId, 'connecting');
            });
            
            // Connect to WebSocket
            window.websocketManager.connect(
                this.connectionId,
                '/ws/bot_status/',
                {
                    onOpen: () => {
                        this.connected = true;
                        console.log('Bot status WebSocket connected');
                    },
                    onClose: () => {
                        this.connected = false;
                        console.log('Bot status WebSocket disconnected');
                        
                        // Set indicators to unknown state
                        Object.keys(this.indicators).forEach(botId => {
                            this.updateIndicator(botId, 'unknown');
                        });
                    },
                    onMessage: this.handleMessage.bind(this),
                    onError: (e) => {
                        console.error('Bot status WebSocket error:', e);
                    }
                },
                true // Auto reconnect
            );
            
            return true;
        } catch (error) {
            console.error('Error connecting to bot status WebSocket:', error);
            return false;
        }
    }
    
    /**
     * Disconnect from the WebSocket
     */
    disconnect() {
        if (window.websocketManager) {
            window.websocketManager.disconnect(this.connectionId);
            this.connected = false;
        }
    }
    
    /**
     * Handle incoming WebSocket messages
     * 
     * @param {Object} data The message data
     */
    handleMessage(data) {
        const { bot_id, status } = data;
        
        if (bot_id && status) {
            this.updateIndicator(bot_id, status);
            
            // Dispatch custom event
            const event = new CustomEvent('botStatusChange', {
                detail: {
                    botId: bot_id,
                    status: status,
                    message: data.message || ''
                }
            });
            document.dispatchEvent(event);
        }
    }
    
    /**
     * Update a status indicator element
     * 
     * @param {string|number} botId The bot ID
     * @param {string} status The new status
     */
    updateIndicator(botId, status) {
        const element = this.indicators[botId];
        if (!element) return;
        
        // Update data attribute
        element.setAttribute('data-status', status);
        
        // Update status dot
        const statusDot = element.querySelector('.status-dot') || element;
        
        // Remove existing status classes
        Object.values(this.statusClasses).forEach(cls => {
            const classes = cls.split(' ');
            classes.forEach(c => statusDot.classList.remove(c));
        });
        
        // Add new status class
        const statusClass = this.statusClasses[status] || this.statusClasses.unknown;
        statusClass.split(' ').forEach(cls => statusDot.classList.add(cls));
        
        // Update title if applicable
        if (element.hasAttribute('title')) {
            element.setAttribute('title', `Bot status: ${status}`);
        }
    }
    
    /**
     * Add a new indicator to track
     * 
     * @param {string|number} botId The bot ID
     * @param {HTMLElement} element The indicator element
     */
    addIndicator(botId, element) {
        this.indicators[botId] = element;
        
        // Set initial status to unknown if not specified
        if (!element.hasAttribute('data-status')) {
            this.updateIndicator(botId, 'unknown');
        }
    }
}

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', () => {
    window.botStatusIndicator = new BotStatusIndicator();
});