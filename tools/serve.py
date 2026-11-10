# -*- coding: utf-8 -*-
"""本地预览用的小静态服务器。

比 `python -m http.server` 多做了两件事：
1. 强制按扩展名给 MIME —— Windows 注册表会把 .js 映射成 text/plain，
   浏览器随即拒绝执行 ES module（报 "Failed to fetch dynamically imported module"）。
2. 关闭缓存，改完文件刷新就能看到。

用法：python tools/serve.py [port]
"""
import functools
import http.server
import os
import socketserver
import sys

TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".glb": "model/gltf-binary",
    ".gltf": "model/gltf+json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".xml": "application/xml; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".wasm": "application/wasm",
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        ext = os.path.splitext(str(path))[1].lower()
        return TYPES.get(ext) or super().guess_type(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):  # 安静一点
        if "404" in (fmt % args):
            super().log_message(fmt, *args)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    handler = functools.partial(Handler, directory=root)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"RobotIC 站点预览： http://127.0.0.1:{port}/")
        print(f"根目录： {root}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
