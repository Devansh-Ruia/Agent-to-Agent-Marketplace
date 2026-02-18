import React from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { Star, TrendingUp, Briefcase, User } from 'lucide-react';

const AgentCards = () => {
  const { marketplaceData } = useWebSocket();

  if (!marketplaceData || !marketplaceData.agents) {
    return (
      <div className="glass-card p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <User size={20} />
          Agents
        </h2>
        <div className="text-center text-gray-400 py-8">
          Loading agents...
        </div>
      </div>
    );
  }

  const getAgentIcon = (type) => {
    const icons = {
      'code_reviewer': '🔍',
      'data_analyst': '📊',
      'copywriter': '✍️',
      'web_scraper': '🕷️',
      'orchestrator': '🎯'
    };
    return icons[type] || '🤖';
  };

  const getStatusColor = (status) => {
    const colors = {
      'idle': 'status-idle',
      'working': 'status-working',
      'bidding': 'status-bidding'
    };
    return colors[status] || 'status-idle';
  };

  return (
    <div className="glass-card p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <User size={20} />
        Agents
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {marketplaceData.agents.map((agent) => (
          <div 
            key={agent.id} 
            className="glass-card p-4 border-l-4 border-l-blue-500 hover:border-l-green-500 transition-all duration-300 animate-slide-up"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{getAgentIcon(agent.type)}</span>
                <div>
                  <h3 className="font-semibold text-white">{agent.name}</h3>
                  <p className="text-xs text-gray-400 capitalize">{agent.type.replace('_', ' ')}</p>
                </div>
              </div>
              <span className={`status-badge ${getStatusColor(agent.status)}`}>
                {agent.status}
              </span>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Balance</span>
                <span className="font-mono text-green-400">
                  ${agent.wallet_balance.toFixed(2)}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Rating</span>
                <div className="flex items-center gap-1">
                  <Star size={14} className="text-yellow-500 fill-current" />
                  <span className="text-sm">{agent.rating.toFixed(1)}</span>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Jobs</span>
                <div className="flex gap-3 text-xs">
                  <span className="text-blue-400">
                    <Briefcase size={12} className="inline mr-1" />
                    {agent.jobs_completed}
                  </span>
                  <span className="text-green-400">
                    <TrendingUp size={12} className="inline mr-1" />
                    {agent.jobs_posted}
                  </span>
                </div>
              </div>
            </div>
            
            {/* Wallet balance indicator */}
            <div className="mt-3 pt-3 border-t border-dark-border">
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, (agent.wallet_balance / 200) * 100)}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentCards;
