from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import atexit
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from agents import IntentAgent, DataAgent, PlannerAgent, NarratorAgent, QueryClassifier, KnowledgeAgent
from models import HolidayPlanModel
from session_manager import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for frontend
CORS(app, origins=['http://localhost:5173'], supports_credentials=True)
logger.info("CORS enabled for frontend (http://localhost:5173)")

# Validate configuration
try:
    Config.validate()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Initialize MongoDB client for intent agent
mongo_client = MongoClient(Config.MONGODB_URI)

# Initialize agents with config
intent_agent = IntentAgent(
    db_client=mongo_client, 
    config=Config,
    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
    azure_key=Config.AZURE_OPENAI_KEY,
    deployment_name=Config.AZURE_OPENAI_DEPLOYMENT,
    api_version=Config.AZURE_OPENAI_API_VERSION
)
data_agent = DataAgent(mongodb_uri=Config.MONGODB_URI, config=Config)
planner_agent = PlannerAgent(
    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
    azure_key=Config.AZURE_OPENAI_KEY,
    deployment_name=Config.AZURE_OPENAI_DEPLOYMENT,
    api_version=Config.AZURE_OPENAI_API_VERSION,
    config=Config
)
narrator_agent = NarratorAgent(
    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
    azure_key=Config.AZURE_OPENAI_KEY,
    deployment_name=Config.AZURE_OPENAI_DEPLOYMENT,
    api_version=Config.AZURE_OPENAI_API_VERSION,
    config=Config
)

# Initialize model
holiday_plan_model = HolidayPlanModel(mongodb_uri=Config.MONGODB_URI)

# Initialize chatbot components
session_manager = SessionManager(
    timeout_hours=Config.SESSION_TIMEOUT_HOURS,
    max_history=Config.MAX_CONVERSATION_HISTORY,
    max_sessions=Config.MAX_ACTIVE_SESSIONS
)

query_classifier = QueryClassifier(
    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
    azure_key=Config.AZURE_OPENAI_KEY,
    deployment_name=Config.AZURE_OPENAI_DEPLOYMENT,
    api_version=Config.AZURE_OPENAI_API_VERSION,
    config=Config
)

knowledge_agent = KnowledgeAgent(
    data_agent=data_agent,
    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
    azure_key=Config.AZURE_OPENAI_KEY,
    deployment_name=Config.AZURE_OPENAI_DEPLOYMENT,
    api_version=Config.AZURE_OPENAI_API_VERSION,
    config=Config
)

# Initialize background scheduler for session cleanup
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=session_manager.cleanup_expired_sessions,
    trigger="interval",
    minutes=Config.SESSION_CLEANUP_INTERVAL_MINUTES,
    id='cleanup_sessions',
    name='Cleanup expired chat sessions',
    replace_existing=True
)
scheduler.start()
logger.info(f"Background scheduler started - cleanup interval: {Config.SESSION_CLEANUP_INTERVAL_MINUTES} minutes")

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

logger.info("All agents, models, and chatbot components initialized successfully")


@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Holiday Planner Service',
        'version': '1.0.0',
        'agents': ['intent', 'data', 'planner', 'narrator', 'query_classifier', 'knowledge'],
        'chatbot': {
            'enabled': True,
            'active_sessions': session_manager.get_active_sessions_count(),
            'session_timeout_hours': Config.SESSION_TIMEOUT_HOURS
        }
    }), 200


@app.route('/api/plan-holiday', methods=['POST'])
def plan_holiday():
    """
    Main orchestration endpoint - Generate complete holiday plan
    
    Request Body:
    {
        "user_input": "Plan a 5-day Goa trip for a couple with beaches and activities",
        "user_id": "optional_user_id"
    }
    
    Response:
    {
        "success": true,
        "plan_id": "mongodb_object_id",
        "intent": {...},
        "itinerary": {...},
        "narrative": "...",
        "metadata": {...}
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if 'user_input' not in data:
            logger.warning("Missing required field: user_input")
            return jsonify({
                'success': False,
                'error': 'Missing required field: user_input'
            }), 400
        
        user_input = data['user_input']
        user_id = data.get('user_id')
        
        logger.info(f"Processing holiday plan request: {user_input[:100]}...")
        
        # Step 1: Parse intent (always use LLM)
        logger.info("Step 1: Parsing intent with LLM...")
        intent = intent_agent.parse_intent_with_llm(user_input)
        
        # Validate intent
        is_valid, error_message = intent_agent.validate_intent(intent)
        if not is_valid:
            logger.error(f"Invalid intent: {error_message}")
            return jsonify({
                'success': False,
                'error': error_message,
                'intent': intent
            }), 400
        
        # Step 2: Fetch context data (always use semantic search)
        logger.info("Step 2: Fetching context data with semantic search...")
        context = data_agent.fetch_context_semantic(
            destination=intent['destination'],
            intent=intent,
            preferences=intent.get('preferences')
        )
        
        # Check if data is available
        availability = data_agent.check_data_availability(intent['destination'])
        if not availability['has_data']:
            logger.warning(f"No data available for destination: {intent['destination']}")
            return jsonify({
                'success': False,
                'error': f"Sorry, we don't have enough data for {intent['destination']} yet.",
                'intent': intent,
                'availability': availability
            }), 404
        
        # Step 3: Create itinerary plan
        logger.info("Step 3: Creating itinerary with Planner Agent...")
        structured_plan = planner_agent.create_plan(intent, context)
        
        # Validate plan
        is_valid, issues = planner_agent.validate_plan(structured_plan, context)
        if not is_valid:
            logger.warning(f"Plan validation issues: {issues}")
            # Continue anyway but log the issues
        
        # Step 4: Generate narrative
        logger.info("Step 4: Generating narrative with Narrator Agent...")
        narrative = narrator_agent.create_narrative(intent, structured_plan)
        summary = narrator_agent.create_summary(intent, structured_plan)
        
        # Step 5: Store plan in MongoDB
        logger.info("Step 5: Storing plan in MongoDB...")
        plan_id = holiday_plan_model.create_plan(
            intent=intent,
            structured_plan=structured_plan,
            narrative=narrative,
            context_used=context,
            user_id=user_id
        )
        
        # Prepare response
        response = {
            'success': True,
            'plan_id': plan_id,
            'intent': intent,
            'itinerary': structured_plan,
            'narrative': narrative,
            'summary': summary,
            'metadata': {
                'destination': intent['destination'],
                'days': intent['days'],
                'people': intent['people'],
                'context_stats': {
                    'hotels': len(context.get('hotels', [])),
                    'restaurants': len(context.get('restaurants', [])),
                    'places': len(context.get('places', [])),
                    'activities': len(context.get('activities', []))
                }
            }
        }
        
        logger.info(f"Holiday plan generated successfully with ID: {plan_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in plan_holiday: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@app.route('/api/agents/intent', methods=['POST'])
def test_intent_agent():
    """Test Intent Agent individually"""
    try:
        data = request.get_json()
        
        if 'user_input' not in data:
            return jsonify({'error': 'Missing user_input'}), 400
        
        # Always use LLM for intent extraction
        intent = intent_agent.parse_intent_with_llm(data['user_input'])
        method_used = 'llm'
        
        is_valid, error_message = intent_agent.validate_intent(intent)
        
        return jsonify({
            'intent': intent,
            'is_valid': is_valid,
            'error_message': error_message,
            'method_used': method_used
        }), 200
        
    except Exception as e:
        logger.error(f"Error in test_intent_agent: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/data', methods=['POST'])
def test_data_agent():
    """Test Data Agent individually"""
    try:
        data = request.get_json()
        
        if 'destination' not in data:
            return jsonify({'error': 'Missing destination'}), 400
        
        # Always use semantic search for context fetching
        intent = data.get('intent', {
            'destination': data['destination'],
            'preferences': data.get('preferences', []),
            'user_context': data.get('user_context', f"Trip to {data['destination']}")
        })
        context = data_agent.fetch_context_semantic(
            destination=data['destination'],
            intent=intent,
            preferences=data.get('preferences')
        )
        method_used = 'semantic'
        
        availability = data_agent.check_data_availability(data['destination'])
        
        return jsonify({
            'context': context,
            'availability': availability,
            'method_used': method_used
        }), 200
        
    except Exception as e:
        logger.error(f"Error in test_data_agent: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/planner', methods=['POST'])
def test_planner_agent():
    """Test Planner Agent individually"""
    try:
        data = request.get_json()
        
        if 'intent' not in data or 'context' not in data:
            return jsonify({'error': 'Missing intent or context'}), 400
        
        structured_plan = planner_agent.create_plan(data['intent'], data['context'])
        is_valid, issues = planner_agent.validate_plan(structured_plan, data['context'])
        
        return jsonify({
            'structured_plan': structured_plan,
            'is_valid': is_valid,
            'validation_issues': issues
        }), 200
        
    except Exception as e:
        logger.error(f"Error in test_planner_agent: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/narrator', methods=['POST'])
def test_narrator_agent():
    """Test Narrator Agent individually"""
    try:
        data = request.get_json()
        
        if 'intent' not in data or 'plan' not in data:
            return jsonify({'error': 'Missing intent or plan'}), 400
        
        narrative = narrator_agent.create_narrative(data['intent'], data['plan'])
        summary = narrator_agent.create_summary(data['intent'], data['plan'])
        
        return jsonify({
            'narrative': narrative,
            'summary': summary
        }), 200
        
    except Exception as e:
        logger.error(f"Error in test_narrator_agent: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/plans/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    """Retrieve a stored holiday plan by ID"""
    try:
        plan = holiday_plan_model.get_plan(plan_id)
        
        if not plan:
            return jsonify({
                'success': False,
                'error': 'Plan not found'
            }), 404
        
        return jsonify({
            'success': True,
            'plan': plan
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_plan: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/plans/user/<user_id>', methods=['GET'])
def get_user_plans(user_id):
    """Retrieve all plans for a specific user"""
    try:
        limit = request.args.get('limit', 10, type=int)
        skip = request.args.get('skip', 0, type=int)
        
        plans = holiday_plan_model.get_user_plans(user_id, limit=limit, skip=skip)
        
        return jsonify({
            'success': True,
            'count': len(plans),
            'plans': plans
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_user_plans: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/plans/destination/<destination>', methods=['GET'])
def get_plans_by_destination(destination):
    """Retrieve recent plans for a specific destination"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        plans = holiday_plan_model.get_plans_by_destination(destination, limit=limit)
        
        return jsonify({
            'success': True,
            'destination': destination,
            'count': len(plans),
            'plans': plans
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_plans_by_destination: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get statistics about stored plans"""
    try:
        stats = holiday_plan_model.get_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# CHATBOT ENDPOINTS
# ============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint - Handle conversational queries with session memory
    
    Request Body:
    {
        "message": "Suggest places to visit in Goa",
        "session_id": "optional-uuid",  # Create new if not provided
        "user_id": "optional-user-id"
    }
    
    Response:
    {
        "success": true,
        "session_id": "uuid",
        "response": "Here are great places in Goa...",
        "query_type": "factual",
        "data_source": "database",  # or "llm_fallback" or "planning"
        "session_expires_at": "2026-01-20T15:30:00Z"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'message' not in data:
            logger.warning("Missing required field: message")
            return jsonify({
                'success': False,
                'error': 'Missing required field: message'
            }), 400
        
        user_message = data['message']
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        
        logger.info(f"Chat request: {user_message[:100]}... session_id: {session_id}")
        
        # Get or create session
        if session_id:
            session = session_manager.get_session(session_id)
            if not session:
                logger.info(f"Session {session_id} not found or expired, creating new session")
                session_id = session_manager.create_session(user_id)
                session = session_manager.get_session(session_id)
        else:
            session_id = session_manager.create_session(user_id)
            session = session_manager.get_session(session_id)
        
        # Add user message to session
        session_manager.add_message(session_id, 'user', user_message)
        
        # Get conversation history and context
        conversation_history = session_manager.get_conversation_history(session_id, limit=10)
        session_context = session_manager.get_context(session_id)
        
        # Classify query
        logger.info("Classifying user query...")
        classification = query_classifier.classify_query(
            user_input=user_message,
            session_context=session_context,
            conversation_history=conversation_history
        )
        
        query_type = classification['type']
        logger.info(f"Query classified as: {query_type}")
        
        # Route based on query type
        if query_type == QueryClassifier.GENERAL:
            # Handle general chat
            response_text = knowledge_agent.handle_general_chat(user_message)
            data_source = "general"
            
        elif query_type == QueryClassifier.PLANNING:
            # Route to holiday planner
            logger.info("Routing to holiday planner...")
            response_text, data_source = _handle_planning_query(
                user_message, session_context, user_id
            )
            
        elif query_type == QueryClassifier.FOLLOWUP:
            # Handle follow-up with context
            logger.info("Handling follow-up query...")
            followup_context = query_classifier.extract_follow_up_context(
                user_message, conversation_history
            )
            
            # Merge follow-up context with session context
            merged_classification = {**classification}
            if 'entities' not in merged_classification:
                merged_classification['entities'] = {}
            merged_classification['entities'].update(followup_context)
            
            # Query database and generate answer
            answer_result = knowledge_agent.answer_question(
                question=user_message,
                session_context=session_context,
                conversation_history=conversation_history,
                classification=merged_classification
            )
            
            response_text = answer_result['response']
            data_source = answer_result['data_source']
            
            # Update session context with new info
            if answer_result['query_params'].get('destination'):
                session_manager.update_context(session_id, {
                    'current_destination': answer_result['query_params']['destination']
                })
            
        else:  # FACTUAL
            # Handle factual query
            logger.info("Handling factual query...")
            answer_result = knowledge_agent.answer_question(
                question=user_message,
                session_context=session_context,
                conversation_history=conversation_history,
                classification=classification
            )
            
            response_text = answer_result['response']
            data_source = answer_result['data_source']
            
            # Update session context
            if answer_result['query_params'].get('destination'):
                session_manager.update_context(session_id, {
                    'current_destination': answer_result['query_params']['destination']
                })
        
        # Add assistant response to session
        session_manager.add_message(session_id, 'assistant', response_text)
        
        # Get updated session info
        session_info = session_manager.get_session_info(session_id)
        
        # Prepare response
        response = {
            'success': True,
            'session_id': session_id,
            'response': response_text,
            'query_type': query_type,
            'data_source': data_source,
            'session_expires_at': session_info['expires_at'],
            'message_count': session_info['message_count']
        }
        
        logger.info(f"Chat response generated successfully for session {session_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'details': str(e)
        }), 500


def _handle_planning_query(user_input: str, session_context: dict, user_id: str = None):
    """
    Internal helper to handle planning queries
    
    Returns:
        tuple: (response_text, data_source)
    """
    try:
        # Parse intent using LLM
        intent = intent_agent.parse_intent_with_llm(user_input)
        
        # Validate intent
        is_valid, error_message = intent_agent.validate_intent(intent)
        if not is_valid:
            return f"I couldn't understand your trip planning request. {error_message}", "planning_error"
        
        # Fetch context using semantic search
        context = data_agent.fetch_context_semantic(
            destination=intent['destination'],
            intent=intent,
            preferences=intent.get('preferences')
        )
        
        # Check data availability
        availability = data_agent.check_data_availability(intent['destination'])
        if not availability['has_data']:
            return f"Sorry, we don't have enough data for {intent['destination']} yet.", "planning_error"
        
        # Create plan
        structured_plan = planner_agent.create_plan(intent, context)
        
        # Generate narrative
        narrative = narrator_agent.create_narrative(intent, structured_plan)
        
        # Store plan
        plan_id = holiday_plan_model.create_plan(
            intent=intent,
            structured_plan=structured_plan,
            narrative=narrative,
            context_used=context,
            user_id=user_id
        )
        
        # Format response
        response_text = f"{narrative}\n\n(Plan ID: {plan_id} - You can retrieve this plan later)"
        
        return response_text, "planning"
        
    except Exception as e:
        logger.error(f"Error in planning query: {e}", exc_info=True)
        return "I encountered an error while creating your trip plan. Please try again.", "planning_error"


@app.route('/api/chat/sessions/<session_id>', methods=['GET'])
def get_chat_session(session_id):
    """
    Retrieve session information and conversation history
    
    Response:
    {
        "success": true,
        "session": {
            "session_id": "uuid",
            "created_at": "...",
            "last_activity": "...",
            "expires_at": "...",
            "message_count": 10,
            "context": {...}
        },
        "conversation": [...]
    }
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found or expired'
            }), 404
        
        session_info = session_manager.get_session_info(session_id)
        conversation_history = session_manager.get_conversation_history(session_id)
        
        return jsonify({
            'success': True,
            'session': session_info,
            'conversation': [
                {
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp'].isoformat()
                }
                for msg in conversation_history
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat/sessions/<session_id>', methods=['DELETE'])
def delete_chat_session(session_id):
    """
    Manually end a chat session
    
    Response:
    {
        "success": true,
        "message": "Session deleted successfully"
    }
    """
    try:
        deleted = session_manager.delete_session(session_id)
        
        if deleted:
            return jsonify({
                'success': True,
                'message': 'Session deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat/sessions/new', methods=['POST'])
def create_new_session():
    """
    Explicitly create a new chat session
    
    Request Body:
    {
        "user_id": "optional-user-id"
    }
    
    Response:
    {
        "success": true,
        "session_id": "uuid",
        "expires_at": "...",
        "timeout_hours": 2
    }
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        
        session_id = session_manager.create_session(user_id)
        session_info = session_manager.get_session_info(session_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'expires_at': session_info['expires_at'],
            'timeout_hours': Config.SESSION_TIMEOUT_HOURS
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat/health', methods=['GET'])
def chat_health():
    """
    Check chatbot health and statistics
    
    Response:
    {
        "success": true,
        "status": "healthy",
        "active_sessions": 42,
        "max_sessions": 1000,
        "session_timeout_hours": 2,
        "cleanup_interval_minutes": 10
    }
    """
    try:
        return jsonify({
            'success': True,
            'status': 'healthy',
            'active_sessions': session_manager.get_active_sessions_count(),
            'max_sessions': Config.MAX_ACTIVE_SESSIONS,
            'session_timeout_hours': Config.SESSION_TIMEOUT_HOURS,
            'cleanup_interval_minutes': Config.SESSION_CLEANUP_INTERVAL_MINUTES,
            'scheduler_running': scheduler.running
        }), 200
        
    except Exception as e:
        logger.error(f"Error in chat health check: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info(f"Starting Holiday Planner Service on port {Config.PORT}")
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
