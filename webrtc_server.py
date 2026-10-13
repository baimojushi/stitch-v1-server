#!/usr/bin/env python3
"""
STITCH-V1 WebRTC Server with unified signaling.
Handles both control (via existing gateway) and video streaming.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass

import mss
import numpy as np
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaRelay
from av import VideoFrame

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webrtc")

# ---- Config ----
WINDOW_TITLE = "UnitySplatsGallery"
WEBRTC_PORT = 8082
WS_SIGNALING_PORT = 8083  # Separate port for WebRTC signaling

# ---- Screen Capture ----
sct = mss.mss()

# Find monitor with Unity window (simple approach: use primary monitor)
monitor = sct.monitors[1]  # Primary monitor
logger.info(f"Capturing monitor: {monitor}")


class UnityVideoTrack(VideoStreamTrack):
    """Video track that captures Unity window frames."""
    
    def __init__(self):
        super().__init__()
        self.frame_count = 0
        
    async def recv(self):
        pts, time_base = await self.next_timestamp()
        
        # Capture frame using mss
        frame = np.array(sct.grab(monitor))
        if frame is None or frame.size == 0:
            # Create blank frame if capture fails
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        else:
            # mss returns BGRA, convert to RGB
            # frame shape: (height, width, 4) - BGRA
            frame = frame[:, :, :3][:, :, ::-1]  # BGR to RGB
            # Resize to target resolution
            h, w = frame.shape[:2]
            if w != 1280 or h != 720:
                import cv2
                frame = cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_LINEAR)
        
        # Convert to VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        
        self.frame_count += 1
        if self.frame_count % 300 == 0:
            logger.info(f"Captured {self.frame_count} frames")
        
        return video_frame


# ---- WebRTC Handling ----
pcs = set()
relay = MediaRelay()

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    
    pc = RTCPeerConnection()
    pcs.add(pc)
    
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"Connection state: {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)
    
    # Add video track
    video_track = UnityVideoTrack()
    pc.addTrack(relay.subscribe(video_track))
    
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })


async def on_shutdown(app):
    # Close all peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()
    camera.stop()


# ---- WebRTC Signaling WebSocket ----
async def signaling_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    logger.info("WebRTC Signaling WebSocket connected")
    pc = None
    
    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
                msg_type = data.get("type", "")
                
                if msg_type == "offer":
                    # Create peer connection
                    pc = RTCPeerConnection()
                    pcs.add(pc)
                    
                    @pc.on("connectionstatechange")
                    async def on_connectionstatechange():
                        logger.info(f"WebRTC Connection state: {pc.connectionState}")
                        if pc.connectionState == "failed":
                            await pc.close()
                            pcs.discard(pc)
                    
                    # Add video track
                    video_track = UnityVideoTrack()
                    pc.addTrack(relay.subscribe(video_track))
                    
                    await pc.setRemoteDescription(RTCSessionDescription(sdp=data["sdp"], type="offer"))
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)
                    
                    await ws.send_json({
                        "type": "answer",
                        "sdp": pc.localDescription.sdp
                    })
                    
                elif msg_type == "ice-candidate" and pc:
                    candidate = data.get("candidate", {})
                    await pc.addIceCandidate(candidate)
                    
            except Exception as e:
                logger.error(f"Signaling error: {e}")
        elif msg.type == web.WSMsgType.ERROR:
            logger.error(f"WS error: {ws.exception()}")
    
    logger.info("WebRTC Signaling WebSocket disconnected")
    if pc:
        await pc.close()
        pcs.discard(pc)
    return ws


# ---- HTTP Routes ----
async def index(request):
    """Serve the mobile controller page."""
    with open(os.path.join(os.path.dirname(__file__), "index.html"), "r") as f:
        return web.Response(text=f.read(), content_type="text/html")


async def health(request):
    return web.json_response({"status": "ok", "service": "stitch-webrtc"})


# ---- Main ----
async def init_app():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_post("/offer", offer)  # HTTP fallback for offer
    app.router.add_get("/ws", signaling_ws)  # WebSocket for signaling
    app.on_shutdown.append(on_shutdown)
    return app


def main():
    parser = argparse.ArgumentParser(description="STITCH-V1 WebRTC Server")
    parser.add_argument("--port", type=int, default=WEBRTC_PORT)
    parser.add_argument("--ws-port", type=int, default=WS_SIGNALING_PORT)
    args = parser.parse_args()
    
    # Run on single port with both HTTP and WebSocket
    app = asyncio.run(init_app())
    web.run_app(app, host="0.0.0.0", port=args.port, print=lambda x: logger.info(x))


if __name__ == "__main__":
    main()