# SentinelAI — Team Onboarding & Project Context

Welcome to the SentinelAI project! If you are joining the team mid-hackathon, this document provides the exact context you need to start contributing immediately without needing to read through the entire chat history.

## 1. Project Overview
**SentinelAI** is an Autonomous Continuous KYC Compliance Intelligence Platform. 
Instead of a standard CRUD app, it is a highly advanced, event-driven architecture designed to autonomously monitor entities, verify news, score risk, and draft Suspicious Activity Reports (SARs) with a Human-in-the-Loop review process.

### The "Hackathon Edge"
To win this hackathon, we are focusing on **Demo Gold**:
1. **Scenario Engine**: Automated, scripted demonstrations of complex cases (e.g., Money Laundering, Sanction Evasion) that trigger the entire pipeline visually.
2. **Animated Decision Graphs**: Replacing standard UI timelines with interactive React Flow graphs showing exactly how risk scores were derived.
3. **Verification Engine**: A dedicated layer for detecting and isolating "Fake News".
4. **Explainability Layer**: Deep traceability for every AI decision.

---

## 2. The Golden Rules (Read Before Coding)
We are strictly abiding by an Enterprise Engineering Contract to ensure zero merge conflicts and a robust architecture:
1. **Interface-Driven Design**: The core business logic depends ONLY on abstract interfaces (e.g., `IMessageBroker`, `ICacheProvider`). 
2. **Infrastructure Mocks**: For the 48-hour hackathon, we are using local mocks (`AsyncioBroker`, `LocalMemoryCache`) to implement these interfaces. Do **NOT** spend time setting up Redis, Kafka, or Vault.
3. **Unit of Work (UoW)**: Any database operation touching multiple repositories MUST execute within an `async with uow:` block to guarantee atomic rollbacks.
4. **LLMOps**: All LLM calls route through `llm_gateway.py` which enforces structured JSON outputs and protects against prompt injection.

---

## 3. Important Documentation
We have generated comprehensive architecture documents. You can find them in the `docs/` directory:
- `docs/engineering_contract.md`: The rigid rules for dependency flow, error handling, and file naming.
- `docs/canonical_domain_model.md`: The frozen database schema. Do not alter these entities (Company, RiskEvent, Alert, etc.) without a team consensus.
- `docs/api_contract.md`: The OpenAPI boundary. The frontend and backend communicate strictly via this contract.
- `docs/implementation_plan.md`: The 5-developer parallel execution roadmap and dependency graph.

---

## 4. Current State (What is Done?)
We have successfully completed **Sprint 1 (Foundation)**:
- **Infrastructure**: `AsyncioMessageBroker`, `InMemoryCacheProvider`, and `EnvSecretsManager` are built and compliant with the domain interfaces.
- **Knowledge Layer**: Scaffolded `knowledge/` folder with `chunker.py`, `embedder.py`, `retriever.py`, and `dataset_loader.py`.
- **API Shells**: FastAPI routing updated to match the API Contract, including the new `/demo/scenarios` endpoints.
- **Frontend Shell**: React + Vite + TypeScript application scaffolded in `frontend/` with Tailwind CSS and React Router configured.

---

## 5. Next Steps (Where to Jump In)
We are currently entering **Sprint 2: Core Engines**. If you are looking for a task, pick one of the following domains:
- **Risk Engine** (`backend/app/services/scoring/`): Break the scoring logic down into independent Rule, Confidence, and Policy engines.
- **Verification Engine** (`backend/app/verification/`): Build the credibility scoring and fact-checking logic for raw news events.
- **Explainability Engine** (`backend/app/explainability/`): Build the decision trace generators.
- **Frontend UI** (`frontend/`): Start building the React Flow component to render the Decision Graph.

*End of Context — Happy Hacking!*
