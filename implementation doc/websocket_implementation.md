# WebSocket Implementation Guide

This document explains how Real-Time WebSockets were implemented in the Open Banking Architecture to enable bidirectional, instant communication between the server and the frontend client.

## 1. The Problem
In standard HTTP, communication is **unidirectional**. The client (e.g., a mobile app) must constantly ask the server, *"Is my payment done yet?"* (a process known as **polling**). Polling every 5 seconds drains mobile batteries and overwhelms the server with thousands of empty requests.

## 2. The WebSocket Solution
WebSockets solve this by keeping a **persistent TCP connection** open. Once connected, the server can instantly "push" data down the wire to the client the exact millisecond an event occurs.

### A. The Connection Manager (`src/routers/websockets.py`)
To handle multiple users connecting at once, we built a `ConnectionManager`. 

```python
class ConnectionManager:
    def __init__(self):
        # Maps an account_id to a list of active WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, account_id: str):
        await websocket.accept()
        if account_id not in self.active_connections:
            self.active_connections[account_id] = []
        self.active_connections[account_id].append(websocket)

    def disconnect(self, websocket: WebSocket, account_id: str):
        if account_id in self.active_connections:
            self.active_connections[account_id].remove(websocket)

    async def send_personal_message(self, message: dict, account_id: str):
        if account_id in self.active_connections:
            for connection in self.active_connections[account_id]:
                await connection.send_json(message)
```
* **Why a Dictionary?** We map `account_id -> [WebSocket1, WebSocket2]`. This allows a user to be logged in on their iPhone and their Laptop at the same time. When a payment arrives, the manager loops through the list and pushes the update to *both* devices instantly.

### B. The Endpoint
Clients connect to the server using the `ws://` protocol instead of `http://`:

```python
@router.websocket("/ws/{account_id}")
async def websocket_endpoint(websocket: WebSocket, account_id: str):
    await manager.connect(websocket, account_id)
    try:
        while True:
            # Keep connection alive and wait for incoming messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, account_id)
```

### C. Triggering the Event (Broadcasting)
In our standard REST endpoints (like `POST /payments`), we simply import the `manager` and tell it to push a message if the transaction succeeds.

**Example from `src/routers/payments.py`:**
```python
from .websockets import manager

# ... inside the payment processing logic ...
if transaction_successful:
    # 1. Update the database
    db.commit()
    
    # 2. Instantly push the new balance to the user's mobile app
    await manager.send_personal_message({
        "type": "PAYMENT_RECEIVED",
        "amount": 500.00,
        "new_balance": 1500.00
    }, account_id)
```

## 3. Long-Term Production Considerations
While this in-memory implementation is perfect for a prototype, here is what changes in a large-scale production environment (e.g., millions of users):

1. **Horizontal Scaling**: If you have 5 backend servers behind a Load Balancer, User A might connect their WebSocket to Server 1, but the payment is processed by Server 3. Server 3's in-memory `active_connections` dictionary doesn't know about User A!
2. **The Fix (Pub/Sub)**: Enterprise systems use **Redis Pub/Sub** or **Kafka**. Server 3 would publish the event to Redis, and Server 1 (which holds the WebSocket) would instantly read it from Redis and push it to the client.
