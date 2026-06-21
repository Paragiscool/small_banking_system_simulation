import { useState } from 'react';

export default function LedgerIntegrity({ accountId }) {
  const [status, setStatus] = useState("IDLE"); // IDLE, VERIFYING, SECURE, COMPROMISED
  const [details, setDetails] = useState(null);

  const verifyLedger = async () => {
    if (!accountId) return;
    
    setStatus("VERIFYING");
    try {
      const res = await fetch(`http://127.0.0.1:8000/admin/verify-ledger/${accountId}`, {
        headers: {
          'Authorization': 'Bearer mock-valid-token'
        }
      });
      const data = await res.json();
      
      // Artificial delay for UX
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      if (res.ok && data.is_valid) {
        setStatus("SECURE");
        setDetails(data);
      } else {
        setStatus("COMPROMISED");
        setDetails(data);
      }
    } catch (err) {
      console.error(err);
      setStatus("COMPROMISED");
      setDetails({ message: "Verification failed due to network or server error." });
    }
  };

  return (
    <div className="glass-panel p-6 flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-white">Ledger Integrity</h2>
        <button 
          onClick={verifyLedger}
          disabled={!accountId || status === "VERIFYING"}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors shadow-lg shadow-indigo-500/20"
        >
          {status === "VERIFYING" ? "Scanning Hash Chain..." : "Verify Cryptographic Chain"}
        </button>
      </div>

      <div className="flex-1 flex flex-col justify-center items-center p-6 border border-white/5 rounded-xl bg-white/5">
        {status === "IDLE" && (
          <p className="text-slate-400 text-center">Click verify to scan the cryptographic hash chain for this account.</p>
        )}
        
        {status === "VERIFYING" && (
          <div className="animate-pulse flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-indigo-400 font-mono text-sm">Recalculating SHA-256 Hashes...</p>
          </div>
        )}

        {status === "SECURE" && (
          <div className="flex flex-col items-center gap-2 text-center">
            <div className="w-16 h-16 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center text-3xl mb-2 shadow-[0_0_30px_rgba(16,185,129,0.3)]">
              ✓
            </div>
            <h3 className="text-emerald-400 font-bold text-lg tracking-widest uppercase">Chain Verified</h3>
            <p className="text-slate-300 text-sm">{details?.message}</p>
            <div className="mt-4 px-4 py-2 bg-black/40 rounded border border-white/10 font-mono text-xs text-slate-500 truncate w-full max-w-[280px]">
              Latest Hash: {details?.latest_hash}
            </div>
          </div>
        )}

        {status === "COMPROMISED" && (
          <div className="flex flex-col items-center gap-2 text-center">
            <div className="w-16 h-16 bg-rose-500/20 text-rose-400 rounded-full flex items-center justify-center text-3xl mb-2 shadow-[0_0_30px_rgba(244,63,94,0.4)] animate-pulse">
              !
            </div>
            <h3 className="text-rose-400 font-bold text-lg tracking-widest uppercase">Tampering Detected</h3>
            <p className="text-slate-300 text-sm">{details?.detail || details?.message}</p>
          </div>
        )}
      </div>
    </div>
  );
}
