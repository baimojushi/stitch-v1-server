import socket
import os
import sys
import time

print(f"PID: {os.getpid()}", flush=True)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    s.bind(('0.0.0.0', 8082))
    s.listen(5)
    print('Bound and listening on 0.0.0.0:8082', flush=True)
    sys.stdout.flush()
    
    # Just sleep, don't accept
    time.sleep(30)
    print('Done sleeping', flush=True)
except Exception as e:
    print(f'Error: {e}', flush=True)
    sys.stdout.flush()
finally:
    s.close()
    print('Socket closed', flush=True)