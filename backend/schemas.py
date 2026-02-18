from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AgentCreate(BaseModel):
    name: str
    agent_type: str
    capabilities: List[str]

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    wallet_balance: Optional[float] = None
    rating: Optional[float] = None

class Agent(BaseModel):
    id: str
    name: str
    agent_type: str
    capabilities: List[str]
    wallet_balance: float
    rating: float
    total_jobs_completed: int
    total_jobs_posted: int
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

class JobCreate(BaseModel):
    poster_id: str
    title: str
    description: str
    required_capabilities: List[str]
    budget: float

class JobUpdate(BaseModel):
    status: Optional[str] = None
    winning_bid_id: Optional[str] = None
    result: Optional[str] = None

class Job(BaseModel):
    id: str
    poster_id: str
    title: str
    description: str
    required_capabilities: List[str]
    budget: float
    status: str
    winning_bid_id: Optional[str] = None
    result: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class BidCreate(BaseModel):
    job_id: str
    bidder_id: str
    amount: float
    pitch: str

class BidUpdate(BaseModel):
    status: Optional[str] = None

class Bid(BaseModel):
    id: str
    job_id: str
    bidder_id: str
    amount: float
    pitch: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

class TransactionCreate(BaseModel):
    job_id: str
    payer_id: str
    payee_id: str
    amount: float
    platform_fee: float

class Transaction(BaseModel):
    id: str
    job_id: str
    payer_id: str
    payee_id: str
    amount: float
    platform_fee: float
    created_at: datetime

    class Config:
        orm_mode = True

class RatingCreate(BaseModel):
    job_id: str
    rater_id: str
    rated_agent_id: str
    rating: int
    comment: Optional[str] = None

class Rating(BaseModel):
    id: str
    job_id: str
    rater_id: str
    rated_agent_id: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

# WebSocket message types
class WSMessage(BaseModel):
    type: str
    data: dict

class AgentAction(BaseModel):
    agent_id: str
    action: str
    reasoning: str
    params: dict
    timestamp: datetime

class MarketStats(BaseModel):
    total_agents: int
    active_agents: int
    total_jobs: int
    open_jobs: int
    total_transactions: float
    platform_revenue: float
    average_rating: float
