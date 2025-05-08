document.addEventListener('DOMContentLoaded', function() {
    // Плавная прокрутка для якорных ссылок
    const anchors = document.querySelectorAll('a[href^="#"]');
    anchors.forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                window.scrollTo({
                    top: target.offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Анимация для раздела особенностей
    const featureCards = document.querySelectorAll('.feature-card');
    
    function checkScroll() {
        featureCards.forEach(card => {
            const cardTop = card.getBoundingClientRect().top;
            const triggerPoint = window.innerHeight * 0.8;
            
            if (cardTop < triggerPoint) {
                card.classList.add('animated');
            }
        });
    }
    
    // Проверяем при загрузке
    checkScroll();
    
    // Проверяем при скролле
    window.addEventListener('scroll', checkScroll);
    
    // Простая анимация для чисел в разделе статистики (если будет добавлен)
    function animateNumbers() {
        const numberElements = document.querySelectorAll('.stats-number');
        
        numberElements.forEach(element => {
            const targetNumber = parseInt(element.getAttribute('data-target'));
            let count = 0;
            const duration = 2000; // ms
            const interval = 50; // ms
            const increment = targetNumber / (duration / interval);
            
            const timer = setInterval(() => {
                count += increment;
                if (count >= targetNumber) {
                    element.textContent = targetNumber;
                    clearInterval(timer);
                } else {
                    element.textContent = Math.floor(count);
                }
            }, interval);
        });
    }
    
    // Обработка событий для слайдера отзывов
    const testimonialSlider = document.querySelector('.testimonials-slider');
    if (testimonialSlider) {
        let isDown = false;
        let startX;
        let scrollLeft;

        testimonialSlider.addEventListener('mousedown', (e) => {
            isDown = true;
            testimonialSlider.classList.add('active');
            startX = e.pageX - testimonialSlider.offsetLeft;
            scrollLeft = testimonialSlider.scrollLeft;
        });

        testimonialSlider.addEventListener('mouseleave', () => {
            isDown = false;
            testimonialSlider.classList.remove('active');
        });

        testimonialSlider.addEventListener('mouseup', () => {
            isDown = false;
            testimonialSlider.classList.remove('active');
        });

        testimonialSlider.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - testimonialSlider.offsetLeft;
            const walk = (x - startX) * 2;
            testimonialSlider.scrollLeft = scrollLeft - walk;
        });
    }
});