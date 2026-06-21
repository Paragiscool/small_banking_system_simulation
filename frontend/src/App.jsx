import { useState } from 'react';
import AccountOverview from './components/AccountOverview';
import TransactionFeed from './components/TransactionFeed';
import FraudQueue from './components/FraudQueue';
import LedgerIntegrity from './components/LedgerIntegrity';
import SimulatePayment from './components/SimulatePayment';

function App() {
  const [accountIdInput, setAccountIdInput] = useState('');
  const [activeAccount, setActiveAccount] = useState('');

  const handleConnect = (e) => {
    e.preventDefault();
    if (accountIdInput.trim()) {
      setActiveAccount(accountIdInput.trim());
    }
  };

  return (
    <div className="min-h-screen p-6 md:p-8 flex flex-col gap-6">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
            Nexus Core Banking
          </h1>
          <p className="text-slate-400 text-sm mt-1">Real-Time Cryptographic Dashboard</p>
        </div>
        
        <form onSubmit={handleConnect} className="flex gap-2 w-full md:w-auto">
          <input 
            type="text" 
            placeholder="Enter Account ID (e.g. 1)" 
            className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-indigo-500/50 transition-colors w-full md:w-64"
            value={accountIdInput}
            onChange={(e) => setAccountIdInput(e.target.value)}
          />
          <button 
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-lg shadow-indigo-500/20"
          >
            Connect
          </button>
        </form>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-[600px]">
        {/* Left Column */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <AccountOverview accountId={activeAccount} />
          <SimulatePayment accountId={activeAccount} />
          <div className="flex-1 min-h-[300px]">
            <FraudQueue />
          </div>
        </div>

        {/* Middle/Right Column */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="flex-1 min-h-[400px]">
            <TransactionFeed accountId={activeAccount} />
          </div>
          <LedgerIntegrity accountId={activeAccount} />
        </div>
      </div>
    </div>
  );
}

export default App;
