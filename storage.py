"""In-memory storage for CrewInsight MVP."""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from threading import Lock

from models import AnalysisResult, AnalysisRequest


class InMemoryStorage:
    """Thread-safe in-memory storage for analysis results."""
    
    def __init__(self, max_results: int = 1000, ttl_hours: int = 24):
        self.max_results = max_results
        self.ttl_hours = ttl_hours
        self._results: Dict[str, AnalysisResult] = {}
        self._lock = Lock()
    
    def create_analysis(self, request: AnalysisRequest) -> str:
        """Create a new analysis request and return its ID."""
        analysis_id = str(uuid.uuid4())
        
        result = AnalysisResult(
            id=analysis_id,
            request=request,
            status="processing",
            created_at=datetime.now()
        )
        
        with self._lock:
            # Clean up old results if we're at capacity
            if len(self._results) >= self.max_results:
                self._cleanup_old_results()
            
            self._results[analysis_id] = result
        
        return analysis_id
    
    def get_analysis(self, analysis_id: str) -> Optional[AnalysisResult]:
        """Get analysis result by ID."""
        with self._lock:
            result = self._results.get(analysis_id)
            
            # Check if result has expired
            if result and self._is_expired(result):
                del self._results[analysis_id]
                return None
            
            return result
    
    def update_analysis(self, analysis_id: str, **updates) -> bool:
        """Update analysis result with new data."""
        with self._lock:
            if analysis_id not in self._results:
                return False
            
            result = self._results[analysis_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(result, key):
                    setattr(result, key, value)
            
            # Update completion timestamp if status changed to completed
            if updates.get('status') == 'completed':
                result.completed_at = datetime.now()
            
            return True
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete analysis result."""
        with self._lock:
            if analysis_id in self._results:
                del self._results[analysis_id]
                return True
            return False
    
    def list_analyses(self, limit: int = 50) -> list[AnalysisResult]:
        """List recent analyses."""
        with self._lock:
            # Clean up expired results first
            self._cleanup_old_results()
            
            # Sort by creation time (newest first) and return limited results
            sorted_results = sorted(
                self._results.values(),
                key=lambda x: x.created_at,
                reverse=True
            )
            
            return sorted_results[:limit]
    
    def _is_expired(self, result: AnalysisResult) -> bool:
        """Check if result has expired based on TTL."""
        expiry_time = result.created_at + timedelta(hours=self.ttl_hours)
        return datetime.now() > expiry_time
    
    def _cleanup_old_results(self):
        """Remove expired results."""
        expired_ids = [
            analysis_id for analysis_id, result in self._results.items()
            if self._is_expired(result)
        ]
        
        for analysis_id in expired_ids:
            del self._results[analysis_id]


# Global storage instance
storage = InMemoryStorage()
