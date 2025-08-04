
import os
from flask import Flask
from flask_migrate import Migrate
from flask_socketio import SocketIO
from app.routes.main import main_bp
from app.models import db
from flask_cors import CORS
from app.config import config_by_name
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


migrate = Migrate()

socketio = SocketIO(cors_allowed_origins="http://localhost:5173", logger=True, engineio_logger=True, debug=True)

limiter = Limiter(
    get_remote_address,
    default_limits=["50 per day", "10 per hour", "2 per minute"],
    storage_uri="memory://",
)
 

def create_app(config_name='development'):
    app = Flask(__name__)
    
    limiter.init_app(app)
    
    app_config = config_by_name.get(config_name, 'development')
    app.config.from_object(app_config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    
    CORS(app)
    from app.routes.transcription import transcription_bp
    from app.models.bot import Bot
    from app.routes.recordingTranscription import recordingTranscription_bp

    
    app.register_blueprint(main_bp)
    app.register_blueprint(transcription_bp)
    app.register_blueprint(recordingTranscription_bp)
   
    
    @app.shell_context_processor
    def make_shell_context():
        """Add useful objects to Flask shell context."""
        return {'db': db, 'Bot': Bot, 'socketio': socketio}
    
    return app
