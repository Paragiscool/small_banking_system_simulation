# Open Banking Technical Report
**Author:** Zetheta Intern  
**Project:** P01D - API Gateway & Developer Portal  

## 1. Executive Summary
This technical report details the architecture and implementation of the Open Banking API Gateway and Sandbox simulation. The objective of this project was to construct a regulatory-compliant banking gateway capable of securely exchanging financial data with Third-Party Providers (TPPs) while simulating a resilient, ACID-compliant Core Banking Ledger.

## 2. Regulatory Landscape Analysis
The platform adheres to the stringent requirements defined by the EU's **Revised Payment Services Directive (PSD2)** and the UK Open Banking Implementation Entity (OBIE). 
- **Consent Models:** Implemented granular, time-bound consent schemas.
- **MFA / SCA:** Supported the simulation of Strong Customer Authentication workflows in the sandbox environment.

## 3. Architecture Design Rationale
The architecture follows a centralized API Gateway pattern intercepting all incoming traffic before routing it to the core microservices (Accounts, Payments).
- **Technology Choice:** Python (FastAPI) was selected over Node.js/Express due to its native support for asynchronous execution, built-in Pydantic schema validation (guaranteeing OpenAPI compliance), and its industry-standard prevalence in data-heavy financial engineering.

## 4. Security Model Analysis
The security architecture strictly implements the **FAPI 1.0 Advanced Profile**.
- **Pushed Authorization Requests (PAR):** Eliminates URL parameter tampering by forcing TPPs to POST signed request objects via a backchannel before browser redirection.
- **Sender-Constrained Tokens:** API Gateway validates that the Access Token matches the Mutual TLS (`X-Client-Cert-Thumbprint`) of the connection, neutralizing token-theft attacks.

## 5. Developer Experience Strategy
We built a visually stunning Developer Portal utilizing modern UI paradigms (Dark mode, glassmorphism). The DX Strategy prioritized:
- **Sandbox Error Injection:** Exposing the `x-sandbox-inject-error` header so TPPs can safely test their own retry/backoff logic against simulated 429 and 500 errors.
- **Interactive Documentation:** Seamless integration with OpenAPI Swagger UI (`/docs`).

## 6. Governance Framework
To ensure maximum availability, we integrated API Governance at the core middleware level:
- **Rate Limiting:** A Fixed Window algorithm limits read-heavy endpoints (`/accounts`) to 300 Req/Min, while compute-heavy endpoints (`/payments`) are throttled to 60 Req/Min.
- **Monitoring:** All requests have their processing latency tracked and returned via the `X-Response-Time` header.

## 7. Limitations and Future Work
- **Database:** The prototype utilizes SQLite. Production deployment requires migrating to a highly-available PostgreSQL cluster.
- **Distributed Rate Limiting:** The in-memory token bucket must be replaced with a Redis-backed Sliding Window implementation for multi-instance deployments.

## 8. References
1. OpenID Foundation (2021). Financial-grade API Security Profile 1.0 - Part 2: Advanced.
2. UK Open Banking Implementation Entity (OBIE). Open Banking Standard Version 3.1.x.
3. European Banking Authority (EBA). Regulatory Technical Standards (RTS) on Strong Customer Authentication (SCA).
4. Internet Engineering Task Force (IETF). RFC 6749: The OAuth 2.0 Authorization Framework.
5. ByteByteGo (2023). Designing Data-Intensive Payment Systems.
