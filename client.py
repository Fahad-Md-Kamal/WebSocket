import socketio
import asyncio

sio = socketio.AsyncClient(reconnection=True)  # Enable auto-reconnect

@sio.event
async def connect():
    print("✅ Connected to server!")
    try:
        await sio.emit('register_user', {'username': 'TerminalUser'})
        await sio.emit('join_room', {'room': 'general'})
    except Exception as e:
        print(f"⚠️ Error during setup: {e}")

@sio.event
async def disconnect():
    print("❌ Disconnected from server")

@sio.event
async def connect_error(err):
    print(f"⚠️ Connection failed: {err}")

@sio.event
async def new_message(data):
    print(f"\n{data['username']}: {data['text']}")
    # print(f"\n[{data['room']}] {data['username']}: {data['text']}")

async def send_messages():
    while True:
        try:
            message = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
            if not message:
                print("❌ Empty message, please try again.")
                continue
            await sio.emit('send_message', {'room': 'general', 'text': message})
        except (KeyboardInterrupt, SystemExit):
            await sio.disconnect()
            break
        except Exception as e:
            print(f"⚠️ Error sending message: {e}")

async def main():
    try:
        await sio.connect('http://localhost:8000?token=11713', wait_timeout=10)
        await send_messages()
    except Exception as e:
        print(f"🚨 Fatal error: {e}")
    finally:
        await sio.disconnect()

if __name__ == '__main__':
    asyncio.run(main())