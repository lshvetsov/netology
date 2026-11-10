import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from math import isfinite
from urllib.parse import parse_qs


def response_for(target):
    path, _, query = target.partition("?")

    if path == "/health":
        return 200, {"status": "ok"}
    if path == "/":
        return 200, {"example": "/fahrenheit?celsius=20"}
    if path != "/fahrenheit":
        return 404, {"error": "Not found"}

    values = parse_qs(query, keep_blank_values=True).get("celsius", [])
    if len(values) == 1:
        try:
            fahrenheit = float(values[0]) * 1.8 + 32
            if isfinite(fahrenheit):
                return 200, {"fahrenheit": round(fahrenheit, 2)}
        except ValueError:
            pass
    return 400, {"error": "Provide one finite celsius value"}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, payload = response_for(self.path)
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    # Контейнер принимает запросы на всех интерфейсах.
    host = "0.0.0.0"  # nosec B104
    port = int(os.environ.get("PORT", "8000"))
    with HTTPServer((host, port), Handler) as server:
        server.serve_forever()
