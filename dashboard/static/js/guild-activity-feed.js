/**
 * Guild Activity Feed Component
 * 
 * Displays real-time guild activity via WebSockets
 */
class GuildActivityFeed {
    /**
     * Initialize the Guild Activity Feed
     * 
     * @param {Object} options Configuration options
     * @param {string} options.containerSelector CSS selector for the feed container (required)
     * @param {number} options.botId Bot ID to filter by (optional)
     * @param {string} options.guildId Guild ID to filter by (optional)
     * @param {number} options.maxEntries Maximum number of entries to display (default: 100)
     * @param {boolean} options.autoConnect Whether to connect automatically (default: true)
     * @param {Function} options.formatEntry Custom function to format each entry (optional)
     */
    constructor(options = {}) {
        if (!options.containerSelector) {
            throw new Error('GuildActivityFeed requires containerSelector option');
        }
        
        this.options = {
            containerSelector: options.containerSelector,
            botId: options.botId || null,
            guildId: options.guildId || null,
            maxEntries: options.maxEntries || 100,
            autoConnect: options.autoConnect !== undefined ? options.autoConnect : true,
            formatEntry: options.formatEntry || this.defaultFormatEntry.bind(this)
        };
        
        this.container = document.querySelector(this.options.containerSelector);
        if (!this.container) {
            throw new Error(`Guild activity feed container not found: ${this.options.containerSelector}`);
        }
        
        this.connected = false;
        this.connectionId = `guild-activity-${this.options.botId || 'all'}-${this.options.guildId || 'all'}`;
        this.entries = [];
        
        // Initialize
        this.render();
        
        if (this.options.autoConnect) {
            this.connect();
        }
    }
    
    /**
     * Connect to the WebSocket for guild activity updates
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
            // Build WebSocket URL based on bot ID and guild ID
            let url = '/ws/guild_activity/';
            
            if (this.options.botId) {
                url += `${this.options.botId}/`;
                
                if (this.options.guildId) {
                    url += `${this.options.guildId}/`;
                }
            } else {
                url += 'all/';
            }
            
            // Connect to WebSocket
            window.websocketManager.connect(
                this.connectionId,
                url,
                {
                    onOpen: () => {
                        this.connected = true;
                        console.log(`Guild activity WebSocket connected: ${url}`);
                        this.addSystemEntry('Connected to guild activity feed');
                    },
                    onClose: () => {
                        this.connected = false;
                        console.log('Guild activity WebSocket disconnected');
                        this.addSystemEntry('Disconnected from guild activity feed');
                    },
                    onMessage: this.handleMessage.bind(this),
                    onError: (e) => {
                        console.error('Guild activity WebSocket error:', e);
                        this.addSystemEntry('Error in guild activity feed connection', true);
                    }
                },
                true // Auto reconnect
            );
            
            return true;
        } catch (error) {
            console.error('Error connecting to guild activity WebSocket:', error);
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
        this.addEntry({
            botId: data.bot_id,
            guildId: data.guild_id,
            eventType: data.event_type,
            timestamp: data.timestamp ? new Date(data.timestamp) : new Date(),
            data: data.data || {}
        });
        
        // Dispatch custom event
        const event = new CustomEvent('guildActivity', {
            detail: {
                botId: data.bot_id,
                guildId: data.guild_id,
                eventType: data.event_type,
                timestamp: data.timestamp,
                data: data.data || {}
            }
        });
        document.dispatchEvent(event);
    }
    
    /**
     * Add a regular activity entry to the feed
     * 
     * @param {Object} entry The entry to add
     */
    addEntry(entry) {
        // Add to entries array
        this.entries.unshift(entry);
        
        // Trim if over max entries
        if (this.entries.length > this.options.maxEntries) {
            this.entries = this.entries.slice(0, this.options.maxEntries);
        }
        
        // Update the DOM
        this.render();
    }
    
    /**
     * Add a system entry to the feed
     * 
     * @param {string} message The system message
     * @param {boolean} isError Whether this is an error message
     */
    addSystemEntry(message, isError = false) {
        const entry = {
            isSystem: true,
            message: message,
            isError: isError,
            timestamp: new Date()
        };
        
        this.entries.unshift(entry);
        
        // Trim if over max entries
        if (this.entries.length > this.options.maxEntries) {
            this.entries = this.entries.slice(0, this.options.maxEntries);
        }
        
        // Update the DOM
        this.render();
    }
    
    /**
     * Clear all entries from the feed
     */
    clearEntries() {
        this.entries = [];
        this.render();
    }
    
    /**
     * Default format function for entries
     * 
     * @param {Object} entry The entry to format
     * @returns {HTMLElement} The formatted entry element
     */
    defaultFormatEntry(entry) {
        const entryElement = document.createElement('div');
        entryElement.className = 'border-b border-gray-200 dark:border-gray-700 p-3 flex items-start';
        
        if (entry.isSystem) {
            // System message
            entryElement.classList.add(entry.isError ? 'bg-red-50 dark:bg-red-900/20' : 'bg-blue-50 dark:bg-blue-900/20');
            
            const icon = document.createElement('div');
            icon.className = 'mr-3 text-lg';
            icon.innerHTML = entry.isError ? '⚠️' : 'ℹ️';
            
            const content = document.createElement('div');
            content.className = 'flex-1';
            
            const messageElement = document.createElement('p');
            messageElement.className = entry.isError ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400';
            messageElement.textContent = entry.message;
            
            const timeElement = document.createElement('span');
            timeElement.className = 'text-xs text-gray-500 dark:text-gray-400';
            timeElement.textContent = this.formatTime(entry.timestamp);
            
            content.appendChild(messageElement);
            content.appendChild(timeElement);
            
            entryElement.appendChild(icon);
            entryElement.appendChild(content);
            
        } else {
            // Regular activity
            const icon = document.createElement('div');
            icon.className = 'mr-3 text-lg';
            
            // Set icon based on event type
            switch (entry.eventType) {
                case 'guild_added':
                    icon.innerHTML = '➕';
                    break;
                case 'guild_removed':
                    icon.innerHTML = '➖';
                    break;
                case 'channels_synced':
                    icon.innerHTML = '🔄';
                    break;
                case 'guild_status_change':
                    icon.innerHTML = '🔔';
                    break;
                default:
                    icon.innerHTML = '📝';
            }
            
            const content = document.createElement('div');
            content.className = 'flex-1';
            
            const headerElement = document.createElement('div');
            headerElement.className = 'flex items-center justify-between mb-1';
            
            const titleElement = document.createElement('h4');
            titleElement.className = 'font-medium text-gray-900 dark:text-gray-100';
            
            // Set title based on event type
            switch (entry.eventType) {
                case 'guild_added':
                    titleElement.textContent = `New guild added: ${entry.data.name || 'Unknown'}`;
                    break;
                case 'guild_removed':
                    titleElement.textContent = `Guild removed: ${entry.data.name || 'Unknown'}`;
                    break;
                case 'channels_synced':
                    titleElement.textContent = `Channels synced: ${entry.data.channel_count || 0} channels`;
                    break;
                case 'guild_status_change':
                    titleElement.textContent = `Guild status changed to ${entry.data.status || 'unknown'}`;
                    break;
                default:
                    titleElement.textContent = `Event: ${entry.eventType}`;
            }
            
            const timeElement = document.createElement('span');
            timeElement.className = 'text-xs text-gray-500 dark:text-gray-400';
            timeElement.textContent = this.formatTime(entry.timestamp);
            
            headerElement.appendChild(titleElement);
            headerElement.appendChild(timeElement);
            
            const metaElement = document.createElement('div');
            metaElement.className = 'text-sm text-gray-600 dark:text-gray-300';
            metaElement.textContent = `Bot #${entry.botId} - Guild ${entry.guildId}`;
            
            content.appendChild(headerElement);
            content.appendChild(metaElement);
            
            // Add additional data if available
            if (entry.data && Object.keys(entry.data).length > 0) {
                const detailsElement = document.createElement('div');
                detailsElement.className = 'mt-1 text-sm text-gray-500 dark:text-gray-400';
                
                // Format based on event type
                switch (entry.eventType) {
                    case 'guild_added':
                        detailsElement.textContent = `Members: ${entry.data.member_count || 'Unknown'}`;
                        break;
                    case 'channels_synced':
                        detailsElement.textContent = `Updated for: ${entry.data.guild_name || 'Unknown guild'}`;
                        break;
                    // Add more event types as needed
                }
                
                content.appendChild(detailsElement);
            }
            
            entryElement.appendChild(icon);
            entryElement.appendChild(content);
        }
        
        return entryElement;
    }
    
    /**
     * Format a timestamp for display
     * 
     * @param {Date} timestamp The timestamp to format
     * @returns {string} Formatted time string
     */
    formatTime(timestamp) {
        if (!(timestamp instanceof Date)) {
            timestamp = new Date(timestamp);
        }
        
        return timestamp.toLocaleTimeString();
    }
    
    /**
     * Render the feed entries in the container
     */
    render() {
        // Clear the container
        this.container.innerHTML = '';
        
        // If no entries, show empty state
        if (this.entries.length === 0) {
            const emptyElement = document.createElement('div');
            emptyElement.className = 'p-4 text-center text-gray-500 dark:text-gray-400';
            emptyElement.textContent = 'No activity yet';
            this.container.appendChild(emptyElement);
            return;
        }
        
        // Add each entry to the container
        this.entries.forEach(entry => {
            const entryElement = this.options.formatEntry(entry);
            this.container.appendChild(entryElement);
        });
    }
}

// Make globally available
window.GuildActivityFeed = GuildActivityFeed;