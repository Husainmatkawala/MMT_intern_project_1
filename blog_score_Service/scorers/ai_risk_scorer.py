import json
import logging
import httpx
from openai import AzureOpenAI
from config import Config

logger = logging.getLogger(__name__)

class AIRiskScorer:
    """Scores blog based on AI-generated content risk using heuristics"""
    
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
        self.max_score = 10
    
    def _create_system_prompt(self):
        """Create system prompt for AI risk analysis (heuristic approach)"""
        return """You are an expert content authenticity evaluator. Analyze whether travel blog content appears to be human-written or AI-generated using HEURISTIC indicators (not strict detection).

IMPORTANT: Use a HEURISTIC approach - look for natural human writing patterns, not strict AI detection. Many well-written pieces may have some AI-like characteristics but are still human-written.

Evaluate the following HEURISTIC indicators:
1. **Natural Variation**: Does the writing have natural variation in sentence length and structure?
2. **Personal Voice**: Does it have a personal, authentic voice with unique expressions?
3. **Imperfections**: Are there natural imperfections, casual language, or personal quirks?
4. **Emotional Authenticity**: Does it feel emotionally authentic and genuine?
5. **Specific Details**: Are there specific, personal details that feel real?
6. **Writing Patterns**: Does it avoid overly perfect or formulaic patterns?

HEURISTIC GUIDELINES:
- Strongly human: Natural variation, personal voice, authentic details, some imperfections
- Mixed: Some AI-like patterns but still feels human, or very polished human writing
- High AI probability: Overly perfect, formulaic, lacks personal voice, too polished

Return a JSON response with:
- "human_probability": "strongly_human" | "mixed" | "high_ai_probability"
- "confidence": float (0.0-1.0, confidence in the assessment)
- "indicators": {
    "natural_variation": true/false,
    "personal_voice": true/false,
    "imperfections": true/false,
    "emotional_authenticity": true/false,
    "specific_details": true/false,
    "writing_patterns": "natural" | "mixed" | "formulaic"
  }
- "reasoning": string (brief explanation of the heuristic assessment)
- "score_category": string ("strongly human", "mixed", or "high ai probability")

Return ONLY valid JSON, no additional text."""
    
    def _create_user_prompt(self, title, travel_experience):
        """Create user prompt with blog content"""
        return f"""Title: {title}

Travel Experience:
{travel_experience}

Using HEURISTIC indicators (not strict detection), assess whether this travel blog appears to be human-written or AI-generated."""
    
    def score(self, title, travel_experience):
        """
        Calculate AI risk score for a blog (heuristic approach)
        
        Args:
            title: Blog title
            travel_experience: Travel experience text
            
        Returns:
            int: Score from 0 to 10
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
            
            human_probability = analysis.get('human_probability', 'mixed')
            score_category = analysis.get('score_category', 'mixed')
            
            # Use human_probability or score_category
            category = human_probability if human_probability else score_category
            
            if category == 'strongly_human' or 'strongly human' in category.lower() or 'human' in category.lower():
                # Score in 8-10 range
                confidence = analysis.get('confidence', 0.8)
                indicators = analysis.get('indicators', {})
                
                # Count positive indicators
                positive_count = sum(1 for k, v in indicators.items() 
                                   if k != 'writing_patterns' and v is True)
                writing_patterns = indicators.get('writing_patterns', 'mixed')
                
                if writing_patterns == 'natural' and positive_count >= 4:
                    return 10
                elif positive_count >= 3:
                    return 9
                else:
                    return 8
                    
            elif category == 'mixed':
                # Score in 4-7 range
                confidence = analysis.get('confidence', 0.5)
                indicators = analysis.get('indicators', {})
                
                positive_count = sum(1 for k, v in indicators.items() 
                                   if k != 'writing_patterns' and v is True)
                writing_patterns = indicators.get('writing_patterns', 'mixed')
                
                if writing_patterns == 'natural' and positive_count >= 2:
                    return 7
                elif positive_count >= 2:
                    return 6
                elif positive_count >= 1:
                    return 5
                else:
                    return 4
                    
            else:  # high_ai_probability
                # Score in 0-3 range
                confidence = analysis.get('confidence', 0.3)
                indicators = analysis.get('indicators', {})
                
                positive_count = sum(1 for k, v in indicators.items() 
                                   if k != 'writing_patterns' and v is True)
                writing_patterns = indicators.get('writing_patterns', 'formulaic')
                
                if writing_patterns == 'formulaic' and positive_count == 0:
                    return 0
                elif positive_count == 0:
                    return 1
                elif positive_count == 1:
                    return 2
                else:
                    return 3
                    
        except Exception as e:
            logger.error(f"Error calculating AI risk score: {e}")
            # Default to middle score if AI fails (assume mixed)
            return 5
