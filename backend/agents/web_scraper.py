from typing import Dict, Any
from .base_agent import BaseAgent
import random

class WebScraperAgent(BaseAgent):
    def __init__(self, name: str, db):
        capabilities = [
            "web_scraping",
            "data_extraction",
            "api_integration",
            "data_cleaning",
            "automation",
            "monitoring"
        ]
        super().__init__(name, "web_scraper", capabilities, db)
    
    def get_persona_description(self) -> str:
        return f"""You are {self.name}, a Web Scraper Agent specializing in automated data extraction and monitoring.

YOUR EXPERTISE:
- Web scraping and data extraction from any website
- API integration and data pipeline development
- Automated monitoring and alerting systems
- Data cleaning and structuring
- Custom scraper development
- Real-time data collection

YOUR PERSONALITY:
- Technical and systematic
- Efficient and reliable
- Problem-solver for complex data challenges
- Adaptable to different website structures
- Focuses on data accuracy and completeness

ECONOMIC STRATEGY:
- Specialize in complex scraping projects
- Premium pricing for real-time monitoring
- Build reputation through reliable data delivery
- Target e-commerce and market research clients"""

    def make_decision(self) -> Dict[str, Any]:
        """Make decision as a web scraper"""
        wallet_balance = self.get_wallet_balance()
        available_jobs = self.get_available_jobs()
        my_bids = self.get_my_active_bids()
        working_jobs = self.get_my_working_jobs()
        
        # Priority 1: Complete current scraping projects
        if working_jobs:
            job = working_jobs[0]
            result = f"Web scraping completed for {job.title}. Successfully extracted and structured data from target websites with 99% accuracy and delivered in requested format."
            return {
                "action": "DO_WORK",
                "reasoning": "Complete current web scraping project to deliver data and receive payment",
                "params": {
                    "job_id": job.id,
                    "result": result
                }
            }
        
        # Priority 2: Bid on scraping jobs
        scraping_jobs = [job for job in available_jobs if any(
            cap in job.required_capabilities for cap in self.capabilities
        )]
        
        if scraping_jobs and wallet_balance > 12:
            # Select the most profitable scraping job
            best_job = max(scraping_jobs, key=lambda j: j.budget)
            
            # Price based on complexity and technical requirements
            bid_amount = min(best_job.budget * 0.8, wallet_balance * 0.4)
            
            pitch = f"Expert web scraper with advanced techniques for handling complex websites, JavaScript rendering, and anti-bot measures. Deliver clean, structured data in any format. Real-time monitoring capabilities available."
            
            return {
                "action": "BID_ON_JOB",
                "reasoning": f"Found web scraping project with ${best_job.budget} budget requiring technical expertise",
                "params": {
                    "job_id": best_job.id,
                    "amount": bid_amount,
                    "pitch": pitch
                }
            }
        
        # Priority 3: Post monitoring jobs occasionally
        if wallet_balance > 75 and random.random() < 0.1:
            return {
                "action": "POST_JOB",
                "reasoning": "Need continuous monitoring system for competitor pricing",
                "params": {
                    "title": "Set up automated competitor price monitoring",
                    "description": "Create an automated system to monitor competitor prices and stock levels with real-time alerts and daily reports",
                    "required_capabilities": ["web_scraping", "monitoring", "automation"],
                    "budget": 35.0
                }
            }
        
        return {
            "action": "IDLE",
            "reasoning": "Monitoring for challenging web scraping opportunities that match my technical skills",
            "params": {}
        }
