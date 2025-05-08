from datetime import datetime, timedelta
from app import db

class Category(db.Model):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    words = db.relationship('Word', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Word(db.Model):
    __tablename__ = 'words'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    translation = db.Column(db.String(100), nullable=False)
    example = db.Column(db.Text)
    context = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    repetitions = db.relationship('Repetition', backref='word', lazy=True, cascade="all, delete-orphan")
    mistakes = db.relationship('Mistake', backref='word', lazy=True, cascade="all, delete-orphan")
    tests = db.relationship('Test', backref='word', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Word {self.word}>'

class Repetition(db.Model):
    __tablename__ = 'repetitions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_level = db.Column(db.Integer, default=0)
    next_review_date = db.Column(db.Date, default=datetime.utcnow().date)
    repeat_count = db.Column(db.Integer, default=0)
    last_result = db.Column(db.Integer, default=0)  # Оценка от 0 до 5
    last_review_date = db.Column(db.Date, default=datetime.utcnow().date)
    
    def __repr__(self):
        return f'<Repetition {self.id} for word_id {self.word_id}>'
    
    def update_next_review_date(self, score):
        """Обновляет дату следующего повторения на основе оценки и алгоритма SRS"""
        self.last_result = score
        today = datetime.utcnow().date()
        self.last_review_date = today
        
        # Логика алгоритма SRS
        if score == 0:
            # Полностью забыл, сброс уровня
            self.user_level = 0
            self.next_review_date = today + timedelta(days=1)
        elif score <= 2:
            # Неуверенное знание
            self.next_review_date = today + timedelta(days=1)
        elif score == 3:
            # Среднее знание
            self.next_review_date = today + timedelta(days=2)
        elif score == 4:
            # Хорошее знание
            self.next_review_date = today + timedelta(days=3)
        elif score == 5:
            # Отличное знание
            self.user_level += 1
            
            # Расчет интервала на основе уровня
            if self.user_level == 1:
                interval = 1
            elif self.user_level == 2:
                interval = 3
            elif self.user_level == 3:
                interval = 7
            elif self.user_level == 4:
                interval = 14
            else:
                interval = 30  # Для уровней 5+
            
            self.next_review_date = today + timedelta(days=interval)
        
        self.repeat_count += 1
        return self.next_review_date

class Mistake(db.Model):
    __tablename__ = 'mistakes'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    mistake_count = db.Column(db.Integer, default=0)
    last_wrong_date = db.Column(db.Date, default=None)
    
    def __repr__(self):
        return f'<Mistake {self.id} for word_id {self.word_id}>'
    
    def increment(self):
        """Увеличивает счетчик ошибок и обновляет дату последней ошибки"""
        self.mistake_count += 1
        self.last_wrong_date = datetime.utcnow().date()

class Test(db.Model):
    __tablename__ = 'tests'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)
    correct_option = db.Column(db.String(100), nullable=False)
    test_type = db.Column(db.String(50), default='multiple_choice')
    difficulty = db.Column(db.Integer, default=1)
    
    def __repr__(self):
        return f'<Test {self.id} for word_id {self.word_id}>'

class TestSession(db.Model):
    __tablename__ = 'test_sessions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    session_type = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.Integer, default=1)
    word_count = db.Column(db.Integer, default=10)
    correct_answers = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    words = db.Column(db.Text)
    current_position = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<TestSession {self.id} type={self.session_type}>'
    
    def calculate_score(self):
        """Рассчитывает финальный счет на основе правильных ответов и сложности"""
        base_points = 10  # базовые очки за правильный ответ
        difficulty_multiplier = self.difficulty * 0.5  # множитель сложности
        
        # Формула: правильные ответы * базовые очки * множитель сложности
        self.score = int(self.correct_answers * base_points * difficulty_multiplier)
        return self.score
    
    def complete_session(self):
        self.completed = True
        self.completed_at = datetime.utcnow()
        self.calculate_score()

class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    words_reviewed = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def __repr__(self):
        return f'<UserProgress {self.date}>'
        
    @classmethod
    def get_or_create_today(cls, user_id=None):
        """Получает или создает запись прогресса на сегодня для указанного пользователя"""
        today = datetime.utcnow().date()

        if user_id:
            progress = cls.query.filter_by(date=today, user_id=user_id).first()
            if not progress:
                progress = cls(date=today, user_id=user_id)
                db.session.add(progress)
                db.session.commit()
        else:
            progress = cls.query.filter_by(date=today, user_id=None).first()
            if not progress:
                progress = cls(date=today)
                db.session.add(progress)
                db.session.commit()
                
        return progress
    
    def calculate_score(self):
        base_points = 10
        # Используем фиксированный множитель
        difficulty_multiplier = 1.0
        self.points = int(self.correct_answers * base_points * difficulty_multiplier)
        return self.points
    
    def complete_session(self):
        """Обновляет статистику пользователя при завершении сессии"""
        self.calculate_score()
