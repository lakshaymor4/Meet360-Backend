from flask import Blueprint, jsonify, request, current_app
from flask_socketio import join_room, leave_room, emit
from app.models.bot import Bot
from app.services.liveTranscriber import LiveTranscriber
from app import limiter
import threading
import uuid
import time
from app.models import db
from app import socketio  

transcription_bp = Blueprint('transcription', __name__, url_prefix='/api/transcription')

active_threads = {}

@transcription_bp.route('/start', methods=['POST'])
@limiter.limit("1 per hour") 
@limiter.limit("1 per minute") 
def start_transcription():
    """Start a transcription session and run it in a background thread."""
    try:
        data = request.get_json()
        meeting_url = data.get('meeting_url')
        user_id = data.get('user_id')  

        if not meeting_url or not user_id:
            return jsonify({'error': 'Meeting URL and User ID are required'}), 400

        bot_id = LiveTranscriber.get_Bod_id(meeting_url)  
      
        print(bot_id)
      
        session_id = str(uuid.uuid4())
        print(session_id)
        bot = Bot(bot_id=bot_id, session_id=session_id, user_id=user_id, status=True)
        db.session.add(bot)
        db.session.commit()

        stop_event = threading.Event()

        def background_task(bot_id, session_id, stop_event, app):
            with app.app_context(): 
                LiveTranscriber.listen_for_updates(bot_id, session_id, stop_event)

        thread = threading.Thread(target=background_task, args=(bot_id, session_id, stop_event, current_app._get_current_object()))
        thread.daemon = True
        thread.start()

        active_threads[session_id] = {
            'thread': thread,
            'stop_event': stop_event
        }

        return jsonify({'success': True, 'bot_id': bot_id, 'session_id': session_id}), 200

    except Exception as e:
        current_app.logger.error(f"Error starting transcription: {str(e)}")
        return jsonify({'error': str(e)}), 500

@transcription_bp.route('/stop/<session_id>', methods=['GET'])
@limiter.limit("20 per hour")  # Allow more stops than starts
def stop_transcription(session_id):
    """Stop a transcription session."""
    try:
        
        if session_id in active_threads:
            active_threads[session_id]['stop_event'].set()
            LiveTranscriber.listen_for_updates
            del active_threads[session_id]

        bot = Bot.query.filter_by(session_id=session_id).first()
        if bot:
            LiveTranscriber.leave(bot.bot_id)
           
            bot.status = False
            db.session.commit()

        return jsonify({'success': True}), 200

    except Exception as e:
        current_app.logger.error(f"Error stopping transcription: {str(e)}")
        return jsonify({'error': str(e)}), 500


@socketio.on('join', namespace='/')
def handle_join(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        print(f"User joined room: {session_id}")

@socketio.on('leave', namespace='/')
def handle_leave(data):
    session_id = data.get('session_id')
    if session_id:
        leave_room(session_id)
        print(f"User left room: {session_id}")

@socketio.on('connect', namespace='/')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connect', {'data': 'Connected', 'sid': request.sid}, room=request.sid)

@socketio.on('disconnect', namespace='/')
def handle_disconnect():
    print(f"Client {request.sid} disconnected from WebSocket")