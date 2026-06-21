import { useState } from 'react';

export default function SimulatePayment({ accountId }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSimulate = async (amount) => {
    if (!accountId) return;
    setLoading(true);
    setResult(null);

    // Hardcode the receiver to the known seeded account (or flip if we are logged in as receiver)
    // Account 1: 5d2d2e3a-208a-4884-be37-bda100184d92 (USD)
    // Account 2: 38f2512f-d882-41a0-a39a-36c869d2ffe9 (USD)
    const receiverId = accountId === "5d2d2e3a-208a-4884-be37-bda100184d92" 
      ? "38f2512f-d882-41a0-a39a-36c869d2ffe9" 
      : "5d2d2e3a-208a-4884-be37-bda100184d92";

    const payload = {
      sender_account_id: accountId,
      receiver_account_id: receiverId,
      amount: amount, 
      currency: "USD"
    };

    try {
      const res = await fetch('http://127.0.0.1:8000/payments/domestic-payments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer mock-valid-token',
          'X-Client-Cert-Thumbprint': 'mock-cert',
          'x-idempotency-key': crypto.randomUUID()
        },
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      if (res.ok) {
        setResult({ success: true, message: `Sent $${amount.toFixed(2)}!` });
      } else {
        setResult({ success: false, message: data.detail || 'Payment failed' });
      }
    } catch (err) {
      setResult({ success: false, message: 'Network error' });
    } finally {
      setLoading(false);
      setTimeout(() => setResult(null), 3000);
    }
  };

  return (
    <div className="glass-panel p-6 flex flex-col items-center justify-center relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-fuchsia-500/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
      
      <h3 className="text-white font-semibold mb-2">Debug Tools</h3>
      <p className="text-slate-400 text-xs text-center mb-4">
        Simulate a transaction to push data through the cryptographic ledger. Amounts over $10,000 will be flagged for fraud.
      </p>
      
      <div className="flex flex-col gap-2 w-full">
        <button 
          onClick={() => handleSimulate(15.00)}
          disabled={!accountId || loading}
          className="bg-fuchsia-600 hover:bg-fuchsia-500 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium transition-colors shadow-[0_0_15px_rgba(192,38,211,0.4)]"
        >
          {loading ? 'Processing...' : 'Simulate $15 Payment'}
        </button>
        
        <button 
          onClick={() => handleSimulate(15000.00)}
          disabled={!accountId || loading}
          className="bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium transition-colors shadow-[0_0_15px_rgba(225,29,72,0.4)]"
        >
          {loading ? 'Processing...' : 'Simulate $15,000 (Fraud)'}
        </button>
      </div>

      {result && (
        <div className={`mt-4 text-sm font-medium ${result.success ? 'text-emerald-400' : 'text-rose-400'}`}>
          {result.message}
        </div>
      )}
    </div>
  );
}
