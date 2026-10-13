#!/usr/bin/env python3
"""
Simple HTTP server for the mobile web controller.
Serves index.html on port 8090.
"""
import http.server
import os
import socketserver

PORT = 8091
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)


if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Mobile web server serving {DIRECTORY} on port {PORT}", flush=True)
        httpd.serve_forever()