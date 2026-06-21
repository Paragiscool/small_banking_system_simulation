import logging
from sqlalchemy.orm import Session
from . import models
from .database import SessionLocal
import uuid

logger = logging.getLogger(__name__)

async def calculate_daily_interest():
    """
    Cron job: Applies 0.05% daily interest to all active accounts.
    """
    logger.info("Starting daily interest calculation job.")
    db: Session = SessionLocal()
    try:
        accounts = db.query(models.Account).filter(models.Account.status == models.AccountStatus.ACTIVE).all()
        for account in accounts:
            balance = db.query(models.Balance).filter(models.Balance.account_id == account.account_id).with_for_update().first()
            if balance and balance.booked_balance > 0:
                interest = round(balance.booked_balance * 0.0005, 2) # 0.05% interest
                if interest > 0:
                    balance.booked_balance += interest
                    balance.available_balance += interest
                    
                    tx_id = f"INT-{str(uuid.uuid4())[:8]}"
                    entry = models.LedgerEntry(
                        transaction_id=tx_id,
                        account_id=account.account_id,
                        amount=interest,
                        entry_type=models.EntryType.CREDIT,
                        status="BOOKED"
                    )
                    db.add(entry)
                    
                    # Invalidate Cache
                    from .cache import invalidate_cache
                    await invalidate_cache(f"balance_{account.account_id}")
                    
                    # WebSocket broadcast
                    import asyncio
                    from .routers.websockets import manager
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(
                            manager.broadcast_to_account(
                                account.account_id,
                                {"type": "INTEREST_CREDITED", "transaction_id": tx_id, "amount": interest}
                            )
                        )
                    except RuntimeError:
                        pass # Not running in an event loop (e.g. tests)
        db.commit()
        logger.info("Daily interest calculation completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error calculating interest: {str(e)}")
    finally:
        db.close()
