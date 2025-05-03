/**
 * Command Log Viewer Component
 * 
 * Displays real-time command execution logs via WebSockets
 */
class CommandLogViewer {
    /**
     * Initialize the Command Log Viewer
     * 
     * @param {Object} options Configuration options
     * @param {string} options.containerSelector CSS selector for the log container (required)
     * @param {number} options.botId Bot ID to filter by (optional)
     * @param {string} options.guildId Guild ID to filter by (optional)
     * @param {number} options.maxEntries Maximum number of entries to display (default: 100)
     * @param {boolean} options.autoConnect Whether to connect automatically (default: true)
     * @param {Function} options.formatEntry Custom function to format each entry (optional)
     */
    constructor(options = {}) {
        if (!options.containerSelector) {
            throw new Error('CommandLogViewer requires containerSelector option');
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
            throw new Error(`Command log container not found: ${this.options.containerSelector}`);
        }
        
        this.connected = false;
        this.connectionId = `command-logs-${this.options.botId || 'all'}-${this.options.guildId || 'all'}`;
        this.entries = [];
        
        // Initialize
        this.render();
        
        if (this.options.autoConnect) {
            this.connect();
        }
    }
    
    /**
     * Connect to the WebSocket for command log updates
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
            let url = '/ws/command_logs/';
            
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
                        console.log(`Command logs WebSocket connected: ${url}`);
                        this.addSystemEntry('Connected to command log feed');
                    },
                    onClose: () => {
                        this.connected = false;
                        console.log('Command logs WebSocket disconnected');
                        this.addSystemEntry('Disconnected from command log feed');
                    },
                    onMessage: this.handleMessage.bind(this),
                    onError: (e) => {
                        console.error('Command logs WebSocket error:', e);
                        this.addSystemEntry('Error in command log feed connection', true);
                    }
                },
                true // Auto reconnect
            );
            
            return true;
        } catch (error) {
            console.error('Error connecting to command logs WebSocket:', error);
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
            commandId: data.command_id,
            commandName: data.command_name,
            botId: data.bot_id,
            userId: data.user_id,
            status: data.status,
            guildId: data.guild_id,
            details: data.details || {},
            timestamp: data.timestamp ? new Date(data.timestamp) : new Date()
        });
        
        // Dispatch custom event
        const event = new CustomEvent('commandLog', {
            detail: {
                commandId: data.command_id,
                commandName: data.command_name,
                botId: data.bot_id,
                userId: data.user_id,
                status: data.status,
                guildId: data.guild_id,
                details: data.details || {},
                timestamp: data.timestamp
            }
        });
        document.dispatchEvent(event);
    }
    
    /**
     * Add a regular log entry
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
     * Add a system entry to the logs
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
     * Clear all entries from the logs
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
        entryElement.className = 'border-b border-gray-200 dark:border-gray-700 p-3';
        
        if (entry.isSystem) {
            // System message
            entryElement.classList.add(entry.isError ? 'bg-red-50 dark:bg-red-900/20' : 'bg-blue-50 dark:bg-blue-900/20');
            
            const messageElement = document.createElement('p');
            messageElement.className = entry.isError ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400';
            messageElement.textContent = entry.message;
            
            const timeElement = document.createElement('span');
            timeElement.className = 'text-xs text-gray-500 dark:text-gray-400 block mt-1';
            timeElement.textContent = this.formatTime(entry.timestamp);
            
            entryElement.appendChild(messageElement);
            entryElement.appendChild(timeElement);
            
        } else {
            // Regular command log
            // Set background color based on status
            if (entry.status === 'success') {
                entryElement.classList.add('bg-green-50', 'dark:bg-green-900/10');
            } else if (entry.status === 'error') {
                entryElement.classList.add('bg-red-50', 'dark:bg-red-900/10');
            }
            
            const headerElement = document.createElement('div');
            headerElement.className = 'flex items-center justify-between mb-1';
            
            const commandElement = document.createElement('h4');
            commandElement.className = 'font-medium text-gray-900 dark:text-gray-100';
            
            // Format command name with status indicator
            const statusIndicator = document.createElement('span');
            statusIndicator.className = 'inline-block w-2 h-2 rounded-full mr-2';
            
            if (entry.status === 'success') {
                statusIndicator.classList.add('bg-green-500');
            } else if (entry.status === 'error') {
                statusIndicator.classList.add('bg-red-500');
            } else {
                statusIndicator.classList.add('bg-yellow-500');
            }
            
            commandElement.appendChild(statusIndicator);
            commandElement.appendChild(document.createTextNode(`/${entry.commandName}`));
            
            const timeElement = document.createElement('span');
            timeElement.className = 'text-xs text-gray-500 dark:text-gray-400';
            timeElement.textContent = this.formatTime(entry.timestamp);
            
            headerElement.appendChild(commandElement);
            headerElement.appendChild(timeElement);
            
            const metaElement = document.createElement('div');
            metaElement.className = 'text-sm text-gray-600 dark:text-gray-300';
            
            // Include bot info
            const botSpan = document.createElement('span');
            botSpan.className = 'mr-3';
            botSpan.textContent = `Bot #${entry.botId}`;
            metaElement.appendChild(botSpan);
            
            // Include user info
            const userSpan = document.createElement('span');
            userSpan.className = 'mr-3';
            userSpan.textContent = `User: ${entry.userId}`;
            metaElement.appendChild(userSpan);
            
            // Include guild info if available
            if (entry.guildId) {
                const guildSpan = document.createElement('span');
                guildSpan.textContent = `Guild: ${entry.guildId}`;
                metaElement.appendChild(guildSpan);
            }
            
            entryElement.appendChild(headerElement);
            entryElement.appendChild(metaElement);
            
            // Add details if available
            if (entry.details && Object.keys(entry.details).length > 0) {
                const detailsElement = document.createElement('div');
                detailsElement.className = 'mt-2 text-sm';
                
                // Add command options if available
                if (entry.details.options) {
                    const optionsElement = document.createElement('div');
                    optionsElement.className = 'text-gray-600 dark:text-gray-300';
                    
                    try {
                        let optionsText = '';
                        if (typeof entry.details.options === 'string') {
                            optionsText = entry.details.options;
                        } else {
                            optionsText = JSON.stringify(entry.details.options);
                        }
                        
                        optionsElement.textContent = `Options: ${optionsText}`;
                    } catch (e) {
                        optionsElement.textContent = 'Options: [Error parsing options]';
                    }
                    
                    detailsElement.appendChild(optionsElement);
                }
                
                // Add error message if status is error
                if (entry.status === 'error' && entry.details.error) {
                    const errorElement = document.createElement('div');
                    errorElement.className = 'text-red-600 dark:text-red-400 mt-1';
                    errorElement.textContent = `Error: ${entry.details.error}`;
                    detailsElement.appendChild(errorElement);
                }
                
                entryElement.appendChild(detailsElement);
            }
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
     * Render the log entries in the container
     */
    render() {
        // Clear the container
        this.container.innerHTML = '';
        
        // If no entries, show empty state
        if (this.entries.length === 0) {
            const emptyElement = document.createElement('div');
            emptyElement.className = 'p-4 text-center text-gray-500 dark:text-gray-400';
            emptyElement.textContent = 'No command logs yet';
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
window.CommandLogViewer = CommandLogViewer;