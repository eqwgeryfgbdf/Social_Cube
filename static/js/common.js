// 主題管理
class ThemeManager {
    constructor() {
        this.themeToggle = document.getElementById('theme-toggle');
        this.themeIcon = this.themeToggle?.querySelector('i');
        this.init();
    }

    init() {
        if (!this.themeToggle) return;
        
        // 檢查本地存儲的主題設置
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            this.setTheme(savedTheme === 'dark');
        } else {
            // 檢查系統主題偏好
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.setTheme(prefersDark);
        }

        // 監聽主題切換按鈕
        this.themeToggle.addEventListener('click', () => {
            const isDark = document.documentElement.classList.toggle('dark-mode');
            this.setTheme(isDark);
        });

        // 監聽系統主題變化
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.setTheme(e.matches);
            }
        });
    }

    setTheme(isDark) {
        document.documentElement.classList.toggle('dark-mode', isDark);
        if (this.themeIcon) {
            this.themeIcon.className = isDark ? 'fas fa-moon' : 'fas fa-sun';
        }
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }
}

// 提示管理
class NotificationManager {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);
        
        // 添加樣式
        const style = document.createElement('style');
        style.textContent = `
            .notification-container {
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 9999;
            }

            .m3-notification {
                background-color: var(--bg-primary);
                color: var(--text-primary);
                padding: 16px;
                border-radius: 8px;
                margin-bottom: 10px;
                box-shadow: var(--m3-elevation-2);
                display: flex;
                align-items: center;
                gap: 12px;
                min-width: 300px;
                max-width: 400px;
                animation: slideIn 0.3s ease-out;
                transition: all 0.3s ease-out;
            }

            .m3-notification.success { border-left: 4px solid #4CAF50; }
            .m3-notification.error { border-left: 4px solid #F44336; }
            .m3-notification.warning { border-left: 4px solid #FFC107; }
            .m3-notification.info { border-left: 4px solid #2196F3; }

            .m3-notification i {
                font-size: 20px;
            }

            .m3-notification .content {
                flex-grow: 1;
            }

            .m3-notification .close {
                cursor: pointer;
                padding: 4px;
                border-radius: 50%;
                transition: background-color 0.2s;
            }

            .m3-notification .close:hover {
                background-color: var(--m3-state-hover);
            }

            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `m3-notification ${type}`;

        let icon;
        switch (type) {
            case 'success':
                icon = 'fas fa-check-circle';
                break;
            case 'error':
                icon = 'fas fa-times-circle';
                break;
            case 'warning':
                icon = 'fas fa-exclamation-triangle';
                break;
            default:
                icon = 'fas fa-info-circle';
        }

        notification.innerHTML = `
            <i class="${icon}"></i>
            <div class="content">${message}</div>
            <div class="close"><i class="fas fa-times"></i></div>
        `;

        this.container.appendChild(notification);

        // 關閉按鈕事件
        notification.querySelector('.close').addEventListener('click', () => {
            this.hide(notification);
        });

        // 自動關閉
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    this.hide(notification);
                }
            }, duration);
        }

        return notification;
    }

    hide(notification) {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// 表單驗證
class FormValidator {
    constructor(form) {
        this.form = form;
        this.init();
    }

    init() {
        this.form.addEventListener('submit', (e) => {
            if (!this.validateForm()) {
                e.preventDefault();
            }
        });

        // 即時驗證
        this.form.querySelectorAll('input, textarea, select').forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
        });
    }

    validateForm() {
        let isValid = true;
        this.form.querySelectorAll('input, textarea, select').forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });
        return isValid;
    }

    validateField(input) {
        const value = input.value.trim();
        let isValid = true;
        let errorMessage = '';

        // 檢查必填欄位
        if (input.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = '此欄位為必填';
        }

        // 檢查最小長度
        if (input.minLength && value.length < input.minLength) {
            isValid = false;
            errorMessage = `最少需要 ${input.minLength} 個字元`;
        }

        // 檢查最大長度
        if (input.maxLength && value.length > input.maxLength) {
            isValid = false;
            errorMessage = `最多只能 ${input.maxLength} 個字元`;
        }

        // 檢查 pattern
        if (input.pattern && !new RegExp(input.pattern).test(value)) {
            isValid = false;
            errorMessage = input.title || '格式不正確';
        }

        // 檢查 email
        if (input.type === 'email' && value && !this.isValidEmail(value)) {
            isValid = false;
            errorMessage = '請輸入有效的電子郵件地址';
        }

        // 檢查 URL
        if (input.type === 'url' && value && !this.isValidUrl(value)) {
            isValid = false;
            errorMessage = '請輸入有效的網址';
        }

        this.showFieldError(input, errorMessage);
        return isValid;
    }

    showFieldError(input, message) {
        const container = input.parentElement;
        let errorElement = container.querySelector('.field-error');
        
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error text-danger mt-1';
            container.appendChild(errorElement);
        }

        if (message) {
            errorElement.textContent = message;
            input.classList.add('is-invalid');
        } else {
            errorElement.textContent = '';
            input.classList.remove('is-invalid');
        }
    }

    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }
}

// 錯誤處理
class ErrorHandler {
    static handle(error, context = '') {
        console.error(`[${context}]`, error);
        notifications.error(this.getErrorMessage(error));
    }

    static getErrorMessage(error) {
        if (typeof error === 'string') {
            return error;
        }
        
        if (error.response) {
            return error.response.data?.message || '伺服器錯誤，請稍後再試';
        }

        if (error.message) {
            return error.message;
        }

        return '發生未知錯誤，請稍後再試';
    }
}

// 初始化
const themeManager = new ThemeManager();
const notifications = new NotificationManager();

// 全局錯誤處理
window.addEventListener('error', (event) => {
    ErrorHandler.handle(event.error, 'Global Error');
});

window.addEventListener('unhandledrejection', (event) => {
    ErrorHandler.handle(event.reason, 'Unhandled Promise Rejection');
});

// 導出全局變數
window.notifications = notifications;
window.ErrorHandler = ErrorHandler;
window.FormValidator = FormValidator; 