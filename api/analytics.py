import json
import numpy as np
from http.server import BaseHTTPRequestHandler
import os


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        # CORS headers
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        # Handle CORS preflight
        if self.headers.get("Origin") and self.command == "OPTIONS":
            return

        try:
            # Read POST body
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data)

            regions = body.get("regions", [])
            threshold_ms = body.get("threshold_ms", 180)

            # Load JSON (try both paths)
            json_paths = ["q-vercel-latency.json", "./q-vercel-latency.json"]
            telemetry = []
            for path in json_paths:
                try:
                    with open(path, "r") as f:
                        telemetry = json.load(f)
                    break
                except:
                    continue

            if not telemetry:
                self.wfile.write(json.dumps({"error": "No telemetry data"}).encode())
                return

            # Process regions
            results = {}
            for region in regions:
                region_data = [r for r in telemetry if r.get("region") == region]
                if not region_data:
                    results[region] = {
                        "avg_latency": 0,
                        "p95_latency": 0,
                        "avg_uptime": 0,
                        "breaches": 0,
                    }
                    continue

                latencies = np.array([r.get("latency_ms", 0) for r in region_data])
                uptimes = np.array([r.get("uptime", 0) for r in region_data])

                results[region] = {
                    "avg_latency": float(np.mean(latencies)),
                    "p95_latency": float(np.percentile(latencies, 95)),
                    "avg_uptime": float(np.mean(uptimes)),
                    "breaches": int(np.sum(latencies > threshold_ms)),
                }

            self.wfile.write(json.dumps(results).encode())

        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps({"status": "ok", "endpoint": "/api/analytics"}).encode()
        )
