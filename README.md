# SentinelAI — Autonomous Continuous KYC Compliance Intelligence Platform

Enterprise compliance platform for continuous entity monitoring, adverse event detection,
explainable risk scoring, investigation timeline generation, SAR drafting, and human review.

## Quick Start

```bash
# 1. Copy env and configure
cp .env.example .env

# 2. Start with Docker Compose
docker compose up --build

# 3. Access
# Backend API:  http://localhost:8000/docs
# Frontend:     http://localhost:5173
```

## Architecture

```
Presentation Layer (React + TypeScript)
        ↓
Application Layer (FastAPI Controllers)
        ↓
Domain Layer (Services + Business Logic)
        ↓
Agent Layer (LangGraph Supervisor + Specialist Agents)
        ↓
Infrastructure Layer (DB, Vector Store, LLM Gateway)
        ↓
Storage Layer (SQLite, ChromaDB)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Tailwind, ShadCN UI, Recharts |
| Backend | FastAPI, Python 3.11+, SQLAlchemy, Pydantic |
| Storage | SQLite (WAL), ChromaDB |
| AI | LangGraph, Gemini, Structured JSON outputs |
| Deployment | Docker, Docker Compose |