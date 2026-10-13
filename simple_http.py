#!/usr/bin/env python3
"""Simple HTTP server for mobile controller page."""
import http.server
import os
import socketserver
import threading
import asyncio
import json
import websockets

PORT = 8082
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run_http():
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"HTTP server on port {PORT}", flush=True)
        httpd.serve_forever()

# WebSocket signaling server on 8083
async def signaling_handler(ws):
    print("WebRTC signaling connected", flush=True)
    async for msg in ws:
        if isinstance(msg, str):
            try:
                data = json.loads(msg)
                msg_type = data.get("type", "")
                print(f"Signaling: {msg_type}", flush=True)
                
                if msg_type == "offer":
                    # In a real implementation, create RTCPeerConnection here
                    # For now, send mock answer
                    await ws.send(json.dumps({
                        "type": "answer",
                        "sdp": "v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=group:BUNDLE 0\r\na=msid-semantic: WMS\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\nc=IN IP4 0.0.0.0\r\na=rtcp:9 IN IP4 0.0.0.0\r\na=ice-ufrag:test\r\na=ice-pwd:test\r\na=mid:0\r\na=sendonly\r\na=rtpmap:96 H264/90000\r\na=fmtp:96 profile-level-id=42e01f;packetization-mode=1\r\n"
                    }))
                elif msg_type == "ice-candidate":
                    # Echo back
                    pass
            except Exception as e:
                print(f"Signaling error: {e}", flush=True)

async def run_ws():
    print("WebSocket signaling on port 8083", flush=True)
    async with websockets.serve(signaling_handler, "0.0.0.0", 8083):
        await asyncio.Future()

if __name__ == "__main__":
    # Run HTTP in thread
    http_thread = threading.Thread(target=run_http, daemon=True)
    http_thread.start()
    
    # Run WebSocket in main thread
    asyncio.run(run_ws())