import json
import logging
import httpx
from openai import AzureOpenAI
from config import Config

logger = logging.getLogger(__name__)

class LanguageQualityScorer:
    """Scores blog based on language quality and readability using AI"""
    
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
        """Create system prompt for language quality analysis"""
        return """You are an expert language quality evaluator for travel blogs. Analyze the grammar, sentence flow, and readability of the writing.

Evaluate the following aspects:
1. **Grammar**: Are there grammatical errors? Is the language correct?
2. **Sentence Flow**: Do sentences flow smoothly? Is the writing coherent?
3. **Readability**: Is the text easy to read and understand?
4. **Engagement**: Is the writing engaging and pleasant to read?
5. **Clarity**: Is the message clear and well-communicated?

Return a JSON response with:
- "quality_level": "clean_engaging" | "average" | "hard_to_read"
- "grammar_score": integer (0-10, 10 being perfect)
- "sentence_flow_score": integer (0-10)
- "readability_score": integer (0-10)
- "engagement_score": integer (0-10)
- "clarity_score": integer (0-10)
- "issues": array of strings (list of specific issues found)
- "overall_quality": string ("clean & engaging", "average", or "hard to read")
- "score_range": string indicating score range ("0-5", "6-10", or "11-15")

Return ONLY valid JSON, no additional text."""
    
    def _create_user_prompt(self, travel_experience):
        """Create user prompt with blog content"""
        return f"""Travel Experience:
{travel_experience}

Analyze the language quality, grammar, sentence flow, and readability of this travel blog."""
    
    def score(self, travel_experience):
        """
        Calculate language quality score for a blog
        
        Args:
            travel_experience: Travel experience text
            
        Returns:
            int: Score from 0 to 15
        """
        try:
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(travel_experience)
            
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
            
            quality_level = analysis.get('quality_level', 'average')
            overall_quality = analysis.get('overall_quality', 'average')
            
            # Use quality_level or overall_quality to determine score
            quality = quality_level if quality_level else overall_quality
            
            if quality == 'clean_engaging' or 'clean' in quality.lower() or 'engaging' in quality.lower():
                # Calculate average of all scores for fine-tuning
                grammar = analysis.get('grammar_score', 10)
                flow = analysis.get('sentence_flow_score', 10)
                readability = analysis.get('readability_score', 10)
                engagement = analysis.get('engagement_score', 10)
                clarity = analysis.get('clarity_score', 10)
                
                avg_score = (grammar + flow + readability + engagement + clarity) / 5
                
                # Map to 11-15 range
                if avg_score >= 9:
                    return 15
                elif avg_score >= 8:
                    return 13
                else:
                    return 11
                    
            elif quality == 'average':
                # Calculate average of all scores
                grammar = analysis.get('grammar_score', 7)
                flow = analysis.get('sentence_flow_score', 7)
                readability = analysis.get('readability_score', 7)
                engagement = analysis.get('engagement_score', 7)
                clarity = analysis.get('clarity_score', 7)
                
                avg_score = (grammar + flow + readability + engagement + clarity) / 5
                
                # Map to 6-10 range
                if avg_score >= 7.5:
                    return 10
                elif avg_score >= 6.5:
                    return 8
                else:
                    return 6
                    
            else:  # hard_to_read
                # Calculate average of all scores
                grammar = analysis.get('grammar_score', 4)
                flow = analysis.get('sentence_flow_score', 4)
                readability = analysis.get('readability_score', 4)
                engagement = analysis.get('engagement_score', 4)
                clarity = analysis.get('clarity_score', 4)
                
                avg_score = (grammar + flow + readability + engagement + clarity) / 5
                
                # Map to 0-5 range
                if avg_score <= 3:
                    return 0
                elif avg_score <= 4:
                    return 2
                else:
                    return 5
                    
        except Exception as e:
            logger.error(f"Error calculating language quality score: {e}")
            # Default to middle score if AI fails
            return 8
