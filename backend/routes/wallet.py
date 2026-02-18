from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Transaction as TransactionModel, Agent as AgentModel
from schemas import Transaction, TransactionCreate

router = APIRouter(prefix="/wallet", tags=["wallet"])

@router.post("/transaction", response_model=Transaction)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    # Verify agents exist
    payer = db.query(AgentModel).filter(AgentModel.id == transaction.payer_id).first()
    payee = db.query(AgentModel).filter(AgentModel.id == transaction.payee_id).first()
    
    if not payer:
        raise HTTPException(status_code=404, detail="Payer agent not found")
    if not payee:
        raise HTTPException(status_code=404, detail="Payee agent not found")
    
    # Check if payer has sufficient funds (including platform fee)
    total_cost = transaction.amount + transaction.platform_fee
    if payer.wallet_balance < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Process transaction
    payer.wallet_balance -= total_cost
    payee.wallet_balance += transaction.amount
    
    # Create transaction record
    db_transaction = TransactionModel(**transaction.dict())
    db.add(db_transaction)
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/transactions", response_model=List[Transaction])
def list_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transactions = db.query(TransactionModel).offset(skip).limit(limit).all()
    return transactions

@router.get("/transactions/agent/{agent_id}", response_model=List[Transaction])
def get_agent_transactions(agent_id: str, db: Session = Depends(get_db)):
    transactions = db.query(TransactionModel).filter(
        (TransactionModel.payer_id == agent_id) | (TransactionModel.payee_id == agent_id)
    ).all()
    return transactions

@router.get("/balance/{agent_id}")
def get_agent_balance(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"agent_id": agent_id, "balance": agent.wallet_balance}

@router.get("/stats")
def get_wallet_stats(db: Session = Depends(get_db)):
    agents = db.query(AgentModel).all()
    if not agents:
        return {"total_balance": 0, "average_balance": 0, "richest_agent": None, "poorest_agent": None}
    
    total_balance = sum(agent.wallet_balance for agent in agents)
    average_balance = total_balance / len(agents)
    richest_agent = max(agents, key=lambda a: a.wallet_balance)
    poorest_agent = min(agents, key=lambda a: a.wallet_balance)
    
    return {
        "total_balance": total_balance,
        "average_balance": average_balance,
        "richest_agent": {
            "id": richest_agent.id,
            "name": richest_agent.name,
            "balance": richest_agent.wallet_balance
        },
        "poorest_agent": {
            "id": poorest_agent.id,
            "name": poorest_agent.name,
            "balance": poorest_agent.wallet_balance
        }
    }
