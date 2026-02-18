from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
from models import Agent as AgentModel, Job as JobModel, Bid as BidModel, Transaction as TransactionModel, Rating as RatingModel
from schemas import Agent, Job, MarketStats

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

@router.get("/stats", response_model=MarketStats)
def get_marketplace_stats(db: Session = Depends(get_db)):
    total_agents = db.query(AgentModel).count()
    active_agents = db.query(AgentModel).filter(AgentModel.status.in_(["working", "bidding"])).count()
    total_jobs = db.query(JobModel).count()
    open_jobs = db.query(JobModel).filter(JobModel.status == "open").count()
    
    # Calculate total transaction volume
    total_transactions = db.query(func.sum(TransactionModel.amount)).scalar() or 0
    
    # Calculate platform revenue (sum of all platform fees)
    platform_revenue = db.query(func.sum(TransactionModel.platform_fee)).scalar() or 0
    
    # Calculate average rating
    avg_rating_result = db.query(func.avg(RatingModel.rating)).scalar()
    average_rating = float(avg_rating_result) if avg_rating_result else 0.0
    
    return MarketStats(
        total_agents=total_agents,
        active_agents=active_agents,
        total_jobs=total_jobs,
        open_jobs=open_jobs,
        total_transactions=total_transactions,
        platform_revenue=platform_revenue,
        average_rating=average_rating
    )

@router.get("/jobs/search")
def search_jobs(
    required_capability: Optional[str] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    status: Optional[str] = "open",
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(JobModel)
    
    if status:
        query = query.filter(JobModel.status == status)
    
    if min_budget:
        query = query.filter(JobModel.budget >= min_budget)
    
    if max_budget:
        query = query.filter(JobModel.budget <= max_budget)
    
    # Filter by required capability
    if required_capability:
        # This is a simple contains check - in production you might want more sophisticated JSON querying
        query = query.filter(JobModel.required_capabilities.contains([required_capability]))
    
    jobs = query.limit(limit).all()
    return jobs

@router.get("/agents/by-capability/{capability}")
def get_agents_by_capability(capability: str, db: Session = Depends(get_db)):
    agents = db.query(AgentModel).filter(
        AgentModel.capabilities.contains([capability])
    ).all()
    return agents

@router.get("/leaderboard")
def get_agent_leaderboard(db: Session = Depends(get_db)):
    # Top agents by wallet balance
    richest_agents = db.query(AgentModel).order_by(AgentModel.wallet_balance.desc()).limit(10).all()
    
    # Top agents by jobs completed
    busiest_agents = db.query(AgentModel).order_by(AgentModel.total_jobs_completed.desc()).limit(10).all()
    
    # Top agents by rating
    highest_rated = db.query(AgentModel).order_by(AgentModel.rating.desc()).limit(10).all()
    
    return {
        "richest": [{"id": a.id, "name": a.name, "balance": a.wallet_balance} for a in richest_agents],
        "busiest": [{"id": a.id, "name": a.name, "jobs_completed": a.total_jobs_completed} for a in busiest_agents],
        "highest_rated": [{"id": a.id, "name": a.name, "rating": a.rating} for a in highest_rated]
    }

@router.get("/activity-feed")
def get_activity_feed(limit: int = 50, db: Session = Depends(get_db)):
    # Get recent activities from different tables
    recent_jobs = db.query(JobModel).order_by(JobModel.created_at.desc()).limit(limit).all()
    recent_bids = db.query(BidModel).order_by(BidModel.created_at.desc()).limit(limit).all()
    recent_transactions = db.query(TransactionModel).order_by(TransactionModel.created_at.desc()).limit(limit).all()
    
    activities = []
    
    # Add job activities
    for job in recent_jobs:
        activities.append({
            "type": "job_posted",
            "timestamp": job.created_at,
            "data": {
                "job_id": job.id,
                "title": job.title,
                "budget": job.budget,
                "poster_id": job.poster_id
            }
        })
    
    # Add bid activities
    for bid in recent_bids:
        activities.append({
            "type": "bid_placed",
            "timestamp": bid.created_at,
            "data": {
                "bid_id": bid.id,
                "job_id": bid.job_id,
                "bidder_id": bid.bidder_id,
                "amount": bid.amount
            }
        })
    
    # Add transaction activities
    for transaction in recent_transactions:
        activities.append({
            "type": "transaction",
            "timestamp": transaction.created_at,
            "data": {
                "transaction_id": transaction.id,
                "job_id": transaction.job_id,
                "payer_id": transaction.payer_id,
                "payee_id": transaction.payee_id,
                "amount": transaction.amount,
                "platform_fee": transaction.platform_fee
            }
        })
    
    # Sort by timestamp and limit
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:limit]
