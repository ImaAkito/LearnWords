# LearnWords

LearnWords — платформа интервальных повторений с геймификацией, контекстом и аналитикой для изучения английских слов.

## Описание

LearnWords помогает эффективно запоминать английские слова с использованием:
- Алгоритма интервальных повторений (SRS, на основе SM-2)
- Оценки запоминания слов от 0 до 5
- Контекста из фильмов и мемов (word-in-context)
- Мини-тестов для закрепления знаний
- Подробной аналитики прогресса и ошибок
- Геймификации процесса обучения (очки, достижения, ранги)

## Функциональность

- Просмотр слов для повторения на сегодня
- Оценка знания слов по шкале от 0 до 5
- Просмотр примеров использования слов в контексте фильмов/мемов
- Прохождение мини-тестов для закрепления знаний
- Отслеживание прогресса и ошибок в виде отчётов и графиков
- Получение рекомендаций по сложным словам
- Авторизация и персонализация процесса обучения
- Отслеживание личной статистики и достижений

## Установка и запуск

### Требования
- Python 3.8+
- Flask
- SQLAlchemy
- Flask-Login
- Другие зависимости (см. requirements.txt)

### Установка

1. Клонируйте репозиторий:
```
git clone https://github.com/user/LearnWords.git
cd LearnWords
```

2. Создайте и активируйте виртуальное окружение:
```
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. Установите зависимости:
```
pip install -r requirements.txt
```

### Запуск

1. Запустите приложение:
```
python main.py
```

2. Откройте в браузере адрес: 
```
http://127.0.0.1:5000/
```

### База данных

Приложение использует SQLite базу данных, которая находится в директории `instance`. База данных уже содержит более 150 слов с примерами, контекстом и оценками сложности.

## Структура проекта

```
LearnWords/
├── app/                      # Основной код приложения
│   ├── models/               # Модели базы данных
│   │   ├── models.py         # Основные модели (слова, повторения)
│   │   └── user.py           # Модель пользователя
│   ├── routes/               # Маршруты Flask
│   │   ├── auth.py           # Маршруты авторизации
│   │   └── main_routes.py    # Основные маршруты приложения
│   ├── static/               # Статические файлы (CSS, JS)
│   │   ├── css/              # Стили
│   │   ├── js/               # JavaScript
│   │   └── uploads/          # Загруженные пользователем файлы
│   ├── templates/            # HTML-шаблоны
│   └── utils/                # Вспомогательные функции
│       ├── auth_utils.py     # Функции авторизации
│       └── srs_utils.py      # Функции алгоритма повторений
├── instance/                 # Экземпляр базы данных
├── migrations/               # Миграции базы данных
├── main.py                   # Точка входа в приложение
└── requirements.txt          # Зависимости проекта
```
