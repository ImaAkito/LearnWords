from functools import wraps
from flask import session, redirect, url_for, flash, request

def login_required(f):
    """Декоратор для проверки авторизации пользователя"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Сохраняем URL, на который пытался перейти пользователь
            session['next_url'] = request.url
            flash('Пожалуйста, войдите в аккаунт для доступа к этой странице', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def is_authenticated():
    """Проверяет, авторизован ли пользователь"""
    return 'user_id' in session 