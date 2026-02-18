import React, { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, Briefcase, Users, Percent, Target, Star } from 'lucide-react';

const EconomyStats = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/marketplace/stats');
      const data = await response.json();
      setStats(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch economy stats:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="glass-card p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <TrendingUp size={20} />
          Economy Stats
        </h2>
        <div className="text-center text-gray-400 py-8">
          Loading economy stats...
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="glass-card p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <TrendingUp size={20} />
          Economy Stats
        </h2>
        <div className="text-center text-gray-400 py-8">
          No economy data available
        </div>
      </div>
    );
  }

  const statItems = [
    {
      label: 'Total Volume',
      value: `$${stats.total_transactions.toFixed(2)}`,
      icon: <DollarSign size={16} className="text-green-500" />,
      color: 'text-green-400'
    },
    {
      label: 'Platform Revenue',
      value: `$${stats.platform_revenue.toFixed(2)}`,
      icon: <TrendingUp size={16} className="text-purple-500" />,
      color: 'text-purple-400'
    },
    {
      label: 'Total Jobs',
      value: stats.total_jobs.toString(),
      icon: <Briefcase size={16} className="text-blue-500" />,
      color: 'text-blue-400'
    },
    {
      label: 'Active Agents',
      value: stats.active_agents.toString(),
      icon: <Users size={16} className="text-orange-500" />,
      color: 'text-orange-400'
    },
    {
      label: 'Open Jobs',
      value: stats.open_jobs.toString(),
      icon: <Target size={16} className="text-yellow-500" />,
      color: 'text-yellow-400'
    },
    {
      label: 'Avg Rating',
      value: `${stats.average_rating.toFixed(1)}/5.0`,
      icon: <Star size={16} className="text-yellow-500" />,
      color: 'text-yellow-400'
    }
  ];

  return (
    <div className="glass-card p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <TrendingUp size={20} />
        Economy Stats
      </h2>
      
      <div className="space-y-3">
        {statItems.map((item, index) => (
          <div 
            key={index}
            className="flex items-center justify-between p-3 glass-card hover:bg-dark-border transition-all duration-200"
          >
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0">
                {item.icon}
              </div>
              <div>
                <p className="text-xs text-gray-400">{item.label}</p>
                <p className={`font-semibold ${item.color}`}>{item.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Economy Health Indicator */}
      <div className="mt-6 pt-4 border-t border-dark-border">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">Market Health</span>
          <span className="text-sm text-green-400">Good</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full transition-all duration-500"
            style={{ 
              width: `${Math.min(100, (stats.active_agents / Math.max(1, stats.total_agents)) * 100)}%` 
            }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {stats.active_agents} of {stats.total_agents} agents active
        </p>
      </div>
      
      {/* Platform Fee Display */}
      <div className="mt-4 p-3 bg-dark-border rounded">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Platform Fee Rate</span>
          <span className="text-sm font-mono text-purple-400">10%</span>
        </div>
        <div className="flex items-center justify-between mt-1">
          <span className="text-xs text-gray-500">Total Collected</span>
          <span className="text-xs font-mono text-green-400">
            ${stats.platform_revenue.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default EconomyStats;
