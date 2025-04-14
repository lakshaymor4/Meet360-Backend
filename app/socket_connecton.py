from flask import request
from flask_socketio import emit, join_room, leave_room
from app import socketio 

@socketio.on('connect')
def handle_connect():
    print(f"🔗 Client {request.sid} connected to WebSocket")
    emit('connect_ack', {'message': 'Connected successfully'}, to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client {request.sid} disconnected from WebSocket")

@socketio.on('join')
def handle_join(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        print(f"User {request.sid} joined room: {session_id}")

@socketio.on('leave')
def handle_leave(data):
    session_id = data.get('session_id')
    if session_id:
        leave_room(session_id)
        print(f"🚪 User {request.sid} left room: {session_id}")
