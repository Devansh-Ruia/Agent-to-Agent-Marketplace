from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Bid as BidModel, Job as JobModel, Agent as AgentModel
from schemas import Bid, BidCreate, BidUpdate

router = APIRouter(prefix="/bids", tags=["bids"])

@router.post("/", response_model=Bid)
def create_bid(bid: BidCreate, db: Session = Depends(get_db)):
    # Verify job exists and is open
    job = db.query(JobModel).filter(JobModel.id == bid.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "open":
        raise HTTPException(status_code=400, detail="Job is not open for bidding")
    
    # Verify agent exists
    agent = db.query(AgentModel).filter(AgentModel.id == bid.bidder_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if agent already bid on this job
    existing_bid = db.query(BidModel).filter(
        BidModel.job_id == bid.job_id,
        BidModel.bidder_id == bid.bidder_id
    ).first()
    if existing_bid:
        raise HTTPException(status_code=400, detail="Agent has already bid on this job")
    
    # Check if agent has sufficient funds (bid should not exceed 50% of wallet)
    if bid.amount > agent.wallet_balance * 0.5:
        raise HTTPException(status_code=400, detail="Bid amount exceeds 50% of wallet balance")
    
    db_bid = BidModel(**bid.dict())
    db.add(db_bid)
    
    # Update agent status to bidding
    agent.status = "bidding"
    
    db.commit()
    db.refresh(db_bid)
    return db_bid

@router.get("/", response_model=List[Bid])
def list_bids(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    bids = db.query(BidModel).offset(skip).limit(limit).all()
    return bids

@router.get("/{bid_id}", response_model=Bid)
def get_bid(bid_id: str, db: Session = Depends(get_db)):
    bid = db.query(BidModel).filter(BidModel.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    return bid

@router.put("/{bid_id}", response_model=Bid)
def update_bid(bid_id: str, bid_update: BidUpdate, db: Session = Depends(get_db)):
    bid = db.query(BidModel).filter(BidModel.id == bid_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    update_data = bid_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bid, field, value)
    
    db.commit()
    db.refresh(bid)
    return bid

@router.get("/agent/{agent_id}", response_model=List[Bid])
def get_agent_bids(agent_id: str, db: Session = Depends(get_db)):
    bids = db.query(BidModel).filter(BidModel.bidder_id == agent_id).all()
    return bids

@router.get("/job/{job_id}", response_model=List[Bid])
def get_job_bids(job_id: str, db: Session = Depends(get_db)):
    bids = db.query(BidModel).filter(BidModel.job_id == job_id).all()
    return bids
