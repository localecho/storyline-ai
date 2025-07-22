#!/usr/bin/env python3
"""
StoryLine AI - Trust But Verify Integration Core
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from config import get_config
from analytics_engine import get_analytics_engine
from validation_layer import get_validation_layer
from quality_assurance import get_automated_qa
from realtime_verification import get_realtime_verification

logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    """System status summary"""
    overall_health: float
    verification_rate: float
    quality_score: float
    active_alerts: int
    last_check: str
    
    @property
    def is_healthy(self) -> bool:
        return self.overall_health >= 0.9

class TrustButVerifyCore:
    """Core Trust But Verify functionality"""
    
    def __init__(self):
        self.analytics = get_analytics_engine()
        self.validator = get_validation_layer()
        self.qa_system = get_automated_qa()
        self.realtime = get_realtime_verification()
        self._initialized = False
    
    def initialize(self):
        """Initialize the system"""
        if self._initialized:
            return
        
        logger.info("Initializing Trust But Verify Core")
        
        # Start real-time verification
        self.realtime.start_realtime_processing()
        
        # Start QA monitoring
        self.qa_system.start_continuous_qa(30)
        
        self._initialized = True
        logger.info("Trust But Verify Core initialized")
    
    def verify_data(self, interface: str, data_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Verify data across all systems"""
        # Real-time verification
        rt_result = self.realtime.verify_realtime(data_type, payload)
        
        # Validation
        val_result = self.validator.validate_interface_data(interface, payload)
        
        # Track event
        self.analytics.track_event(
            payload.get('session_id', 'system'),
            payload.get('child_id', 'system'), 
            f'{interface}_verification',
            {'data_type': data_type}
        )
        
        return {
            'verified': rt_result.verification_status.value == 'verified',
            'validation_passed': val_result.is_valid,
            'confidence': min(rt_result.confidence_score, val_result.confidence_score),
            'errors': val_result.errors,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_status(self) -> SystemStatus:
        """Get system status"""
        qa_summary = self.qa_system.get_qa_summary()
        rt_metrics = self.realtime.get_verification_metrics(60)
        alerts = self.realtime.get_active_alerts()
        
        return SystemStatus(
            overall_health=qa_summary.get('latest_quality_score', 0.8),
            verification_rate=rt_metrics.get('success_rate', 0.95),
            quality_score=qa_summary.get('latest_quality_score', 0.8),
            active_alerts=len(alerts),
            last_check=datetime.now().isoformat()
        )

# Global instance
tbv_core = TrustButVerifyCore()

def get_tbv_core() -> TrustButVerifyCore:
    """Get Trust But Verify core instance"""
    return tbv_core

def initialize_tbv():
    """Initialize Trust But Verify"""
    tbv_core.initialize()

def verify_phone_call(session_id: str, phone: str, duration: int) -> Dict[str, Any]:
    """Verify phone call data"""
    return tbv_core.verify_data('phone', 'phone_call', {
        'session_id': session_id,
        'phone_number': phone,
        'duration_seconds': duration
    })

def verify_story(content: str, age: int, interests: List[str]) -> Dict[str, Any]:
    """Verify story content"""
    return tbv_core.verify_data('ai', 'story_generation', {
        'story_content': content,
        'child_age': age,
        'child_interests': interests
    })

def get_health() -> Dict[str, Any]:
    """Get system health"""
    status = tbv_core.get_status()
    return {
        'healthy': status.is_healthy,
        'health_score': status.overall_health,
        'verification_rate': status.verification_rate,
        'active_alerts': status.active_alerts,
        'last_check': status.last_check
    }