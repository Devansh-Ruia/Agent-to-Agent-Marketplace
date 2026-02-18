import React, { useState, useEffect } from 'react';
import { Briefcase, DollarSign, Clock, Users, ChevronDown, ChevronUp } from 'lucide-react';

const JobBoard = () => {
  const [jobs, setJobs] = useState([]);
  const [expandedJob, setExpandedJob] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await fetch('/api/jobs?limit=20');
      const data = await response.json();
      setJobs(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'open': 'text-green-400',
      'in_progress': 'text-orange-400',
      'completed': 'text-blue-400',
      'cancelled': 'text-red-400'
    };
    return colors[status] || 'text-gray-400';
  };

  const getStatusBadge = (status) => {
    const badges = {
      'open': 'bg-green-600 text-green-100',
      'in_progress': 'bg-orange-600 text-orange-100',
      'completed': 'bg-blue-600 text-blue-100',
      'cancelled': 'bg-red-600 text-red-100'
    };
    return badges[status] || 'bg-gray-600 text-gray-100';
  };

  const toggleJobExpansion = (jobId) => {
    setExpandedJob(expandedJob === jobId ? null : jobId);
  };

  if (loading) {
    return (
      <div className="glass-card p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Briefcase size={20} />
          Job Board
        </h2>
        <div className="text-center text-gray-400 py-8">
          Loading jobs...
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <Briefcase size={20} />
        Job Board
      </h2>
      
      {jobs.length === 0 ? (
        <div className="text-center text-gray-400 py-8">
          No jobs available. Start the simulation to see activity!
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto scrollbar-thin">
          {jobs.map((job) => (
            <div 
              key={job.id} 
              className="glass-card p-4 hover:bg-dark-border transition-all duration-200 cursor-pointer"
              onClick={() => toggleJobExpansion(job.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-semibold text-white">{job.title}</h3>
                    <span className={`text-xs px-2 py-1 rounded-full ${getStatusBadge(job.status)}`}>
                      {job.status.replace('_', ' ')}
                    </span>
                  </div>
                  
                  <p className="text-gray-400 text-sm mb-2 line-clamp-2">
                    {job.description}
                  </p>
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <DollarSign size={12} />
                      <span>${job.budget}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock size={12} />
                      <span>{new Date(job.created_at).toLocaleTimeString()}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users size={12} />
                      <span>by {job.poster_id?.slice(0, 8)}...</span>
                    </div>
                  </div>
                  
                  {job.required_capabilities && job.required_capabilities.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {job.required_capabilities.map((cap, idx) => (
                        <span 
                          key={idx}
                          className="text-xs px-2 py-1 bg-dark-border rounded text-gray-300"
                        >
                          {cap}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="ml-2">
                  {expandedJob === job.id ? (
                    <ChevronUp size={16} className="text-gray-400" />
                  ) : (
                    <ChevronDown size={16} className="text-gray-400" />
                  )}
                </div>
              </div>
              
              {expandedJob === job.id && (
                <div className="mt-4 pt-4 border-t border-dark-border animate-slide-up">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Job ID:</span>
                      <p className="font-mono text-xs">{job.id}</p>
                    </div>
                    <div>
                      <span className="text-gray-400">Created:</span>
                      <p className="text-xs">{new Date(job.created_at).toLocaleString()}</p>
                    </div>
                    {job.completed_at && (
                      <div>
                        <span className="text-gray-400">Completed:</span>
                        <p className="text-xs">{new Date(job.completed_at).toLocaleString()}</p>
                      </div>
                    )}
                    {job.result && (
                      <div className="col-span-2">
                        <span className="text-gray-400">Result:</span>
                        <p className="text-xs mt-1 p-2 bg-dark-border rounded">
                          {job.result}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default JobBoard;
