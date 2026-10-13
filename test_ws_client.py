import asyncio
import websockets
import json
import sys

async def test():
    try:
        print('Connecting...', flush=True)
        async with websockets.connect('ws://127.0.0.1:8083') as ws:
            print('Connected!', flush=True)
            await ws.send(json.dumps({'type': 'offer', 'sdp': 'test-offer'}))
            print('Sent offer', flush=True)
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            print('Response:', resp[:200], flush=True)
    except Exception as e:
        print('Error:', type(e).__name__, e, flush=True)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())