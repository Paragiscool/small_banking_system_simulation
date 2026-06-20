# 🏦 Zetheta Open Banking API Gateway & Developer Portal
**ZETHETA_PROJECT_CODE:** P01D  
**ZETHETA_PROJECT_TITLE:** Open Banking API Gateway & Developer Portal Design

This repository contains the complete 7-day implementation of a core banking system prototype, built to simulate an Open Banking environment conforming to **FAPI 1.0 Advanced** and **PSD2/CDR** regulatory standards.

## 🚀 Project Overview

The project features a **FastAPI** backend that acts as the Core Ledger and API Gateway, alongside a premium **Developer Portal** frontend built in Vanilla HTML/CSS/JS for Third-Party Providers (TPPs) to securely register and obtain API keys.

### Key Architectural Features:
1. **Double-Entry Ledger:** Atomic transaction execution with pessimistic row-level locking (`SELECT ... FOR UPDATE`) to strictly prevent race conditions.
2. **Financial-Grade Security:** Simulates Mutual TLS (mTLS) certificate binding and Pushed Authorization Requests (PAR).
3. **Idempotency Engine:** Prevents double-charging via `x-idempotency-key` interceptors on the `/domestic-payments` endpoint.
4. **API Governance:** In-memory Rate Limiting (Token Bucket) enforcing endpoint-specific quotas, coupled with global Latency Monitoring and Error Logging.
5. **Sandbox Isolation:** A dedicated `/sandbox` routing module featuring dynamic **Error Injection** (`x-sandbox-inject-error`) allowing TPPs to intentionally trigger timeouts and HTTP faults to test resilience.

## 🛠️ Technology Stack
- **Backend:** Python, FastAPI, Uvicorn
- **Database:** SQLite (for rapid prototype resetting), SQLAlchemy ORM
- **Frontend:** Vanilla HTML, CSS (Glassmorphism + Dark Mode), JS
- **Validation:** Pydantic 

## 📖 Quick Start Guide

### 1. Installation
Ensure you are using **Python 3.12+**. Install the required dependencies:
```bash
pip install fastapi uvicorn sqlalchemy pyjwt cryptography pydantic pydantic-settings
```

### 2. Seed the Database
Initialize the SQLite database with synthetic test users and accounts:
```bash
python seed_data.py
```

### 3. Run the Backend API
Start the FastAPI server:
```bash
uvicorn src.main:app --reload
```
View the interactive Swagger OpenAPI docs at `http://localhost:8000/docs`.

### 4. View the Developer Portal
Open `portal/index.html` in your browser, or start a local Python HTTP server:
```bash
cd portal
python -m http.server 3000
```
Navigate to `http://localhost:3000`.

## 🌐 API Endpoint Summary

| Category | Endpoint | Method | Purpose |
| :--- | :--- | :--- | :--- |
| **Auth** | `/oauth/par` | `POST` | Pushed Authorization Requests |
| **Auth** | `/oauth/token` | `POST` | Exchange code for certificate-bound tokens |
| **Accounts** | `/accounts` | `GET` | List all accounts (Opaque UUIDs) |
| **Accounts** | `/accounts/{id}/balances` | `GET` | Retrieve available/booked balances |
| **Payments** | `/payments/domestic-payments` | `POST` | Initiate an atomic double-entry payment |
| **Sandbox** | `/sandbox/authenticate` | `POST` | Simulate Strong Customer Authentication |

## ⚖️ Standards Compliance Matrix
| Standard | Implementation Method |
| :--- | :--- |
| **FAPI 1.0 Advanced** | Sender-constrained tokens (mTLS mock), PAR support |
| **PSD2 / Open Banking** | Granular scopes, opaque identifiers, isolated Sandbox |
| **ACID Compliance** | Database transactions, atomicity, pessimistic row locks |
