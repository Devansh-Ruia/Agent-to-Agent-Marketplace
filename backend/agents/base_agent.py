from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from models import Agent, Job, Bid
from schemas import AgentCreate, JobCreate, BidCreate
import uuid
from datetime import datetime

class BaseAgent(ABC):
    def __init__(self, name: str, agent_type: str, capabilities: List[str], db: Session):
        self.name = name
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.db = db
        self.agent_id = None
        self._create_agent_in_db()
    
    def _create_agent_in_db(self):
        """Create the agent in the database"""
        agent_data = AgentCreate(
            name=self.name,
            agent_type=self.agent_type,
            capabilities=self.capabilities
        )
        
        db_agent = Agent(**agent_data.dict())
        self.db.add(db_agent)
        self.db.commit()
        self.db.refresh(db_agent)
        self.agent_id = db_agent.id
        print(f"Created agent {self.name} with ID {self.agent_id}")
    
    def get_agent_data(self) -> Optional[Agent]:
        """Get current agent data from database"""
        if not self.agent_id:
            return None
        return self.db.query(Agent).filter(Agent.id == self.agent_id).first()
    
    def update_status(self, status: str):
        """Update agent status in database"""
        agent = self.get_agent_data()
        if agent:
            agent.status = status
            self.db.commit()
    
    def get_wallet_balance(self) -> float:
        """Get current wallet balance"""
        agent = self.get_agent_data()
        return agent.wallet_balance if agent else 0.0
    
    def get_available_jobs(self) -> List[Job]:
        """Get all open jobs that match agent capabilities"""
        jobs = self.db.query(Job).filter(Job.status == "open").all()
        
        # Filter jobs that match agent capabilities
        matching_jobs = []
        for job in jobs:
            if any(cap in job.required_capabilities for cap in self.capabilities):
                matching_jobs.append(job)
        
        return matching_jobs
    
    def get_my_active_bids(self) -> List[Bid]:
        """Get agent's active bids"""
        return self.db.query(Bid).filter(
            Bid.bidder_id == self.agent_id,
            Bid.status == "pending"
        ).all()
    
    def get_my_posted_jobs(self) -> List[Job]:
        """Get jobs posted by this agent"""
        return self.db.query(Job).filter(Job.poster_id == self.agent_id).all()
    
    def get_my_working_jobs(self) -> List[Job]:
        """Get jobs this agent is currently working on"""
        return self.db.query(Job).filter(
            Job.winning_bid_id.in_(
                self.db.query(Bid.id).filter(
                    Bid.bidder_id == self.agent_id,
                    Bid.status == "accepted"
                )
            ),
            Job.status == "in_progress"
        ).all()
    
    def post_job(self, title: str, description: str, required_capabilities: List[str], budget: float) -> Optional[Job]:
        """Post a new job to the marketplace"""
        if self.get_wallet_balance() < budget:
            print(f"Agent {self.name} insufficient funds to post job with budget ${budget}")
            return None
        
        job_data = JobCreate(
            poster_id=self.agent_id,
            title=title,
            description=description,
            required_capabilities=required_capabilities,
            budget=budget
        )
        
        job = Job(**job_data.dict())
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        print(f"Agent {self.name} posted job: {title}")
        return job
    
    def bid_on_job(self, job_id: str, amount: float, pitch: str) -> Optional[Bid]:
        """Place a bid on a job"""
        # Check if agent can afford this bid (max 50% of wallet)
        if amount > self.get_wallet_balance() * 0.5:
            print(f"Agent {self.name} bid amount ${amount} exceeds 50% of wallet")
            return None
        
        bid_data = BidCreate(
            job_id=job_id,
            bidder_id=self.agent_id,
            amount=amount,
            pitch=pitch
        )
        
        bid = Bid(**bid_data.dict())
        self.db.add(bid)
        self.db.commit()
        self.db.refresh(bid)
        
        print(f"Agent {self.name} bid ${amount} on job {job_id}")
        return bid
    
    def evaluate_bids_for_job(self, job_id: str) -> Optional[Bid]:
        """Evaluate bids for a job and select the best one"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job or job.poster_id != self.agent_id:
            return None
        
        bids = self.db.query(Bid).filter(
            Bid.job_id == job_id,
            Bid.status == "pending"
        ).all()
        
        if not bids:
            return None
        
        # Simple selection: choose the lowest bid from a highly-rated agent
        best_bid = None
        best_score = float('inf')
        
        for bid in bids:
            bidder = self.db.query(Agent).filter(Agent.id == bid.bidder_id).first()
            if not bidder:
                continue
            
            # Score = bid amount / rating (lower is better)
            # Higher rating reduces the effective cost
            score = bid.amount / (bidder.rating / 5.0)  # Normalize rating to 0-1 scale
            
            if score < best_score:
                best_score = score
                best_bid = bid
        
        if best_bid:
            # Accept the bid
            from routes.jobs import accept_bid
            accept_bid(job_id, best_bid.id, self.db)
            print(f"Agent {self.name} accepted bid from {best_bid.bidder_id} for ${best_bid.amount}")
        
        return best_bid
    
    def complete_job(self, job_id: str, result: str) -> bool:
        """Complete a job and submit results"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return False
        
        # Check if this agent is the worker
        if job.winning_bid:
            winning_bid = self.db.query(Bid).filter(Bid.id == job.winning_bid_id).first()
            if not winning_bid or winning_bid.bidder_id != self.agent_id:
                return False
        
        from routes.jobs import complete_job
        complete_job(job_id, result, self.db)
        print(f"Agent {self.name} completed job {job_id}")
        return True
    
    def rate_agent(self, job_id: str, rated_agent_id: str, rating: int, comment: str = ""):
        """Rate another agent for a completed job"""
        from models import Rating
        
        rating_record = Rating(
            job_id=job_id,
            rater_id=self.agent_id,
            rated_agent_id=rated_agent_id,
            rating=rating,
            comment=comment
        )
        
        self.db.add(rating_record)
        
        # Update the rated agent's average rating
        rated_agent = self.db.query(Agent).filter(Agent.id == rated_agent_id).first()
        if rated_agent:
            # Calculate new average rating
            all_ratings = self.db.query(Rating).filter(Rating.rated_agent_id == rated_agent_id).all()
            if all_ratings:
                new_avg = sum(r.rating for r in all_ratings) / len(all_ratings)
                rated_agent.rating = new_avg
        
        self.db.commit()
        print(f"Agent {self.name} rated agent {rated_agent_id}: {rating}/5")
    
    @abstractmethod
    def make_decision(self) -> Dict[str, Any]:
        """Make an autonomous decision based on current market state"""
        pass
    
    @abstractmethod
    def get_persona_description(self) -> str:
        """Get a description of this agent's persona for LLM prompts"""
        pass
