import asyncio
import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, create_tables
from models import Agent, Job, Bid, Transaction
from services.agent_brain import AgentBrain
from services.economy import EconomyService
from agents.code_reviewer import CodeReviewerAgent
from agents.data_analyst import DataAnalystAgent
from agents.copywriter import CopywriterAgent
from agents.web_scraper import WebScraperAgent
from agents.orchestrator import OrchestratorAgent

# Configuration
TICK_INTERVAL = int(os.getenv("TICK_INTERVAL", "5"))  # seconds
STARTING_BALANCE = float(os.getenv("STARTING_BALANCE", "100.0"))
PLATFORM_FEE_RATE = float(os.getenv("PLATFORM_FEE_RATE", "0.10"))

class MarketplaceSimulation:
    def __init__(self):
        self.db = SessionLocal()
        self.agent_brain = AgentBrain(self.db)
        self.economy_service = EconomyService(self.db)
        self.agents = []
        self.tick_count = 0
        self.running = False
        self.websocket_connections = set()
        
    def initialize_agents(self):
        """Initialize the autonomous agents"""
        print("Initializing agents...")
        
        # Create agent instances
        self.agents = [
            CodeReviewerAgent("CodeReviewer-01", self.db),
            DataAnalystAgent("DataAnalyst-01", self.db),
            CopywriterAgent("CopyWriter-01", self.db),
            WebScraperAgent("WebScraper-01", self.db),
            OrchestratorAgent("Orchestrator-00", self.db)
        ]
        
        print(f"Created {len(self.agents)} agents")
        
        # Orchestrator starts by posting some initial jobs
        orchestrator = self.agents[-1]  # Last agent is orchestrator
        initial_jobs = [
            {
                "title": "Analyze customer sales data",
                "description": "Need comprehensive analysis of Q4 sales data to identify trends and opportunities",
                "required_capabilities": ["data_analysis", "statistical_analysis"],
                "budget": 25.0
            },
            {
                "title": "Review API security implementation",
                "description": "Security review needed for REST API with focus on authentication and authorization",
                "required_capabilities": ["security_audit", "code_review"],
                "budget": 30.0
            }
        ]
        
        for job_data in initial_jobs:
            orchestrator.post_job(**job_data)
            print(f"Orchestrator posted initial job: {job_data['title']}")
    
    def process_completed_jobs(self):
        """Process payments for completed jobs"""
        completed_jobs = self.db.query(Job).filter(
            Job.status == "completed",
            Job.result.isnot(None)
        ).all()
        
        for job in completed_jobs:
            # Check if payment has already been processed
            existing_transaction = self.db.query(Transaction).filter(
                Transaction.job_id == job.id
            ).first()
            
            if not existing_transaction and job.winning_bid_id:
                # Process payment
                transaction = self.economy_service.process_job_payment(job.id)
                if transaction:
                    print(f"Processed payment for job {job.id}: ${transaction.amount} to worker, ${transaction.platform_fee} platform fee")
                    
                    # Broadcast transaction
                    self.broadcast_message({
                        "type": "transaction",
                        "data": {
                            "transaction_id": transaction.id,
                            "job_id": job.id,
                            "amount": transaction.amount,
                            "platform_fee": transaction.platform_fee,
                            "payer_id": transaction.payer_id,
                            "payee_id": transaction.payee_id
                        }
                    })
    
    def get_marketplace_state(self):
        """Get current marketplace state for broadcasting"""
        stats = self.economy_service.get_marketplace_economics()
        agents = self.db.query(Agent).all()
        
        return {
            "type": "marketplace_update",
            "data": {
                "tick": self.tick_count,
                "timestamp": datetime.utcnow().isoformat(),
                "stats": stats,
                "agents": [
                    {
                        "id": agent.id,
                        "name": agent.name,
                        "type": agent.agent_type,
                        "wallet_balance": agent.wallet_balance,
                        "rating": agent.rating,
                        "status": agent.status,
                        "jobs_completed": agent.total_jobs_completed,
                        "jobs_posted": agent.total_jobs_posted
                    } for agent in agents
                ],
                "open_jobs": len(self.db.query(Job).filter(Job.status == "open").all()),
                "active_jobs": len(self.db.query(Job).filter(Job.status == "in_progress").all()),
                "completed_jobs": len(self.db.query(Job).filter(Job.status == "completed").all())
            }
        }
    
    def broadcast_message(self, message):
        """Broadcast message to all WebSocket connections"""
        if self.websocket_connections:
            message_str = json.dumps(message)
            # In a real implementation, this would send to actual WebSocket connections
            print(f"Broadcasting: {message['type']}")
    
    async def run_agent_tick(self, agent):
        """Run a single tick for one agent"""
        try:
            # Get agent data
            agent_data = self.db.query(Agent).filter(Agent.id == agent.agent_id).first()
            if not agent_data:
                return
            
            # Get decision from agent brain
            decision = self.agent_brain.get_llm_decision(
                agent_data, 
                agent.get_persona_description()
            )
            
            # Execute decision
            result = self.agent_brain.execute_decision(agent_data, decision)
            
            # Log the action
            action_log = {
                "type": "agent_action",
                "data": {
                    "agent_id": agent.agent_id,
                    "agent_name": agent.name,
                    "action": decision.get("action"),
                    "reasoning": decision.get("reasoning"),
                    "success": result.get("success", False),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            print(f"[{agent.name}] {decision.get('action')}: {decision.get('reasoning')}")
            self.broadcast_message(action_log)
            
        except Exception as e:
            print(f"Error running agent tick for {agent.name}: {e}")
    
    async def simulation_tick(self):
        """Run one tick of the simulation"""
        print(f"\n=== Simulation Tick {self.tick_count} ===")
        
        # Process completed jobs and payments
        self.process_completed_jobs()
        
        # Run agent ticks in parallel
        agent_tasks = [self.run_agent_tick(agent) for agent in self.agents]
        await asyncio.gather(*agent_tasks)
        
        # Broadcast marketplace state
        state_update = self.get_marketplace_state()
        self.broadcast_message(state_update)
        
        # Print summary
        stats = self.economy_service.get_marketplace_economics()
        print(f"Marketplace Stats - Total Volume: ${stats['total_transaction_volume']:.2f}, "
              f"Platform Revenue: ${stats['total_platform_revenue']:.2f}, "
              f"Completion Rate: {stats['completion_rate']:.1f}%")
        
        self.tick_count += 1
    
    async def run_simulation(self):
        """Main simulation loop"""
        print("Starting Agent Marketplace Simulation...")
        
        # Initialize database
        create_tables()
        
        # Initialize agents
        self.initialize_agents()
        
        print(f"Simulation running with {TICK_INTERVAL} second ticks")
        print("Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while self.running:
                await self.simulation_tick()
                await asyncio.sleep(TICK_INTERVAL)
        except KeyboardInterrupt:
            print("\nSimulation stopped by user")
            self.running = False
        except Exception as e:
            print(f"Simulation error: {e}")
            self.running = False
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False

# Main entry point
if __name__ == "__main__":
    simulation = MarketplaceSimulation()
    asyncio.run(simulation.run_simulation())
