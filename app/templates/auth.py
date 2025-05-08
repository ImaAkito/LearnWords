from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

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
        
    return render_template('profile.html', user=user) 
 
 