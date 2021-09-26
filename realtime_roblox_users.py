from threading import Thread, Lock
from socket import socket
from time import sleep
from ssl import create_default_context
from itertools import cycle
from collections import deque
import orjson

set_title = __import__("ctypes").windll.kernel32.SetConsoleTitleW

id_count = 0
id_cache = deque(maxlen=1000)
context = create_default_context()
lock = Lock()
proxies = set()

# Load proxies from file.
with open("proxies.txt") as fp:
    while (line := fp.readline()):
        host, _, port = line.partition(":")
        proxies.add((host.lower(), int(port)))
    proxy_iter = cycle(proxies)

# Find latest user.
with socket() as sock:
    sock.connect(("www.roblox.com", 443))
    sock = context.wrap_socket(sock, server_hostname="www.roblox.com")
    for id_length in range(13, 0, -1):
        for leading_digit in map(str, range(9, 0, -1)):
            test_id = id_count + int(leading_digit + ("0" * (id_length - 1)))
            sock.send(f"GET /users/{test_id}/profile HTTP/1.1\nHost:www.roblox.com\n\n".encode())
            if sock.recv(1048576).startswith(b"HTTP/1.1 200"):
                while not sock.recv(1048576).endswith(b"</script>"):
                    pass
                id_count = test_id
                break
    sock.shutdown(2)

def scanner():
    global id_count

    while True:
        with socket() as sock:
            sock.settimeout(5)
            try:
                sock.connect(next(proxy_iter))
                sock.send(b"CONNECT users.roblox.com:443 HTTP/1.1\r\n\r\n")
                resp = sock.recv(1024000)
                if not (resp.startswith(b"HTTP/1.1 200") or
                        resp.startswith(b"HTTP/1.0 200")):
                    break
                sock = context.wrap_socket(sock, server_hostname="users.roblox.com")
                while True:
                    payload = f"{{\"userIds\":[{','.join(map(str, range(id_count + 1, id_count + 100 + 2)))}]}}"
                    sock.send(f"POST /v1/users HTTP/1.1\nHost:users.roblox.com\nContent-Length:{len(payload)}\nContent-Type:application/json\n\n{payload}".encode())
                    resp = sock.recv(1024000)
                    if resp.startswith(b"HTTP/1.1 200"):
                        for user in orjson.loads(resp.split(b"\r\n\r\n", 1)[1])["data"]:
                            with lock:
                                if not user["id"] in id_cache:
                                    id_cache.append(user["id"])
                                    print(f"roblox.com/users/{user['id']}/profile", "|", user["name"])
                        with lock:
                            if user["id"] > id_count:
                                id_count = user["id"]
                                set_title(f"ID: {id_count:,}")
                    sleep(2)
            except:
                pass
            finally:
                try:
                    sock.shutdown(2)
                except OSError:
                    pass

for _ in range(250):
    Thread(target=scanner).start()
