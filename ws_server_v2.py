import asyncio
import websockets
import json
import sys

async def handler(ws):
    print('Client connected', file=sys.stderr, flush=True)
    async for msg in ws:
        data = json.loads(msg)
        t = data.get('type', '')
        print(f'Received: {t}', file=sys.stderr, flush=True)
        if t == 'offer':
            await ws.send(json.dumps({'type': 'answer', 'sdp': 'test-answer'}))

async def main():
    print('Starting server on 8083...', file=sys.stderr, flush=True)
    server = await websockets.serve(handler, '0.0.0.0', 8083)
    print('Server listening on 8083', file=sys.stderr, flush=True)
    for s in server.sockets:
        print(f'Bound to: {s.getsockname()}', file=sys.stderr, flush=True)
    await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())