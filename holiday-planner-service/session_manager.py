import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session Manager - Handle temporary conversation sessions with 2-hour TTL
    
    Responsibility: Create, manage, and cleanup conversation sessions with in-memory storage
    Thread-safe operations for concurrent access
    """
    
    def __init__(self, timeout_hours: int = 2, max_history: int = 20, max_sessions: int = 1000):
        """
        Initialize Session Manager
        
        Args:
            timeout_hours (int): Session expiration time in hours (default: 2)
            max_history (int): Maximum messages to keep per session (default: 20)
            max_sessions (int): Maximum concurrent sessions allowed (default: 1000)
        """
        self.sessions: Dict[str, dict] = {}
        self.timeout_hours = timeout_hours
        self.max_history = max_history
        self.max_sessions = max_sessions
        self.lock = Lock()
        
        logger.info(f"SessionManager initialized - timeout: {timeout_hours}h, "
                   f"max_history: {max_history}, max_sessions: {max_sessions}")
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation session
        
        Args:
            user_id (str, optional): User identifier for tracking
            
        Returns:
            str: Unique session ID (UUID)
            
        Raises:
            RuntimeError: If maximum concurrent sessions limit reached
        """
        with self.lock:
            # Check session limit
            if len(self.sessions) >= self.max_sessions:
                logger.warning(f"Maximum session limit reached ({self.max_sessions})")
                # Try cleanup first
                self.cleanup_expired_sessions()
                
                # Still at limit after cleanup
                if len(self.sessions) >= self.max_sessions:
                    raise RuntimeError(f"Maximum concurrent sessions limit reached ({self.max_sessions})")
            
            session_id = str(uuid.uuid4())
            now = datetime.now()
            
            self.sessions[session_id] = {
                'session_id': session_id,
                'user_id': user_id,
                'created_at': now,
                'last_activity': now,
                'expires_at': now + timedelta(hours=self.timeout_hours),
                'messages': [],
                'context': {}
            }
            
            logger.info(f"Session created: {session_id}, user_id: {user_id}")
            return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Retrieve session by ID
        
        Args:
            session_id (str): Session UUID
            
        Returns:
            dict or None: Session data if exists and not expired, else None
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if not session:
                logger.debug(f"Session not found: {session_id}")
                return None
            
            # Check expiration
            if self.is_session_expired(session_id):
                logger.info(f"Session expired: {session_id}")
                self.delete_session(session_id)
                return None
            
            return session
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add a message to session conversation history
        
        Args:
            session_id (str): Session UUID
            role (str): Message role ('user' or 'assistant')
            content (str): Message content
            
        Returns:
            bool: True if message added successfully, False otherwise
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if not session:
                logger.warning(f"Cannot add message - session not found: {session_id}")
                return False
            
            # Check expiration
            if self.is_session_expired(session_id):
                logger.warning(f"Cannot add message - session expired: {session_id}")
                self.delete_session(session_id)
                return False
            
            # Add message
            message = {
                'role': role,
                'content': content,
                'timestamp': datetime.now()
            }
            session['messages'].append(message)
            
            # Update last activity
            session['last_activity'] = datetime.now()
            
            # Trim history if exceeds max_history
            if len(session['messages']) > self.max_history:
                session['messages'] = session['messages'][-self.max_history:]
                logger.debug(f"Trimmed session history to {self.max_history} messages")
            
            logger.debug(f"Message added to session {session_id} - role: {role}, "
                        f"total messages: {len(session['messages'])}")
            return True
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[dict]:
        """
        Get conversation history for a session
        
        Args:
            session_id (str): Session UUID
            limit (int, optional): Maximum number of recent messages to return
            
        Returns:
            list: List of messages with role, content, and timestamp
        """
        session = self.get_session(session_id)
        
        if not session:
            return []
        
        messages = session['messages']
        
        if limit and limit > 0:
            return messages[-limit:]
        
        return messages
    
    def update_context(self, session_id: str, context_updates: dict) -> bool:
        """
        Update session context (e.g., current destination, preferences)
        
        Args:
            session_id (str): Session UUID
            context_updates (dict): Context fields to update
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if not session:
                logger.warning(f"Cannot update context - session not found: {session_id}")
                return False
            
            if self.is_session_expired(session_id):
                logger.warning(f"Cannot update context - session expired: {session_id}")
                self.delete_session(session_id)
                return False
            
            # Update context
            session['context'].update(context_updates)
            session['last_activity'] = datetime.now()
            
            logger.debug(f"Context updated for session {session_id}: {context_updates}")
            return True
    
    def get_context(self, session_id: str) -> dict:
        """
        Get session context
        
        Args:
            session_id (str): Session UUID
            
        Returns:
            dict: Session context or empty dict if not found
        """
        session = self.get_session(session_id)
        return session['context'] if session else {}
    
    def is_session_expired(self, session_id: str) -> bool:
        """
        Check if session has expired (beyond 2-hour TTL)
        
        Args:
            session_id (str): Session UUID
            
        Returns:
            bool: True if expired, False otherwise
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return True
        
        return datetime.now() > session['expires_at']
    
    def delete_session(self, session_id: str) -> bool:
        """
        Manually delete a session
        
        Args:
            session_id (str): Session UUID
            
        Returns:
            bool: True if deleted, False if not found
        """
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Session deleted: {session_id}")
                return True
            
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions from memory
        
        Returns:
            int: Number of sessions removed
        """
        with self.lock:
            now = datetime.now()
            expired_sessions = [
                sid for sid, session in self.sessions.items()
                if now > session['expires_at']
            ]
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
            return len(expired_sessions)
    
    def get_active_sessions_count(self) -> int:
        """
        Get count of active sessions
        
        Returns:
            int: Number of active sessions
        """
        return len(self.sessions)
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        Get session metadata (without full message history)
        
        Args:
            session_id (str): Session UUID
            
        Returns:
            dict or None: Session info with metadata
        """
        session = self.get_session(session_id)
        
        if not session:
            return None
        
        return {
            'session_id': session['session_id'],
            'user_id': session['user_id'],
            'created_at': session['created_at'].isoformat(),
            'last_activity': session['last_activity'].isoformat(),
            'expires_at': session['expires_at'].isoformat(),
            'message_count': len(session['messages']),
            'context': session['context']
        }
    
    def get_all_sessions_info(self) -> List[dict]:
        """
        Get metadata for all active sessions
        
        Returns:
            list: List of session metadata
        """
        with self.lock:
            return [
                self.get_session_info(session_id)
                for session_id in self.sessions.keys()
            ]
    
    # Itinerary tracking methods
    
    def store_itinerary(self, session_id: str, itinerary: dict, intent: dict = None) -> bool:
        """
        Store generated itinerary in session context for follow-up queries
        
        Args:
            session_id (str): Session UUID
            itinerary (dict): Complete itinerary structure with day-wise breakdown
            intent (dict): Original intent used to generate the itinerary
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if not session:
                logger.warning(f"Cannot store itinerary - session not found: {session_id}")
                return False
            
            if self.is_session_expired(session_id):
                logger.warning(f"Cannot store itinerary - session expired: {session_id}")
                self.delete_session(session_id)
                return False
            
            # Store itinerary and related metadata
            session['context']['last_itinerary'] = {
                'itinerary': itinerary,
                'intent': intent or {},
                'destination': intent.get('destination') if intent else None,
                'days': intent.get('days') if intent else len(itinerary.get('days', [])),
                'stored_at': datetime.now().isoformat()
            }
            
            session['last_activity'] = datetime.now()
            
            logger.info(f"Itinerary stored in session {session_id} for destination: {intent.get('destination') if intent else 'Unknown'}")
            return True
    
    def get_itinerary(self, session_id: str) -> Optional[dict]:
        """
        Retrieve stored itinerary from session
        
        Args:
            session_id (str): Session UUID
            
        Returns:
            dict or None: Stored itinerary data or None if not found
        """
        session = self.get_session(session_id)
        
        if not session:
            return None
        
        return session['context'].get('last_itinerary')
    
    def get_itinerary_day(self, session_id: str, day_number: int) -> Optional[dict]:
        """
        Retrieve specific day from stored itinerary
        
        Args:
            session_id (str): Session UUID
            day_number (int): Day number (1-indexed)
            
        Returns:
            dict or None: Day details or None if not found
        """
        itinerary_data = self.get_itinerary(session_id)
        
        if not itinerary_data:
            logger.debug(f"No itinerary found in session {session_id}")
            return None
        
        itinerary = itinerary_data.get('itinerary', {})
        days = itinerary.get('days', [])
        
        # Day numbers are 1-indexed, array is 0-indexed
        if 1 <= day_number <= len(days):
            return days[day_number - 1]
        
        logger.debug(f"Day {day_number} not found in itinerary (total days: {len(days)})")
        return None
    
    def has_itinerary(self, session_id: str) -> bool:
        """
        Check if session has a stored itinerary
        
        Args:
            session_id (str): Session UUID
            
        Returns:
            bool: True if itinerary exists, False otherwise
        """
        return self.get_itinerary(session_id) is not None
