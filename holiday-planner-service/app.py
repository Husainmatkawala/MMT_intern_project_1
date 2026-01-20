from flask import Flask, request, jsonify
import logging
from pymongo import MongoClient
from config import Config
from agents import IntentAgent, DataAgent, PlannerAgent, NarratorAgent
from models import HolidayPlanModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

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

logger.info("All agents and models initialized successfully")


@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Holiday Planner Service',
        'version': '1.0.0',
        'agents': ['intent', 'data', 'planner', 'narrator']
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
        
        # Step 1: Parse intent (use LLM if enabled)
        logger.info("Step 1: Parsing intent...")
        if Config.USE_LLM_INTENT_EXTRACTION:
            logger.info("Using LLM-based intent extraction")
            intent = intent_agent.parse_intent_with_llm(user_input)
        else:
            logger.info("Using regex-based intent extraction")
            intent = intent_agent.parse_intent(user_input)
            # Add user_context for semantic search compatibility
            intent['user_context'] = user_input
        
        # Validate intent
        is_valid, error_message = intent_agent.validate_intent(intent)
        if not is_valid:
            logger.error(f"Invalid intent: {error_message}")
            return jsonify({
                'success': False,
                'error': error_message,
                'intent': intent
            }), 400
        
        # Step 2: Fetch context data (use semantic search if enabled)
        logger.info("Step 2: Fetching context data from MongoDB...")
        if Config.USE_SEMANTIC_SEARCH:
            logger.info("Using semantic search for context retrieval")
            context = data_agent.fetch_context_semantic(
                destination=intent['destination'],
                intent=intent,
                preferences=intent.get('preferences')
            )
        else:
            logger.info("Using traditional city-based context retrieval")
            context = data_agent.fetch_context(
                destination=intent['destination'],
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
        
        # Support both LLM and regex-based extraction
        use_llm = data.get('use_llm', Config.USE_LLM_INTENT_EXTRACTION)
        
        if use_llm:
            intent = intent_agent.parse_intent_with_llm(data['user_input'])
            method_used = 'llm'
        else:
            intent = intent_agent.parse_intent(data['user_input'])
            intent['user_context'] = data['user_input']
            method_used = 'regex'
        
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
        
        # Support both semantic and traditional context fetching
        use_semantic = data.get('use_semantic', Config.USE_SEMANTIC_SEARCH)
        
        if use_semantic:
            # For semantic search, we need an intent with user_context
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
        else:
            context = data_agent.fetch_context(
                destination=data['destination'],
                preferences=data.get('preferences')
            )
            method_used = 'traditional'
        
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
