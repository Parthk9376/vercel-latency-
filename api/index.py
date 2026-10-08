from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Record(BaseModel):
    region: str
    service: str
    latency_ms: float
    uptime_pct: float
    timestamp: int


class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: float


def percentile(values, p):
    values = sorted(values)

    if not values:
        return 0

    k = (len(values) - 1) * p
    f = int(k)
    c = min(f + 1, len(values) - 1)

    if f == c:
        return values[f]

    return values[f] + (values[c] - values[f]) * (k - f)


@app.get("/")
def home():
    return {"message": "Latency API is running"}


@app.post("/api/latency")
def latency(body: RequestBody, records: List[Record]):
    result = []

    for region in body.regions:
        region_records = [
            r for r in records
            if r.region == region
        ]

        if not region_records:
            continue

        latencies = [r.latency_ms for r in region_records]
        uptimes = [r.uptime_pct for r in region_records]

        result.append({
            "region": region,
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile(latencies, 0.95),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                1 for x in latencies
                if x > body.threshold_ms
            )
        })

    return result
