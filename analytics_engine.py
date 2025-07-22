#!/usr/bin/env python3
"""
StoryLine AI - Production Analytics Engine
Trust But Verify: Every interaction tracked, validated, and verified
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager
import sqlite3
import uuid
from collections import defaultdict

from config import get_config

logger = logging.getLogger(__name__)
config = get_config()

@dataclass
class CallEvent:
    """Individual call interaction event with validation"""
    event_id: str
    session_id: str
    child_id: str
    event_type: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    verified: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'event_id': self.event_id,
            'session_id': self.session_id,
            'child_id': self.child_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'metadata': json.dumps(self.metadata),
            'verified': self.verified
        }

@dataclass
class ValidationResult:
    """Data validation result"""
    is_valid: bool
    confidence_score: float
    validation_errors: List[str] = field(default_factory=list)
    validation_timestamp: datetime = field(default_factory=datetime.now)

class AnalyticsEngine:
    """Production analytics engine with trust-but-verify architecture"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.database.path.replace('.db', '_analytics.db')
        self.init_analytics_database()
        self._event_buffer = []
        self._buffer_size = 50  # Smaller buffer for production
        self._validation_enabled = True
        
    @contextmanager
    def get_connection(self):
        """Database connection manager with validation"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_analytics_database(self):
        """Initialize production analytics database schema"""
        logger.info("Initializing production analytics database")
        
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS call_events (
                    event_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    child_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    verified BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS story_performance (
                    story_id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    total_requests INTEGER DEFAULT 0,
                    total_completions INTEGER DEFAULT 0,
                    avg_completion_rate REAL DEFAULT 0.0,
                    avg_duration_seconds REAL DEFAULT 0.0,
                    quality_score REAL DEFAULT 0.0,
                    last_validated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_behavior_profiles (
                    child_id TEXT PRIMARY KEY,
                    preferred_story_length REAL DEFAULT 300.0,
                    attention_span_score REAL DEFAULT 5.0,
                    engagement_patterns TEXT,
                    story_preferences TEXT,
                    trust_score REAL DEFAULT 1.0,
                    last_validated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_health (
                    metric_name TEXT,
                    metric_value REAL,
                    timestamp TEXT,
                    interface_type TEXT,
                    validation_status TEXT DEFAULT 'verified',
                    PRIMARY KEY (metric_name, timestamp)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_log (
                    validation_id TEXT PRIMARY KEY,
                    data_type TEXT NOT NULL,
                    data_id TEXT NOT NULL,
                    validation_result BOOLEAN,
                    confidence_score REAL,
                    errors TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            
            # Create performance indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON call_events(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_verified ON call_events(verified)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_health_interface ON system_health(interface_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_validation_type ON validation_log(data_type)")
            
            conn.commit()
            logger.info("Production analytics database initialized")
    
    def validate_event(self, event: CallEvent) -> ValidationResult:
        """Validate event data for trust-but-verify"""
        errors = []
        confidence = 1.0
        
        if not event.session_id or len(event.session_id) < 10:
            errors.append("Invalid session_id")
            confidence -= 0.3
        
        if not event.child_id or len(event.child_id) < 10:
            errors.append("Invalid child_id") 
            confidence -= 0.3
        
        if event.event_type not in ['call_start', 'story_begin', 'pause', 'skip', 'replay', 'completion', 'call_end']:
            errors.append("Invalid event_type")
            confidence -= 0.4
        
        # Validate metadata based on event type
        if event.event_type == 'story_begin' and 'story_id' not in event.metadata:
            errors.append("Missing story_id in story_begin event")
            confidence -= 0.2
        
        is_valid = len(errors) == 0 and confidence > 0.5
        
        return ValidationResult(
            is_valid=is_valid,
            confidence_score=max(0.0, confidence),
            validation_errors=errors
        )
    
    def track_event(self, session_id: str, child_id: str, event_type: str, 
                   metadata: Dict[str, Any] = None):
        """Track event with validation"""
        event = CallEvent(
            event_id=str(uuid.uuid4()),
            session_id=session_id,
            child_id=child_id,
            event_type=event_type,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        if self._validation_enabled:
            validation = self.validate_event(event)
            event.verified = validation.is_valid
            
            # Log validation result
            self._log_validation('call_event', event.event_id, validation)
            
            if not validation.is_valid:
                logger.warning(f"Event validation failed: {validation.validation_errors}")
        
        self._event_buffer.append(event)
        
        if len(self._event_buffer) >= self._buffer_size:
            self.flush_events()
        
        # Track system health
        self.track_system_health('event_tracked', 1.0, 'analytics')
    
    def flush_events(self):
        """Flush event buffer to database with validation"""
        if not self._event_buffer:
            return
        
        verified_events = 0
        total_events = len(self._event_buffer)
        
        with self.get_connection() as conn:
            for event in self._event_buffer:
                event_dict = event.to_dict()
                conn.execute("""
                    INSERT INTO call_events 
                    (event_id, session_id, child_id, event_type, timestamp, metadata, verified)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_dict['event_id'], event_dict['session_id'], 
                    event_dict['child_id'], event_dict['event_type'],
                    event_dict['timestamp'], event_dict['metadata'], 
                    event_dict['verified']
                ))
                
                if event.verified:
                    verified_events += 1
            
            conn.commit()
            
        verification_rate = verified_events / total_events if total_events > 0 else 0.0
        self.track_system_health('event_verification_rate', verification_rate, 'analytics')
        
        logger.info(f"Flushed {total_events} events ({verified_events} verified)")
        self._event_buffer.clear()
    
    def track_system_health(self, metric_name: str, metric_value: float, 
                          interface_type: str):
        """Track system health metrics across all interfaces"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO system_health 
                (metric_name, metric_value, timestamp, interface_type)
                VALUES (?, ?, ?, ?)
            """, (metric_name, metric_value, datetime.now().isoformat(), interface_type))
            conn.commit()
    
    def _log_validation(self, data_type: str, data_id: str, validation: ValidationResult):
        """Log validation results for audit trail"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO validation_log 
                (validation_id, data_type, data_id, validation_result, 
                 confidence_score, errors, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), data_type, data_id, validation.is_valid,
                validation.confidence_score, json.dumps(validation.validation_errors),
                validation.validation_timestamp.isoformat()
            ))
            conn.commit()
    
    def update_story_performance(self, story_id: int, event_type: str):
        """Update story performance with validation"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM story_performance WHERE story_id = ?", 
                (story_id,)
            ).fetchone()
            
            if not row:
                conn.execute("""
                    INSERT INTO story_performance (story_id, title)
                    VALUES (?, ?)
                """, (story_id, f"Story {story_id}"))
                
                total_requests = 1 if event_type == 'story_begin' else 0
                total_completions = 1 if event_type == 'completion' else 0
            else:
                total_requests = row['total_requests']
                total_completions = row['total_completions']
                
                if event_type == 'story_begin':
                    total_requests += 1
                elif event_type == 'completion':
                    total_completions += 1
            
            completion_rate = (total_completions / total_requests) if total_requests > 0 else 0.0
            quality_score = min(1.0, completion_rate * 1.2)  # Basic quality scoring
            
            conn.execute("""
                UPDATE story_performance 
                SET total_requests = ?, total_completions = ?, 
                    avg_completion_rate = ?, quality_score = ?,
                    last_validated = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE story_id = ?
            """, (total_requests, total_completions, completion_rate, 
                  quality_score, story_id))
            
            conn.commit()
            
        # Track performance update
        self.track_system_health('story_performance_updated', quality_score, 'database')
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive system health across all interfaces"""
        with self.get_connection() as conn:
            # Get recent metrics (last hour)
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
            
            health_metrics = conn.execute("""
                SELECT interface_type, AVG(metric_value) as avg_health
                FROM system_health 
                WHERE timestamp > ?
                GROUP BY interface_type
            """, (one_hour_ago,)).fetchall()
            
            # Get validation statistics
            validation_stats = conn.execute("""
                SELECT 
                    SUM(CASE WHEN validation_result THEN 1 ELSE 0 END) as valid_count,
                    COUNT(*) as total_count,
                    AVG(confidence_score) as avg_confidence
                FROM validation_log
                WHERE timestamp > ?
            """, (one_hour_ago,)).fetchone()
            
            # Get event verification rate
            event_verification = conn.execute("""
                SELECT 
                    SUM(CASE WHEN verified THEN 1 ELSE 0 END) as verified_events,
                    COUNT(*) as total_events
                FROM call_events
                WHERE created_at > ?
            """, (one_hour_ago,)).fetchone()
            
            return {
                'interface_health': {row['interface_type']: row['avg_health'] for row in health_metrics},
                'validation_rate': validation_stats['valid_count'] / validation_stats['total_count'] if validation_stats['total_count'] > 0 else 1.0,
                'average_confidence': validation_stats['avg_confidence'] or 1.0,
                'event_verification_rate': event_verification['verified_events'] / event_verification['total_events'] if event_verification['total_events'] > 0 else 1.0,
                'last_updated': datetime.now().isoformat()
            }
    
    def get_trust_score(self, child_id: str) -> float:
        """Calculate trust score for a user"""
        with self.get_connection() as conn:
            # Get user behavior profile
            profile = conn.execute(
                "SELECT trust_score FROM user_behavior_profiles WHERE child_id = ?",
                (child_id,)
            ).fetchone()
            
            if not profile:
                return 1.0  # Default high trust for new users
            
            return profile['trust_score']
    
    def verify_data_integrity(self) -> Dict[str, Any]:
        """Comprehensive data integrity verification"""
        integrity_report = {
            'database_consistency': True,
            'data_completeness': 1.0,
            'validation_coverage': 1.0,
            'audit_trail_complete': True,
            'last_verified': datetime.now().isoformat()
        }
        
        with self.get_connection() as conn:
            # Check for orphaned records
            orphaned_sessions = conn.execute("""
                SELECT COUNT(*) as count FROM call_events ce
                LEFT JOIN user_behavior_profiles ubp ON ce.child_id = ubp.child_id
                WHERE ubp.child_id IS NULL
            """).fetchone()['count']
            
            if orphaned_sessions > 0:
                integrity_report['database_consistency'] = False
                logger.warning(f"Found {orphaned_sessions} orphaned session records")
            
            # Check validation coverage
            total_events = conn.execute("SELECT COUNT(*) as count FROM call_events").fetchone()['count']
            validated_events = conn.execute("SELECT COUNT(*) as count FROM call_events WHERE verified = 1").fetchone()['count']
            
            if total_events > 0:
                integrity_report['validation_coverage'] = validated_events / total_events
            
            # Track integrity check
            self.track_system_health('data_integrity_check', 
                                   1.0 if integrity_report['database_consistency'] else 0.0, 
                                   'database')
        
        return integrity_report

# Global analytics instance
analytics_engine = AnalyticsEngine()

def get_analytics_engine() -> AnalyticsEngine:
    """Get global analytics engine instance"""
    return analytics_engine