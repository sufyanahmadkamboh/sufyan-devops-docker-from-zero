"""simple-app: a tiny web app used to learn Dockerfiles.

The app is not the point. It is small on purpose so you can focus on Docker:
it reads two environment variables and tells you which container answered.
"""
import os
import socket

from flask import Flask

app = Flask(__name__)

APP_ENV = os.environ.get("APP_ENV", "development")
GREETING = os.environ.get("GREETING", "Hello from simple-app")


@app.route("/")
def home():
    # socket.gethostname() inside a container returns the container ID (short form)
    return (f"{GREETING}!\n"
            f"environment: {APP_ENV}\n"
            f"container hostname: {socket.gethostname()}\n")


@app.route("/health")
def health():
    return "ok\n"


if __name__ == "__main__":
    # 0.0.0.0 = listen on every network interface of the container.
    # 127.0.0.1 would only accept connections from inside the container itself.
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    print(f"simple-app starting on {host}:{port} (APP_ENV={APP_ENV})", flush=True)
    app.run(host=host, port=port)
