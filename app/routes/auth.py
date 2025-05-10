from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from app import db
from app.models.user import User
from app.models.models import UserProgress, Repetition, TestSession
from app.utils.srs_utils import get_user_rank

auth_bp = Blueprint('auth', __name__)

# Конфигурация для загрузки файлов
UPLOAD_FOLDER = 'app/static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Создаем папку для загрузки файлов, если её нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Проверка данных
        if not username or not email or not password:
            flash('Все поля должны быть заполнены', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return render_template('register.html')
            
        # Проверка существующего пользователя
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Пользователь с таким именем уже существует', 'danger')
            return render_template('register.html')
            
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Этот email уже используется', 'danger')
            return render_template('register.html')
        
        # Создание нового пользователя
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Вход пользователя"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Проверка данных
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Неверное имя пользователя или пароль', 'danger')
            return render_template('login.html')
            
        # Аутентификация пользователя
        session['user_id'] = user.id
        
        # Обновление времени последнего входа
        user.update_last_login()
        
        flash(f'Добро пожаловать, {user.username}!', 'success')
        return redirect(url_for('main.index'))
        
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Выход пользователя"""
    session.pop('user_id', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
def profile():
    """Страница профиля пользователя"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Пожалуйста, войдите в систему', 'warning')
        return redirect(url_for('auth.login'))
        
    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        flash('Пользователь не найден', 'error')
        return redirect(url_for('auth.login'))
    
    # Получаем данные для отображения в профиле
    user_progress = UserProgress.get_or_create_today(user_id=user_id)
    
    # Подсчитываем общее количество очков для данного пользователя
    total_points = db.session.query(db.func.sum(UserProgress.points)).filter(UserProgress.user_id == user_id).scalar() or 0
    user_progress.points = total_points
    
    # Получаем ранг пользователя
    rank = get_user_rank(total_points)
    
    # Получаем дополнительную статистику для данного пользователя
    mastered_words = Repetition.query.filter(
        Repetition.user_id == user_id,
        Repetition.user_level >= 4
    ).count()
    completed_tests = TestSession.query.filter_by(completed=True).count()
    
    return render_template('profile.html', 
                          user=user,
                          user_progress=user_progress,
                          rank=rank,
                          mastered_words=mastered_words,
                          completed_tests=completed_tests)

@auth_bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    """Редактирование профиля пользователя"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Пожалуйста, войдите в систему', 'warning')
        return redirect(url_for('auth.login'))
        
    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        flash('Пользователь не найден', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Проверяем, если имя пользователя изменилось
        if username != user.username:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Пользователь с таким именем уже существует', 'danger')
                return render_template('edit_profile.html', user=user)
            user.username = username
        
        # Проверяем, если email изменился
        if email != user.email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Этот email уже используется', 'danger')
                return render_template('edit_profile.html', user=user)
            user.email = email
        
        # Если введен текущий пароль, проверяем его и обновляем на новый
        if current_password:
            if not check_password_hash(user.password, current_password):
                flash('Текущий пароль неверен', 'danger')
                return render_template('edit_profile.html', user=user)
                
            if not new_password:
                flash('Введите новый пароль', 'danger')
                return render_template('edit_profile.html', user=user)
                
            if new_password != confirm_password:
                flash('Пароли не совпадают', 'danger')
                return render_template('edit_profile.html', user=user)
                
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        # Обработка загрузки аватарки
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file.filename != '':
                if not allowed_file(avatar_file.filename):
                    flash('Разрешены только изображения форматов: png, jpg, jpeg, gif', 'danger')
                    return render_template('edit_profile.html', user=user)
                
                # Генерируем безопасное имя файла
                filename = secure_filename(f"{user.id}_{avatar_file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                
                # Сохраняем файл
                avatar_file.save(filepath)
                
                # Обновляем URL аватарки
                user.avatar_url = f"/static/uploads/avatars/{filename}"
        
        db.session.commit()
        flash('Профиль успешно обновлен', 'success')
        return redirect(url_for('auth.profile'))
        
    return render_template('edit_profile.html', user=user) 
 
 