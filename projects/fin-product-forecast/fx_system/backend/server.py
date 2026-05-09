#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from data_sources import fetch_all_sources
from db import get_rates, init_db, latest_model, save_model_run, upsert_rates
from modeling import linreg_predict, regimes_json, unsupervised_regimes

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_FILE = ROOT / "frontend" / "index.html"


class ApiHandler(BaseHTTPRequestHandler):
    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw or "{}")

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            html = FRONTEND_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if parsed.path == "/api/rates":
            qs = parse_qs(parsed.query)
            pair = (qs.get("pair") or ["USDCNY"])[0].upper()
            limit = int((qs.get("limit") or ["300"])[0])
            rows = get_rates(pair=pair, limit=limit)
            return self._json(
                {
                    "pair": pair,
                    "count": len(rows),
                    "items": [dict(r) for r in rows],
                }
            )

        if parsed.path == "/api/model/latest":
            qs = parse_qs(parsed.query)
            pair = (qs.get("pair") or ["USDCNY"])[0].upper()
            model = latest_model(pair)
            if not model:
                return self._json({"error": "model not found"}, status=404)
            return self._json({"item": dict(model)})

        self._json({"error": "not found"}, status=404)

    def do_POST(self):  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/api/ingest":
            try:
                rows, errors = fetch_all_sources()
                inserted = upsert_rates(rows) if rows else 0
                pairs = sorted({r[1] for r in rows})
                return self._json({"ok": len(rows) > 0, "fetched": len(rows), "inserted": inserted, "pairs": pairs, "errors": errors})
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "error": str(e)}, status=500)

        if parsed.path == "/api/import-csv":
            body = self._read_json()
            pair = str(body.get("pair", "USDCNY")).upper()
            source = str(body.get("source", "LOCAL"))
            rows = body.get("rows", [])
            normalized = []
            for r in rows:
                ts = str(r.get("ts"))
                rate = float(r.get("rate"))
                normalized.append((source, pair, ts, rate))
            inserted = upsert_rates(normalized) if normalized else 0
            return self._json({"ok": True, "inserted": inserted, "pair": pair})

        if parsed.path == "/api/train":
            body = self._read_json()
            pair = str(body.get("pair", "USDCNY")).upper()
            horizon = int(body.get("horizon", 5))
            rows = get_rates(pair=pair, limit=800)
            if len(rows) < 120:
                return self._json({"error": f"not enough data for {pair}"}, status=400)

            rates = [float(r["rate"]) for r in reversed(rows)]
            slope, intercept, preds = linreg_predict(rates, horizon=horizon)
            regimes = unsupervised_regimes(rates)
            run_id = save_model_run(
                pair=pair,
                trained_at=dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                horizon=horizon,
                slope=slope,
                intercept=intercept,
                inertia=float(regimes["inertia"]),
                regimes_json=regimes_json(regimes),
            )
            return self._json(
                {
                    "ok": True,
                    "run_id": run_id,
                    "pair": pair,
                    "horizon": horizon,
                    "predictions": preds,
                    "regimes": {
                        "counts": regimes["counts"],
                        "centers": regimes["centers"],
                        "inertia": regimes["inertia"],
                    },
                }
            )

        self._json({"error": "not found"}, status=404)


def main() -> None:
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", 8010), ApiHandler)
    print("FX system running: http://127.0.0.1:8010")
    server.serve_forever()


if __name__ == "__main__":
    main()
