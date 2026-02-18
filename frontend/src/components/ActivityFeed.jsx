import React from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { Activity, DollarSign, Briefcase, Star, Clock } from 'lucide-react';

const ActivityFeed = () => {
  const { activityFeed, isConnected } = useWebSocket();

  const getActivityIcon = (type, data) => {
    if (type === 'agent_action') {
      switch (data.action) {
        case 'BID_ON_JOB':
          return <Briefcase size={14} className="text-orange-400" />;
        case 'DO_WORK':
          return <Activity size={14} className="text-blue-400" />;
        case 'POST_JOB':
          return <Briefcase size={14} className="text-green-400" />;
        case 'EVALUATE_BIDS':
          return <Star size={14} className="text-purple-400" />;
        case 'RATE':
          return <Star size={14} className="text-yellow-400" />;
        default:
          return <Activity size={14} className="text-gray-400" />;
      }
    } else if (type === 'transaction') {
      return <DollarSign size={14} className="text-green-400" />;
    }
    return <Activity size={14} className="text-gray-400" />;
  };

  const formatActivityMessage = (item) => {
    if (item.type === 'agent_action') {
      const { agent_name, action, reasoning } = item.data;
      return (
        <>
          <span className="font-semibold text-white">{agent_name}</span>
          <span className="text-blue-400"> {action.toLowerCase().replace('_', ' ')}</span>
          <span className="text-gray-400"> - {reasoning}</span>
        </>
      );
    } else if (item.type === 'transaction') {
      const { amount, platform_fee } = item.data;
      return (
        <>
          <span className="text-green-400">💰 Transaction:</span>
          <span className="text-white"> ${amount}</span>
          <span className="text-gray-400"> (Fee: ${platform_fee})</span>
        </>
      );
    }
    return <span className="text-gray-400">Unknown activity</span>;
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="glass-card p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <Activity size={20} />
        Activity Feed
      </h2>
      
      <div className="flex items-center gap-2 mb-4">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
        <span className="text-xs text-gray-400">
          {isConnected ? 'Live updates' : 'Disconnected'}
        </span>
      </div>
      
      {activityFeed.length === 0 ? (
        <div className="text-center text-gray-400 py-8">
          <Activity size={32} className="mx-auto mb-2 opacity-50" />
          <p className="text-sm">No activity yet. Start the simulation to see live updates!</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-80 overflow-y-auto scrollbar-thin">
          {activityFeed.map((item, index) => (
            <div 
              key={`${item.type}-${index}`}
              className="flex items-start gap-3 p-3 glass-card hover:bg-dark-border transition-all duration-200 animate-slide-up"
            >
              <div className="flex-shrink-0 mt-1">
                {getActivityIcon(item.type, item.data)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="text-sm">
                  {formatActivityMessage(item)}
                </div>
                
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                  <Clock size={10} />
                  <span>{formatTime(item.data.timestamp || new Date().toISOString())}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {activityFeed.length > 0 && (
        <div className="mt-4 pt-4 border-t border-dark-border text-center">
          <p className="text-xs text-gray-500">
            Showing latest {activityFeed.length} activities
          </p>
        </div>
      )}
    </div>
  );
};

export default ActivityFeed;
