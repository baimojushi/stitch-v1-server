#!/usr/bin/env python3
"""
Mobile WebSocket -> Unity UDP control gateway.

WebSocket clients send RemoteInputPacket JSON to Unity's RemoteControlUdpReceiver.
The gateway forwards each packet over UDP to the Unity player running in the
same Exhibition WSL distribution.

Usage:
    /opt/exhibition/venv/bin/python3 control_gateway.py --listen 0.0.0.0 --port 8765 \
        --unity-host 127.0.0.1 --unity-port 7777
"""
import argparse
import asyncio
import json
import socket
import sys

import websockets


async def main():
    ap = argparse.ArgumentParser(description="Mobile WebSocket -> Unity UDP control gateway")
    ap.add_argument("--listen", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--unity-host", default="127.0.0.1")
    ap.add_argument("--unity-port", type=int, default=7777)
    args = ap.parse_args()

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target = (args.unity_host, args.unity_port)
    clients = 0

    async def handler(ws):
        nonlocal clients
        clients += 1
        print(f"[gateway] client connected ({clients} active)", flush=True)
        try:
            async for message in ws:
                if isinstance(message, str):
                    # Validate JSON before forwarding
                    try:
                        json.loads(message)
                    except json.JSONDecodeError:
                        print(f"[gateway] dropping malformed packet", flush=True)
                        continue
                    udp.sendto(message.encode("utf-8"), target)
        finally:
            clients -= 1
            print(f"[gateway] client disconnected ({clients} active)", flush=True)

    print(f"Control gateway ws://{args.listen}:{args.port} -> udp://{args.unity_host}:{args.unity_port}",
          flush=True)
    async with websockets.serve(handler, args.listen, args.port, max_size=65536):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[gateway] shutting down", flush=True)
        sys.exit(0)