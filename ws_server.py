import asyncio
import websockets
import json

async def handler(ws):
    print('Client connected', flush=True)
    async for msg in ws:
        data = json.loads(msg)
        t = data.get('type', '')
        print(f'Received: {t}', flush=True)
        if t == 'offer':
            await ws.send(json.dumps({'type': 'answer', 'sdp': 'v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=group:BUNDLE 0\r\na=msid-semantic: WMS\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\nc=IN IP4 0.0.0.0\r\na=rtcp:9 IN IP4 0.0.0.0\r\na=ice-ufrag:test\r\na=ice-pwd:test\r\na=mid:0\r\na=sendonly\r\na=rtpmap:96 H264/90000\r\na=fmtp:96 profile-level-id=42e01f;packetization-mode=1\r\n'}))
        elif t == 'ice-candidate':
            pass

async def main():
    print('WebSocket signaling on 8083', flush=True)
    async with websockets.serve(handler, '0.0.0.0', 8083):
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())