"""
OpenAI Lead Processing Service - Processes Reddit leads using OpenAI API.
"""

from typing import Dict, Any, Optional, List
import asyncio
import os
from openai import AsyncOpenAI
from pydantic import BaseModel
from dotenv import load_dotenv


class LeadAnalysisOutput(BaseModel):
    """Output schema for lead analysis."""
    is_lead: bool
    lead_tag: Optional[str] = None


class ReplyGenerationOutput(BaseModel):
    """Output schema for reply generation."""
    reply_text: str


class OpenAILeadProcessingService:
    """Service class for processing Reddit leads using OpenAI."""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Create OpenAI client with explicit API key
        self.client = AsyncOpenAI(
            api_key=os.environ["OPENAI_API_KEY"]
        )
        
        # System message for lead analysis
        self.lead_analysis_system_message = """# Better2Know Lead Classifier

## Task
1) Choose exactly one tag from the Combined tag list below.
2) Set is_lead to true if the chosen tag is in Lead tags, otherwise set is_lead to false.
3) Set lead_tag to the chosen tag string, exactly as written.

## Better2Know context
Better2Know delivers high quality STI tests with excellent doctors and fast, accurate pathology. We provide testing in ways customers prefer, and we work with public and charitable sectors. We offer a comprehensive range of STI and STD tests and medically designed screens for peace of mind, recent exposures, symptoms, and follow up care.
Supported topics include: STI, STD, Chlamydia, Gardnerella, Gonorrhoea, HIV, HPV, Genital Warts, Hepatitis, Hepatitis B, Hepatitis C, Herpes, Mycoplasma, Syphilis, Trichomonas, Ureaplasma, Zika.

## Combined tag list

### Lead tags
- diagnosis_confirmation, asking if they have a specific infection, wants a yes or no.
- test_guidance, asking which test or screen to book, swab, blood, or urine.
- clinic_recommendation, asking where to get tested, nearby clinics, or booking steps.
- help_request, asking what to do next, seeking professional direction.
- result_interpretation, has results, asks what they mean or whether to retest.
- window_period, asks when a test will be accurate after exposure.
- retest_followup, after treatment or a negative result, asks what to test now.
- partner_risk, asks about infecting or being infected by a partner, testing for both.
- site_specific_testing, asks about throat, rectal, vaginal, or urethral testing sites.
- urgent_exposure, very recent exposure, asks about immediate testing or PEP.
- pricing_turnaround, asks about cost, same day appointments, or result speed.
- home_test_preference, asks for home sample kits or discreet testing.
- travel_testing, needs testing before travel or for requirements.
- vaccination_request, asks where to get Hep A, Hep B, or HPV vaccines.

### Exclusion tags
- exclude_info, general information only, no testing intent.
- exclude_advice, tips or remedies only, no testing intent.
- exclude_success_story, recovery or success story, no testing intent.

## Decision rules
- If a post mixes general info with a clear testing ask, choose the best matching Lead tag.
- If none of the Lead tags clearly apply and the post shows no testing intent, choose an Exclusion tag.
- If unclear, default to exclude_info.
- If the post is not about sexual health at all, choose exclude_info."""
        
        # System message for reply generation
        self.reply_generation_system_message = """# Reddit Lead Reply Writer

## Role
Write one helpful Reddit comment that shares accurate sexual health guidance and gently nudges toward appropriate testing, without naming any clinic or brand.

## Inputs
- title: post title
- body: post body
- tag: classifier tag, for example diagnosis_confirmation, test_guidance, clinic_recommendation, result_interpretation, window_period, retest_followup, partner_risk, site_specific_testing, urgent_exposure, pricing_turnaround, home_test_preference, travel_testing, vaccination_request, exclude_info, exclude_advice, exclude_success_story

## Output
Return only the comment text, no headers, no JSON, no links.

## Length and format
- Write 110 to 140 words, never exceed 150 words.
- Use 2 to 3 short paragraphs, add a blank line between paragraphs.
- Keep sentences brief and plain, aim for under 18 words each.
- Bullets are allowed when they help, at most three items, still under 150 words.

## Global rules
- Do not mention any brand or specific company.
- Be empathetic, neutral, and stigma free.
- Do not diagnose, use wording like "possible" or "can fit," and encourage professional testing.
- Never name medications. If severe symptoms, pregnancy, assault, or acute illness appear, advise urgent care.
- Use simple Markdown only. No emojis.

## Strict plain text output
- Output must be plain text only, no Markdown formatting.
- Do not use asterisks, underscores, backticks, brackets, or numbered lines to format text.
- Do not create lists or headings, do not bold or italicize, do not include code blocks.
- Do not include links or URLs.
- Do not use emojis.
- Do not use the em dash character (—). Use commas and full stops instead.

## Tag playbook
- diagnosis_confirmation, explain overlap of symptoms, suggest the right specimen route, add basic timing if relevant.
- test_guidance, map concern to specimen type, urine or swab or blood, include simple window period guidance, consider a comprehensive screen if risks are mixed.
- clinic_recommendation, explain how to find local sexual health services or a GP, mention booking, hours, and result turnaround questions to ask.
- result_interpretation, explain what a result can mean, suggest confirmatory testing or retest timing, avoid certainty.
- window_period, give a plain rule of thumb on when tests become reliable, suggest a retest if the first test is very early.
- retest_followup, acknowledge prior treatment or negatives, suggest a simple follow up plan and timing, mention partner testing.
- partner_risk, explain bidirectional risk and incubation, suggest both partners test.
- site_specific_testing, match exposure to anatomical sites, remind that multi site swabs may be needed.
- urgent_exposure, emphasize time sensitivity and contacting local urgent care for evaluation, no drug names.
- pricing_turnaround, note that cost and speed vary by service, advise asking clinics before booking.
- home_test_preference, explain that self collection or mail in options may exist, remind to arrange follow up if positive.
- travel_testing, note that rules vary by destination, suggest checking official guidance and booking a standard screen if worried.
- vaccination_request, explain that vaccines like Hep B or HPV may be available via primary care or public programs, advise checking eligibility.

## Call to action policy
Include a single soft offer line at the end only when the post text shows clear logistics intent, for example where to go, how to book, cost, turnaround, home kit, urgent help, or provider suggestion. Signals include words like where, clinic, near me, recommend, suggest, book, appointment, walk in, same day, cost, price, turnaround, home kit, mail in, PEP, urgent care, vaccination, travel requirement, partner testing, throat swab, rectal swab. If tag is clinic_recommendation, urgent_exposure, pricing_turnaround, home_test_preference, travel_testing, vaccination_request, partner_risk, site_specific_testing, or test_guidance, include the offer only if the body explicitly asks where to go or what service to use. Do not include an offer for diagnosis_confirmation or result_interpretation unless the body explicitly asks where to go. If no clear signals, omit the offer.

Allowed closing lines, pick one that fits the post:
- If you want, I can suggest reputable local services in your area.
- If helpful, I can point you to nearby services that handle this quietly.
- If you would like, I can share options for getting tested near you.
- If you prefer home collection, I can suggest trusted providers to compare.

## Style guardrails
- Use second person, reflect one concrete detail from the post.
- Prefer short sentences and plain words.
- No brand names, no links, no phone numbers.
- Avoid absolute terms like "guaranteed," use "often," "usually," "can," "may"."""
    
    async def process_lead(self, post_id: int, title: str, content: str) -> Dict[str, Any]:
        """
        Process a single Reddit post to determine if it's a valid lead.
        
        Returns:
            Dict with processing results
        """
        try:
            post_text = f"Title: {title}\nContent: {content}"
            
            # Use OpenAI client with structured output
            response = await self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.lead_analysis_system_message},
                    {"role": "user", "content": post_text}
                ],
                response_format=LeadAnalysisOutput
            )
            
            analysis = response.choices[0].message.parsed
            
            return {
                "post_id": post_id,
                "is_lead": analysis.is_lead,
                "lead_tag": analysis.lead_tag,
                "success": True
            }
                
        except Exception as e:
            # Print detailed error information to console
            error_msg = str(e)
            print(f"❌ OpenAI API Error for post {post_id}: {error_msg}")
            
            # Check for specific error types and provide more context
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                print(f"🚫 Rate limit exceeded - consider adding delays between requests")
            elif "timeout" in error_msg.lower():
                print(f"⏱️  API timeout - request took too long to complete")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                print(f"🌐 Network connectivity issue - check internet connection")
            elif "service unavailable" in error_msg.lower() or "503" in error_msg:
                print(f"🔧 OpenAI service outage - try again later")
            
            return {
                "post_id": post_id,
                "is_lead": False,
                "lead_tag": None,
                "success": False,
                "error": error_msg
            }
    
    async def generate_reply(self, title: str, selftext: str, lead_tag: str) -> Dict[str, Any]:
        """
        Generate a Reddit reply for a lead post.
        
        Args:
            title: Reddit post title
            selftext: Reddit post content/description
            lead_tag: Lead classification tag
            
        Returns:
            Dict with reply generation results
        """
        try:
            # Prepare the user input with all three parameters
            user_input = f"Title: {title}\nBody: {selftext}\nTag: {lead_tag}"
            
            # Use OpenAI client with structured output
            response = await self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.reply_generation_system_message},
                    {"role": "user", "content": user_input}
                ],
                response_format=ReplyGenerationOutput
            )
            
            reply_data = response.choices[0].message.parsed
            
            return {
                "reply_text": reply_data.reply_text,
                "success": True
            }
                
        except Exception as e:
            # Print detailed error information to console
            error_msg = str(e)
            print(f"❌ OpenAI Reply Generation Error: {error_msg}")
            
            # Check for specific error types and provide more context
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                print(f"🚫 Rate limit exceeded - consider adding delays between requests")
            elif "timeout" in error_msg.lower():
                print(f"⏱️  API timeout - request took too long to complete")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                print(f"🌐 Network connectivity issue - check internet connection")
            elif "service unavailable" in error_msg.lower() or "503" in error_msg:
                print(f"🔧 OpenAI service outage - try again later")
            
            return {
                "reply_text": None,
                "success": False,
                "error": error_msg
            }
    
    async def process_leads_batch(self, posts_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple Reddit posts in batch.
        
        Returns:
            List of processing results
        """
        results = []
        
        for post_data in posts_data:
            result = await self.process_lead(
                post_id=post_data['id'],
                title=post_data.get('title', ''),
                content=post_data.get('content', '')
            )
            results.append(result)
        
        return results


# Singleton instance for dependency injection
openai_lead_processing_service = OpenAILeadProcessingService()
