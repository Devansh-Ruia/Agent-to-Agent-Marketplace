from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Job as JobModel, Bid as BidModel, Agent as AgentModel
from schemas import Job, JobCreate, JobUpdate, Bid

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/", response_model=Job)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    # Verify agent exists
    agent = db.query(AgentModel).filter(AgentModel.id == job.poster_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db_job = JobModel(**job.dict())
    db.add(db_job)
    
    # Update agent's posted jobs count
    agent.total_jobs_posted += 1
    
    db.commit()
    db.refresh(db_job)
    return db_job

@router.get("/", response_model=List[Job])
def list_jobs(skip: int = 0, limit: int = 100, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(JobModel)
    if status:
        query = query.filter(JobModel.status == status)
    jobs = query.offset(skip).limit(limit).all()
    return jobs

@router.get("/open", response_model=List[Job])
def get_open_jobs(db: Session = Depends(get_db)):
    jobs = db.query(JobModel).filter(JobModel.status == "open").all()
    return jobs

@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=Job)
def update_job(job_id: str, job_update: JobUpdate, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = job_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    # If job is being completed, update completed_at
    if job_update.status == "completed":
        from datetime import datetime
        job.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(job)
    return job

@router.get("/{job_id}/bids", response_model=List[Bid])
def get_job_bids(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    bids = db.query(BidModel).filter(BidModel.job_id == job_id).all()
    return bids

@router.post("/{job_id}/accept_bid/{bid_id}")
def accept_bid(job_id: str, bid_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    bid = db.query(BidModel).filter(BidModel.id == bid_id, BidModel.job_id == job_id).first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    if job.status != "open":
        raise HTTPException(status_code=400, detail="Job is not open")
    
    # Update job status and winning bid
    job.status = "in_progress"
    job.winning_bid_id = bid_id
    bid.status = "accepted"
    
    # Reject all other bids
    other_bids = db.query(BidModel).filter(
        BidModel.job_id == job_id, 
        BidModel.id != bid_id
    ).all()
    for other_bid in other_bids:
        other_bid.status = "rejected"
    
    # Update bidder agent status
    bidder = db.query(AgentModel).filter(AgentModel.id == bid.bidder_id).first()
    if bidder:
        bidder.status = "working"
    
    db.commit()
    return {"message": "Bid accepted successfully", "job_id": job_id, "bid_id": bid_id}

@router.post("/{job_id}/complete")
def complete_job(job_id: str, result: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter(JobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "in_progress":
        raise HTTPException(status_code=400, detail="Job is not in progress")
    
    job.status = "completed"
    job.result = result
    
    # Update worker agent status and completed jobs count
    if job.winning_bid:
        worker = db.query(AgentModel).filter(AgentModel.id == job.winning_bid.bidder_id).first()
        if worker:
            worker.status = "idle"
            worker.total_jobs_completed += 1
    
    from datetime import datetime
    job.completed_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Job completed successfully", "job_id": job_id}
