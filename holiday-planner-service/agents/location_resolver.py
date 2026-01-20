import logging
from typing import Optional, List, Dict, Tuple
from rapidfuzz import fuzz, process
from pymongo import MongoClient

logger = logging.getLogger(__name__)


class LocationResolver:
    """
    Location Resolution Service - Handle fuzzy matching, aliases, and geographic hierarchy
    
    Responsibilities:
    1. Resolve spelling variations and aliases (e.g., Vizag -> Visakhapatnam)
    2. Handle phonetic and fuzzy matching for typos
    3. Map state names to cities for hierarchical queries
    4. Provide best-match suggestions when exact matches fail
    """
    
    # Location aliases - common abbreviations and alternate names
    LOCATION_ALIASES = {
        # Common city aliases
        'vizag': 'Visakhapatnam',
        'vishakapatnam': 'Visakhapatnam',
        'vishakhapatnam': 'Visakhapatnam',
        'bombay': 'Mumbai',
        'calcutta': 'Kolkata',
        'madras': 'Chennai',
        'bangalore': 'Bengaluru',
        'banaras': 'Varanasi',
        'benares': 'Varanasi',
        'kashi': 'Varanasi',
        'pondicherry': 'Puducherry',
        'pondy': 'Puducherry',
        'ooty': 'Udhagamandalam',
        'trivandrum': 'Thiruvananthapuram',
        'cochin': 'Kochi',
        'coonoor': 'Coonoor',
        'shimoga': 'Shivamogga',
        'mysuru': 'Mysore',
        'mangaluru': 'Mangalore',
        'kozhikode': 'Calicut',
        'calicut': 'Kozhikode',
        
        # State aliases
        'ap': 'Arunachal Pradesh',
        'ar': 'Arunachal Pradesh',
        'arunachal': 'Arunachal Pradesh',
        'hp': 'Himachal Pradesh',
        'himachal': 'Himachal Pradesh',
        'up': 'Uttar Pradesh',
        'mp': 'Madhya Pradesh',
        'uk': 'Uttarakhand',
        'wb': 'West Bengal',
        'tn': 'Tamil Nadu',
        'kl': 'Kerala',
        'ka': 'Karnataka',
        'mh': 'Maharashtra',
        'rj': 'Rajasthan',
        'gj': 'Gujarat',
        'pb': 'Punjab',
        'hr': 'Haryana',
        'jh': 'Jharkhand',
        'or': 'Odisha',
        'cg': 'Chhattisgarh',
        'goa': 'Goa',
    }
    
    # State to cities mapping - hierarchical location understanding
    STATE_TO_CITIES = {
        'Arunachal Pradesh': ['Tawang', 'Itanagar', 'Ziro', 'Bomdila', 'Pasighat'],
        'Himachal Pradesh': ['Manali', 'Shimla', 'Dharamshala', 'Kasauli', 'Kullu', 'Dalhousie'],
        'Uttarakhand': ['Nainital', 'Mussoorie', 'Rishikesh', 'Haridwar', 'Dehradun', 'Auli'],
        'Jammu and Kashmir': ['Srinagar', 'Gulmarg', 'Pahalgam', 'Jammu', 'Leh', 'Ladakh'],
        'Ladakh': ['Leh', 'Nubra Valley', 'Pangong Lake'],
        'Punjab': ['Amritsar', 'Chandigarh', 'Ludhiana', 'Patiala'],
        'Haryana': ['Gurugram', 'Faridabad', 'Panipat'],
        'Delhi': ['New Delhi', 'Delhi'],
        'Rajasthan': ['Jaipur', 'Udaipur', 'Jodhpur', 'Jaisalmer', 'Pushkar', 'Mount Abu'],
        'Uttar Pradesh': ['Agra', 'Varanasi', 'Lucknow', 'Mathura', 'Vrindavan'],
        'Bihar': ['Patna', 'Gaya', 'Bodhgaya'],
        'Sikkim': ['Gangtok', 'Pelling', 'Lachung'],
        'West Bengal': ['Kolkata', 'Darjeeling', 'Siliguri', 'Dooars'],
        'Odisha': ['Puri', 'Bhubaneswar', 'Konark'],
        'Jharkhand': ['Ranchi', 'Jamshedpur'],
        'Chhattisgarh': ['Raipur', 'Bastar'],
        'Madhya Pradesh': ['Bhopal', 'Indore', 'Gwalior', 'Khajuraho', 'Ujjain'],
        'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara', 'Dwarka', 'Somnath', 'Rann of Kutch'],
        'Maharashtra': ['Mumbai', 'Pune', 'Nashik', 'Aurangabad', 'Lonavala', 'Mahabaleshwar'],
        'Goa': ['North Goa', 'South Goa', 'Panaji', 'Margao'],
        'Karnataka': ['Bengaluru', 'Mysore', 'Coorg', 'Hampi', 'Mangalore', 'Gokarna'],
        'Kerala': ['Kochi', 'Munnar', 'Alleppey', 'Wayanad', 'Kovalam', 'Thekkady', 'Kumarakom'],
        'Tamil Nadu': ['Chennai', 'Ooty', 'Kodaikanal', 'Madurai', 'Rameswaram', 'Kanyakumari'],
        'Andhra Pradesh': ['Visakhapatnam', 'Tirupati', 'Vijayawada', 'Hyderabad'],
        'Telangana': ['Hyderabad', 'Warangal'],
        'Meghalaya': ['Shillong', 'Cherrapunji', 'Dawki'],
        'Assam': ['Guwahati', 'Kaziranga'],
        'Nagaland': ['Kohima', 'Dimapur'],
        'Manipur': ['Imphal'],
        'Mizoram': ['Aizawl'],
        'Tripura': ['Agartala'],
        'Andaman and Nicobar Islands': ['Port Blair', 'Havelock Island', 'Neil Island'],
        'Lakshadweep': ['Agatti', 'Kavaratti'],
    }
    
    def __init__(self, mongodb_uri: str = None):
        """
        Initialize LocationResolver
        
        Args:
            mongodb_uri (str): Optional MongoDB URI to fetch dynamic locations
        """
        self.mongodb_uri = mongodb_uri
        self.db_locations = []
        
        # Build a comprehensive list of all known locations
        self.known_locations = set()
        
        # Add alias targets
        self.known_locations.update(self.LOCATION_ALIASES.values())
        
        # Add states
        self.known_locations.update(self.STATE_TO_CITIES.keys())
        
        # Add cities
        for cities in self.STATE_TO_CITIES.values():
            self.known_locations.update(cities)
        
        # Fetch locations from database if available
        if mongodb_uri:
            self._fetch_db_locations()
        
        self.known_locations = sorted(list(self.known_locations))
        logger.info(f"LocationResolver initialized with {len(self.known_locations)} known locations")
    
    def _fetch_db_locations(self):
        """Fetch unique locations from MongoDB"""
        try:
            client = MongoClient(self.mongodb_uri)
            db = client.get_default_database()
            
            # Get unique cities from all collections
            for collection_name in ['hotels', 'restaurants', 'places', 'activities']:
                if collection_name in db.list_collection_names():
                    cities = db[collection_name].distinct('city')
                    self.db_locations.extend(cities)
                    self.known_locations.update(cities)
            
            logger.info(f"Fetched {len(self.db_locations)} locations from database")
            
        except Exception as e:
            logger.warning(f"Could not fetch locations from database: {e}")
    
    def resolve_location(self, user_input: str, threshold: int = 80) -> Optional[str]:
        """
        Resolve a location from user input using multiple strategies
        
        Strategies (in order):
        1. Check exact match in aliases
        2. Check exact match (case-insensitive) in known locations
        3. Fuzzy match against known locations
        4. Return None if no good match found
        
        Args:
            user_input (str): User's location input
            threshold (int): Minimum fuzzy match score (0-100)
            
        Returns:
            str: Resolved location name or None
        """
        if not user_input:
            return None
        
        user_input_lower = user_input.strip().lower()
        user_input_title = user_input.strip().title()
        
        logger.info(f"Resolving location: {user_input}")
        
        # Strategy 1: Check aliases
        if user_input_lower in self.LOCATION_ALIASES:
            resolved = self.LOCATION_ALIASES[user_input_lower]
            logger.info(f"Resolved via alias: {user_input} -> {resolved}")
            return resolved
        
        # Strategy 2: Exact match (case-insensitive)
        for location in self.known_locations:
            if location.lower() == user_input_lower:
                logger.info(f"Resolved via exact match: {user_input} -> {location}")
                return location
        
        # Strategy 3: Fuzzy matching
        match_result = process.extractOne(
            user_input_title,
            self.known_locations,
            scorer=fuzz.WRatio,
            score_cutoff=threshold
        )
        
        if match_result:
            matched_location, score, _ = match_result
            logger.info(f"Resolved via fuzzy match: {user_input} -> {matched_location} (score: {score})")
            return matched_location
        
        logger.warning(f"Could not resolve location: {user_input}")
        return None
    
    def resolve_with_confidence(self, user_input: str) -> Tuple[Optional[str], float, str]:
        """
        Resolve location with confidence score and method
        
        Args:
            user_input (str): User's location input
            
        Returns:
            tuple: (resolved_location, confidence_score, resolution_method)
        """
        if not user_input:
            return None, 0.0, "none"
        
        user_input_lower = user_input.strip().lower()
        user_input_title = user_input.strip().title()
        
        # Check aliases
        if user_input_lower in self.LOCATION_ALIASES:
            return self.LOCATION_ALIASES[user_input_lower], 1.0, "alias"
        
        # Exact match
        for location in self.known_locations:
            if location.lower() == user_input_lower:
                return location, 1.0, "exact"
        
        # Fuzzy match
        match_result = process.extractOne(
            user_input_title,
            self.known_locations,
            scorer=fuzz.WRatio
        )
        
        if match_result:
            matched_location, score, _ = match_result
            confidence = score / 100.0
            return matched_location, confidence, "fuzzy"
        
        return None, 0.0, "none"
    
    def get_cities_for_state(self, state: str) -> List[str]:
        """
        Get list of cities for a given state
        
        Args:
            state (str): State name
            
        Returns:
            list: List of city names in that state
        """
        # First resolve the state name
        resolved_state = self.resolve_location(state)
        
        if resolved_state and resolved_state in self.STATE_TO_CITIES:
            cities = self.STATE_TO_CITIES[resolved_state]
            logger.info(f"Found {len(cities)} cities for state: {resolved_state}")
            return cities
        
        logger.warning(f"No cities found for state: {state}")
        return []
    
    def is_state(self, location: str) -> bool:
        """
        Check if a location is a state
        
        Args:
            location (str): Location name
            
        Returns:
            bool: True if location is a state
        """
        resolved = self.resolve_location(location)
        return resolved in self.STATE_TO_CITIES
    
    def get_suggestions(self, user_input: str, limit: int = 5) -> List[Tuple[str, float]]:
        """
        Get location suggestions for ambiguous input
        
        Args:
            user_input (str): User's location input
            limit (int): Maximum number of suggestions
            
        Returns:
            list: List of (location, score) tuples
        """
        if not user_input:
            return []
        
        user_input_title = user_input.strip().title()
        
        matches = process.extract(
            user_input_title,
            self.known_locations,
            scorer=fuzz.WRatio,
            limit=limit
        )
        
        suggestions = [(match[0], match[1] / 100.0) for match in matches if match[1] >= 60]
        logger.info(f"Generated {len(suggestions)} suggestions for: {user_input}")
        
        return suggestions
    
    def get_location_info(self, location: str) -> Dict:
        """
        Get comprehensive information about a location
        
        Args:
            location (str): Location name
            
        Returns:
            dict: Location information including type, hierarchy, etc.
        """
        resolved = self.resolve_location(location)
        
        if not resolved:
            return {
                'resolved': None,
                'type': 'unknown',
                'is_state': False,
                'parent_state': None,
                'child_cities': []
            }
        
        # Check if it's a state
        if resolved in self.STATE_TO_CITIES:
            return {
                'resolved': resolved,
                'type': 'state',
                'is_state': True,
                'parent_state': None,
                'child_cities': self.STATE_TO_CITIES[resolved]
            }
        
        # Check if it's a city and find parent state
        parent_state = None
        for state, cities in self.STATE_TO_CITIES.items():
            if resolved in cities:
                parent_state = state
                break
        
        return {
            'resolved': resolved,
            'type': 'city',
            'is_state': False,
            'parent_state': parent_state,
            'child_cities': []
        }
