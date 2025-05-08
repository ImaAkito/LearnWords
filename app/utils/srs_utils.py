import json
import random
from datetime import datetime, timedelta
from app import db
from app.models.models import Word, Repetition, Mistake, Test, UserProgress, TestSession
from sqlalchemy.sql import func

def add_new_word(word, translation, example=None, context=None, user_id=None):
    """Добавляет новое слово в базу данных и создает связанные записи"""
    # Проверяем, существует ли такое слово
    existing_word = Word.query.filter_by(word=word).first()
    if existing_word:
        return None, "Слово уже существует"
    
    # Создаем новое слово
    new_word = Word(
        word=word,
        translation=translation,
        example=example,
        context=context
    )
    db.session.add(new_word)
    db.session.flush()  # Для получения ID слова
    
    # Создаем запись для повторений
    repetition = Repetition(
        word_id=new_word.id,
        user_id=user_id,
        user_level=0,
        next_review_date=datetime.utcnow().date()
    )
    db.session.add(repetition)
    
    # Создаем запись для ошибок
    mistake = Mistake(
        word_id=new_word.id,
        mistake_count=0
    )
    db.session.add(mistake)
    
    db.session.commit()
    return new_word, "Слово успешно добавлено"

def get_words_for_review():
    """Получает слова для повторения на сегодня"""
    today = datetime.utcnow().date()
    repetitions = Repetition.query.filter(Repetition.next_review_date <= today).all()
    
    words_data = []
    for rep in repetitions:
        word = Word.query.get(rep.word_id)
        words_data.append({
            'id': word.id,
            'word': word.word,
            'translation': word.translation,
            'example': word.example,
            'context': word.context,
            'level': rep.user_level,
            'repetition_id': rep.id
        })
    
    return words_data

def update_streak():
    """Обновляет полосу успеха пользователя"""
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    today_progress = UserProgress.query.filter_by(date=today).first()
    yesterday_progress = UserProgress.query.filter_by(date=yesterday).first()
    
    if not today_progress:
        today_progress = UserProgress(date=today, streak=0)
        db.session.add(today_progress)
    
    # Если у нас есть прогресс за вчера и пользователь выполнил хотя бы одно повторение сегодня
    if yesterday_progress and today_progress.words_reviewed > 0:
        today_progress.streak = yesterday_progress.streak + 1
        
        # Начисляем бонусные очки за серию повторений более 3 дней
        if today_progress.streak >= 3:
            today_progress.points += 20  # Бонус за серию
    elif today_progress.words_reviewed == 0:
        # Сбрасываем серию, если нет повторений сегодня
        today_progress.streak = 0
    
    db.session.commit()
    return today_progress.streak

def create_test_for_word(word_id, test_type='multiple_choice', difficulty=None):
    """Создает тест для слова с указанным типом и сложностью
        word_id (int): ID слова
        test_type (str): Тип теста (multiple_choice, translation, matching)
        difficulty (int): Сложность теста (если None, будет взята из уровня слова)
    """
    word = Word.query.get(word_id)
    if not word:
        return None
    
    # Проверяем, есть ли уже тест для этого слова и типа
    existing_test = Test.query.filter_by(word_id=word_id, test_type=test_type).first()
    if existing_test:
        return existing_test
    
    # Если сложность не указана, берем ее из уровня слова
    if difficulty is None:
        repetition = Repetition.query.filter_by(word_id=word_id).first()
        if repetition:
            difficulty = min(repetition.user_level, 5)
        else:
            difficulty = 1
    
    if test_type == 'multiple_choice':
        return _create_multiple_choice_test(word, difficulty)
    elif test_type == 'translation':
        return _create_translation_test(word, difficulty)
    elif test_type == 'matching':
        return _create_matching_test(word, difficulty)
    else:
        # По умолчанию создаем тест с множественным выбором
        return _create_multiple_choice_test(word, difficulty)

def _create_multiple_choice_test(word, difficulty):
    # Количество вариантов зависит от сложности
    option_count = min(3 + difficulty, 6)
    
    # Получаем другие слова для создания вариантов
    other_words = Word.query.filter(Word.id != word.id).order_by(func.random()).limit(option_count - 1).all()
    
    # Создаем варианты ответов
    options = [word.translation]
    for other_word in other_words:
        options.append(other_word.translation)
    
    # Перемешиваем варианты
    random.shuffle(options)
    
    # Создаем тест
    test = Test(
        word_id=word.id,
        question=f"Выберите правильный перевод слова '{word.word}'",
        options=json.dumps(options),
        correct_option=word.translation,
        test_type='multiple_choice',
        difficulty=difficulty
    )
    
    db.session.add(test)
    db.session.commit()
    
    return test

def _create_translation_test(word, difficulty):
    # Для теста на перевод варианты не нужны, но формат хранения сохраняем
    test = Test(
        word_id=word.id,
        question=f"Введите перевод слова '{word.word}'",
        options=json.dumps([]),  # Пустой список опций
        correct_option=word.translation,
        test_type='translation',
        difficulty=difficulty
    )
    
    db.session.add(test)
    db.session.commit()
    
    return test

def _create_matching_test(word, difficulty):
    # Получаем другие слова для сопоставления
    match_count = min(3 + difficulty, 6)
    other_words = Word.query.filter(Word.id != word.id).order_by(func.random()).limit(match_count - 1).all()
    
    # Создаем пары для сопоставления
    words = [{'id': word.id, 'word': word.word, 'translation': word.translation}]
    for other_word in other_words:
        words.append({'id': other_word.id, 'word': other_word.word, 'translation': other_word.translation})
    
    # Создаем тест
    test = Test(
        word_id=word.id,
        question=f"Сопоставьте слова с их переводами",
        options=json.dumps(words),
        correct_option=json.dumps({w['word']: w['translation'] for w in words}),
        test_type='matching',
        difficulty=difficulty
    )
    
    db.session.add(test)
    db.session.commit()
    
    return test

def create_test_session(session_type, difficulty=None, word_count=10, category_id=None):
    # Если сложность не указана, используем автовыбор на основе прогресса
    if difficulty is None:
        progress = UserProgress.get_or_create_today()
        if progress.points < 200:
            difficulty = 1
        elif progress.points < 500:
            difficulty = 2
        elif progress.points < 1000:
            difficulty = 3
        elif progress.points < 2000:
            difficulty = 4
        else:
            difficulty = 5
    
    # Выбираем слова для теста в зависимости от типа сессии
    if session_type == 'daily':
        # Для ежедневного теста берем из слов для повторения сегодня
        today = datetime.utcnow().date()
        word_ids = [r.word_id for r in Repetition.query.filter(
            Repetition.next_review_date <= today
        ).order_by(func.random()).limit(word_count).all()]
        
        # Если слов для повторения недостаточно, добавляем случайные
        if len(word_ids) < word_count:
            additional_ids = [w.id for w in Word.query.filter(~Word.id.in_(word_ids))
                             .order_by(func.random()).limit(word_count - len(word_ids)).all()]
            word_ids.extend(additional_ids)
    
    elif session_type == 'thematic':
        if category_id:
            # Для тематического теста с указанной категорией выбираем слова из этой категории
            word_ids = [w.id for w in Word.query.filter_by(category_id=category_id)
                       .order_by(func.random()).limit(word_count).all()]
            
            # Если слов в категории недостаточно, добавляем случайные
            if len(word_ids) < word_count:
                additional_ids = [w.id for w in Word.query.filter(~Word.id.in_(word_ids))
                                .order_by(func.random()).limit(word_count - len(word_ids)).all()]
                word_ids.extend(additional_ids)
        else:
            # Для тематического теста без указанной категории выбираем слова на основе выявленных ошибок
            mistake_word_ids = [m.word_id for m in Mistake.query.filter(
                Mistake.mistake_count > 0
            ).order_by(Mistake.mistake_count.desc()).limit(word_count).all()]
            
            # Если ошибок недостаточно, добавляем случайные
            if len(mistake_word_ids) < word_count:
                additional_ids = [w.id for w in Word.query.filter(~Word.id.in_(mistake_word_ids))
                                .order_by(func.random()).limit(word_count - len(mistake_word_ids)).all()]
                word_ids = mistake_word_ids + additional_ids
            else:
                word_ids = mistake_word_ids[:word_count]
    
    else:
        # Для кастомного теста просто выбираем случайные слова
        word_ids = [w.id for w in Word.query.order_by(func.random()).limit(word_count).all()]
    
    # Создаем тестовую сессию
    test_session = TestSession(
        session_type=session_type,
        difficulty=difficulty,
        word_count=len(word_ids),
        total_questions=len(word_ids),
        words=json.dumps(word_ids)
    )
    
    db.session.add(test_session)
    db.session.commit()
    
    return test_session

def check_achievements(user_progress):
    """Проверяет и возвращает достижения пользователя"""
    achievements = []
    
    # Проверяем количество изученных слов
    total_words = Word.query.count()
    if total_words >= 10:
        achievements.append("Первые 10 слов")
    
    # Проверяем streak
    if user_progress.streak >= 3:
        achievements.append("3 дня подряд")
    
    # Проверяем слова без ошибок
    mastered_words = db.session.query(Word).join(
        Repetition, Word.id == Repetition.word_id
    ).filter(
        Repetition.user_level >= 3
    ).join(
        Mistake, Word.id == Mistake.word_id
    ).filter(
        Mistake.mistake_count == 0
    ).count()
    
    if mastered_words >= 10:
        achievements.append("10 слов без ошибок")
    
    return achievements

def get_user_rank(points):
    if points < 100:
        return "Новичок"
    elif points < 500:
        return "Ученик"
    elif points < 1000:
        return "Мастер"
    elif points < 2000:
        return "Профи"
    else:
        return "Мастер слов"