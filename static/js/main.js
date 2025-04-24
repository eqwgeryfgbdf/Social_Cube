// Theme Management
class ThemeManager {
    constructor() {
        this.darkModeKey = 'socialcube_dark_mode';
        this.init();
    }

    init() {
        // 檢查本地存儲的主題設定
        const isDarkMode = localStorage.getItem(this.darkModeKey) === 'true';
        if (isDarkMode) {
            document.documentElement.classList.add('dark-mode');
        }

        // 監聽系統主題變更
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            this.setDarkMode(e.matches);
        });
    }

    setDarkMode(enabled) {
        document.documentElement.classList.toggle('dark-mode', enabled);
        localStorage.setItem(this.darkModeKey, enabled);
    }

    toggleDarkMode() {
        const isDarkMode = document.documentElement.classList.toggle('dark-mode');
        localStorage.setItem(this.darkModeKey, isDarkMode);
    }
}

// UI Components
class UIManager {
    constructor() {
        this.initTooltips();
        this.initDraggableTables();
        this.initMobileNav();
        this.initScrollSpy();
    }

    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }

    initDraggableTables() {
        document.querySelectorAll('.draggable-table tbody').forEach(tbody => {
            new Sortable(tbody, {
                animation: 150,
                handle: '.drag-handle',
                onEnd: function(evt) {
                    // 發送新順序到服務器
                    const newOrder = Array.from(evt.to.children).map(tr => tr.dataset.id);
                    this.updateOrder(newOrder);
                }
            });
        });
    }

    initMobileNav() {
        const toggle = document.querySelector('.mobile-nav-toggle');
        const sidebar = document.querySelector('.sidebar');
        
        if (toggle && sidebar) {
            toggle.addEventListener('click', () => {
                sidebar.classList.toggle('active');
            });

            // 點擊外部關閉側邊欄
            document.addEventListener('click', (e) => {
                if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
                    sidebar.classList.remove('active');
                }
            });
        }
    }

    initScrollSpy() {
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            // 監聽滾動位置以更新導航狀態
            mainContent.addEventListener('scroll', () => {
                const scrollPosition = mainContent.scrollTop;
                document.querySelectorAll('[data-spy="scroll"]').forEach(section => {
                    const sectionTop = section.offsetTop;
                    const sectionHeight = section.offsetHeight;
                    if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                        const id = section.getAttribute('id');
                        document.querySelector(`.nav-link[href="#${id}"]`)?.classList.add('active');
                    } else {
                        const id = section.getAttribute('id');
                        document.querySelector(`.nav-link[href="#${id}"]`)?.classList.remove('active');
                    }
                });
            });
        }
    }

    async updateOrder(newOrder) {
        try {
            const response = await fetch('/api/update-order/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ order: newOrder })
            });
            
            if (!response.ok) {
                throw new Error('更新順序失敗');
            }
            
            const result = await response.json();
            if (result.success) {
                this.showToast('順序更新成功', 'success');
            }
        } catch (error) {
            console.error('更新順序時發生錯誤:', error);
            this.showToast('更新順序失敗，請稍後再試', 'error');
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} position-fixed bottom-0 end-0 m-3`;
        toast.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">通知</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        document.body.appendChild(toast);
        new bootstrap.Toast(toast).show();
        
        // 自動移除
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Form Validation
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
        this.form.querySelectorAll('input, select, textarea').forEach(field => {
            field.addEventListener('blur', () => {
                this.validateField(field);
            });
        });
    }

    validateForm() {
        let isValid = true;
        this.form.querySelectorAll('input, select, textarea').forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        return isValid;
    }

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        // 必填欄位檢查
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = '此欄位為必填';
        }

        // 電子郵件格式檢查
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = '請輸入有效的電子郵件地址';
            }
        }

        // 密碼強度檢查
        if (field.type === 'password' && value) {
            if (value.length < 8) {
                isValid = false;
                errorMessage = '密碼長度至少需要8個字元';
            } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(value)) {
                isValid = false;
                errorMessage = '密碼需包含大小寫字母和數字';
            }
        }

        // 更新 UI
        this.updateFieldStatus(field, isValid, errorMessage);
        return isValid;
    }

    updateFieldStatus(field, isValid, errorMessage = '') {
        const feedbackElement = field.nextElementSibling;
        
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
            if (feedbackElement?.classList.contains('invalid-feedback')) {
                feedbackElement.remove();
            }
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            if (!feedbackElement?.classList.contains('invalid-feedback')) {
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = errorMessage;
                field.parentNode.insertBefore(feedback, field.nextSibling);
            } else {
                feedbackElement.textContent = errorMessage;
            }
        }
    }
}

// API 請求處理
class APIHandler {
    constructor() {
        this.baseUrl = '/api';
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    async request(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            }
        };

        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...defaultOptions,
                ...options,
                headers: {
                    ...defaultOptions.headers,
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return { success: true, data };
        } catch (error) {
            console.error('API request failed:', error);
            return { success: false, error: error.message };
        }
    }

    // 常用 API 方法
    async getBotList() {
        return this.request('/bots/');
    }

    async createBot(botData) {
        return this.request('/bots/', {
            method: 'POST',
            body: JSON.stringify(botData)
        });
    }

    async updateBot(botId, botData) {
        return this.request(`/bots/${botId}/`, {
            method: 'PUT',
            body: JSON.stringify(botData)
        });
    }

    async deleteBot(botId) {
        return this.request(`/bots/${botId}/`, {
            method: 'DELETE'
        });
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
    window.uiManager = new UIManager();
    window.api = new APIHandler();

    // 初始化所有表單驗證
    document.querySelectorAll('form').forEach(form => {
        new FormValidator(form);
    });

    // Wait for the DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize tooltips lazily
        const initTooltips = () => {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
        };

        // Lazy load tooltips when needed
        const tooltipContainer = document.querySelector('.tooltip-container');
        if (tooltipContainer) {
            const tooltipObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        initTooltips();
                        tooltipObserver.disconnect();
                    }
                });
            });
            tooltipObserver.observe(tooltipContainer);
        }

        // Add smooth scrolling using requestAnimationFrame
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset;
                    const startPosition = window.pageYOffset;
                    const distance = targetPosition - startPosition;
                    let startTime = null;

                    function animation(currentTime) {
                        if (startTime === null) startTime = currentTime;
                        const timeElapsed = currentTime - startTime;
                        const run = ease(timeElapsed, startPosition, distance, 500);
                        window.scrollTo(0, run);
                        if (timeElapsed < 500) requestAnimationFrame(animation);
                    }

                    function ease(t, b, c, d) {
                        t /= d / 2;
                        if (t < 1) return c / 2 * t * t + b;
                        t--;
                        return -c / 2 * (t * (t - 2) - 1) + b;
                    }

                    requestAnimationFrame(animation);
                }
            });
        });

        // Auto-hide alerts after 5 seconds with fade effect
        const alerts = document.querySelectorAll('.alert');
        if (alerts.length) {
            const alertObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            entry.target.style.opacity = '0';
                            entry.target.style.transition = 'opacity 0.5s ease';
                            setTimeout(() => {
                                const bsAlert = new bootstrap.Alert(entry.target);
                                bsAlert.close();
                            }, 500);
                        }, 5000);
                    }
                });
            });
            alerts.forEach(alert => alertObserver.observe(alert));
        }

        // Optimize card animations using event delegation and requestAnimationFrame
        const cardContainer = document.querySelector('.card-container');
        if (cardContainer) {
            cardContainer.addEventListener('mouseover', function(e) {
                const card = e.target.closest('.card');
                if (card) {
                    requestAnimationFrame(() => {
                        card.style.transform = 'translateY(-5px)';
                        card.style.transition = 'transform 0.2s ease-in-out';
                    });
                }
            });

            cardContainer.addEventListener('mouseout', function(e) {
                const card = e.target.closest('.card');
                if (card) {
                    requestAnimationFrame(() => {
                        card.style.transform = 'translateY(0)';
                    });
                }
            });
        }

        // Add lazy loading for images
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });
        images.forEach(img => imageObserver.observe(img));
    });
}); 