import json
import logging
import httpx
from openai import AzureOpenAI
from config import Config

logger = logging.getLogger(__name__)

class AuthenticityScorer:
    """Scores blog based on authenticity and consistency using AI"""
    
    def __init__(self):
        """Initialize Azure OpenAI client"""
        http_client = httpx.Client()
        self.client = AzureOpenAI(
            api_key=Config.AZURE_OPENAI_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
            http_client=http_client
        )
        self.deployment = Config.AZURE_OPENAI_DEPLOYMENT
        self.max_score = 15
    
    def _create_system_prompt(self):
        """Create system prompt for authenticity analysis"""
        return """You are an expert content authenticity evaluator for travel blogs. Analyze the logical consistency and coherence of the story.

Evaluate the following aspects:
1. **Temporal Consistency**: Do events follow a logical timeline? Are there contradictions in time?
2. **Geographic Consistency**: Do locations make sense? Are distances and travel times realistic?
3. **Factual Consistency**: Are details consistent throughout? (e.g., hotel names, prices, dates)
4. **Narrative Coherence**: Does the story flow logically? Are there plot holes or contradictions?
5. **Realistic Details**: Are the experiences and descriptions believable?

Return a JSON response with:
- "consistency_level": "fully_consistent" | "minor_issues" | "major_inconsistencies"
- "issues_found": array of strings (list of any inconsistencies found)
- "temporal_consistency": true/false
- "geographic_consistency": true/false
- "factual_consistency": true/false
- "narrative_coherence": true/false
- "realistic_details": true/false
- "score_range": string indicating score range ("0-5", "8-12", or "15")

Return ONLY valid JSON, no additional text."""
    
    def _create_user_prompt(self, title, travel_experience):
        """Create user prompt with blog content"""
        return f"""Title: {title}

Travel Experience:
{travel_experience}

Analyze the authenticity and consistency of this travel blog story."""
    
    def score(self, title, travel_experience):
        """
        Calculate authenticity score for a blog
        
        Args:
            title: Blog title
            travel_experience: Travel experience text
            
        Returns:
            int: Score from 0 to 15
        """
        try:
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(title, travel_experience)
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            analysis = json.loads(content)
            
            consistency_level = analysis.get('consistency_level', 'minor_issues')
            
            # Map consistency level to score
            if consistency_level == 'fully_consistent':
                # Check if all aspects are consistent
                temporal = analysis.get('temporal_consistency', True)
                geographic = analysis.get('geographic_consistency', True)
                factual = analysis.get('factual_consistency', True)
                narrative = analysis.get('narrative_coherence', True)
                realistic = analysis.get('realistic_details', True)
                
                if temporal and geographic and factual and narrative and realistic:
                    return self.max_score
                else:
                    # Mostly consistent but some minor issues
                    return 12
                    
            elif consistency_level == 'minor_issues':
                # Return score in the 8-12 range
                issues = analysis.get('issues_found', [])
                if len(issues) == 0:
                    return 12
                elif len(issues) <= 2:
                    return 10
                else:
                    return 8
                    
            else:  # major_inconsistencies
                # Return score in the 0-5 range
                issues = analysis.get('issues_found', [])
                if len(issues) >= 3:
                    return 0
                elif len(issues) == 2:
                    return 2
                else:
                    return 5
                    
        except Exception as e:
            logger.error(f"Error calculating authenticity score: {e}")
            # Default to middle score if AI fails
            return 8
