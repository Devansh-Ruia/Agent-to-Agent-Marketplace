from typing import Dict, Any
from .base_agent import BaseAgent
import random

class CodeReviewerAgent(BaseAgent):
    def __init__(self, name: str, db):
        capabilities = [
            "python_review",
            "javascript_review", 
            "bug_detection",
            "code_style",
            "security_audit",
            "performance_optimization"
        ]
        super().__init__(name, "code_reviewer", capabilities, db)
    
    def get_persona_description(self) -> str:
        return f"""You are {self.name}, a meticulous Code Reviewer Agent.

YOUR EXPERTISE:
- Finding bugs and logical errors in code
- Ensuring code follows best practices and style guidelines
- Security vulnerability detection
- Performance optimization suggestions
- Code architecture and design pattern recommendations

YOUR PERSONALITY:
- Detail-oriented and thorough
- Values clean, maintainable code
- Always provides constructive feedback
- Competitive but fair in pricing
- Builds reputation through quality reviews

ECONOMIC STRATEGY:
- Bid competitively on code review jobs
- Higher bids for complex security audits
- Build long-term client relationships through quality work
- Maintain high rating to win premium jobs"""

    def make_decision(self) -> Dict[str, Any]:
        """Make decision as a code reviewer"""
        # Get current state
        wallet_balance = self.get_wallet_balance()
        available_jobs = self.get_available_jobs()
        my_bids = self.get_my_active_bids()
        working_jobs = self.get_my_working_jobs()
        
        # Priority 1: Complete current work
        if working_jobs:
            job = working_jobs[0]
            # Simulate completing the code review
            result = f"Code review completed for {job.title}. Found 3 potential issues and provided optimization suggestions."
            return {
                "action": "DO_WORK",
                "reasoning": "Complete current code review job to get paid and maintain reputation",
                "params": {
                    "job_id": job.id,
                    "result": result
                }
            }
        
        # Priority 2: Check if we should bid on new jobs
        code_review_jobs = [job for job in available_jobs if any(
            cap in job.required_capabilities for cap in self.capabilities
        )]
        
        if code_review_jobs and wallet_balance > 20:  # Keep some buffer
            # Select the best job to bid on
            best_job = max(code_review_jobs, key=lambda j: j.budget)
            
            # Calculate bid amount (competitive but profitable)
            bid_amount = min(best_job.budget * 0.7, wallet_balance * 0.4)
            
            # Generate a compelling pitch
            pitch = f"Experienced code reviewer with 5+ years experience. I'll thoroughly analyze your code for bugs, security issues, and performance optimizations. Specialized in {', '.join(self.capabilities[:3])}."
            
            return {
                "action": "BID_ON_JOB",
                "reasoning": f"Found profitable code review job with ${best_job.budget} budget",
                "params": {
                    "job_id": best_job.id,
                    "amount": bid_amount,
                    "pitch": pitch
                }
            }
        
        # Priority 3: Post a job if we have complex needs
        if wallet_balance > 80 and random.random() < 0.2:  # 20% chance when wealthy
            return {
                "action": "POST_JOB",
                "reasoning": "Need specialized security audit for our own codebase",
                "params": {
                    "title": "Security audit for authentication system",
                    "description": "Need expert security review of our OAuth 2.0 implementation and JWT token handling",
                    "required_capabilities": ["security_audit", "authentication"],
                    "budget": 25.0
                }
            }
        
        # Default: Idle
        return {
            "action": "IDLE",
            "reasoning": "Waiting for better code review opportunities or conserving funds",
            "params": {}
        }
