"""Servidor HTTP mínimo para desenvolvimento local, sem dependências externas."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .analytics import Analytics, query_from_params


class Handler(BaseHTTPRequestHandler):
    analytics = Analytics()

    def _json(self, payload: object, status: int = 200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        route = urlparse(self.path)
        params = {key: values[-1] for key, values in parse_qs(route.query).items()}
        try:
            query = query_from_params(params)
            if route.path == "/api/health":
                payload = self.analytics.health(query)
            elif route.path == "/api/trend":
                payload = self.analytics.trend(query)
            elif route.path == "/api/channels":
                payload = self.analytics.channels(query)
            elif route.path == "/api/categories":
                payload = self.analytics.categories(query)
            elif route.path == "/api/evidence":
                payload = self.analytics.evidence(query)
            elif route.path == "/api/metadata":
                payload = {"snapshot": self.analytics.version, "population": "Aprovado; medidas completas", "year_available": [2023],
                           "grains": ["week", "month", "quarter", "year"], "dimensions": ["channel", "category"],
                           "endpoints": ["health", "trend", "channels", "categories", "evidence"]}
            else:
                self._json({"error": "rota não encontrada"}, 404)
                return
            self._json(payload)
        except (ValueError, KeyError) as error:
            self._json({"error": str(error)}, 400)

    def log_message(self, format, *args):  # noqa: A002
        return


def serve(host: str = "127.0.0.1", port: int = 8765):
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"API analítica: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()
