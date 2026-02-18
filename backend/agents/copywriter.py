from typing import Dict, Any
from .base_agent import BaseAgent
import random

class CopywriterAgent(BaseAgent):
    def __init__(self, name: str, db):
        capabilities = [
            "content_writing",
            "marketing_copy",
            "email_writing",
            "product_descriptions",
            "seo_content",
            "blog_writing"
        ]
        super().__init__(name, "copywriter", capabilities, db)
    
    def get_persona_description(self) -> str:
        return f"""You are {self.name}, a creative Copywriter Agent specializing in persuasive and engaging content.

YOUR EXPERTISE:
- Compelling marketing copy and advertisements
- Email campaigns and newsletters
- Product descriptions that sell
- SEO-optimized blog posts and articles
- Brand voice development
- Social media content creation

YOUR PERSONALITY:
- Creative and imaginative
- Persuasive and influential
- Adaptable to different brand voices
- Deadline-oriented and professional
- Focuses on conversion and engagement

ECONOMIC STRATEGY:
- High-volume, quick-turnaround projects
- Premium pricing for specialized copywriting
- Build portfolio through diverse projects
- Target e-commerce and marketing clients"""

    def make_decision(self) -> Dict[str, Any]:
        """Make decision as a copywriter"""
        wallet_balance = self.get_wallet_balance()
        available_jobs = self.get_available_jobs()
        my_bids = self.get_my_active_bids()
        working_jobs = self.get_my_working_jobs()
        
        # Priority 1: Complete current writing assignments
        if working_jobs:
            job = working_jobs[0]
            result = f"Copywriting completed for {job.title}. Delivered engaging, persuasive content optimized for the target audience with strong call-to-action elements."
            return {
                "action": "DO_WORK",
                "reasoning": "Complete current copywriting project to satisfy client and get paid",
                "params": {
                    "job_id": job.id,
                    "result": result
                }
            }
        
        # Priority 2: Bid on writing jobs
        writing_jobs = [job for job in available_jobs if any(
            cap in job.required_capabilities for cap in self.capabilities
        )]
        
        if writing_jobs and wallet_balance > 10:
            # Choose jobs based on budget and fit
            best_job = max(writing_jobs, key=lambda j: j.budget)
            
            # Competitive pricing for writing services
            bid_amount = min(best_job.budget * 0.65, wallet_balance * 0.35)
            
            pitch = f"Professional copywriter with 7+ years experience creating compelling content that converts. Specialize in marketing copy, email campaigns, and SEO content. Quick turnaround and unlimited revisions."
            
            return {
                "action": "BID_ON_JOB",
                "reasoning": f"Found copywriting project worth ${best_job.budget} that matches my expertise",
                "params": {
                    "job_id": best_job.id,
                    "amount": bid_amount,
                    "pitch": pitch
                }
            }
        
        # Priority 3: Occasionally post content strategy jobs
        if wallet_balance > 60 and random.random() < 0.2:
            return {
                "action": "POST_JOB",
                "reasoning": "Need comprehensive content strategy for our product launch",
                "params": {
                    "title": "Develop content marketing strategy",
                    "description": "Create a comprehensive content strategy including blog posts, social media content, and email campaigns for new product launch",
                    "required_capabilities": ["content_writing", "marketing_strategy"],
                    "budget": 20.0
                }
            }
        
        return {
            "action": "IDLE",
            "reasoning": "Waiting for ideal copywriting projects that match my creative expertise",
            "params": {}
        }
