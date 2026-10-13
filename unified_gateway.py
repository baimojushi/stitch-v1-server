#!/usr/bin/env python3
"""
Unified WebSocket server for STITCH-V1:
- Control signaling: forwards JSON to Unity via UDP (port 7777)
- WebRTC signaling: handles offer/answer/ICE for video streaming
"""
import argparse
import asyncio
import json
import socket
import sys

import websockets

class UnifiedGateway:
    def __init__(self, unity_host, unity_port):
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target = (unity_host, unity_port)
        self.control_clients = set()
        self.webrtc_clients = set()
        self.clients = 0

    async def handler(self, ws):
        self.clients += 1
        client_id = self.clients
        print(f"[gateway] client #{client_id} connected ({len(self.control_clients) + len(self.webrtc_clients)} active)", flush=True)
        
        is_control = False
        is_webrtc = False
        
        try:
            async for message in ws:
                if isinstance(message, str):
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        print(f"[gateway] client #{client_id}: dropping malformed packet", flush=True)
                        continue
                    
                    msg_type = data.get("type", "")
                    
                    # Determine client type from first message
                    if not is_control and not is_webrtc:
                        if msg_type in ("move", "look", "use", "reset"):
                            is_control = True
                            self.control_clients.add(client_id)
                            print(f"[gateway] client #{client_id}: registered as CONTROL", flush=True)
                        elif msg_type in ("offer", "answer", "ice-candidate", "candidate"):
                            is_webrtc = True
                            self.webrtc_clients.add(client_id)
                            print(f"[gateway] client #{client_id}: registered as WEBRTC", flush=True)
                    
                    # Handle based on type
                    if is_control:
                        # Forward control packets to Unity via UDP
                        self.udp.sendto(message.encode("utf-8"), self.target)
                    
                    elif is_webrtc:
                        # Handle WebRTC signaling - broadcast to other WebRTC clients
                        # In a real setup, you'd route to specific peer
                        for wc in self.webrtc_clients:
                            if wc != client_id:
                                # Would need to track ws per client_id
                                pass
                        # For now, just acknowledge
                        await ws.send(json.dumps({"type": "ack", "original_type": msg_type}))
                        
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"[gateway] client #{client_id}: error: {e}", flush=True)
        finally:
            self.control_clients.discard(client_id)
            self.webrtc_clients.discard(client_id)
            print(f"[gateway] client #{client_id} disconnected ({len(self.control_clients) + len(self.webrtc_clients)} active)", flush=True)


async def main():
    ap = argparse.ArgumentParser(description="Unified STITCH-V1 Gateway: Control + WebRTC Signaling")
    ap.add_argument("--listen", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--unity-host", default="127.0.0.1")
    ap.add_argument("--unity-port", type=int, default=7777)
    args = ap.parse_args()

    gateway = UnifiedGateway(args.unity_host, args.unity_port)

    print(f"Unified Gateway ws://{args.listen}:{args.port}", flush=True)
    print(f"  Control -> UDP {args.unity_host}:{args.unity_port}", flush=True)
    print(f"  WebRTC Signaling (multiplexed)", flush=True)
    
    async with websockets.serve(gateway.handler, args.listen, args.port, max_size=65536):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[gateway] shutting down", flush=True)
        sys.exit(0)