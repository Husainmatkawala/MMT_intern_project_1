import logging
import json
from openai import AzureOpenAI
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class QueryClassifier:
    """
    Query Classification Agent - Determine query type and route appropriately
    
    Responsibility: Classify user queries as factual, planning, follow-up, or general chat
    Extract entities and context for downstream processing
    """
    
    # Query type constants
    FACTUAL = "factual"
    PLANNING = "planning"
    FOLLOWUP = "followup"
    GENERAL = "general"
    
    def __init__(self, azure_endpoint: str, azure_key: str, deployment_name: str, 
                 api_version: str, config=None):
        """
        Initialize Query Classifier
        
        Args:
            azure_endpoint (str): Azure OpenAI endpoint
            azure_key (str): Azure OpenAI API key
            deployment_name (str): Model deployment name
            api_version (str): Azure OpenAI API version
            config: Optional config object
        """
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_key,
            api_version=api_version
        )
        self.deployment_name = deployment_name
        self.config = config
        
        # Get config values
        self.temperature = getattr(config, 'TEMPERATURE', 0.7) if config else 0.7
        self.max_tokens = getattr(config, 'CHAT_RESPONSE_MAX_TOKENS', 500) if config else 500
        
        logger.info("QueryClassifier initialized with Azure OpenAI")
    
    def classify_query(self, user_input: str, session_context: dict = None, 
                      conversation_history: List[dict] = None) -> Dict:
        """
        Classify user query and extract relevant entities
        
        Args:
            user_input (str): User's message
            session_context (dict): Current session context (destination, preferences, etc.)
            conversation_history (list): Recent conversation messages
            
        Returns:
            dict: Classification result with type, entities, and metadata
        """
        logger.info(f"Classifying query: {user_input[:100]}...")
        
        # Build classification prompt
        system_prompt = self._build_classification_prompt()
        user_prompt = self._build_user_prompt(user_input, session_context, conversation_history)
        
        try:
            # Call Azure OpenAI for classification
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more deterministic classification
                max_tokens=300
            )
            
            classification_text = response.choices[0].message.content.strip()
            logger.debug(f"LLM classification response: {classification_text}")
            
            # Parse JSON response
            classification = self._parse_classification_response(classification_text)
            
            logger.info(f"Query classified as: {classification['type']}")
            return classification
            
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}", exc_info=True)
            
            # Fallback to rule-based classification
            logger.info("Falling back to rule-based classification")
            return self._rule_based_classification(user_input, session_context, conversation_history)
    
    def _build_classification_prompt(self) -> str:
        """Build system prompt for query classification"""
        return """You are a travel query classifier. Classify user messages into one of these types:

1. **factual** - Questions about travel information that can be answered from a database
   Examples: "List hotels in Goa", "What are good restaurants in Mumbai?", "Places to visit near Baga Beach"
   
2. **planning** - Requests to create a travel itinerary or plan a trip
   Examples: "Plan a 5-day trip to Goa", "Create an itinerary for Rajasthan", "Help me plan my vacation"
   
3. **followup** - Follow-up questions referencing previous conversation
   Examples: "Which ones are near the beach?", "Tell me more about the first one", "What about their ratings?"
   
4. **general** - Greetings, thanks, or general conversation
   Examples: "Hello", "Thank you", "That's helpful", "Goodbye"

Return a JSON object with this structure:
{
    "type": "factual|planning|followup|general",
    "entities": {
        "destination": "extracted destination or null",
        "query_type": "hotels|restaurants|places|activities|general",
        "filters": ["list of filters like 'near beach', 'with rating > 4']
    },
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of classification"
}

Be precise and consider the conversation context when provided."""
    
    def _build_user_prompt(self, user_input: str, session_context: dict = None, 
                          conversation_history: List[dict] = None) -> str:
        """Build user prompt with context"""
        prompt_parts = [f"User message: \"{user_input}\""]
        
        # Add session context if available
        if session_context:
            context_info = []
            if session_context.get('current_destination'):
                context_info.append(f"Current destination: {session_context['current_destination']}")
            if session_context.get('current_preferences'):
                context_info.append(f"Preferences: {', '.join(session_context['current_preferences'])}")
            
            if context_info:
                prompt_parts.append(f"\nSession context:\n" + "\n".join(context_info))
        
        # Add recent conversation history if available
        if conversation_history and len(conversation_history) > 0:
            history_text = "\n".join([
                f"{msg['role']}: {msg['content'][:100]}"
                for msg in conversation_history[-3:]  # Last 3 messages
            ])
            prompt_parts.append(f"\nRecent conversation:\n{history_text}")
        
        return "\n".join(prompt_parts)
    
    def _parse_classification_response(self, response_text: str) -> Dict:
        """Parse LLM JSON response"""
        try:
            # Try to extract JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            classification = json.loads(response_text)
            
            # Validate required fields
            if 'type' not in classification:
                raise ValueError("Missing 'type' field in classification")
            
            # Ensure entities dict exists
            if 'entities' not in classification:
                classification['entities'] = {}
            
            # Set defaults
            classification.setdefault('confidence', 0.8)
            classification.setdefault('reasoning', '')
            
            return classification
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse classification JSON: {e}")
            # Return default factual classification
            return {
                'type': self.FACTUAL,
                'entities': {},
                'confidence': 0.5,
                'reasoning': 'Fallback due to parsing error'
            }
    
    def _rule_based_classification(self, user_input: str, session_context: dict = None,
                                  conversation_history: List[dict] = None) -> Dict:
        """
        Fallback rule-based classification if LLM fails
        
        Args:
            user_input (str): User's message
            session_context (dict): Current session context
            conversation_history (list): Recent conversation
            
        Returns:
            dict: Classification result
        """
        user_input_lower = user_input.lower()
        
        # General greetings/thanks
        general_keywords = ['hello', 'hi', 'hey', 'thank', 'thanks', 'bye', 'goodbye', 'okay', 'ok']
        if any(keyword in user_input_lower for keyword in general_keywords) and len(user_input.split()) <= 3:
            return {
                'type': self.GENERAL,
                'entities': {},
                'confidence': 0.9,
                'reasoning': 'Detected greeting or acknowledgment'
            }
        
        # Planning keywords
        planning_keywords = ['plan', 'itinerary', 'trip', 'vacation', 'create a plan', 'suggest a plan']
        if any(keyword in user_input_lower for keyword in planning_keywords):
            # Check for duration indicators
            has_duration = any(word in user_input_lower for word in ['day', 'days', 'week', 'weeks'])
            
            if has_duration:
                return {
                    'type': self.PLANNING,
                    'entities': {},
                    'confidence': 0.85,
                    'reasoning': 'Contains planning keywords and duration'
                }
        
        # Follow-up indicators
        followup_indicators = ['which ones', 'which one', 'tell me more', 'what about', 'how about', 
                               'the first', 'the second', 'those', 'these', 'them', 'it']
        
        if any(indicator in user_input_lower for indicator in followup_indicators):
            if conversation_history and len(conversation_history) > 0:
                return {
                    'type': self.FOLLOWUP,
                    'entities': {},
                    'confidence': 0.8,
                    'reasoning': 'Contains follow-up indicators with conversation history'
                }
        
        # Factual query patterns
        factual_keywords = {
            'hotels': ['hotel', 'hotels', 'stay', 'accommodation'],
            'restaurants': ['restaurant', 'restaurants', 'food', 'eat', 'dining'],
            'places': ['place', 'places', 'visit', 'attraction', 'sights', 'see'],
            'activities': ['activity', 'activities', 'do', 'things to do']
        }
        
        detected_query_type = 'general'
        for query_type, keywords in factual_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                detected_query_type = query_type
                break
        
        # Extract destination if mentioned
        destination = self._extract_destination_simple(user_input)
        
        # Default to factual if it looks like a question
        question_indicators = ['list', 'show', 'give', 'suggest', 'recommend', 'what', 'where', 'which']
        if any(indicator in user_input_lower for indicator in question_indicators):
            return {
                'type': self.FACTUAL,
                'entities': {
                    'destination': destination,
                    'query_type': detected_query_type
                },
                'confidence': 0.7,
                'reasoning': 'Contains question indicators'
            }
        
        # Default to factual
        return {
            'type': self.FACTUAL,
            'entities': {
                'destination': destination,
                'query_type': detected_query_type
            },
            'confidence': 0.6,
            'reasoning': 'Default classification'
        }
    
    def _extract_destination_simple(self, text: str) -> Optional[str]:
        """Simple destination extraction using common patterns"""
        text_lower = text.lower()
        
        # Common Indian destinations
        common_destinations = [
            'goa', 'mumbai', 'delhi', 'bangalore', 'jaipur', 'udaipur', 'kerala',
            'ladakh', 'manali', 'shimla', 'rishikesh', 'varanasi', 'agra', 'kolkata',
            'chennai', 'hyderabad', 'pune', 'mysore', 'ooty', 'darjeeling', 'tawang',
            'kashmir', 'andaman', 'lakshadweep', 'meghalaya', 'sikkim', 'arunachal pradesh'
        ]
        
        for destination in common_destinations:
            if destination in text_lower:
                return destination.capitalize()
        
        return None
    
    def extract_follow_up_context(self, user_input: str, conversation_history: List[dict]) -> Dict:
        """
        Extract context from follow-up questions
        
        Args:
            user_input (str): User's follow-up question
            conversation_history (list): Recent conversation messages
            
        Returns:
            dict: Extracted context with references resolved
        """
        if not conversation_history:
            return {}
        
        logger.info(f"Extracting follow-up context for: {user_input[:100]}")
        
        # Get the last assistant response
        last_assistant_message = None
        for msg in reversed(conversation_history):
            if msg['role'] == 'assistant':
                last_assistant_message = msg['content']
                break
        
        if not last_assistant_message:
            return {}
        
        # Build prompt to extract context
        system_prompt = """You are a context extractor. Given a follow-up question and the previous assistant response, 
extract what the user is referring to.

Return JSON:
{
    "referring_to": "hotels|restaurants|places|activities|previous_response",
    "filters": ["extracted filters like 'near beach', 'with high rating'"],
    "destination": "destination if mentioned or null"
}"""
        
        user_prompt = f"""Follow-up question: "{user_input}"

Previous assistant response: "{last_assistant_message[:500]}"

Extract the context."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            context_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            if "```json" in context_text:
                json_start = context_text.find("```json") + 7
                json_end = context_text.find("```", json_start)
                context_text = context_text[json_start:json_end].strip()
            
            context = json.loads(context_text)
            logger.debug(f"Extracted follow-up context: {context}")
            
            return context
            
        except Exception as e:
            logger.warning(f"Failed to extract follow-up context: {e}")
            return {}
