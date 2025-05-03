document.addEventListener('DOMContentLoaded', () => {
    const botCards = document.querySelectorAll('.bot-card');
    const addBotBtn = document.querySelector('#add-bot-btn');
    const addBotDialog = document.querySelector('#add-bot-dialog');
    
    // Card hover effects
    const addHoverListeners = card => {
        card.addEventListener('mouseenter', () => card.classList.add('hover'));
        card.addEventListener('mouseleave', () => card.classList.remove('hover'));
    };

    botCards.forEach(addHoverListeners);

    // Bot status update
    const updateBotStatus = () => {
        botCards.forEach(card => {
            const statusDot = card.querySelector('.status-indicator');
            const botId = card.dataset.botId;
            
            fetch(`/bot/${botId}/status/`)
                .then(response => response.json())
                .then(data => {
                    statusDot.classList.remove(data.online ? 'status-offline' : 'status-online');
                    statusDot.classList.add(data.online ? 'status-online' : 'status-offline');
                    
                    // Update statistics if available
                    if (data.stats) {
                        card.querySelector('.server-count').textContent = data.stats.server_count;
                        card.querySelector('.user-count').textContent = data.stats.user_count;
                        card.querySelector('.command-count').textContent = data.stats.command_count;
                    }
                })
                .catch(error => {
                    console.error('Error fetching bot status:', error);
                    statusDot.classList.remove('status-online');
                    statusDot.classList.add('status-offline');
                });
        });
    };

    // Add bot dialog
    if (addBotBtn && addBotDialog) {
        addBotBtn.addEventListener('click', () => {
            addBotDialog.showModal();
        });

        addBotDialog.querySelector('.close-dialog').addEventListener('click', () => {
            addBotDialog.close();
        });

        const addBotForm = addBotDialog.querySelector('form');
        addBotForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(addBotForm);
            
            try {
                const response = await fetch('/bot/add/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });

                const data = await response.json();
                
                if (response.ok) {
                    showToast('success', '機器人新增成功！');
                    window.location.href = `/bot/${data.bot_id}/dashboard/`;
                } else {
                    showToast('error', data.error || '新增機器人時發生錯誤');
                }
            } catch (error) {
                console.error('Error adding bot:', error);
                showToast('error', '新增機器人時發生錯誤');
            }
        });
    }

    // Delete bot
    document.querySelectorAll('.delete-bot-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const botId = btn.dataset.botId;
            
            if (confirm('確定要刪除這個機器人嗎？此操作無法復原。')) {
                try {
                    const response = await fetch(`/bot/${botId}/delete/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        }
                    });

                    if (response.ok) {
                        showToast('success', '機器人已成功刪除');
                        const card = document.querySelector(`[data-bot-id="${botId}"]`);
                        card.remove();
                        
                        // Show empty state if no bots left
                        if (document.querySelectorAll('.bot-card').length === 0) {
                            document.querySelector('.empty-state').style.display = 'flex';
                        }
                    } else {
                        const data = await response.json();
                        showToast('error', data.error || '刪除機器人時發生錯誤');
                    }
                } catch (error) {
                    console.error('Error deleting bot:', error);
                    showToast('error', '刪除機器人時發生錯誤');
                }
            }
        });
    });

    // Initialize status updates
    updateBotStatus();
    setInterval(updateBotStatus, 30000);

    // Utility functions
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showToast(type, message) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }, 100);
    }
}); 