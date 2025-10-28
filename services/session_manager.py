"""
Session Manager Service
Manages user sessions and conversation history
"""

from typing import Dict, List, Optional
import json
import os
from datetime import datetime
from loguru import logger


class SessionManager:
    """
    Service for managing user sessions and conversation history
    Maintains session state and chat memory
    """
    
    def __init__(self, storage_dir: str = "data/sessions"):
        """
        Initialize session manager
        
        Args:
            storage_dir: Directory to store session data
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # In-memory cache of active sessions
        self.sessions = {}
        
        logger.info(f"Session Manager initialized with storage: {storage_dir}")
    
    def create_session(self, session_id: str, file_paths: List[str]) -> Dict:
        """
        Create a new session
        
        Args:
            session_id: Unique session identifier
            file_paths: List of uploaded file paths
            
        Returns:
            Session data
        """
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "file_paths": file_paths,
            "history": [],
            "metadata": {}
        }
        
        self.sessions[session_id] = session_data
        self._save_session(session_id)
        
        logger.info(f"Created session: {session_id}")
        return session_data
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session exists
        """
        if session_id in self.sessions:
            return True
        
        # Check if session file exists
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(session_file):
            self._load_session(session_id)
            return True
        
        return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None
        """
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Try to load from disk
        if self._load_session(session_id):
            return self.sessions[session_id]
        
        return None
    
    def add_to_history(self, session_id: str, role: str, content: str):
        """
        Add message to conversation history
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        if not self.session_exists(session_id):
            logger.warning(f"Session {session_id} does not exist")
            return
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.sessions[session_id]["history"].append(message)
        self._save_session(session_id)
        
        logger.debug(f"Added {role} message to session {session_id}")
    
    def get_history(self, session_id: str, last_n: Optional[int] = None) -> List[Dict]:
        """
        Get conversation history
        
        Args:
            session_id: Session identifier
            last_n: Number of recent messages to return (None for all)
            
        Returns:
            List of messages
        """
        if not self.session_exists(session_id):
            return []
        
        history = self.sessions[session_id]["history"]
        
        if last_n:
            return history[-last_n:]
        
        return history
    
    def update_metadata(self, session_id: str, key: str, value: any):
        """
        Update session metadata
        
        Args:
            session_id: Session identifier
            key: Metadata key
            value: Metadata value
        """
        if not self.session_exists(session_id):
            logger.warning(f"Session {session_id} does not exist")
            return
        
        self.sessions[session_id]["metadata"][key] = value
        self._save_session(session_id)
    
    def delete_session(self, session_id: str):
        """
        Delete a session
        
        Args:
            session_id: Session identifier
        """
        # Remove from memory
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        # Remove file
        session_file = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(session_file):
            os.remove(session_file)
            logger.info(f"Deleted session: {session_id}")
    
    def list_sessions(self) -> List[str]:
        """
        List all session IDs
        
        Returns:
            List of session IDs
        """
        sessions = []
        
        # Get from memory
        sessions.extend(self.sessions.keys())
        
        # Get from disk
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                session_id = filename[:-5]  # Remove .json
                if session_id not in sessions:
                    sessions.append(session_id)
        
        return sessions
    
    def _save_session(self, session_id: str):
        """Save session data to disk"""
        try:
            session_file = os.path.join(self.storage_dir, f"{session_id}.json")
            
            with open(session_file, 'w') as f:
                json.dump(self.sessions[session_id], f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {str(e)}")
    
    def _load_session(self, session_id: str) -> bool:
        """Load session data from disk"""
        try:
            session_file = os.path.join(self.storage_dir, f"{session_id}.json")
            
            if not os.path.exists(session_file):
                return False
            
            with open(session_file, 'r') as f:
                self.sessions[session_id] = json.load(f)
            
            logger.debug(f"Loaded session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {str(e)}")
            return False