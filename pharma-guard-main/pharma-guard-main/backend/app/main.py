from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="PharmaGuard API",
    description="Pharmacogenomic Risk Prediction System — RIFT 2026 Hackathon",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # In production, set to your frontend domain
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import analysis, health
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

@app.get("/")
async def root():
    return {
        "service": "PharmaGuard",
        "docs": "/docs",
        "health": "/api/health",
        "analyze": "POST /api/analyze",
    }
