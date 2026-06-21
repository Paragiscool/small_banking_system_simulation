import { useState, useEffect } from 'react';

export default function FraudQueue() {
  const [queue, setQueue] = useState([]);

  const fetchQueue = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/admin/fraud-queue', {
        headers: {
          'Authorization': 'Bearer mock-valid-token'
        }
      });
      const data = await res.json();
      setQueue(data.fraud_queue || []);
    } catch (err) {
      console.error("Failed to fetch fraud queue", err);
    }
  };

  useEffect(() => {
    fetchQueue();
    // Poll every 10 seconds for new fraud alerts
    const interval = setInterval(fetchQueue, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (transactionId, action) => {
    // Step A: Cache the current state so we can rollback if things go wrong
    const previousQueue = [...queue];
    
    // Step B: Optimistically remove the item from the UI INSTANTLY
    setQueue(prev => prev.filter(tx => tx.transaction_id !== transactionId));

    try {
      // Step C: Fire the backend request
      const endpoint = action === 'approve' 
        ? 'http://127.0.0.1:8000/admin/approve-transaction'
        : 'http://127.0.0.1:8000/admin/reject-transaction';

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': 'Bearer mock-valid-token'
        },
        body: JSON.stringify({ transaction_id: transactionId })
      });
      
      if (!res.ok) {
        throw new Error(`Backend failed to ${action}`);
      }
    } catch (err) {
      // Step D: THE ROLLBACK
      console.error("Action failed, rolling back UI:", err);
      setQueue(previousQueue);
      alert(`Failed to ${action} transaction. Network error or server crashed.`);
    }
  };

  return (
    <div className="glass-panel p-6 flex flex-col h-full">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          Fraud Queue
          {queue.length > 0 && (
            <span className="bg-rose-500 text-white text-xs font-bold px-2 py-0.5 rounded-full animate-pulse">
              {queue.length}
            </span>
          )}
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-3">
        {queue.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-400 text-sm">
            No transactions pending review.
          </div>
        ) : (
          queue.map(tx => (
            <div key={tx.transaction_id} className="bg-white/5 border border-amber-500/30 p-4 rounded-xl flex justify-between items-center group hover:bg-white/10 transition-colors">
              <div>
                <div className="text-amber-400 text-sm font-semibold mb-1">${tx.amount.toFixed(2)}</div>
                <div className="text-slate-400 text-xs font-mono">From: {tx.account_id}</div>
                <div className="text-slate-500 text-[10px] font-mono mt-1">Tx: {tx.transaction_id.substring(0,8)}...</div>
              </div>
              
              <div className="flex flex-col gap-2">
                <button 
                  onClick={() => handleAction(tx.transaction_id, 'approve')}
                  className="px-3 py-1 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 text-xs font-semibold rounded transition-colors border border-emerald-500/30"
                >
                  Approve
                </button>
                <button 
                  onClick={() => handleAction(tx.transaction_id, 'reject')}
                  className="px-3 py-1 bg-rose-500/20 text-rose-400 hover:bg-rose-500/30 text-xs font-semibold rounded transition-colors border border-rose-500/30"
                >
                  Reject
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
