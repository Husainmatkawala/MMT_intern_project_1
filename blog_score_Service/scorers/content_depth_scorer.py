import json
import logging
import httpx
from openai import AzureOpenAI
from config import Config

logger = logging.getLogger(__name__)

class ContentDepthScorer:
    """Scores blog based on content depth and completeness using AI"""
    
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
        self.max_score = 20
    
    def _count_words(self, text):
        """Count words in text"""
        if not text:
            return 0
        return len(text.split())
    
    def _create_system_prompt(self):
        """Create system prompt for content depth analysis"""
        return """You are an expert content quality evaluator for travel blogs. Analyze the content structure and completeness.

Evaluate the following aspects:
1. **Structure**: Does the content have a clear beginning, middle, and end?
2. **Coverage**: Does it cover what, where, when, and how?
   - What: What happened, what was experienced
   - Where: Location/destination details
   - When: Time/timing information
   - How: How the experience unfolded, methods used

Return a JSON response with:
- "has_structure": true/false (clear beginning, middle, end)
- "coverage": {
    "what": true/false,
    "where": true/false,
    "when": true/false,
    "how": true/false
  }
- "word_count": integer (exact word count)
- "structure_quality": "excellent" | "good" | "fair" | "poor"
- "coverage_score": integer (0-4, count of covered aspects)

Return ONLY valid JSON, no additional text."""
    
    def _create_user_prompt(self, title, travel_experience):
        """Create user prompt with blog content"""
        return f"""Title: {title}

Travel Experience:
{travel_experience}

Analyze the content depth and completeness of this travel blog."""
    
    def score(self, title, travel_experience):
        """
        Calculate content depth score for a blog
        
        Args:
            title: Blog title
            travel_experience: Travel experience text
            
        Returns:
            int: Score from 0 to 20
        """
        try:
            # First, count words
            word_count = self._count_words(travel_experience)
            
            # Base score on word count
            if word_count < 50:
                return 0
            elif word_count < 100:
                base_score = 8
            elif word_count < 150:
                base_score = 14
            else:
                base_score = 14  # Will be upgraded to 20 if structure is good
            
            # For blogs with >150 words, check structure using AI
            if word_count >= 150:
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
                    
                    # Verify word count matches
                    ai_word_count = analysis.get('word_count', word_count)
                    if abs(ai_word_count - word_count) > 10:
                        logger.warning(f"Word count mismatch: AI={ai_word_count}, actual={word_count}")
                    
                    # Check structure and coverage
                    has_structure = analysis.get('has_structure', False)
                    coverage = analysis.get('coverage', {})
                    coverage_score = analysis.get('coverage_score', 0)
                    
                    # Calculate coverage count
                    if isinstance(coverage, dict):
                        coverage_count = sum(1 for v in coverage.values() if v is True)
                    else:
                        coverage_count = coverage_score
                    
                    # Upgrade to full score if structure is good and coverage is adequate
                    if has_structure and coverage_count >= 3:
                        return self.max_score
                    elif has_structure or coverage_count >= 3:
                        return 18
                    else:
                        return base_score
                    
                except Exception as e:
                    logger.error(f"Error in AI analysis for content depth: {e}")
                    # Fall back to base score if AI fails
                    return base_score
            else:
                # For shorter blogs, return base score
                return base_score
                
        except Exception as e:
            logger.error(f"Error calculating content depth score: {e}")
            # Fallback: return score based on word count only
            word_count = self._count_words(travel_experience)
            if word_count < 50:
                return 0
            elif word_count < 100:
                return 8
            elif word_count < 150:
                return 14
            else:
                return 14
