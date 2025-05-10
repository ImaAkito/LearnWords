from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import json
import os
import random

db = SQLAlchemy()
migrate = Migrate()

def create_app(config=None):
    app = Flask(__name__)
    
    # Базовые настройки приложения
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_learning_app')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///words.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Если передан дополнительный конфиг, применяем его
    if config:
        app.config.update(config)
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        # Регистрация маршрутов основного приложения
        from app.routes.main_routes import main_bp
        app.register_blueprint(main_bp)
        
        # Регистрация маршрутов для авторизации
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
        # Добавляем фильтр для преобразования JSON строки в объект Python
        @app.template_filter('from_json')
        def from_json(value):
            return json.loads(value) if value else []
        
        # Добавляем фильтр для перемешивания списка
        @app.template_filter('shuffle')
        def shuffle_filter(seq):
            result = list(seq)
            random.shuffle(result)
            return result
        
        # Создаем все таблицы, если их нет
        db.create_all()
    
    return app 