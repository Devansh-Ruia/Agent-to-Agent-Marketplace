import openai
import json
import os
from typing import Dict, Any, List
from models import Agent, Job, Bid
from sqlalchemy.orm import Session

openai.api_key = os.getenv("OPENAI_API_KEY")

AGENT_DECISION_PROMPT = """
You are {agent_name}, an autonomous AI agent in a marketplace economy.

YOUR PROFILE:
- Type: {agent_type}
- Capabilities: {capabilities}
- Wallet Balance: ${wallet_balance:.2f}
- Rating: {rating:.1f}/5.0
- Jobs Completed: {jobs_completed}
- Jobs Posted: {jobs_posted}

CURRENT MARKETPLACE STATE:
Open Jobs: {open_jobs_json}
Your Active Bids: {active_bids_json}
Your Posted Jobs: {posted_jobs_json}
Jobs You're Working On: {working_jobs_json}

RULES:
- You must make economically rational decisions
- Don't bid more than 50% of your wallet on a single job
- Don't bid on jobs outside your capabilities
- Aim to maximize your wallet balance over time
- Consider the job poster's budget — bid competitively
- If no good jobs are available, IDLE and wait
- Complete your current work before taking on new jobs
- When posting jobs, ensure you have sufficient funds

{persona_description}

Choose ONE action and respond in this exact JSON format:
{{
  "action": "POST_JOB" | "BID_ON_JOB" | "EVALUATE_BIDS" | "DO_WORK" | "RATE" | "IDLE",
  "reasoning": "brief explanation of your economic reasoning",
  "params": {{ ... action-specific parameters ... }}
}}

ACTION PARAMETERS:
- POST_JOB: {{"title": "...", "description": "...", "required_capabilities": [...], "budget": 0.0}}
- BID_ON_JOB: {{"job_id": "...", "amount": 0.0, "pitch": "..."}}
- EVALUATE_BIDS: {{"job_id": "..."}}
- DO_WORK: {{"job_id": "...", "result": "..."}}
- RATE: {{"job_id": "...", "rated_agent_id": "...", "rating": 5, "comment": "..."}}
- IDLE: {{}}
"""

class AgentBrain:
    def __init__(self, db: Session):
        self.db = db
    
    def get_llm_decision(self, agent: Agent, persona_description: str) -> Dict[str, Any]:
        """Get decision from LLM for an agent"""
        
        # Get marketplace state
        open_jobs = self.db.query(Job).filter(Job.status == "open").all()
        active_bids = self.db.query(Bid).filter(
            Bid.bidder_id == agent.id,
            Bid.status == "pending"
        ).all()
        posted_jobs = self.db.query(Job).filter(Job.poster_id == agent.id).all()
        working_jobs = self.db.query(Job).filter(
            Job.winning_bid_id.in_(
                self.db.query(Bid.id).filter(
                    Bid.bidder_id == agent.id,
                    Bid.status == "accepted"
                )
            ),
            Job.status == "in_progress"
        ).all()
        
        # Convert to JSON for prompt
        open_jobs_json = json.dumps([
            {
                "id": job.id,
                "title": job.title,
                "description": job.description[:100] + "...",
                "required_capabilities": job.required_capabilities,
                "budget": job.budget
            } for job in open_jobs
        ], indent=2)
        
        active_bids_json = json.dumps([
            {
                "id": bid.id,
                "job_id": bid.job_id,
                "amount": bid.amount,
                "status": bid.status
            } for bid in active_bids
        ], indent=2)
        
        posted_jobs_json = json.dumps([
            {
                "id": job.id,
                "title": job.title,
                "status": job.status,
                "budget": job.budget
            } for job in posted_jobs
        ], indent=2)
        
        working_jobs_json = json.dumps([
            {
                "id": job.id,
                "title": job.title,
                "budget": job.budget
            } for job in working_jobs
        ], indent=2)
        
        # Build the prompt
        prompt = AGENT_DECISION_PROMPT.format(
            agent_name=agent.name,
            agent_type=agent.agent_type,
            capabilities=", ".join(agent.capabilities),
            wallet_balance=agent.wallet_balance,
            rating=agent.rating,
            jobs_completed=agent.total_jobs_completed,
            jobs_posted=agent.total_jobs_posted,
            open_jobs_json=open_jobs_json,
            active_bids_json=active_bids_json,
            posted_jobs_json=posted_jobs_json,
            working_jobs_json=working_jobs_json,
            persona_description=persona_description
        )
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an autonomous AI agent making economic decisions in a marketplace. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            decision_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                decision = json.loads(decision_text)
                
                # Validate decision structure
                if "action" not in decision or "reasoning" not in decision:
                    raise ValueError("Missing required fields")
                
                if "params" not in decision:
                    decision["params"] = {}
                
                return decision
                
            except json.JSONDecodeError as e:
                print(f"Failed to parse LLM response as JSON: {e}")
                print(f"Response was: {decision_text}")
                return self._get_fallback_decision(agent)
                
        except Exception as e:
            print(f"Error getting LLM decision for {agent.name}: {e}")
            return self._get_fallback_decision(agent)
    
    def _get_fallback_decision(self, agent: Agent) -> Dict[str, Any]:
        """Fallback decision logic when LLM fails"""
        
        # Simple rule-based fallback
        working_jobs = self.db.query(Job).filter(
            Job.winning_bid_id.in_(
                self.db.query(Bid.id).filter(
                    Bid.bidder_id == agent.id,
                    Bid.status == "accepted"
                )
            ),
            Job.status == "in_progress"
        ).all()
        
        if working_jobs:
            return {
                "action": "DO_WORK",
                "reasoning": "Complete current work (fallback logic)",
                "params": {"job_id": working_jobs[0].id, "result": "Work completed"}
            }
        
        if agent.wallet_balance < 20:
            return {
                "action": "IDLE",
                "reasoning": "Low funds, waiting for opportunities (fallback)",
                "params": {}
            }
        
        open_jobs = self.db.query(Job).filter(Job.status == "open").all()
        matching_jobs = [job for job in open_jobs if any(
            cap in job.required_capabilities for cap in agent.capabilities
        )]
        
        if matching_jobs and agent.wallet_balance > 20:
            job = matching_jobs[0]
            bid_amount = min(job.budget * 0.7, agent.wallet_balance * 0.4)
            
            return {
                "action": "BID_ON_JOB",
                "reasoning": "Found matching job (fallback logic)",
                "params": {
                    "job_id": job.id,
                    "amount": bid_amount,
                    "pitch": "Experienced agent ready to complete this task."
                }
            }
        
        return {
            "action": "IDLE",
            "reasoning": "No suitable opportunities found (fallback)",
            "params": {}
        }
    
    def execute_decision(self, agent: Agent, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's decision and return result"""
        
        action = decision.get("action")
        params = decision.get("params", {})
        
        try:
            if action == "POST_JOB":
                from routes.jobs import create_job
                from schemas import JobCreate
                
                job_data = JobCreate(
                    poster_id=agent.id,
                    title=params["title"],
                    description=params["description"],
                    required_capabilities=params["required_capabilities"],
                    budget=params["budget"]
                )
                
                job = create_job(job_data, self.db)
                return {"success": True, "action": "POST_JOB", "job_id": job.id}
            
            elif action == "BID_ON_JOB":
                from routes.bids import create_bid
                from schemas import BidCreate
                
                bid_data = BidCreate(
                    job_id=params["job_id"],
                    bidder_id=agent.id,
                    amount=params["amount"],
                    pitch=params["pitch"]
                )
                
                bid = create_bid(bid_data, self.db)
                return {"success": True, "action": "BID_ON_JOB", "bid_id": bid.id}
            
            elif action == "EVALUATE_BIDS":
                # This would need to be implemented in the agent class
                # For now, return a placeholder
                return {"success": True, "action": "EVALUATE_BIDS", "job_id": params.get("job_id")}
            
            elif action == "DO_WORK":
                from routes.jobs import complete_job
                result = complete_job(params["job_id"], params["result"], self.db)
                return {"success": True, "action": "DO_WORK", "job_id": params["job_id"]}
            
            elif action == "RATE":
                # Rating logic would go here
                return {"success": True, "action": "RATE", "job_id": params.get("job_id")}
            
            elif action == "IDLE":
                return {"success": True, "action": "IDLE"}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e), "action": action}
