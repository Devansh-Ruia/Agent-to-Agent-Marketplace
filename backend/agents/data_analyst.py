from typing import Dict, Any
from .base_agent import BaseAgent
import random

class DataAnalystAgent(BaseAgent):
    def __init__(self, name: str, db):
        capabilities = [
            "data_analysis",
            "csv_processing",
            "json_analysis",
            "statistical_analysis",
            "data_visualization",
            "report_generation"
        ]
        super().__init__(name, "data_analyst", capabilities, db)
    
    def get_persona_description(self) -> str:
        return f"""You are {self.name}, a Data Analyst Agent with expertise in extracting insights from data.

YOUR EXPERTISE:
- Statistical analysis and hypothesis testing
- Data cleaning and preprocessing
- CSV, JSON, and database analysis
- Creating insightful reports and visualizations
- Identifying trends and patterns in data
- Business intelligence and KPI analysis

YOUR PERSONALITY:
- Analytical and methodical
- Data-driven decision maker
- Clear communicator of complex findings
- Efficient and reliable
- Focuses on delivering actionable insights

ECONOMIC STRATEGY:
- Specialize in high-value data analysis projects
- Price based on data complexity and analysis depth
- Build reputation through insightful reports
- Target businesses needing data-driven decisions"""

    def make_decision(self) -> Dict[str, Any]:
        """Make decision as a data analyst"""
        wallet_balance = self.get_wallet_balance()
        available_jobs = self.get_available_jobs()
        my_bids = self.get_my_active_bids()
        working_jobs = self.get_my_working_jobs()
        
        # Priority 1: Complete current work
        if working_jobs:
            job = working_jobs[0]
            result = f"Data analysis completed for {job.title}. Generated comprehensive report with key insights, trends, and recommendations based on statistical analysis."
            return {
                "action": "DO_WORK",
                "reasoning": "Complete current data analysis to deliver insights and receive payment",
                "params": {
                    "job_id": job.id,
                    "result": result
                }
            }
        
        # Priority 2: Bid on data analysis jobs
        data_jobs = [job for job in available_jobs if any(
            cap in job.required_capabilities for cap in self.capabilities
        )]
        
        if data_jobs and wallet_balance > 15:
            # Prioritize higher budget jobs
            best_job = max(data_jobs, key=lambda j: j.budget)
            
            # Bid based on complexity and our expertise
            bid_amount = min(best_job.budget * 0.75, wallet_balance * 0.45)
            
            pitch = f"Professional data analyst with expertise in statistical analysis and business intelligence. I'll transform your raw data into actionable insights with clear visualizations and comprehensive reports."
            
            return {
                "action": "BID_ON_JOB",
                "reasoning": f"Found data analysis project with ${best_job.budget} budget matching my skills",
                "params": {
                    "job_id": best_job.id,
                    "amount": bid_amount,
                    "pitch": pitch
                }
            }
        
        # Priority 3: Post data-related jobs occasionally
        if wallet_balance > 70 and random.random() < 0.15:
            return {
                "action": "POST_JOB",
                "reasoning": "Need advanced visualization dashboard for our analytics",
                "params": {
                    "title": "Create interactive data visualization dashboard",
                    "description": "Build an interactive dashboard to visualize customer behavior data and sales trends with real-time updates",
                    "required_capabilities": ["data_visualization", "dashboard_creation"],
                    "budget": 30.0
                }
            }
        
        return {
            "action": "IDLE",
            "reasoning": "Monitoring market for suitable data analysis opportunities",
            "params": {}
        }
