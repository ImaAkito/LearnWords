from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, session
from datetime import datetime
import json
from app import db
from app.models.models import Word, Repetition, Mistake, Test, UserProgress, TestSession, Category
from app.utils.srs_utils import add_new_word, update_streak, create_test_for_word, check_achievements, create_test_session
from app.utils.auth_utils import login_required, is_authenticated

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Главная страница приложения"""
    # Если пользователь не авторизован, показываем лендинг
    if not is_authenticated():
        return render_template('landing.html')
        
    # Для авторизованного пользователя показываем основную страницу
    user_id = session.get('user_id')
    
    # Получаем количество слов для повторения сегодня
    today = datetime.utcnow().date()
    words_to_review = Repetition.query.filter(
        Repetition.next_review_date <= today,
        Repetition.user_id == user_id
    ).count()
    
    # Получаем статистику пользователя
    progress = UserProgress.get_or_create_today(user_id=user_id)
    
    # Подсчитываем общее количество очков из всех записей прогресса
    total_points = db.session.query(db.func.sum(UserProgress.points)).filter(
        UserProgress.user_id == user_id
    ).scalar() or 0
    
    # Устанавливаем общее количество очков в объект прогресса
    progress.points = total_points
    
    return render_template('index.html', 
                           words_to_review=words_to_review, 
                           progress=progress)

@main_bp.route('/add_word', methods=['POST'])
@login_required
def add_word():
    """Добавляет новое слово в базу данных"""
    word = request.form.get('word')
    translation = request.form.get('translation')
    example = request.form.get('example')
    context = request.form.get('context')
    
    if not word or not translation:
        flash('Слово и перевод обязательны для заполнения.', 'danger')
        return redirect(url_for('main.index'))
    
    user_id = session.get('user_id')
    new_word, message = add_new_word(word, translation, example, context, user_id=user_id)
    
    if new_word:
        flash(f'Слово "{word}" успешно добавлено!', 'success')
    else:
        flash(message, 'warning')
    
    return redirect(url_for('main.index'))

@main_bp.route('/review')
@login_required
def review():
    """Страница для повторения слов, запланированных на сегодня"""
    user_id = session.get('user_id')
    today = datetime.utcnow().date()
    repetitions = Repetition.query.filter(
        Repetition.next_review_date <= today,
        Repetition.user_id == user_id
    ).all()
    
    if not repetitions:
        # Если нет слов для повторения, перенаправляем на главную
        return render_template('no_words.html')
    
    words_data = []
    for rep in repetitions:
        word = Word.query.get(rep.word_id)
        words_data.append({
            'id': word.id,
            'word': word.word,
            'translation': word.translation,
            'example': word.example,
            'context': word.context,
            'level': rep.user_level
        })
    
    return render_template('review.html', words=words_data)

@main_bp.route('/word/<int:word_id>')
@login_required
def word_detail(word_id):
    """Детальная информация о слове"""
    user_id = session.get('user_id')
    
    word = Word.query.get_or_404(word_id)
    repetition = Repetition.query.filter_by(word_id=word_id, user_id=user_id).first_or_404()
    mistake = Mistake.query.filter_by(word_id=word_id).first()
    
    return render_template('word_detail.html', 
                           word=word, 
                           repetition=repetition, 
                           mistake=mistake)

@main_bp.route('/rate_word', methods=['POST'])
@login_required
def rate_word():
    """Оценка знания слова"""
    user_id = session.get('user_id')
    data = request.json
    word_id = data.get('word_id')
    score = int(data.get('score'))
    
    # Получаем повторение и обновляем его
    repetition = Repetition.query.filter_by(word_id=word_id, user_id=user_id).first()
    if not repetition:
        return jsonify({'status': 'error', 'message': 'Слово не найдено'})
    
    # Обновляем дату следующего повторения
    repetition.update_next_review_date(score)
    
    # Если оценка низкая (0-2), увеличиваем счетчик ошибок
    if score <= 2:
        mistake = Mistake.query.filter_by(word_id=word_id).first()
        if not mistake:
            mistake = Mistake(word_id=word_id)
            db.session.add(mistake)
        mistake.increment()
    
    # Если достигнут уровень 3, создаем тест для слова
    if repetition.user_level == 3 and score >= 4:
        create_test_for_word(word_id)
    
    # Обновляем прогресс пользователя
    progress = UserProgress.get_or_create_today(user_id=user_id)
    progress.words_reviewed += 1
    if score >= 3:
        progress.correct_answers += 1
        progress.points += 10
    
    # Обновляем streak
    update_streak()
    
    db.session.commit()
    
    return jsonify({'status': 'success', 'next_date': repetition.next_review_date.strftime('%Y-%m-%d')})

@main_bp.route('/reset_word/<int:word_id>', methods=['POST'])
@login_required
def reset_word(word_id):
    """Сбрасывает прогресс слова на начальный уровень"""
    user_id = session.get('user_id')
    repetition = Repetition.query.filter_by(word_id=word_id, user_id=user_id).first()
    if not repetition:
        return jsonify({'status': 'error', 'message': 'Слово не найдено'})
    
    # Сбрасываем уровень и устанавливаем повторение на завтра
    repetition.user_level = 0
    repetition.next_review_date = datetime.utcnow().date()
    db.session.commit()
    
    return jsonify({'status': 'success'})

@main_bp.route('/progress')
@login_required
def show_progress():
    """Страница статистики и прогресса"""
    user_id = session.get('user_id')
    progress_records = UserProgress.query.filter_by(user_id=user_id).order_by(UserProgress.date.desc()).limit(30).all()
    
    # Получаем статистику по словам
    total_words = Repetition.query.filter_by(user_id=user_id).count()
    mastered_words = Repetition.query.filter(
        Repetition.user_level >= 4,
        Repetition.user_id == user_id
    ).count()
    
    # Получаем проблемные слова для пользователя
    problem_words_list = db.session.query(
        Word, Mistake
    ).join(
        Mistake, Word.id == Mistake.word_id
    ).join(
        Repetition, Word.id == Repetition.word_id
    ).filter(
        Mistake.mistake_count > 2,
        Repetition.user_id == user_id
    ).order_by(
        Mistake.mistake_count.desc()
    ).limit(5).all()
    
    problem_words = len(problem_words_list)
    
    return render_template('progress.html', 
                           progress_records=progress_records,
                           total_words=total_words,
                           mastered_words=mastered_words,
                           problem_words=problem_words,
                           problem_words_list=problem_words_list)

@main_bp.route('/test/<int:word_id>')
@login_required
def take_test(word_id):
    """Страница для мини-теста по слову"""
    user_id = session.get('user_id')
    word = Word.query.get_or_404(word_id)
    repetition = Repetition.query.filter_by(word_id=word_id, user_id=user_id).first()
    
    # Проверяем, что уровень слова >= 3
    if not repetition or repetition.user_level < 3:
        flash('Это слово ещё не готово для тестирования.', 'warning')
        return redirect(url_for('main.word_detail', word_id=word_id))
    
    # Получаем или создаем тест для этого слова
    test = Test.query.filter_by(word_id=word_id).first()
    if not test:
        test = create_test_for_word(word_id)
        if not test:
            return render_template('no_test.html')
    
    # Преобразуем строку опций в список для шаблона
    options = json.loads(test.options)
    
    return render_template('test.html', 
                           word=word, 
                           test=test, 
                           options=options)

@main_bp.route('/recommendations')
@login_required
def recommendations():
    """Страница с рекомендациями по изучению"""
    user_id = session.get('user_id')
    
    # Получаем статистику пользователя
    progress = UserProgress.get_or_create_today(user_id=user_id)
    
    # Подсчитываем общее количество очков
    total_points = db.session.query(db.func.sum(UserProgress.points)).filter(
        UserProgress.user_id == user_id
    ).scalar() or 0
    
    # Получаем все достижения пользователя
    achievements = check_achievements(progress)
    
    # Получаем список слов для повторения сегодня
    today = datetime.utcnow().date()
    words_to_review = Repetition.query.filter(
        Repetition.next_review_date <= today,
        Repetition.user_id == user_id
    ).count()
    
    # Получаем проблемные слова для пользователя
    problem_words = db.session.query(
        Word, Mistake
    ).join(
        Mistake, Word.id == Mistake.word_id
    ).join(
        Repetition, Word.id == Repetition.word_id
    ).filter(
        Mistake.mistake_count > 2,
        Repetition.user_id == user_id
    ).order_by(
        Mistake.mistake_count.desc()
    ).limit(5).all()
    
    return render_template('recommendations.html',
                           progress=progress,
                           total_points=total_points,
                           achievements=achievements,
                           words_to_review=words_to_review,
                           problem_words=problem_words)

@main_bp.route('/tests')
@login_required
def tests():
    """Страница со списком доступных тестов"""
    user_id = session.get('user_id')
    
    # Получаем количество слов для повторения сегодня (для ежедневного теста)
    today = datetime.utcnow().date()
    daily_words_count = Repetition.query.filter(
        Repetition.next_review_date <= today,
        Repetition.user_id == user_id
    ).count()
    
    # Получаем количество проблемных слов (для тематического теста)
    problem_words_count = db.session.query(
        Repetition
    ).join(
        Mistake, Repetition.word_id == Mistake.word_id
    ).filter(
        Mistake.mistake_count > 0,
        Repetition.user_id == user_id
    ).count()
    
    # Получаем активные тестовые сессии
    active_sessions = TestSession.query.filter_by(completed=False).all()
    
    # Получаем завершенные тестовые сессии
    completed_sessions = TestSession.query.filter_by(completed=True).order_by(TestSession.completed_at.desc()).limit(5).all()
    
    return render_template('tests.html',
                           daily_words_count=daily_words_count,
                           problem_words_count=problem_words_count,
                           active_sessions=active_sessions,
                           completed_sessions=completed_sessions)

@main_bp.route('/tests/new', methods=['GET', 'POST'])
@login_required
def new_test():
    """Создание нового теста"""
    if request.method == 'POST':
        session_type = request.form.get('session_type', 'custom')
        difficulty = int(request.form.get('difficulty', 1))
        word_count = int(request.form.get('word_count', 10))
        
        # Создаем новую тестовую сессию
        test_session = create_test_session(session_type, difficulty, word_count)
        
        if test_session:
            return redirect(url_for('main.take_test_session', session_id=test_session.id))
        else:
            flash('Не удалось создать тест. Недостаточно слов.', 'danger')
            return redirect(url_for('main.tests'))
    
    # GET-запрос, возвращаем форму создания теста
    return render_template('new_test.html')

@main_bp.route('/tests/session/<int:session_id>')
@login_required
def take_test_session(session_id):
    """Прохождение тестовой сессии"""
    # Получаем тестовую сессию
    test_session = TestSession.query.get_or_404(session_id)
    
    # Если сессия уже завершена, перенаправляем на результаты
    if test_session.completed:
        return redirect(url_for('main.test_results', session_id=session_id))
    
    # Получаем список слов для теста
    word_ids = json.loads(test_session.words)
    
    # Проверяем текущую позицию в тесте
    current_position = test_session.current_position
    
    # Если пройдены все слова, завершаем тест
    if current_position >= len(word_ids):
        test_session.complete_session()
        db.session.commit()
        return redirect(url_for('main.test_results', session_id=session_id))
    
    # Получаем текущее слово
    current_word_id = word_ids[current_position]
    word = Word.query.get(current_word_id)
    
    # Создаем тест с разными типами на основе позиции
    test_types = ['multiple_choice', 'translation', 'matching']
    test_type = test_types[current_position % len(test_types)]
    
    # Получаем или создаем тест для текущего слова и типа
    test = Test.query.filter_by(word_id=current_word_id, test_type=test_type).first()
    if not test:
        test = create_test_for_word(current_word_id, test_type=test_type, difficulty=test_session.difficulty)
    
    # Преобразуем строку опций в список для шаблона
    options = json.loads(test.options)
    
    # Для тестов на сопоставление преобразуем опции в нужный формат
    if test.test_type == 'matching':
        if isinstance(options, list):
            # Если опции пришли в виде списка, преобразуем их в словарь
            options = {item['word']: item['translation'] for item in options}
        options = {
            'items': [{'key': k, 'value': v} for k, v in options.items()]
        }
    
    # Передаем данные в шаблон
    progress = {
        'current': current_position + 1,
        'total': len(word_ids),
        'percent': int(((current_position + 1) / len(word_ids)) * 100)
    }
    
    # Выбираем шаблон в зависимости от типа теста
    template_name = f'test_{test.test_type}.html'
    
    return render_template(template_name,
                          test_session=test_session,
                          word=word,
                          test=test,
                          options=options,
                          progress=progress)

@main_bp.route('/tests/submit', methods=['POST'])
@login_required
def submit_test_answer():
    """Обработка ответа на вопрос в тестовой сессии"""
    user_id = session.get('user_id')
    data = request.json
    session_id = data.get('session_id')
    test_id = data.get('test_id')
    answer = data.get('answer')
    
    # Получаем тестовую сессию
    test_session = TestSession.query.get(session_id)
    if not test_session or test_session.completed:
        return jsonify({'status': 'error', 'message': 'Тестовая сессия не найдена или уже завершена'})
    
    # Получаем тест
    test = Test.query.get(test_id)
    if not test:
        return jsonify({'status': 'error', 'message': 'Тест не найден'})
    
    # Проверяем ответ
    correct = False
    matching_results = None
    
    if test.test_type == 'multiple_choice':
        correct = answer == test.correct_option
    elif test.test_type == 'translation':
        # Для перевода проверяем совпадение без учета регистра
        correct = answer.lower().strip() == test.correct_option.lower().strip()
    elif test.test_type == 'matching':
        # Для сопоставления проверяем все пары
        correct_pairs = json.loads(test.correct_option)
        user_pairs = json.loads(answer)
        correct = correct_pairs == user_pairs
        
        # Создаем структуру для отображения результатов сопоставления
        matching_results = {}
        for key, user_value in user_pairs.items():
            correct_value = correct_pairs.get(key)
            matching_results[key] = {
                'user': user_value,
                'correct': user_value == correct_value,
                'correct_answer': correct_value
            }
    
    # СУПЕР ПРОСТАЯ ЛОГИКА:
    # Если ответ правильный, увеличиваем счетчик правильных ответов
    if correct:
        test_session.correct_answers += 1
        
        # Обновляем Repetition для текущего слова
        repetition = Repetition.query.filter_by(word_id=test.word_id, user_id=user_id).first()
        if repetition:
            # Правильный ответ засчитываем как оценку 5
            repetition.update_next_review_date(5)
    else:
        # Если ответ неправильный, увеличиваем счетчик ошибок
        mistake = Mistake.query.filter_by(word_id=test.word_id).first()
        if not mistake:
            mistake = Mistake(word_id=test.word_id)
            db.session.add(mistake)
        mistake.increment()
    
    # Обновляем прогресс пользователя в любом случае
    progress = UserProgress.get_or_create_today(user_id=user_id)
    progress.words_reviewed += 1
    if correct:
        progress.correct_answers += 1
    
    # Переходим к следующему слову (не вопросу!)
    test_session.current_position += 1
    
    # Проверяем, завершен ли тест
    all_completed = test_session.current_position >= len(json.loads(test_session.words))
    if all_completed:
        # Завершаем сессию
        test_session.complete_session()
        
        # Обновляем статистику пользователя
        progress = UserProgress.get_or_create_today(user_id=user_id)
        progress.points += test_session.score
    
    db.session.commit()
    
    # Формируем ответ
    response_data = {
        'status': 'success',
        'correct': correct,
        'correct_answer': test.correct_option,
        'all_completed': all_completed,
        'next_url': url_for('main.test_results', session_id=session_id) if all_completed else url_for('main.take_test_session', session_id=session_id)
    }
    
    # Добавляем результаты сопоставления, если есть
    if matching_results is not None:
        response_data['matching_results'] = matching_results
    
    return jsonify(response_data)

@main_bp.route('/tests/results/<int:session_id>')
@login_required
def test_results(session_id):
    """Результаты тестовой сессии"""
    # Получаем тестовую сессию
    test_session = TestSession.query.get_or_404(session_id)
    
    # Если сессия не завершена, перенаправляем на её прохождение
    if not test_session.completed:
        return redirect(url_for('main.take_test_session', session_id=session_id))
    
    # Получаем все слова из теста
    word_ids = json.loads(test_session.words)
    words = Word.query.filter(Word.id.in_(word_ids)).all()
    
    # Создаем словарь слов для удобного доступа в шаблоне
    words_dict = {word.id: word for word in words}
    
    # Подготавливаем результаты для отображения
    correct_answers = test_session.correct_answers  # Количество правильно отвеченных слов
    total_words = test_session.word_count  # Общее количество слов в тесте
    
    # Рассчитываем процент правильных ответов
    percent = 0
    if total_words > 0:
        percent = int((correct_answers / total_words) * 100)
    
    results = {
        'correct': correct_answers,
        'total': total_words,
        'percent': percent,
        'score': test_session.score
    }
    
    return render_template('test_results.html',
                           test_session=test_session,
                           words=words,
                           words_dict=words_dict,
                           results=results,
                           percentage=percent) 