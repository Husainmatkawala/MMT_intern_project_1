import logging
import json
from openai import AzureOpenAI
from typing import Dict, List, Optional
from .data_agent import DataAgent

logger = logging.getLogger(__name__)


class KnowledgeAgent:
    """
    Knowledge Agent - Answer travel questions using database context
    
    Responsibility: Handle factual travel queries by fetching data from MongoDB
    and generating natural language answers grounded in database content
    """
    
    def __init__(self, data_agent: DataAgent, azure_endpoint: str, azure_key: str,
                 deployment_name: str, api_version: str, config=None):
        """
        Initialize Knowledge Agent
        
        Args:
            data_agent (DataAgent): Initialized DataAgent for database queries
            azure_endpoint (str): Azure OpenAI endpoint
            azure_key (str): Azure OpenAI API key
            deployment_name (str): Model deployment name
            api_version (str): Azure OpenAI API version
            config: Optional config object
        """
        self.data_agent = data_agent
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_key,
            api_version=api_version
        )
        self.deployment_name = deployment_name
        self.config = config
        
        # Get config values
        self.temperature = getattr(config, 'CHAT_TEMPERATURE', 0.7) if config else 0.7
        self.max_tokens = getattr(config, 'CHAT_RESPONSE_MAX_TOKENS', 500) if config else 500
        
        logger.info("KnowledgeAgent initialized")
    
    def answer_question(self, question: str, session_context: dict = None,
                       conversation_history: List[dict] = None,
                       classification: dict = None) -> Dict:
        """
        Answer a travel-related question using database context
        
        Args:
            question (str): User's question
            session_context (dict): Current session context
            conversation_history (list): Recent conversation
            classification (dict): Query classification result
            
        Returns:
            dict: Answer with response text, data source, and metadata
        """
        logger.info(f"Answering question: {question[:100]}...")
        
        # Extract query parameters from question and context
        query_params = self._extract_query_params(
            question, session_context, classification
        )
        
        logger.debug(f"Query parameters: {query_params}")
        
        # Query database
        db_results = self.query_database(query_params)
        
        # Check if we have data
        has_data = self._has_relevant_data(db_results)
        
        if has_data:
            # Generate answer with database context
            answer = self.generate_answer_with_context(question, db_results, query_params)
            data_source = "database"
        else:
            # No data available - provide helpful message
            answer = self._generate_no_data_response(query_params)
            data_source = "none"
        
        return {
            'response': answer,
            'data_source': data_source,
            'query_params': query_params,
            'results_count': self._count_results(db_results)
        }
    
    def _extract_query_params(self, question: str, session_context: dict = None,
                             classification: dict = None) -> Dict:
        """
        Extract query parameters from question and context
        
        Args:
            question (str): User's question
            session_context (dict): Session context
            classification (dict): Query classification
            
        Returns:
            dict: Query parameters for database
        """
        params = {
            'destination': None,
            'query_type': 'general',
            'filters': [],
            'user_context': question
        }
        
        # Extract from classification
        if classification and 'entities' in classification:
            entities = classification['entities']
            params['destination'] = entities.get('destination')
            params['query_type'] = entities.get('query_type', 'general')
            params['filters'] = entities.get('filters', [])
        
        # Check session context for destination
        if not params['destination'] and session_context:
            params['destination'] = session_context.get('current_destination')
        
        # Try to extract destination from question if still not found
        if not params['destination']:
            params['destination'] = self._extract_destination_from_question(question)
        
        return params
    
    def _extract_destination_from_question(self, question: str) -> Optional[str]:
        """Extract destination from question text"""
        question_lower = question.lower()
        
        # Common Indian destinations
        destinations = [
            'goa', 'mumbai', 'delhi', 'bangalore', 'jaipur', 'udaipur', 'kerala',
            'ladakh', 'manali', 'shimla', 'rishikesh', 'varanasi', 'agra', 'kolkata',
            'chennai', 'hyderabad', 'pune', 'mysore', 'ooty', 'darjeeling', 'kashmir',
            'andaman', 'lakshadweep', 'meghalaya', 'sikkim', 'tawang', 'arunachal pradesh'
        ]
        
        for dest in destinations:
            if dest in question_lower:
                return dest.capitalize()
        
        return None
    
    def query_database(self, query_params: Dict) -> Dict:
        """
        Query database using DataAgent
        
        Args:
            query_params (dict): Query parameters
            
        Returns:
            dict: Database results
        """
        destination = query_params.get('destination')
        query_type = query_params.get('query_type', 'general')
        user_context = query_params.get('user_context', '')
        
        if not destination:
            logger.warning("No destination specified for query")
            return {}
        
        logger.info(f"Querying database for {destination} - type: {query_type}")
        
        # Check if destination has data
        availability = self.data_agent.check_data_availability(destination)
        if not availability.get('has_data'):
            logger.info(f"No data available for destination: {destination}")
            return {}
        
        try:
            # Use semantic search if enabled
            if self.config and getattr(self.config, 'USE_SEMANTIC_SEARCH', True):
                # Build intent for semantic search
                intent = {
                    'destination': destination,
                    'user_context': user_context,
                    'preferences': []
                }
                
                context = self.data_agent.fetch_context_semantic(
                    destination=destination,
                    intent=intent,
                    preferences=None
                )
            else:
                # Traditional city-based search
                context = self.data_agent.fetch_context(
                    destination=destination,
                    preferences=None
                )
            
            # Filter results based on query type
            filtered_results = self._filter_by_query_type(context, query_type)
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error querying database: {e}", exc_info=True)
            return {}
    
    def _filter_by_query_type(self, context: Dict, query_type: str) -> Dict:
        """
        Filter context results based on query type
        
        Args:
            context (dict): Full context from DataAgent
            query_type (str): Type of query (hotels, restaurants, places, etc.)
            
        Returns:
            dict: Filtered results
        """
        if query_type == 'hotels':
            return {'hotels': context.get('hotels', [])}
        elif query_type == 'restaurants':
            return {'restaurants': context.get('restaurants', [])}
        elif query_type == 'places':
            return {'places': context.get('places', [])}
        elif query_type == 'activities':
            return {'activities': context.get('activities', [])}
        else:
            # Return all data for general queries
            return context
    
    def _has_relevant_data(self, db_results: Dict) -> bool:
        """Check if database results contain relevant data"""
        if not db_results:
            return False
        
        # Check if any collection has results
        for key, value in db_results.items():
            if isinstance(value, list) and len(value) > 0:
                return True
            elif isinstance(value, dict):
                # Handle nested structures like transport
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, list) and len(nested_value) > 0:
                        return True
        
        return False
    
    def _count_results(self, db_results: Dict) -> int:
        """Count total results from database"""
        count = 0
        
        for key, value in db_results.items():
            if isinstance(value, list):
                count += len(value)
            elif isinstance(value, dict):
                for nested_value in value.values():
                    if isinstance(nested_value, list):
                        count += len(nested_value)
        
        return count
    
    def generate_answer_with_context(self, question: str, db_context: Dict,
                                     query_params: Dict) -> str:
        """
        Generate natural language answer using database context
        
        Args:
            question (str): User's question
            db_context (dict): Database results
            query_params (dict): Query parameters
            
        Returns:
            str: Natural language answer
        """
        logger.info("Generating answer with database context")
        
        # Format database results for LLM
        formatted_context = self.format_database_results(db_context, query_params)
        
        # Build prompt
        system_prompt = self._build_answer_system_prompt()
        user_prompt = self._build_answer_user_prompt(question, formatted_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            logger.debug(f"Generated answer length: {len(answer)} chars")
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}", exc_info=True)
            # Fallback to formatted results
            return formatted_context
    
    def _build_answer_system_prompt(self) -> str:
        """Build system prompt for answer generation"""
        return """You are a helpful travel assistant. Answer the user's question using ONLY the provided database information.

Guidelines:
- Be conversational and friendly
- Provide specific details from the database (names, ratings, descriptions)
- If the data doesn't fully answer the question, acknowledge what information is available
- Format responses clearly with bullet points or numbered lists when appropriate
- Do NOT make up information not in the database
- If the database lacks specific details, say "I don't have that information"
- Keep responses concise but informative (aim for 150-300 words)"""
    
    def _build_answer_user_prompt(self, question: str, formatted_context: str) -> str:
        """Build user prompt with question and context"""
        return f"""User question: "{question}"

Available database information:
{formatted_context}

Please answer the user's question using only the information provided above."""
    
    def format_database_results(self, db_results: Dict, query_params: Dict) -> str:
        """
        Format database results as readable text for LLM
        
        Args:
            db_results (dict): Database results
            query_params (dict): Query parameters
            
        Returns:
            str: Formatted text representation
        """
        formatted_parts = []
        destination = query_params.get('destination', 'the destination')
        
        # Format hotels
        if 'hotels' in db_results and db_results['hotels']:
            hotels = db_results['hotels'][:10]  # Limit to top 10
            hotel_list = []
            for i, hotel in enumerate(hotels, 1):
                name = hotel.get('name', 'Unknown')
                rating = hotel.get('rating')
                # Handle rating - could be a value or list
                if isinstance(rating, list):
                    rating_str = rating[0] if rating else 'N/A'
                else:
                    rating_str = rating if rating else 'N/A'
                
                desc = hotel.get('description', '')
                # Handle description - could be a string or list
                if isinstance(desc, list):
                    desc_str = desc[0] if desc else 'No description'
                else:
                    desc_str = desc if desc else 'No description'
                
                hotel_list.append(f"{i}. {name} (Rating: {rating_str})\n   {desc_str[:100]}")
            
            formatted_parts.append(f"Hotels in {destination}:\n" + "\n".join(hotel_list))
        
        # Format restaurants
        if 'restaurants' in db_results and db_results['restaurants']:
            restaurants = db_results['restaurants'][:10]
            restaurant_list = []
            for i, restaurant in enumerate(restaurants, 1):
                name = restaurant.get('name', 'Unknown')
                rating = restaurant.get('rating')
                # Handle rating - could be a value or list
                if isinstance(rating, list):
                    rating_str = rating[0] if rating else 'N/A'
                else:
                    rating_str = rating if rating else 'N/A'
                
                desc = restaurant.get('description', '')
                # Handle description - could be a string or list
                if isinstance(desc, list):
                    desc_str = desc[0] if desc else 'No description'
                else:
                    desc_str = desc if desc else 'No description'
                
                restaurant_list.append(f"{i}. {name} (Rating: {rating_str})\n   {desc_str[:100]}")
            
            formatted_parts.append(f"Restaurants in {destination}:\n" + "\n".join(restaurant_list))
        
        # Format places
        if 'places' in db_results and db_results['places']:
            places = db_results['places'][:10]
            place_list = []
            for i, place in enumerate(places, 1):
                name = place.get('name', 'Unknown')
                rating = place.get('rating')
                # Handle rating - could be a value or list
                if isinstance(rating, list):
                    rating_str = rating[0] if rating else 'N/A'
                else:
                    rating_str = rating if rating else 'N/A'
                
                desc = place.get('description', '')
                # Handle description - could be a string or list
                if isinstance(desc, list):
                    desc_str = desc[0] if desc else 'No description'
                else:
                    desc_str = desc if desc else 'No description'
                
                place_list.append(f"{i}. {name} (Rating: {rating_str})\n   {desc_str[:100]}")
            
            formatted_parts.append(f"Places to visit in {destination}:\n" + "\n".join(place_list))
        
        # Format activities
        if 'activities' in db_results and db_results['activities']:
            activities = db_results['activities'][:10]
            activity_list = []
            for i, activity in enumerate(activities, 1):
                name = activity.get('name', 'Unknown')
                activity_type = activity.get('type', '')
                
                desc = activity.get('description', '')
                # Handle description - could be a string or list
                if isinstance(desc, list):
                    desc_str = desc[0] if desc else 'No description'
                else:
                    desc_str = desc if desc else 'No description'
                
                type_info = f" ({activity_type})" if activity_type else ""
                activity_list.append(f"{i}. {name}{type_info}\n   {desc_str[:100]}")
            
            formatted_parts.append(f"Activities in {destination}:\n" + "\n".join(activity_list))
        
        # Format transport if present
        if 'transport' in db_results:
            transport = db_results['transport']
            if transport.get('cabs'):
                formatted_parts.append(f"Cab services available: {len(transport['cabs'])} options")
            if transport.get('buses'):
                formatted_parts.append(f"Bus services available: {len(transport['buses'])} options")
        
        if not formatted_parts:
            return "No specific data available."
        
        return "\n\n".join(formatted_parts)
    
    def _generate_no_data_response(self, query_params: Dict) -> str:
        """
        Generate response when no database data is available
        
        Args:
            query_params (dict): Query parameters
            
        Returns:
            str: Helpful no-data message
        """
        destination = query_params.get('destination')
        
        if destination:
            return f"I don't have information about {destination} in our database yet. We're constantly adding new destinations. Is there another destination you'd like to explore?"
        else:
            return "I couldn't find the destination you're asking about. Could you please specify which city or location you're interested in?"
    
    def handle_general_chat(self, message: str) -> str:
        """
        Handle general conversational messages (greetings, thanks, etc.)
        
        Args:
            message (str): User's message
            
        Returns:
            str: Conversational response
        """
        message_lower = message.lower().strip()
        
        # Greetings
        if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey']):
            return "Hello! I'm your travel assistant. I can help you find hotels, restaurants, places to visit, and plan trips. What would you like to know?"
        
        # Thanks
        elif any(thanks in message_lower for thanks in ['thank', 'thanks']):
            return "You're welcome! Is there anything else you'd like to know about travel destinations?"
        
        # Goodbye
        elif any(bye in message_lower for bye in ['bye', 'goodbye']):
            return "Goodbye! Have a great trip! Feel free to come back if you need more travel information."
        
        # Default
        else:
            return "I'm here to help with travel information. You can ask me about hotels, restaurants, places to visit, or request a trip plan!"
