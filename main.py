import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import socketio
import uvicorn
from typing import Dict, List

app = FastAPI()

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socketio_app = socketio.ASGIApp(sio, app)

users: Dict[str, str] = {}
chat_rooms: Dict[str, List[str]] = {}

class UserRegister(BaseModel):
    username: str

class Message(BaseModel):
    room: str
    text: str

@app.get("/")
async def home():
    return {"message": "Chat server is running"}

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    auth_token = environ.get('HTTP_AUTHORIZATION') or environ.get('QUERY_STRING')
    if not auth_token or "11713" not in auth_token:
        raise ConnectionRefusedError('Authentication failed')
    print(f"Authenticated connection: {sid}")

@sio.event
async def disconnect(sid):
    if sid in users:
        username = users[sid]
        print(f"User disconnected: {username} (sid: {sid})")
        # Leave all rooms
        for room in list(chat_rooms.keys()):
            if sid in chat_rooms[room]:
                chat_rooms[room].remove(sid)
                await sio.emit('user_left', {'username': username, 'room': room}, room=room)
        del users[sid]

@sio.event
async def register_user(sid, data):
    """Register username after connection"""
    username = data['username']
    users[sid] = username
    await sio.emit('user_online', {'username': username})

@sio.event
async def join_room(sid, data):
    """Join a chat room"""
    room = data['room']
    username = users.get(sid, "Anonymous")
    
    if room not in chat_rooms:
        chat_rooms[room] = []
    
    chat_rooms[room].append(sid)
    await sio.enter_room(sid, room)
    await sio.emit('user_joined', {'username': username, 'room': room}, room=room)
    await sio.emit('room_users', {'room': room, 'users': [users[sid] for sid in chat_rooms[room]]}, room=room)

@sio.event
async def send_message(sid, data):
    """Send message to room"""
    room = data['room']
    text = data['text']
    username = users.get(sid, "Anonymous")
    
    if room not in chat_rooms or sid not in chat_rooms[room]:
        raise Exception("Not in this room")
    
    await sio.emit('new_message', {
        'room': room,
        'username': username,
        'text': text,
        'timestamp': int(time.time())
    }, room=room)

if __name__ == "__main__":
    uvicorn.run(socketio_app, host="0.0.0.0", port=8000)
    