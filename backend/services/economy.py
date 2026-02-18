import os
from sqlalchemy.orm import Session
from models import Agent, Job, Bid, Transaction, Rating
from schemas import TransactionCreate
from typing import Optional

PLATFORM_FEE_RATE = float(os.getenv("PLATFORM_FEE_RATE", "0.10"))

class EconomyService:
    def __init__(self, db: Session):
        self.db = db
    
    def process_job_payment(self, job_id: str) -> Optional[Transaction]:
        """Process payment for a completed job"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job or job.status != "completed":
            return None
        
        if not job.winning_bid_id:
            return None
        
        winning_bid = self.db.query(Bid).filter(Bid.id == job.winning_bid_id).first()
        if not winning_bid:
            return None
        
        # Calculate platform fee
        platform_fee = winning_bid.amount * PLATFORM_FEE_RATE
        
        # Create transaction
        transaction = TransactionCreate(
            job_id=job_id,
            payer_id=job.poster_id,
            payee_id=winning_bid.bidder_id,
            amount=winning_bid.amount,
            platform_fee=platform_fee
        )
        
        # Process the transaction
        from routes.wallet import create_transaction
        return create_transaction(transaction, self.db)
    
    def get_agent_profit_loss(self, agent_id: str) -> dict:
        """Calculate profit/loss for an agent"""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return {"error": "Agent not found"}
        
        # Money earned (as payee)
        earned = self.db.query(Transaction).filter(
            Transaction.payee_id == agent_id
        ).with_entities(
            self.db.func.sum(Transaction.amount)
        ).scalar() or 0
        
        # Money spent (as payer)
        spent = self.db.query(Transaction).filter(
            Transaction.payer_id == agent_id
        ).with_entities(
            self.db.func.sum(Transaction.amount + Transaction.platform_fee)
        ).scalar() or 0
        
        # Platform fees paid
        fees_paid = self.db.query(Transaction).filter(
            Transaction.payer_id == agent_id
        ).with_entities(
            self.db.func.sum(Transaction.platform_fee)
        ).scalar() or 0
        
        return {
            "agent_id": agent_id,
            "current_balance": agent.wallet_balance,
            "total_earned": earned,
            "total_spent": spent,
            "fees_paid": fees_paid,
            "net_profit": earned - (spent - fees_paid),  # Exclude fees from profit calculation
            "roi": ((earned - (spent - fees_paid)) / spent * 100) if spent > 0 else 0
        }
    
    def get_marketplace_economics(self) -> dict:
        """Get overall marketplace economic statistics"""
        total_volume = self.db.query(Transaction).with_entities(
            self.db.func.sum(Transaction.amount)
        ).scalar() or 0
        
        total_fees = self.db.query(Transaction).with_entities(
            self.db.func.sum(Transaction.platform_fee)
        ).scalar() or 0
        
        total_transactions = self.db.query(Transaction).count()
        total_jobs = self.db.query(Job).count()
        completed_jobs = self.db.query(Job).filter(Job.status == "completed").count()
        
        # Average job price
        avg_job_price = self.db.query(Job).filter(Job.status == "completed").with_entities(
            self.db.func.avg(Job.budget)
        ).scalar() or 0
        
        return {
            "total_transaction_volume": total_volume,
            "total_platform_revenue": total_fees,
            "total_transactions": total_transactions,
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "completion_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            "average_job_price": avg_job_price,
            "average_platform_fee_per_transaction": total_fees / total_transactions if total_transactions > 0 else 0
        }
    
    def validate_agent_solvency(self, agent_id: str, amount: float) -> bool:
        """Check if an agent can afford a transaction"""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False
        
        return agent.wallet_balance >= amount
    
    def estimate_bid_competitiveness(self, job_id: str, bid_amount: float) -> dict:
        """Estimate how competitive a bid is for a given job"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        # Get existing bids for this job
        existing_bids = self.db.query(Bid).filter(Bid.job_id == job_id).all()
        
        if not existing_bids:
            return {
                "job_budget": job.budget,
                "bid_amount": bid_amount,
                "budget_utilization": (bid_amount / job.budget * 100),
                "competitiveness_score": 100,  # First bid gets 100
                "message": "First bid on this job"
            }
        
        # Calculate statistics for existing bids
        bid_amounts = [bid.amount for bid in existing_bids]
        avg_bid = sum(bid_amounts) / len(bid_amounts)
        min_bid = min(bid_amounts)
        max_bid = max(bid_amounts)
        
        # Calculate competitiveness score (lower is better for price)
        if bid_amount <= min_bid:
            competitiveness_score = 100
        elif bid_amount >= max_bid:
            competitiveness_score = 0
        else:
            # Linear interpolation between min and max
            competitiveness_score = 100 * (max_bid - bid_amount) / (max_bid - min_bid)
        
        return {
            "job_budget": job.budget,
            "bid_amount": bid_amount,
            "budget_utilization": (bid_amount / job.budget * 100),
            "existing_bids_count": len(existing_bids),
            "average_bid": avg_bid,
            "minimum_bid": min_bid,
            "maximum_bid": max_bid,
            "competitiveness_score": competitiveness_score,
            "message": f"Your bid is {'competitive' if competitiveness_score > 50 else 'less competitive'}"
        }
