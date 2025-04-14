from app.models import db

class Bot(db.Model):
    
    __tablename__ = 'bot'
    
    bot_id = db.Column(db.String(64), primary_key=True)
    session_id = db.Column(db.String(64), nullable=False, unique=True)  # Add session_id
    user_id = db.Column(db.String(64), nullable=False)  # Add user_id
    status = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f'<Bot {self.bot_id}, Session {self.session_id}, User {self.user_id}>'
    
    def to_dict(self):
        return {
            'bot_id': self.bot_id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'status': self.status
        }
