import json
import numpy as np
import os
import traceback


def handler(request):
    try:
        # CORS preflight
        if request["method"] == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                },
            }

        # Parse POST body
        body = json.loads(request["body"])
        regions = body.get("regions", [])
        threshold_ms = body.get("threshold_ms", 180)

        # Try multiple possible JSON paths (Vercel serverless quirk)
        json_paths = [
            "./q-vercel-latency.json",
            "q-vercel-latency.json",
            "/var/task/q-vercel-latency.json",
        ]
        telemetry = []
        for path in json_paths:
            try:
                with open(path, "r") as f:
                    telemetry = json.load(f)
                break
            except:
                continue

        if not telemetry:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Telemetry file not found"}),
            }

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

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json",
            },
            "body": json.dumps(results),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e), "traceback": traceback.format_exc()}),
        }
