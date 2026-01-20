import logging
from pymongo import MongoClient
from bson import ObjectId
from typing import List
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class DataAgent:
    """
    Data Retrieval Agent - Fetch relevant data from MongoDB collections
    
    Responsibility: Query MongoDB for hotels, restaurants, activities, places, transport
    based on destination. Supports both traditional city-based filtering and semantic similarity search.
    """
    
    def __init__(self, mongodb_uri: str, config=None):
        """
        Initialize Data Agent with MongoDB connection
        
        Args:
            mongodb_uri (str): MongoDB connection string
            config: Optional config object for query limits
        """
        self.client = MongoClient(mongodb_uri)
        self.db = self.client.get_default_database()
        self.config = config
        
        # Get query limits from config or use defaults
        self.limit_hotels = getattr(config, 'QUERY_LIMIT_HOTELS', 10) if config else 10
        self.limit_restaurants = getattr(config, 'QUERY_LIMIT_RESTAURANTS', 10) if config else 10
        self.limit_activities = getattr(config, 'QUERY_LIMIT_ACTIVITIES', 15) if config else 15
        self.limit_places = getattr(config, 'QUERY_LIMIT_PLACES', 15) if config else 15
        self.limit_cabs = getattr(config, 'QUERY_LIMIT_CABS', 5) if config else 5
        self.limit_buses = getattr(config, 'QUERY_LIMIT_BUSES', 5) if config else 5
        
        # Initialize embedding service for semantic search
        try:
            embedding_model = getattr(config, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2') if config else 'all-MiniLM-L6-v2'
            self.embedding_service = EmbeddingService(model_name=embedding_model)
            self.semantic_enabled = True
            logger.info("DataAgent: Semantic search enabled with EmbeddingService")
        except Exception as e:
            logger.warning(f"Failed to initialize EmbeddingService: {e}. Semantic search disabled.")
            self.embedding_service = None
            self.semantic_enabled = False
        
        # Collections
        self.hotels = self.db['hotels']
        self.restaurants = self.db['restaurants']
        self.activities = self.db['activities']
        self.places = self.db['places']
        self.cabs = self.db['cabs']
        self.buses = self.db['buses']
        
        logger.info("DataAgent initialized with MongoDB connection")
    
    def fetch_context(self, destination: str, preferences: list = None) -> dict:
        """
        Fetch all relevant data for a destination
        
        Args:
            destination (str): City/destination name
            preferences (list): User preferences to filter activities/places
            
        Returns:
            dict: Context data with hotels, restaurants, activities, places, transport
        """
        logger.info(f"Fetching context for destination: {destination}")
        
        context = {
            'destination': destination,
            'hotels': self._fetch_hotels(destination),
            'restaurants': self._fetch_restaurants(destination),
            'activities': self._fetch_activities(destination, preferences),
            'places': self._fetch_places(destination),
            'transport': {
                'cabs': self._fetch_cabs(destination),
                'buses': self._fetch_buses(destination)
            }
        }
        
        # Log stats
        logger.info(f"Context fetched - Hotels: {len(context['hotels'])}, "
                   f"Restaurants: {len(context['restaurants'])}, "
                   f"Activities: {len(context['activities'])}, "
                   f"Places: {len(context['places'])}, "
                   f"Cabs: {len(context['transport']['cabs'])}, "
                   f"Buses: {len(context['transport']['buses'])}")
        
        return context
    
    def _fetch_hotels(self, destination: str) -> list:
        """Fetch hotels for destination"""
        try:
            hotels = list(self.hotels.find(
                {'city': {'$regex': destination, '$options': 'i'}},
                {'_id': 0, 'hotel_name': 1, 'city': 1, 'state': 1, 'rating': 1, 'description': 1}
            ).limit(self.limit_hotels))
            
            # Clean up data
            for hotel in hotels:
                hotel['name'] = hotel.pop('hotel_name', 'Unknown Hotel')
                # Keep only first description if multiple exist
                if isinstance(hotel.get('description'), list) and hotel['description']:
                    hotel['description'] = hotel['description'][0]
                # Keep only first rating if multiple exist
                if isinstance(hotel.get('rating'), list) and hotel['rating']:
                    hotel['rating'] = hotel['rating'][0]
            
            logger.info(f"Fetched {len(hotels)} hotels")
            return hotels
        except Exception as e:
            logger.error(f"Error fetching hotels: {e}")
            return []
    
    def _fetch_restaurants(self, destination: str) -> list:
        """Fetch restaurants for destination"""
        try:
            restaurants = list(self.restaurants.find(
                {'city': {'$regex': destination, '$options': 'i'}},
                {'_id': 0, 'restaurant_name': 1, 'city': 1, 'state': 1, 'rating': 1, 'description': 1}
            ).limit(self.limit_restaurants))
            
            # Clean up data
            for restaurant in restaurants:
                restaurant['name'] = restaurant.pop('restaurant_name', 'Unknown Restaurant')
                if isinstance(restaurant.get('description'), list) and restaurant['description']:
                    restaurant['description'] = restaurant['description'][0]
                if isinstance(restaurant.get('rating'), list) and restaurant['rating']:
                    restaurant['rating'] = restaurant['rating'][0]
            
            logger.info(f"Fetched {len(restaurants)} restaurants")
            return restaurants
        except Exception as e:
            logger.error(f"Error fetching restaurants: {e}")
            return []
    
    def _fetch_activities(self, destination: str, preferences: list = None) -> list:
        """Fetch activities for destination"""
        try:
            query = {'city': {'$regex': destination, '$options': 'i'}}
            
            # Filter by preferences if provided
            if preferences:
                # Map preferences to activity types
                type_filters = []
                preference_to_type = {
                    'beach': ['beach', 'water'],
                    'adventure': ['adventure', 'trekking', 'climbing'],
                    'activities': ['sports', 'activity'],
                    'nightlife': ['nightlife', 'club', 'bar']
                }
                
                for pref in preferences:
                    if pref in preference_to_type:
                        type_filters.extend(preference_to_type[pref])
                
                if type_filters:
                    query['type'] = {'$regex': '|'.join(type_filters), '$options': 'i'}
            
            activities = list(self.activities.find(
                query,
                {'_id': 0, 'activity_name': 1, 'type': 1, 'city': 1, 'state': 1, 'description': 1}
            ).limit(self.limit_activities))
            
            # Clean up data
            for activity in activities:
                activity['name'] = activity.pop('activity_name', 'Unknown Activity')
                if isinstance(activity.get('description'), list) and activity['description']:
                    activity['description'] = activity['description'][0]
            
            logger.info(f"Fetched {len(activities)} activities")
            return activities
        except Exception as e:
            logger.error(f"Error fetching activities: {e}")
            return []
    
    def _fetch_places(self, destination: str) -> list:
        """Fetch places/attractions for destination"""
        try:
            places = list(self.places.find(
                {'city': {'$regex': destination, '$options': 'i'}},
                {'_id': 0, 'place_name': 1, 'city': 1, 'state': 1, 'rating': 1, 'description': 1}
            ).limit(self.limit_places))
            
            # Clean up data
            for place in places:
                place['name'] = place.pop('place_name', 'Unknown Place')
                if isinstance(place.get('description'), list) and place['description']:
                    place['description'] = place['description'][0]
                if isinstance(place.get('rating'), list) and place['rating']:
                    place['rating'] = place['rating'][0]
            
            logger.info(f"Fetched {len(places)} places")
            return places
        except Exception as e:
            logger.error(f"Error fetching places: {e}")
            return []
    
    def _fetch_cabs(self, destination: str) -> list:
        """Fetch cab services for destination"""
        try:
            cabs = list(self.cabs.find(
                {'city': {'$regex': destination, '$options': 'i'}},
                {'_id': 0, 'service_name': 1, 'city': 1, 'rating': 1, 'contact': 1}
            ).limit(self.limit_cabs))
            
            # Clean up data
            for cab in cabs:
                cab['name'] = cab.pop('service_name', 'Unknown Service')
                if isinstance(cab.get('rating'), list) and cab['rating']:
                    cab['rating'] = cab['rating'][0]
                if isinstance(cab.get('contact'), list) and cab['contact']:
                    cab['contact'] = cab['contact'][0]
            
            logger.info(f"Fetched {len(cabs)} cab services")
            return cabs
        except Exception as e:
            logger.error(f"Error fetching cabs: {e}")
            return []
    
    def _fetch_buses(self, destination: str) -> list:
        """Fetch bus services for destination"""
        try:
            buses = list(self.buses.find(
                {'city': {'$regex': destination, '$options': 'i'}},
                {'_id': 0, 'service_name': 1, 'city': 1, 'rating': 1, 'contact': 1}
            ).limit(self.limit_buses))
            
            # Clean up data
            for bus in buses:
                bus['name'] = bus.pop('service_name', 'Unknown Service')
                if isinstance(bus.get('rating'), list) and bus['rating']:
                    bus['rating'] = bus['rating'][0]
                if isinstance(bus.get('contact'), list) and bus['contact']:
                    bus['contact'] = bus['contact'][0]
            
            logger.info(f"Fetched {len(buses)} bus services")
            return buses
        except Exception as e:
            logger.error(f"Error fetching buses: {e}")
            return []
    
    def check_data_availability(self, destination: str) -> dict:
        """
        Check if data is available for a destination
        
        Args:
            destination (str): Destination to check
            
        Returns:
            dict: Availability status for each collection
        """
        availability = {
            'hotels': self.hotels.count_documents({'city': {'$regex': destination, '$options': 'i'}}) > 0,
            'restaurants': self.restaurants.count_documents({'city': {'$regex': destination, '$options': 'i'}}) > 0,
            'activities': self.activities.count_documents({'city': {'$regex': destination, '$options': 'i'}}) > 0,
            'places': self.places.count_documents({'city': {'$regex': destination, '$options': 'i'}}) > 0,
            'cabs': self.cabs.count_documents({'city': {'$regex': destination, '$options': 'i'}}) > 0,
            'buses': self.buses.count_documents({'city': {'$regex': destination, '$options': 'i'}}) > 0,
        }
        
        availability['has_data'] = any(availability.values())
        
        return availability
    
    def fetch_context_semantic(self, destination: str, intent: dict, preferences: list = None) -> dict:
        """
        Fetch relevant documents using semantic similarity search
        
        Args:
            destination (str): City/destination name
            intent (dict): Full intent dict with user_context
            preferences (list): User preferences to filter activities/places
            
        Returns:
            dict: Context data with semantically similar documents
        """
        if not self.semantic_enabled:
            logger.warning("Semantic search not enabled, falling back to traditional fetch_context")
            return self.fetch_context(destination, preferences)
        
        logger.info(f"Fetching context with semantic search for destination: {destination}")
        
        # Build query text from intent
        query_text = self._build_query_text(intent)
        logger.info(f"Query text for semantic search: {query_text[:100]}...")
        
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(query_text)
        
        # Fetch from each collection with semantic ranking
        context = {
            'destination': destination,
            'hotels': self._fetch_hotels_semantic(destination, query_embedding),
            'restaurants': self._fetch_restaurants_semantic(destination, query_embedding),
            'activities': self._fetch_activities_semantic(destination, query_embedding),
            'places': self._fetch_places_semantic(destination, query_embedding),
            'transport': {
                'cabs': self._fetch_cabs_semantic(destination, query_embedding),
                'buses': self._fetch_buses_semantic(destination, query_embedding)
            }
        }
        
        # Log stats
        logger.info(f"Semantic context fetched - Hotels: {len(context['hotels'])}, "
                   f"Restaurants: {len(context['restaurants'])}, "
                   f"Activities: {len(context['activities'])}, "
                   f"Places: {len(context['places'])}, "
                   f"Cabs: {len(context['transport']['cabs'])}, "
                   f"Buses: {len(context['transport']['buses'])}")
        
        return context
    
    def _build_query_text(self, intent: dict) -> str:
        """
        Build query text from intent for semantic search
        
        Args:
            intent (dict): Intent dictionary with destination, preferences, user_context
            
        Returns:
            str: Combined query text for embedding
        """
        parts = []
        
        # Add destination
        if intent.get('destination'):
            parts.append(f"Destination: {intent['destination']}")
        
        # Add preferences
        if intent.get('preferences'):
            parts.append(f"Preferences: {', '.join(intent['preferences'])}")
        
        # Add user context (most important for semantic matching)
        if intent.get('user_context'):
            parts.append(intent['user_context'])
        
        query_text = ". ".join(parts)
        return query_text if query_text else "General travel"
    
    def _fetch_hotels_semantic(self, destination: str, query_embedding: List[float]) -> list:
        """Fetch hotels using semantic similarity"""
        try:
            # Fetch all hotels for destination
            hotels = list(self.hotels.find(
                {'city': {'$regex': destination, '$options': 'i'}}
            ))
            
            if not hotels:
                logger.info(f"No hotels found for destination: {destination}")
                return []
            
            # Generate text representations for hotels
            hotel_texts = [self._create_hotel_text(h) for h in hotels]
            
            # Generate embeddings for hotels
            hotel_embeddings = self.embedding_service.generate_embeddings_batch(hotel_texts)
            
            # Calculate similarities
            similarities = [
                self.embedding_service.cosine_similarity(query_embedding, emb)
                for emb in hotel_embeddings
            ]
            
            # Combine hotels with scores and sort
            hotels_with_scores = list(zip(hotels, similarities))
            hotels_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top K with cleaned data
            result = []
            for hotel, score in hotels_with_scores[:self.limit_hotels]:
                cleaned = self._clean_hotel_data(hotel)
                cleaned['similarity_score'] = float(score)
                result.append(cleaned)
            
            logger.info(f"Fetched {len(result)} hotels with semantic ranking")
            return result
            
        except Exception as e:
            logger.error(f"Error in semantic hotel fetch: {e}")
            return self._fetch_hotels(destination)
    
    def _fetch_restaurants_semantic(self, destination: str, query_embedding: List[float]) -> list:
        """Fetch restaurants using semantic similarity"""
        try:
            # Fetch all restaurants for destination
            restaurants = list(self.restaurants.find(
                {'city': {'$regex': destination, '$options': 'i'}}
            ))
            
            if not restaurants:
                logger.info(f"No restaurants found for destination: {destination}")
                return []
            
            # Generate text representations
            restaurant_texts = [self._create_restaurant_text(r) for r in restaurants]
            
            # Generate embeddings
            restaurant_embeddings = self.embedding_service.generate_embeddings_batch(restaurant_texts)
            
            # Calculate similarities
            similarities = [
                self.embedding_service.cosine_similarity(query_embedding, emb)
                for emb in restaurant_embeddings
            ]
            
            # Combine and sort
            restaurants_with_scores = list(zip(restaurants, similarities))
            restaurants_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top K with cleaned data
            result = []
            for restaurant, score in restaurants_with_scores[:self.limit_restaurants]:
                cleaned = self._clean_restaurant_data(restaurant)
                cleaned['similarity_score'] = float(score)
                result.append(cleaned)
            
            logger.info(f"Fetched {len(result)} restaurants with semantic ranking")
            return result
            
        except Exception as e:
            logger.error(f"Error in semantic restaurant fetch: {e}")
            return self._fetch_restaurants(destination)
    
    def _fetch_activities_semantic(self, destination: str, query_embedding: List[float]) -> list:
        """Fetch activities using semantic similarity"""
        try:
            # Fetch all activities for destination
            activities = list(self.activities.find(
                {'city': {'$regex': destination, '$options': 'i'}}
            ))
            
            if not activities:
                logger.info(f"No activities found for destination: {destination}")
                return []
            
            # Generate text representations
            activity_texts = [self._create_activity_text(a) for a in activities]
            
            # Generate embeddings
            activity_embeddings = self.embedding_service.generate_embeddings_batch(activity_texts)
            
            # Calculate similarities
            similarities = [
                self.embedding_service.cosine_similarity(query_embedding, emb)
                for emb in activity_embeddings
            ]
            
            # Combine and sort
            activities_with_scores = list(zip(activities, similarities))
            activities_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top K with cleaned data
            result = []
            for activity, score in activities_with_scores[:self.limit_activities]:
                cleaned = self._clean_activity_data(activity)
                cleaned['similarity_score'] = float(score)
                result.append(cleaned)
            
            logger.info(f"Fetched {len(result)} activities with semantic ranking")
            return result
            
        except Exception as e:
            logger.error(f"Error in semantic activity fetch: {e}")
            return self._fetch_activities(destination, None)
    
    def _fetch_places_semantic(self, destination: str, query_embedding: List[float]) -> list:
        """Fetch places using semantic similarity"""
        try:
            # Fetch all places for destination
            places = list(self.places.find(
                {'city': {'$regex': destination, '$options': 'i'}}
            ))
            
            if not places:
                logger.info(f"No places found for destination: {destination}")
                return []
            
            # Generate text representations
            place_texts = [self._create_place_text(p) for p in places]
            
            # Generate embeddings
            place_embeddings = self.embedding_service.generate_embeddings_batch(place_texts)
            
            # Calculate similarities
            similarities = [
                self.embedding_service.cosine_similarity(query_embedding, emb)
                for emb in place_embeddings
            ]
            
            # Combine and sort
            places_with_scores = list(zip(places, similarities))
            places_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top K with cleaned data
            result = []
            for place, score in places_with_scores[:self.limit_places]:
                cleaned = self._clean_place_data(place)
                cleaned['similarity_score'] = float(score)
                result.append(cleaned)
            
            logger.info(f"Fetched {len(result)} places with semantic ranking")
            return result
            
        except Exception as e:
            logger.error(f"Error in semantic place fetch: {e}")
            return self._fetch_places(destination)
    
    def _fetch_cabs_semantic(self, destination: str, query_embedding: List[float]) -> list:
        """Fetch cabs using semantic similarity"""
        try:
            # Fetch all cabs for destination
            cabs = list(self.cabs.find(
                {'city': {'$regex': destination, '$options': 'i'}}
            ))
            
            if not cabs:
                logger.info(f"No cabs found for destination: {destination}")
                return []
            
            # Generate text representations
            cab_texts = [self._create_cab_text(c) for c in cabs]
            
            # Generate embeddings
            cab_embeddings = self.embedding_service.generate_embeddings_batch(cab_texts)
            
            # Calculate similarities
            similarities = [
                self.embedding_service.cosine_similarity(query_embedding, emb)
                for emb in cab_embeddings
            ]
            
            # Combine and sort
            cabs_with_scores = list(zip(cabs, similarities))
            cabs_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top K with cleaned data
            result = []
            for cab, score in cabs_with_scores[:self.limit_cabs]:
                cleaned = self._clean_cab_data(cab)
                cleaned['similarity_score'] = float(score)
                result.append(cleaned)
            
            logger.info(f"Fetched {len(result)} cabs with semantic ranking")
            return result
            
        except Exception as e:
            logger.error(f"Error in semantic cab fetch: {e}")
            return self._fetch_cabs(destination)
    
    def _fetch_buses_semantic(self, destination: str, query_embedding: List[float]) -> list:
        """Fetch buses using semantic similarity"""
        try:
            # Fetch all buses for destination
            buses = list(self.buses.find(
                {'city': {'$regex': destination, '$options': 'i'}}
            ))
            
            if not buses:
                logger.info(f"No buses found for destination: {destination}")
                return []
            
            # Generate text representations
            bus_texts = [self._create_bus_text(b) for b in buses]
            
            # Generate embeddings
            bus_embeddings = self.embedding_service.generate_embeddings_batch(bus_texts)
            
            # Calculate similarities
            similarities = [
                self.embedding_service.cosine_similarity(query_embedding, emb)
                for emb in bus_embeddings
            ]
            
            # Combine and sort
            buses_with_scores = list(zip(buses, similarities))
            buses_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top K with cleaned data
            result = []
            for bus, score in buses_with_scores[:self.limit_buses]:
                cleaned = self._clean_bus_data(bus)
                cleaned['similarity_score'] = float(score)
                result.append(cleaned)
            
            logger.info(f"Fetched {len(result)} buses with semantic ranking")
            return result
            
        except Exception as e:
            logger.error(f"Error in semantic bus fetch: {e}")
            return self._fetch_buses(destination)
    
    # Text creation methods for semantic search
    
    def _create_hotel_text(self, hotel: dict) -> str:
        """Create searchable text representation for hotel"""
        parts = []
        
        if hotel.get('hotel_name'):
            parts.append(hotel['hotel_name'])
        
        if hotel.get('city'):
            parts.append(f"in {hotel['city']}")
        
        if hotel.get('description'):
            desc = hotel['description']
            if isinstance(desc, list) and desc:
                desc = desc[0]
            parts.append(str(desc))
        
        if hotel.get('rating'):
            rating = hotel['rating']
            if isinstance(rating, list) and rating:
                rating = rating[0]
            parts.append(f"Rating: {rating}")
        
        return ". ".join(str(p) for p in parts)
    
    def _create_restaurant_text(self, restaurant: dict) -> str:
        """Create searchable text representation for restaurant"""
        parts = []
        
        if restaurant.get('restaurant_name'):
            parts.append(restaurant['restaurant_name'])
        
        if restaurant.get('city'):
            parts.append(f"in {restaurant['city']}")
        
        if restaurant.get('description'):
            desc = restaurant['description']
            if isinstance(desc, list) and desc:
                desc = desc[0]
            parts.append(str(desc))
        
        if restaurant.get('rating'):
            rating = restaurant['rating']
            if isinstance(rating, list) and rating:
                rating = rating[0]
            parts.append(f"Rating: {rating}")
        
        return ". ".join(str(p) for p in parts)
    
    def _create_activity_text(self, activity: dict) -> str:
        """Create searchable text representation for activity"""
        parts = []
        
        if activity.get('activity_name'):
            parts.append(activity['activity_name'])
        
        if activity.get('type'):
            parts.append(f"Type: {activity['type']}")
        
        if activity.get('city'):
            parts.append(f"in {activity['city']}")
        
        if activity.get('description'):
            desc = activity['description']
            if isinstance(desc, list) and desc:
                desc = desc[0]
            parts.append(str(desc))
        
        return ". ".join(str(p) for p in parts)
    
    def _create_place_text(self, place: dict) -> str:
        """Create searchable text representation for place"""
        parts = []
        
        if place.get('place_name'):
            parts.append(place['place_name'])
        
        if place.get('city'):
            parts.append(f"in {place['city']}")
        
        if place.get('description'):
            desc = place['description']
            if isinstance(desc, list) and desc:
                desc = desc[0]
            parts.append(str(desc))
        
        if place.get('rating'):
            rating = place['rating']
            if isinstance(rating, list) and rating:
                rating = rating[0]
            parts.append(f"Rating: {rating}")
        
        return ". ".join(str(p) for p in parts)
    
    def _create_cab_text(self, cab: dict) -> str:
        """Create searchable text representation for cab service"""
        parts = []
        
        if cab.get('service_name'):
            parts.append(cab['service_name'])
        
        parts.append("Cab service")
        
        if cab.get('city'):
            parts.append(f"in {cab['city']}")
        
        if cab.get('rating'):
            rating = cab['rating']
            if isinstance(rating, list) and rating:
                rating = rating[0]
            parts.append(f"Rating: {rating}")
        
        return ". ".join(str(p) for p in parts)
    
    def _create_bus_text(self, bus: dict) -> str:
        """Create searchable text representation for bus service"""
        parts = []
        
        if bus.get('service_name'):
            parts.append(bus['service_name'])
        
        parts.append("Bus service")
        
        if bus.get('city'):
            parts.append(f"in {bus['city']}")
        
        if bus.get('rating'):
            rating = bus['rating']
            if isinstance(rating, list) and rating:
                rating = rating[0]
            parts.append(f"Rating: {rating}")
        
        return ". ".join(str(p) for p in parts)
    
    # Data cleaning methods
    
    def _clean_hotel_data(self, hotel: dict) -> dict:
        """Clean hotel data for output"""
        cleaned = {
            'name': hotel.get('hotel_name', 'Unknown Hotel'),
            'city': hotel.get('city', ''),
            'state': hotel.get('state', ''),
        }
        
        # Handle description
        desc = hotel.get('description', '')
        if isinstance(desc, list) and desc:
            desc = desc[0]
        cleaned['description'] = desc
        
        # Handle rating
        rating = hotel.get('rating', 'N/A')
        if isinstance(rating, list) and rating:
            rating = rating[0]
        cleaned['rating'] = rating
        
        return cleaned
    
    def _clean_restaurant_data(self, restaurant: dict) -> dict:
        """Clean restaurant data for output"""
        cleaned = {
            'name': restaurant.get('restaurant_name', 'Unknown Restaurant'),
            'city': restaurant.get('city', ''),
            'state': restaurant.get('state', ''),
        }
        
        # Handle description
        desc = restaurant.get('description', '')
        if isinstance(desc, list) and desc:
            desc = desc[0]
        cleaned['description'] = desc
        
        # Handle rating
        rating = restaurant.get('rating', 'N/A')
        if isinstance(rating, list) and rating:
            rating = rating[0]
        cleaned['rating'] = rating
        
        return cleaned
    
    def _clean_activity_data(self, activity: dict) -> dict:
        """Clean activity data for output"""
        cleaned = {
            'name': activity.get('activity_name', 'Unknown Activity'),
            'type': activity.get('type', ''),
            'city': activity.get('city', ''),
            'state': activity.get('state', ''),
        }
        
        # Handle description
        desc = activity.get('description', '')
        if isinstance(desc, list) and desc:
            desc = desc[0]
        cleaned['description'] = desc
        
        return cleaned
    
    def _clean_place_data(self, place: dict) -> dict:
        """Clean place data for output"""
        cleaned = {
            'name': place.get('place_name', 'Unknown Place'),
            'city': place.get('city', ''),
            'state': place.get('state', ''),
        }
        
        # Handle description
        desc = place.get('description', '')
        if isinstance(desc, list) and desc:
            desc = desc[0]
        cleaned['description'] = desc
        
        # Handle rating
        rating = place.get('rating', 'N/A')
        if isinstance(rating, list) and rating:
            rating = rating[0]
        cleaned['rating'] = rating
        
        return cleaned
    
    def _clean_cab_data(self, cab: dict) -> dict:
        """Clean cab data for output"""
        cleaned = {
            'name': cab.get('service_name', 'Unknown Service'),
            'city': cab.get('city', ''),
        }
        
        # Handle rating
        rating = cab.get('rating', 'N/A')
        if isinstance(rating, list) and rating:
            rating = rating[0]
        cleaned['rating'] = rating
        
        # Handle contact
        contact = cab.get('contact', '')
        if isinstance(contact, list) and contact:
            contact = contact[0]
        cleaned['contact'] = contact
        
        return cleaned
    
    def _clean_bus_data(self, bus: dict) -> dict:
        """Clean bus data for output"""
        cleaned = {
            'name': bus.get('service_name', 'Unknown Service'),
            'city': bus.get('city', ''),
        }
        
        # Handle rating
        rating = bus.get('rating', 'N/A')
        if isinstance(rating, list) and rating:
            rating = rating[0]
        cleaned['rating'] = rating
        
        # Handle contact
        contact = bus.get('contact', '')
        if isinstance(contact, list) and contact:
            contact = contact[0]
        cleaned['contact'] = contact
        
        return cleaned
