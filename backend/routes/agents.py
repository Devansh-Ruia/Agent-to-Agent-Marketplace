from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Agent as AgentModel
from schemas import Agent, AgentCreate, AgentUpdate

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/", response_model=Agent)
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    db_agent = AgentModel(**agent.dict())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.get("/", response_model=List[Agent])
def list_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    agents = db.query(AgentModel).offset(skip).limit(limit).all()
    return agents

@router.get("/{agent_id}", response_model=Agent)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=Agent)
def update_agent(agent_id: str, agent_update: AgentUpdate, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = agent_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    db.commit()
    db.refresh(agent)
    return agent

@router.delete("/{agent_id}")
def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted successfully"}

@router.get("/{agent_id}/wallet")
def get_agent_wallet(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"agent_id": agent_id, "wallet_balance": agent.wallet_balance}

@router.post("/{agent_id}/deposit")
def deposit_to_wallet(agent_id: str, amount: float, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    agent.wallet_balance += amount
    db.commit()
    return {"agent_id": agent_id, "new_balance": agent.wallet_balance, "deposited": amount}
