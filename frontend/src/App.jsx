import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import { WebSocketProvider } from './contexts/WebSocketContext';

function App() {
  return (
    <WebSocketProvider>
      <div className="min-h-screen bg-dark-bg">
        <Dashboard />
      </div>
    </WebSocketProvider>
  );
}

export default App;
