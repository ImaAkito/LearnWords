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
    
    // Добавляем эффекты при наведении на кнопки
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseover', function() {
            this.style.transform = 'scale(1.05)';
        });
        
        button.addEventListener('mouseout', function() {
            this.style.transform = 'scale(1)';
        });
    });
});