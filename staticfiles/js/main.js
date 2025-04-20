// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Hamburger menu functionality
    const hamburger = document.querySelector('.hamburger');
    const nav = document.querySelector('.nav');
    
    if (hamburger) {
        hamburger.addEventListener('click', function() {
            this.classList.toggle('active');
            nav.classList.toggle('active');
        });
    }

    // Back to top button functionality
    const backToTop = document.getElementById('backToTop');
    
    if (backToTop) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });

        backToTop.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Initialize animations for elements with fade-in class
    const fadeElements = document.querySelectorAll('.fade-in');
    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    });

    fadeElements.forEach(element => {
        fadeObserver.observe(element);
    });

    // Get the start button element
    const startButton = document.getElementById('startButton');
    
    // Add click event listener to the start button
    if (startButton) {
        startButton.addEventListener('click', function() {
            // Smooth scroll to features section
            const featuresSection = document.querySelector('.features');
            if (featuresSection) {
                featuresSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    }

    // Add smooth scrolling for all navigation links
    const navigationLinks = document.querySelectorAll('nav a');
    navigationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId.startsWith('#')) {
                e.preventDefault();
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Add animation to feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.classList.add('fade-in');
    });

    // Handle message dismissal with animation
    const messages = document.querySelectorAll('.message');
    messages.forEach(message => {
        // Add close button with animation
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '×';
        closeButton.className = 'message-close';
        closeButton.style.cssText = `
            float: right;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0 0.5rem;
            transition: all 0.3s ease;
        `;
        message.insertBefore(closeButton, message.firstChild);

        // Add hover effect to close button
        closeButton.addEventListener('mouseenter', () => {
            closeButton.style.transform = 'rotate(90deg)';
        });
        closeButton.addEventListener('mouseleave', () => {
            closeButton.style.transform = 'rotate(0)';
        });

        // Add click event to close button
        closeButton.addEventListener('click', () => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                message.remove();
            }, 300);
        });

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });

    // Theme switching functionality
    const themeSwitch = document.querySelector('.theme-switch input[type="checkbox"]');
    const currentTheme = localStorage.getItem('theme');

    // Set initial theme with animation
    if (currentTheme) {
        document.documentElement.setAttribute('data-theme', currentTheme);
        if (currentTheme === 'dark') {
            themeSwitch.checked = true;
        }
    }

    // Handle theme switch with animation
    themeSwitch.addEventListener('change', (e) => {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    });

    // Language selection functionality
    const languageSelect = document.querySelector('.language-selector select');
    if (languageSelect) {
        languageSelect.addEventListener('change', (e) => {
            const form = e.target.closest('form');
            if (form) {
                // Add loading spinner
                const spinner = document.createElement('div');
                spinner.className = 'spinner';
                form.appendChild(spinner);
                
                form.submit();
            }
        });
    }

    // Initialize animations for bot cards
    const botCards = document.querySelectorAll('.bot-card');
    botCards.forEach(card => {
        card.classList.add('fade-in');
    });

    // Animate bot cards on scroll
    const botCardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                botCardObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    botCards.forEach(card => {
        botCardObserver.observe(card);
    });

    // Form validation and animation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('invalid', (e) => {
                e.preventDefault();
                input.classList.add('invalid');
            });
            
            input.addEventListener('input', () => {
                if (input.validity.valid) {
                    input.classList.remove('invalid');
                }
            });
        });
    });
}); 