import logging
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

logger = logging.getLogger(__name__)


class HolidayPlanModel:
    """
    MongoDB model for storing holiday plans
    
    Schema:
    {
        "_id": ObjectId,
        "user_id": str (optional),
        "intent": {
            "destination": str,
            "days": int,
            "people": int,
            "preferences": [str]
        },
        "structured_plan": {...},
        "narrative": str,
        "context_used": {...},
        "created_at": datetime,
        "updated_at": datetime
    }
    """
    
    def __init__(self, mongodb_uri: str):
        """
        Initialize Holiday Plan Model with MongoDB connection
        
        Args:
            mongodb_uri (str): MongoDB connection string
        """
        self.client = MongoClient(mongodb_uri)
        self.db = self.client.get_default_database()
        self.collection = self.db['holiday_plans']
        
        # Create indexes
        self._create_indexes()
        
        logger.info("HolidayPlanModel initialized")
    
    def _create_indexes(self):
        """Create indexes for efficient querying"""
        try:
            # Index on user_id for user history queries
            self.collection.create_index('user_id')
            
            # Index on destination for analytics
            self.collection.create_index('intent.destination')
            
            # Index on created_at for sorting
            self.collection.create_index('created_at')
            
            logger.info("Indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def create_plan(self, intent: dict, structured_plan: dict, narrative: str, 
                   context_used: dict, user_id: str = None) -> str:
        """
        Create and store a new holiday plan
        
        Args:
            intent (dict): User intent
            structured_plan (dict): Day-wise itinerary
            narrative (str): Human-readable description
            context_used (dict): DB context snapshot
            user_id (str, optional): User ID if authenticated
            
        Returns:
            str: Plan ID (MongoDB ObjectId as string)
        """
        logger.info(f"Creating new holiday plan for {intent.get('destination')}")
        
        now = datetime.utcnow()
        
        document = {
            'user_id': user_id,
            'intent': intent,
            'structured_plan': structured_plan,
            'narrative': narrative,
            'context_used': context_used,
            'created_at': now,
            'updated_at': now
        }
        
        try:
            result = self.collection.insert_one(document)
            plan_id = str(result.inserted_id)
            
            logger.info(f"Holiday plan created successfully with ID: {plan_id}")
            return plan_id
            
        except Exception as e:
            logger.error(f"Error creating holiday plan: {e}")
            raise
    
    def get_plan(self, plan_id: str) -> dict:
        """
        Retrieve a holiday plan by ID
        
        Args:
            plan_id (str): Plan ID (MongoDB ObjectId as string)
            
        Returns:
            dict: Holiday plan document or None if not found
        """
        logger.info(f"Retrieving holiday plan: {plan_id}")
        
        try:
            plan = self.collection.find_one({'_id': ObjectId(plan_id)})
            
            if plan:
                # Convert ObjectId to string for JSON serialization
                plan['_id'] = str(plan['_id'])
                logger.info(f"Holiday plan retrieved successfully")
            else:
                logger.warning(f"Holiday plan not found: {plan_id}")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error retrieving holiday plan: {e}")
            return None
    
    def get_user_plans(self, user_id: str, limit: int = 10, skip: int = 0) -> list:
        """
        Retrieve all holiday plans for a user
        
        Args:
            user_id (str): User ID
            limit (int): Maximum number of plans to return
            skip (int): Number of plans to skip (for pagination)
            
        Returns:
            list: List of holiday plan documents
        """
        logger.info(f"Retrieving holiday plans for user: {user_id}")
        
        try:
            plans = list(self.collection.find(
                {'user_id': user_id}
            ).sort('created_at', -1).skip(skip).limit(limit))
            
            # Convert ObjectIds to strings
            for plan in plans:
                plan['_id'] = str(plan['_id'])
            
            logger.info(f"Retrieved {len(plans)} holiday plans for user")
            return plans
            
        except Exception as e:
            logger.error(f"Error retrieving user plans: {e}")
            return []
    
    def update_plan(self, plan_id: str, updates: dict) -> bool:
        """
        Update a holiday plan
        
        Args:
            plan_id (str): Plan ID
            updates (dict): Fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Updating holiday plan: {plan_id}")
        
        try:
            # Add updated_at timestamp
            updates['updated_at'] = datetime.utcnow()
            
            result = self.collection.update_one(
                {'_id': ObjectId(plan_id)},
                {'$set': updates}
            )
            
            success = result.modified_count > 0
            
            if success:
                logger.info(f"Holiday plan updated successfully")
            else:
                logger.warning(f"No changes made to holiday plan")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating holiday plan: {e}")
            return False
    
    def delete_plan(self, plan_id: str) -> bool:
        """
        Delete a holiday plan
        
        Args:
            plan_id (str): Plan ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Deleting holiday plan: {plan_id}")
        
        try:
            result = self.collection.delete_one({'_id': ObjectId(plan_id)})
            
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"Holiday plan deleted successfully")
            else:
                logger.warning(f"Holiday plan not found for deletion")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting holiday plan: {e}")
            return False
    
    def get_plans_by_destination(self, destination: str, limit: int = 10) -> list:
        """
        Retrieve recent plans for a specific destination
        
        Args:
            destination (str): Destination name
            limit (int): Maximum number of plans to return
            
        Returns:
            list: List of holiday plan documents
        """
        logger.info(f"Retrieving holiday plans for destination: {destination}")
        
        try:
            plans = list(self.collection.find(
                {'intent.destination': {'$regex': destination, '$options': 'i'}}
            ).sort('created_at', -1).limit(limit))
            
            # Convert ObjectIds to strings
            for plan in plans:
                plan['_id'] = str(plan['_id'])
            
            logger.info(f"Retrieved {len(plans)} holiday plans for destination")
            return plans
            
        except Exception as e:
            logger.error(f"Error retrieving plans by destination: {e}")
            return []
    
    def get_statistics(self) -> dict:
        """
        Get statistics about stored plans
        
        Returns:
            dict: Statistics including total plans, destinations, etc.
        """
        try:
            total_plans = self.collection.count_documents({})
            
            # Get unique destinations
            destinations = self.collection.distinct('intent.destination')
            
            # Get plans from last 7 days
            from datetime import timedelta
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_plans = self.collection.count_documents({
                'created_at': {'$gte': seven_days_ago}
            })
            
            stats = {
                'total_plans': total_plans,
                'unique_destinations': len(destinations),
                'destinations': destinations[:10],  # Top 10
                'recent_plans_7days': recent_plans
            }
            
            logger.info(f"Statistics retrieved: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error retrieving statistics: {e}")
            return {}
