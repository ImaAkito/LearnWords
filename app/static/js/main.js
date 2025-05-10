/**
 * Основной JavaScript-файл для LearnWords
 */

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всплывающих подсказок Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Функция для анимации появления элементов при скролле
    function animateOnScroll() {
        const elements = document.querySelectorAll('.animate-on-scroll');
        elements.forEach(element => {
            const position = element.getBoundingClientRect();
            // Если элемент виден на экране
            if(position.top < window.innerHeight && position.bottom >= 0) {
                element.classList.add('slide-up');
            }
        });
    }

    // Добавляем класс для анимации при скролле
    window.addEventListener('scroll', animateOnScroll);
    // Запускаем один раз при загрузке страницы
    animateOnScroll();

    // Обработка формы добавления нового слова
    const addWordForm = document.getElementById('addWordForm');
    if (addWordForm) {
        addWordForm.addEventListener('submit', function(event) {
            // Валидация формы (пример простой валидации)
            const wordInput = document.getElementById('word');
            const translationInput = document.getElementById('translation');
            
            if (!wordInput.value.trim() || !translationInput.value.trim()) {
                event.preventDefault();
                alert('Пожалуйста, заполните обязательные поля: Слово и Перевод');
                return false;
            }
        });
    }

    // Функция для обновления даты и времени
    function updateDateTime() {
        const dateTimeElement = document.getElementById('current-date-time');
        if (dateTimeElement) {
            const now = new Date();
            const options = { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            dateTimeElement.textContent = now.toLocaleDateString('ru-RU', options);
        }
    }

    // Обновляем дату и время каждую минуту
    updateDateTime();
    setInterval(updateDateTime, 60000);

    // Показываем уведомление о необходимости повторения
    function showReminderNotification() {
        const wordCount = document.getElementById('words-to-review-count');
        if (wordCount && parseInt(wordCount.textContent) > 0) {
            const wordsToReview = parseInt(wordCount.textContent);
            
            // Проверяем поддержку уведомлений
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('LearnWords напоминает', {
                    body: `У вас ${wordsToReview} слов для повторения сегодня!`,
                    icon: '/static/img/logo.png'
                });
            }
        }
    }

    // Запрашиваем разрешение на отправку уведомлений
    if ('Notification' in window && Notification.permission !== 'denied') {
        const notificationBtn = document.getElementById('enable-notifications');
        if (notificationBtn) {
            notificationBtn.addEventListener('click', function() {
                Notification.requestPermission().then(function(permission) {
                    if (permission === 'granted') {
                        showReminderNotification();
                    }
                });
            });
        }
    }
}); 