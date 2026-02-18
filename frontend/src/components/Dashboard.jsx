import React, { useState, useEffect } from 'react';
import { Play, Pause, Activity, Users, Briefcase, DollarSign, TrendingUp } from 'lucide-react';
import { useWebSocket } from '../contexts/WebSocketContext';
import AgentCards from './AgentCards';
import JobBoard from './JobBoard';
import ActivityFeed from './ActivityFeed';
import EconomyStats from './EconomyStats';

const Dashboard = () => {
  const { isConnected, marketplaceData, activityFeed } = useWebSocket();
  const [isSimulationRunning, setIsSimulationRunning] = useState(false);

  const startSimulation = async () => {
    try {
      const response = await fetch('/api/simulation/start', { method: 'POST' });
      const data = await response.json();
      setIsSimulationRunning(true);
      console.log('Simulation started:', data);
    } catch (error) {
      console.error('Failed to start simulation:', error);
    }
  };

  const stopSimulation = async () => {
    try {
      const response = await fetch('/api/simulation/stop', { method: 'POST' });
      const data = await response.json();
      setIsSimulationRunning(false);
      console.log('Simulation stopped:', data);
    } catch (error) {
      console.error('Failed to stop simulation:', error);
    }
  };

  useEffect(() => {
    // Check simulation status on mount
    fetch('/api/simulation/status')
      .then(res => res.json())
      .then(data => setIsSimulationRunning(data.status === 'running'))
      .catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-dark-bg p-6">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">🤖 Agent Marketplace</h1>
            <p className="text-gray-400">Real-time autonomous agent economy simulation</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
              <span className="text-sm text-gray-400">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            
            <button
              onClick={isSimulationRunning ? stopSimulation : startSimulation}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                isSimulationRunning 
                  ? 'bg-red-600 hover:bg-red-700 text-white' 
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {isSimulationRunning ? (
                <>
                  <Pause size={16} />
                  Stop Simulation
                </>
              ) : (
                <>
                  <Play size={16} />
                  Start Simulation
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Quick Stats */}
      {marketplaceData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="glass-card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Agents</p>
                <p className="text-2xl font-bold">{marketplaceData.stats.total_agents || 0}</p>
              </div>
              <Users className="text-blue-500" size={24} />
            </div>
          </div>
          
          <div className="glass-card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Open Jobs</p>
                <p className="text-2xl font-bold">{marketplaceData.open_jobs || 0}</p>
              </div>
              <Briefcase className="text-green-500" size={24} />
            </div>
          </div>
          
          <div className="glass-card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Volume</p>
                <p className="text-2xl font-bold">
                  ${(marketplaceData.stats.total_transaction_volume || 0).toFixed(2)}
                </p>
              </div>
              <DollarSign className="text-yellow-500" size={24} />
            </div>
          </div>
          
          <div className="glass-card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Platform Revenue</p>
                <p className="text-2xl font-bold">
                  ${(marketplaceData.stats.total_platform_revenue || 0).toFixed(2)}
                </p>
              </div>
              <TrendingUp className="text-purple-500" size={24} />
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Agent Cards and Job Board */}
        <div className="lg:col-span-2 space-y-6">
          <AgentCards />
          <JobBoard />
        </div>
        
        {/* Right Column - Activity Feed and Economy Stats */}
        <div className="space-y-6">
          <ActivityFeed />
          <EconomyStats />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
