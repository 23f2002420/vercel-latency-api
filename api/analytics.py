import json
import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: int


# Load telemetry data once
with open("q-vercel-latency.json", "r") as f:
    TELEMETRY = json.load(f)


@app.post("/analytics")
async def analytics(body: RequestBody):
    results = {}
    for region in body.regions:
        region_data = [r for r in TELEMETRY if r["region"] == region]
        latencies = np.array([r["latency_ms"] for r in region_data])
        uptimes = np.array([r["uptime"] for r in region_data])

        results[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": int(np.sum(latencies > body.threshold_ms)),
        }
    return results
