import { useState, useEffect, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

export default function TransactionFeed({ accountId }) {
  const [transactions, setTransactions] = useState([]);
  const [toast, setToast] = useState(null);
  
  // Use WS hook
  const wsUrl = accountId ? `ws://127.0.0.1:8000/ws/${accountId}` : null;
  const { isConnected, lastMessage } = useWebSocket(wsUrl);

  // Initial fetch
  useEffect(() => {
    if (!accountId) return;
    fetch(`http://127.0.0.1:8000/accounts/${accountId}/transactions`, {
      headers: {
        'Authorization': 'Bearer mock-valid-token',
        'X-Client-Cert-Thumbprint': 'mock-cert'
      }
    })
      .then(res => res.json())
      .then(data => {
        if (data.transactions) {
          setTransactions(data.transactions);
        }
      })
      .catch(err => console.error("Failed to load initial transactions:", err));
  }, [accountId]);

  // Handle incoming WS messages
  useEffect(() => {
    if (!lastMessage) return;
    
    if (lastMessage.type === "PAYMENT_RECEIVED" || lastMessage.type === "INTEREST_CREDITED") {
      const newTx = {
        transaction_id: lastMessage.transaction_id,
        amount: lastMessage.amount,
        status: lastMessage.status,
        created_at: new Date().toISOString(),
        entry_type: "CREDIT"
      };
      
      setTransactions(prev => [newTx, ...prev]);
      
      setToast(`Received +$${lastMessage.amount.toFixed(2)}`);
      setTimeout(() => setToast(null), 3000);
    }
    
    if (lastMessage.type === "PAYMENT_SENT") {
      const newTx = {
        transaction_id: lastMessage.transaction_id,
        amount: -lastMessage.amount,
        status: lastMessage.status,
        created_at: new Date().toISOString(),
        entry_type: "DEBIT"
      };
      
      setTransactions(prev => [newTx, ...prev]);
      
      setToast(`Sent -$${lastMessage.amount.toFixed(2)}`);
      setTimeout(() => setToast(null), 3000);
    }

    if (lastMessage.type === "PAYMENT_REJECTED") {
      const newTx = {
        transaction_id: lastMessage.transaction_id,
        amount: lastMessage.amount,
        status: "REJECTED",
        created_at: new Date().toISOString(),
        entry_type: "CREDIT" // Refund
      };
      
      setTransactions(prev => [newTx, ...prev]);
      
      setToast(`Refunded +$${lastMessage.amount.toFixed(2)}`);
      setTimeout(() => setToast(null), 3000);
    }
  }, [lastMessage]);

  return (
    <div className="glass-panel p-6 relative overflow-hidden flex flex-col h-full">
      {/* Toast Notification */}
      {toast && (
        <div className="absolute top-4 right-4 bg-green-500/20 text-green-300 border border-green-500/50 px-4 py-2 rounded-lg shadow-lg animate-bounce z-50 backdrop-blur-md">
          {toast}
        </div>
      )}

      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">Live Transaction Feed</h2>
        <div className={`px-3 py-1 text-xs font-semibold rounded-full flex items-center gap-2 ${isConnected ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></span>
          {isConnected ? 'Connected' : 'Reconnecting...'}
        </div>
      </div>
      
      {!accountId && <p className="text-slate-400">Please enter an Account ID above.</p>}
      
      {accountId && (
        <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
          <table className="w-full text-left text-sm">
            <thead className="text-slate-400 sticky top-0 bg-slate-900/90 backdrop-blur-sm z-10">
              <tr>
                <th className="pb-3 font-medium">Time</th>
                <th className="pb-3 font-medium">Type</th>
                <th className="pb-3 font-medium">Amount</th>
                <th className="pb-3 font-medium text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {transactions.map((tx, idx) => (
                <tr key={`${tx.transaction_id}-${idx}`} className="hover:bg-white/5 transition-colors group">
                  <td className="py-3 text-slate-300 font-mono text-xs">
                    {new Date(tx.created_at).toLocaleTimeString()}
                  </td>
                  <td className="py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${tx.entry_type === 'CREDIT' ? 'bg-green-500/10 text-green-400' : 'bg-rose-500/10 text-rose-400'}`}>
                      {tx.entry_type}
                    </span>
                  </td>
                  <td className="py-3 font-medium text-white">
                    {tx.entry_type === 'CREDIT' ? '+' : '-'}${Math.abs(tx.amount).toFixed(2)}
                  </td>
                  <td className="py-3 text-right">
                    <span className={`px-2 py-0.5 rounded text-xs ${tx.status === 'SETTLED' || tx.status === 'BOOKED' ? 'text-slate-300' : 'text-amber-400 bg-amber-400/10'}`}>
                      {tx.status}
                    </span>
                  </td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td colSpan="4" className="py-8 text-center text-slate-500">No transactions found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
