import { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

export default function AccountOverview({ accountId }) {
  const [balance, setBalance] = useState({ available_balance: 0, booked_balance: 0 });
  
  // Also listen to websocket to instantly update balance!
  const wsUrl = accountId ? `ws://127.0.0.1:8000/ws/${accountId}` : null;
  const { lastMessage } = useWebSocket(wsUrl);

  const fetchBalance = async () => {
    if (!accountId) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/accounts/${accountId}/balances`, {
        headers: {
          'Authorization': 'Bearer mock-valid-token',
          'X-Client-Cert-Thumbprint': 'mock-cert'
        }
      });
      if (res.ok) {
        const data = await res.json();
        setBalance(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Initial load
  useEffect(() => {
    fetchBalance();
  }, [accountId]);

  // Update on websocket event
  useEffect(() => {
    if (lastMessage && (lastMessage.type === "PAYMENT_RECEIVED" || lastMessage.type === "INTEREST_CREDITED" || lastMessage.type === "PAYMENT_SENT" || lastMessage.type === "PAYMENT_REJECTED")) {
      // Small delay to let DB settle if needed, or rely on event data if balance is provided.
      // Easiest approach for accurate real-time is simply re-fetching balance:
      fetchBalance();
    }
  }, [lastMessage]);

  return (
    <div className="glass-panel p-6">
      <h2 className="text-xl font-semibold text-white mb-6">Account Overview</h2>
      
      {!accountId ? (
        <div className="text-slate-400 text-sm h-24 flex items-center">No account selected.</div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="text-slate-400 text-xs font-semibold tracking-wider uppercase mb-2">Available Balance</div>
            <div className="text-3xl font-bold text-white">${balance.available_balance.toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-xl p-4 relative overflow-hidden">
            <div className="text-slate-400 text-xs font-semibold tracking-wider uppercase mb-2">Booked Ledger</div>
            <div className="text-xl font-medium text-slate-300 mt-2">${balance.booked_balance.toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
          </div>
        </div>
      )}
    </div>
  );
}
