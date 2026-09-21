"""Servidor HTTP mínimo para desenvolvimento local, sem dependências externas."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import ai
from .alerts import Alerts
from .analytics import Analytics, query_from_params
from .fronts import Fronts

MAX_BODY = 8192


class Handler(BaseHTTPRequestHandler):
    analytics = Analytics()
    fronts = Fronts(analytics)
    alerts = Alerts(analytics, fronts)

    def _json(self, payload: object, status: int = 200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):  # noqa: N802
        # O POST da investigação envia JSON, o que dispara preflight no navegador.
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):  # noqa: N802
        route = urlparse(self.path)
        if route.path != "/api/ai/investigate":
            self._json({"error": "rota não encontrada"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self._json({"error": "Content-Length inválido"}, 400)
            return
        if length > MAX_BODY:
            self._json({"error": "corpo acima do limite aceito"}, 413)
            return
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            params = {key: str(value) for key, value in (body.get("filters") or {}).items() if value not in (None, "")}
            query = query_from_params(params)
            context = self.analytics.investigation_context(query)
            self._json(ai.ask(body.get("question", ""), context))
        except (ValueError, KeyError, UnicodeDecodeError) as error:
            self._json({"error": str(error)}, 400)
        except ai.AIError as error:
            # 502: a camada analítica respondeu; quem falhou foi o provedor.
            self._json({"error": str(error), "provider_unavailable": True}, 502)

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
            elif route.path == "/api/alerts":
                payload = self.alerts.evaluate(query)
            elif route.path == "/api/fronts":
                payload = {"items": [{"id": key, **{k: v for k, v in spec.items()}}
                                     for key, spec in Fronts.FRONTS.items()]}
            elif route.path.startswith("/api/front/"):
                payload = self.fronts.payload(route.path[len("/api/front/"):], query)
            elif route.path == "/api/ai/status":
                payload = ai.status()
            elif route.path == "/api/ai/suggestions":
                payload = {"context": self.analytics.context(query),
                           "available": ai.available(),
                           "items": self.analytics.suggestions(query)}
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
