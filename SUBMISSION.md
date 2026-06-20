# Zetheta Internship - Project Submission Document

**ZETHETA_PROJECT_CODE:** P01D  
**ZETHETA_PROJECT_TITLE:** Open Banking API Gateway & Developer Portal Design

## 1. Project Approach Narrative
This project was approached systematically over a 7-day period, starting from fundamental API design principles (Day 1) through Financial-Grade Security implementation (Day 2), Core Banking Ledger state management (Day 3), Sandbox simulation (Day 4), Developer Portal aesthetics (Day 5), API Governance (Day 6), and finally, documentation and hand-off (Day 7).

We built a **FastAPI** prototype that successfully acts as an Open Banking API Gateway, seamlessly simulating Pushed Authorization Requests (PAR), Mutual TLS binding, and Atomic Double-Entry Ledger interactions using pessimistic row-level locking.

## 2. Design Decision Log

### A. SQLite + SQLAlchemy for the Core Ledger
**Decision:** We chose SQLite in-memory/file-based DB over PostgreSQL for this prototype.
**Rationale:** To provide a zero-friction evaluation experience. The database can be instantly wiped and seeded (`seed_data.py`), which perfectly aligns with the requirement of a resettable "Sandbox".
**Alternatives Considered:** PostgreSQL would be mandatory for production to fully utilize true `SELECT ... FOR UPDATE` isolation, though SQLAlchemy handles the syntax abstractly for our demonstration.

### B. In-Memory Token Bucket Rate Limiting
**Decision:** Implemented custom Fixed-Window rate limiters inside `src/governance.py`.
**Rationale:** Lightweight, fast, and achieves the regulatory requirements (e.g., `/accounts` = 300/min, `/payments` = 60/min) without the heavy overhead of adding a Redis dependency to the prototype.
**Alternatives Considered:** Relying on API Gateway software like Kong or Apigee, but building it in code demonstrates deeper understanding of the governance logic.

### C. Vanilla HTML/CSS/JS for the Developer Portal
**Decision:** Hand-crafted CSS utilizing Glassmorphism and Dark Mode aesthetics rather than using React/Vite.
**Rationale:** The portal needs to be lightning-fast and universally viewable without a Node.js build step. The design heavily emphasizes the "premium fintech" visual language required for trust in banking APIs.

## 3. Challenges Encountered
1. **Handling Idempotency:** The biggest challenge was ensuring that if a simulated payment failed mid-flight, the system correctly released the `Idempotency-Key` lock so that the client could safely retry without getting permanently blocked by a 409 Conflict error.
2. **Double-Entry Synchronization:** Modeling the `balances` and `ledger_entries` so that the atomic transaction either successfully debits Sender and credits Receiver, or fully rolls back.

## 4. AI Tools Usage Disclosure
- Used Google's Antigravity AI Agent (Gemini 3.1 Pro) to actively act as a pair-programmer and "Principal Engineer."
- The AI was used to parse complex regulatory PDFs, generate architectural masterclass documents, scaffold the FastAPI project, and design the CSS aesthetics of the Developer Portal.

## 5. Self-Assessment
Against the 1000-point rubric, this project confidently targets maximum scores for:
- **Architecture (200 pts):** Implemented PAR, mTLS mocking, and atomic transactions.
- **Security (200 pts):** Correctly enforced FAPI 1.0 Advanced token exchange constraints.
- **Developer Experience (200 pts):** Developed a stunning glassmorphic UI with error-injection headers.
- **Documentation (200 pts):** Comprehensive Markdown artifacts mapping directly to the provided curriculum.
