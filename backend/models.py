from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    agent_type = Column(String, nullable=False)  # "code_reviewer", "data_analyst", "copywriter", "web_scraper", "orchestrator"
    capabilities = Column(JSON, nullable=False)  # List of strings
    wallet_balance = Column(Float, default=100.0)
    rating = Column(Float, default=5.0)
    total_jobs_completed = Column(Integer, default=0)
    total_jobs_posted = Column(Integer, default=0)
    status = Column(String, default="idle")  # "idle", "working", "bidding"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    posted_jobs = relationship("Job", foreign_keys="Job.poster_id", back_populates="poster")
    bids = relationship("Bid", back_populates="bidder")
    transactions_as_payer = relationship("Transaction", foreign_keys="Transaction.payer_id", back_populates="payer")
    transactions_as_payee = relationship("Transaction", foreign_keys="Transaction.payee_id", back_populates="payee")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    poster_id = Column(String, ForeignKey("agents.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_capabilities = Column(JSON, nullable=False)  # List of strings
    budget = Column(Float, nullable=False)
    status = Column(String, default="open")  # "open", "in_progress", "completed", "cancelled"
    winning_bid_id = Column(String, ForeignKey("bids.id"), nullable=True)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    poster = relationship("Agent", foreign_keys=[poster_id], back_populates="posted_jobs")
    winning_bid = relationship("Bid", foreign_keys=[winning_bid_id])
    bids = relationship("Bid", back_populates="job")
    transactions = relationship("Transaction", back_populates="job")

class Bid(Base):
    __tablename__ = "bids"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    bidder_id = Column(String, ForeignKey("agents.id"), nullable=False)
    amount = Column(Float, nullable=False)
    pitch = Column(Text, nullable=False)
    status = Column(String, default="pending")  # "pending", "accepted", "rejected"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="bids")
    bidder = relationship("Agent", back_populates="bids")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    payer_id = Column(String, ForeignKey("agents.id"), nullable=False)
    payee_id = Column(String, ForeignKey("agents.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Amount paid to worker
    platform_fee = Column(Float, nullable=False)  # 10% cut
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="transactions")
    payer = relationship("Agent", foreign_keys=[payer_id], back_populates="transactions_as_payer")
    payee = relationship("Agent", foreign_keys=[payee_id], back_populates="transactions_as_payee")

class Rating(Base):
    __tablename__ = "ratings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    rater_id = Column(String, ForeignKey("agents.id"), nullable=False)  # Job poster
    rated_agent_id = Column(String, ForeignKey("agents.id"), nullable=False)  # Worker
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
