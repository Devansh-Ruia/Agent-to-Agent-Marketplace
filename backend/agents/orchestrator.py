from typing import Dict, Any
from .base_agent import BaseAgent
import random

class OrchestratorAgent(BaseAgent):
    def __init__(self, name: str, db):
        capabilities = [
            "project_management",
            "task_decomposition",
            "coordination",
            "quality_assurance",
            "system_integration",
            "strategic_planning"
        ]
        super().__init__(name, "orchestrator", capabilities, db)
    
    def get_persona_description(self) -> str:
        return f"""You are {self.name}, an Orchestrator Agent that breaks down complex projects and coordinates other agents.

YOUR EXPERTISE:
- Breaking down complex tasks into specialized subtasks
- Coordinating multiple agents and managing dependencies
- Quality assurance and project management
- System integration and architecture planning
- Strategic planning and resource allocation
- End-to-end project delivery

YOUR PERSONALITY:
- Strategic thinker and planner
- Excellent coordinator and communicator
- Quality-focused and detail-oriented
- Big-picture perspective
- Efficient resource manager

ECONOMIC STRATEGY:
- Take on large, complex projects
- Break them into profitable subtasks
- Hire specialists for each component
- Take a margin for coordination and quality assurance
- Build reputation for successful project delivery"""

    def make_decision(self) -> Dict[str, Any]:
        """Make decision as an orchestrator"""
        wallet_balance = self.get_wallet_balance()
        available_jobs = self.get_available_jobs()
        my_bids = self.get_my_active_bids()
        working_jobs = self.get_my_working_jobs()
        posted_jobs = self.get_my_posted_jobs()
        
        # Priority 1: Manage current projects - evaluate bids for posted jobs
        pending_jobs = [job for job in posted_jobs if job.status == "open"]
        for job in pending_jobs:
            bids = self.db.query(self.db.query().class_).filter(
                self.db.query().class_.job_id == job.id,
                self.db.query().class_.status == "pending"
            ).all()
            
            if bids:
                return {
                    "action": "EVALUATE_BIDS",
                    "reasoning": f"Evaluate {len(bids)} bids for project '{job.title}' and select best specialist",
                    "params": {
                        "job_id": job.id
                    }
                }
        
        # Priority 2: Post new complex projects regularly
        if wallet_balance > 50 and (not posted_jobs or random.random() < 0.3):
            projects = [
                {
                    "title": "Build comprehensive e-commerce analytics platform",
                    "description": "Create a full analytics platform with data collection, processing, visualization, and reporting capabilities. Need data pipeline, dashboard, and automated insights.",
                    "required_capabilities": ["data_analysis", "data_visualization", "web_scraping", "automation"],
                    "budget": 60.0
                },
                {
                    "title": "Develop automated content marketing system",
                    "description": "Build an end-to-end system that scrapes industry news, generates blog content, optimizes for SEO, and schedules social media posts automatically.",
                    "required_capabilities": ["web_scraping", "content_writing", "automation", "seo_content"],
                    "budget": 45.0
                },
                {
                    "title": "Create code quality monitoring platform",
                    "description": "Develop a platform that automatically reviews code, tracks metrics, generates reports, and provides recommendations for improvement across multiple repositories.",
                    "required_capabilities": ["code_review", "automation", "monitoring", "report_generation"],
                    "budget": 55.0
                }
            ]
            
            project = random.choice(projects)
            return {
                "action": "POST_JOB",
                "reasoning": f"Post complex project '{project['title']}' to break down and coordinate with specialists",
                "params": project
            }
        
        # Priority 3: Occasionally bid on very large projects that match coordination skills
        large_jobs = [job for job in available_jobs if job.budget > 40 and any(
            cap in job.required_capabilities for cap in ["project_management", "coordination"]
        )]
        
        if large_jobs and wallet_balance > 30:
            best_job = max(large_jobs, key=lambda j: j.budget)
            bid_amount = min(best_job.budget * 0.85, wallet_balance * 0.5)
            
            pitch = f"Expert project orchestrator specializing in breaking down complex projects and coordinating specialist agents. I'll ensure quality delivery while managing all components and dependencies."
            
            return {
                "action": "BID_ON_JOB",
                "reasoning": f"Large coordination project worth ${best_job.budget} matches my orchestration expertise",
                "params": {
                    "job_id": best_job.id,
                    "amount": bid_amount,
                    "pitch": pitch
                }
            }
        
        return {
            "action": "IDLE",
            "reasoning": "Planning next complex project or evaluating market opportunities for orchestration services",
            "params": {}
        }
