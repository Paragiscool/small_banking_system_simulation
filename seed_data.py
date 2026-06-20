from src import models
from src.database import SessionLocal, engine
import uuid

# Recreate DB
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Seed Accounts
account1_id = str(uuid.uuid4())
account2_id = str(uuid.uuid4())

acc1 = models.Account(account_id=account1_id, user_id="user-123", internal_account_number="10000001", currency="USD")
acc2 = models.Account(account_id=account2_id, user_id="user-456", internal_account_number="20000002", currency="USD")

db.add(acc1)
db.add(acc2)

# Seed Balances
bal1 = models.Balance(account_id=account1_id, available_balance=5000.0, booked_balance=5000.0)
bal2 = models.Balance(account_id=account2_id, available_balance=150.0, booked_balance=150.0)

db.add(bal1)
db.add(bal2)

db.commit()
db.close()

print(f"Seeded Accounts!")
print(f"Account 1 (Sender): {account1_id} - Balance: $5000.0")
print(f"Account 2 (Receiver): {account2_id} - Balance: $150.0")
