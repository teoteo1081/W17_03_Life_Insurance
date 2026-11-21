#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Máy chủ trên máy để sửa portfolio (lưu file qua /api/save, đăng lên web qua /api/publish).

Cách dễ nhất: bấm đúp MO_EDITOR.bat. Hoặc chạy:
    python dev_server.py           # rồi tự mở http://localhost:8000/editor_workspace/editor_portfolio.html
    python dev_server.py --open    # tự mở trình duyệt vào editor
"""

import argparse
import os
import socket
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path

from server import BASE_DIR, make_server

EDITOR_PATH = "/editor_workspace/editor_portfolio.html"
PORT_TRIES = 10


def _listening(port):
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _serves_this_folder(port):
    """Cổng đang bận: có phải chính máy chủ của thư mục này không (so nội dung index.html)?"""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/index.html", timeout=2) as r:
            return r.read() == (BASE_DIR / "index.html").read_bytes()
    except Exception:
        return False


def main(argv):
    parser = argparse.ArgumentParser(description="Máy chủ sửa portfolio trên máy")
    parser.add_argument("--open", action="store_true", help="tự mở trình duyệt vào editor")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    args = parser.parse_args(argv)

    server = None
    for port in range(args.port, args.port + PORT_TRIES):
        if _listening(port):
            if _serves_this_folder(port):
                url = f"http://localhost:{port}{EDITOR_PATH}"
                print(f"Máy chủ của thư mục này đang chạy sẵn ở cổng {port}. Mở lại editor: {url}")
                if args.open:
                    webbrowser.open(url)
                return 0
            continue
        try:
            server = make_server(port)
            break
        except OSError:
            continue
    if server is None:
        print(f"Không mở được máy chủ: các cổng {args.port}-{args.port + PORT_TRIES - 1} đều đang bận.")
        return 1

    port = server.server_address[1]
    url = f"http://localhost:{port}{EDITOR_PATH}"
    print("=" * 64)
    print(" EDITOR PORTFOLIO đang chạy")
    print(f" Mở trang sửa: {url}")
    print(" Sửa chữ xong, bấm [🚀 Lưu & đăng lên web] trên thanh công cụ.")
    print(" GIỮ CỬA SỔ NÀY MỞ trong lúc sửa. Sửa xong thì đóng cửa sổ là xong.")
    print(f" Thư mục: {Path(BASE_DIR)}")
    print("=" * 64)
    sys.stdout.flush()
    if args.open:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
