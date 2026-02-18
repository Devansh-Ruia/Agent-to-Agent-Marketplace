from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import json
import asyncio
from typing import List

from database import get_db, create_tables
from routes import agents, jobs, bids, wallet, marketplace
from simulation import MarketplaceSimulation

# Initialize FastAPI app
app = FastAPI(
    title="Agent Marketplace API",
    description="A marketplace where autonomous AI agents can discover, hire, and pay other AI agents for tasks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router)
app.include_router(jobs.router)
app.include_router(bids.router)
app.include_router(wallet.router)
app.include_router(marketplace.router)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.simulation = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        if self.active_connections:
            message_str = json.dumps(message)
            disconnected = []
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)

manager = ConnectionManager()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Agent Marketplace API",
        "docs": "/docs",
        "websocket": "/ws",
        "simulation": "/simulation/start"
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

# Simulation endpoints
@app.post("/simulation/start")
async def start_simulation():
    """Start the marketplace simulation"""
    if manager.simulation and manager.simulation.running:
        return {"message": "Simulation is already running"}
    
    # Create new simulation instance
    manager.simulation = MarketplaceSimulation()
    
    # Set up broadcasting to WebSocket connections
    original_broadcast = manager.simulation.broadcast_message
    async def broadcast_to_websockets(message):
        await manager.broadcast(message)
        # Also call original broadcast for console logging
        original_broadcast(message)
    
    manager.simulation.broadcast_message = broadcast_to_websockets
    
    # Start simulation in background
    asyncio.create_task(manager.simulation.run_simulation())
    
    return {"message": "Simulation started", "status": "running"}

@app.post("/simulation/stop")
async def stop_simulation():
    """Stop the marketplace simulation"""
    if not manager.simulation:
        return {"message": "No simulation running"}
    
    manager.simulation.stop_simulation()
    manager.simulation = None
    
    return {"message": "Simulation stopped", "status": "stopped"}

@app.get("/simulation/status")
async def get_simulation_status():
    """Get current simulation status"""
    if not manager.simulation:
        return {"status": "stopped", "tick": 0}
    
    return {
        "status": "running" if manager.simulation.running else "stopped",
        "tick": manager.simulation.tick_count,
        "agents": len(manager.simulation.agents),
        "connections": len(manager.active_connections)
    }

# Serve frontend (for development)
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the dashboard HTML"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Agent Marketplace Dashboard</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: white; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: #2a2a2a; padding: 20px; border-radius: 8px; text-align: center; }
            .agents { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .agent-card { background: #2a2a2a; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; }
            .activity { background: #2a2a2a; padding: 20px; border-radius: 8px; height: 300px; overflow-y: scroll; }
            .status-idle { border-left-color: #9E9E9E; }
            .status-working { border-left-color: #2196F3; }
            .status-bidding { border-left-color: #FF9800; }
            .job-open { color: #4CAF50; }
            .job-progress { color: #FF9800; }
            .job-completed { color: #2196F3; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Agent Marketplace Dashboard</h1>
                <p>Real-time autonomous agent economy simulation</p>
                <button onclick="startSimulation()">Start Simulation</button>
                <button onclick="stopSimulation()">Stop Simulation</button>
                <button onclick="connectWebSocket()">Connect WebSocket</button>
            </div>
            
            <div class="stats" id="stats">
                <div class="stat-card">
                    <h3>Total Agents</h3>
                    <p id="total-agents">0</p>
                </div>
                <div class="stat-card">
                    <h3>Open Jobs</h3>
                    <p id="open-jobs">0</p>
                </div>
                <div class="stat-card">
                    <h3>Total Volume</h3>
                    <p id="total-volume">$0</p>
                </div>
                <div class="stat-card">
                    <h3>Platform Revenue</h3>
                    <p id="platform-revenue">$0</p>
                </div>
            </div>
            
            <div class="agents" id="agents">
                <!-- Agent cards will be populated here -->
            </div>
            
            <div class="activity">
                <h3>📊 Activity Feed</h3>
                <div id="activity-log">
                    <p>Connecting to marketplace...</p>
                </div>
            </div>
        </div>

        <script>
            let ws = null;
            
            function connectWebSocket() {
                if (ws) ws.close();
                
                ws = new WebSocket('ws://localhost:8000/ws');
                
                ws.onopen = function() {
                    console.log('WebSocket connected');
                    addActivity('Connected to marketplace');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function() {
                    console.log('WebSocket disconnected');
                    addActivity('Disconnected from marketplace');
                };
            }
            
            function handleMessage(data) {
                if (data.type === 'marketplace_update') {
                    updateStats(data.data);
                    updateAgents(data.data.agents);
                } else if (data.type === 'agent_action') {
                    addActivity(`${data.data.agent_name}: ${data.data.action} - ${data.data.reasoning}`);
                } else if (data.type === 'transaction') {
                    addActivity(`💰 Transaction: $${data.data.amount} (Fee: $${data.data.platform_fee})`);
                }
            }
            
            function updateStats(data) {
                document.getElementById('total-agents').textContent = data.stats.total_agents || 0;
                document.getElementById('open-jobs').textContent = data.open_jobs || 0;
                document.getElementById('total-volume').textContent = `$${(data.stats.total_transaction_volume || 0).toFixed(2)}`;
                document.getElementById('platform-revenue').textContent = `$${(data.stats.total_platform_revenue || 0).toFixed(2)}`;
            }
            
            function updateAgents(agents) {
                const container = document.getElementById('agents');
                container.innerHTML = agents.map(agent => `
                    <div class="agent-card status-${agent.status}">
                        <h4>${agent.name}</h4>
                        <p><strong>Type:</strong> ${agent.type}</p>
                        <p><strong>Balance:</strong> $${agent.wallet_balance.toFixed(2)}</p>
                        <p><strong>Rating:</strong> ${agent.rating.toFixed(1)}/5.0</p>
                        <p><strong>Status:</strong> ${agent.status}</p>
                        <p><strong>Jobs:</strong> ${agent.jobs_completed} completed, ${agent.jobs_posted} posted</p>
                    </div>
                `).join('');
            }
            
            function addActivity(message) {
                const log = document.getElementById('activity-log');
                const entry = document.createElement('p');
                entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
                log.appendChild(entry);
                log.scrollTop = log.scrollHeight;
            }
            
            async function startSimulation() {
                try {
                    const response = await fetch('/simulation/start', {method: 'POST'});
                    const data = await response.json();
                    addActivity(`Simulation: ${data.message}`);
                } catch (error) {
                    addActivity(`Error starting simulation: ${error.message}`);
                }
            }
            
            async function stopSimulation() {
                try {
                    const response = await fetch('/simulation/stop', {method: 'POST'});
                    const data = await response.json();
                    addActivity(`Simulation: ${data.message}`);
                } catch (error) {
                    addActivity(`Error stopping simulation: ${error.message}`);
                }
            }
            
            // Auto-connect on page load
            connectWebSocket();
        </script>
    </body>
    </html>
    """

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    print("Agent Marketplace API started!")
    print("Dashboard available at: http://localhost:8000/dashboard")
    print("API docs available at: http://localhost:8000/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
