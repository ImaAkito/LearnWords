from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Связи с другими таблицами
    progress = db.relationship('UserProgress', backref='user', lazy=True)
    repetitions = db.relationship('Repetition', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_user_data(self):
        """Возвращает основные данные пользователя"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
    
    def update_last_login(self):
        """Обновляет время последнего входа"""
        self.last_login = datetime.utcnow()
        db.session.commit() 
 
 