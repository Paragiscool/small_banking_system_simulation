import hashlib

def generate_ledger_hash(previous_hash: str, account_id: str, amount: float, entry_type: str, transaction_id: str) -> str:
    """
    Generate a cryptographic hash for a ledger entry to create a tamper-evident chain.
    H_n = SHA256(H_{n-1} + account_id + amount + direction + nonce/transaction_id)
    """
    amount_str = f"{amount:.2f}"
    payload = f"{previous_hash}{account_id}{amount_str}{entry_type}{transaction_id}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()
