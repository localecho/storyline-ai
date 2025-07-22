#!/usr/bin/env python3
"""
StoryLine AI - Data Validation Layer
Trust But Verify: Comprehensive validation across all interfaces
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re
import sqlite3
from contextlib import contextmanager

from config import get_config
from analytics_engine import get_analytics_engine

logger = logging.getLogger(__name__)
config = get_config()

class ValidationLevel(Enum):
    """Validation strictness levels"""
    BASIC = "basic"
    STANDARD = "standard" 
    STRICT = "strict"
    PARANOID = "paranoid"

class InterfaceType(Enum):
    """Interface types for validation"""
    PHONE = "phone"
    DATABASE = "database"
    AI = "ai"
    ANALYTICS = "analytics"
    BUSINESS = "business"

@dataclass
class ValidationRule:
    """Individual validation rule"""
    name: str
    validator: Callable
    error_message: str
    weight: float = 1.0
    interface: InterfaceType = InterfaceType.DATABASE
    level: ValidationLevel = ValidationLevel.STANDARD

@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    interface_type: str
    data_type: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    confidence_score: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        return self.passed_checks / self.total_checks if self.total_checks > 0 else 0.0
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed"""
        return self.success_rate >= 0.95 and self.confidence_score >= 0.8

class DataValidationLayer:
    """Comprehensive data validation system"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.analytics = get_analytics_engine()
        self._validation_rules = self._initialize_validation_rules()
        
    def _initialize_validation_rules(self) -> Dict[str, List[ValidationRule]]:
        """Initialize validation rules for each interface"""
        return {
            'phone': self._get_phone_validation_rules(),
            'database': self._get_database_validation_rules(), 
            'ai': self._get_ai_validation_rules(),
            'analytics': self._get_analytics_validation_rules(),
            'business': self._get_business_validation_rules()
        }
    
    def _get_phone_validation_rules(self) -> List[ValidationRule]:
        """Validation rules for phone interface"""
        return [
            ValidationRule(
                name="valid_phone_number",
                validator=lambda x: self._validate_phone_number(x.get('phone_number', '')),
                error_message="Invalid phone number format",
                interface=InterfaceType.PHONE
            ),
            ValidationRule(
                name="call_duration_reasonable",
                validator=lambda x: 5 <= x.get('duration_seconds', 0) <= 1800,  # 5 sec to 30 min
                error_message="Call duration outside reasonable range",
                interface=InterfaceType.PHONE
            ),
            ValidationRule(
                name="session_id_format",
                validator=lambda x: self._validate_session_id(x.get('session_id', '')),
                error_message="Invalid session ID format",
                interface=InterfaceType.PHONE
            ),
            ValidationRule(
                name="audio_quality_check",
                validator=lambda x: x.get('audio_quality_score', 1.0) >= 0.7,
                error_message="Audio quality below acceptable threshold",
                interface=InterfaceType.PHONE,
                level=ValidationLevel.STRICT
            )
        ]
    
    def _get_database_validation_rules(self) -> List[ValidationRule]:
        """Validation rules for database interface"""
        return [
            ValidationRule(
                name="child_id_format",
                validator=lambda x: self._validate_uuid(x.get('child_id', '')),
                error_message="Invalid child ID format",
                interface=InterfaceType.DATABASE
            ),
            ValidationRule(
                name="child_age_range",
                validator=lambda x: 2 <= x.get('age', 0) <= 12,
                error_message="Child age outside valid range (2-12)",
                interface=InterfaceType.DATABASE
            ),
            ValidationRule(
                name="story_content_length",
                validator=lambda x: 100 <= len(x.get('content', '')) <= 5000,
                error_message="Story content length invalid",
                interface=InterfaceType.DATABASE
            ),
            ValidationRule(
                name="timestamp_format",
                validator=lambda x: self._validate_timestamp(x.get('created_at', '')),
                error_message="Invalid timestamp format",
                interface=InterfaceType.DATABASE
            ),
            ValidationRule(
                name="foreign_key_integrity",
                validator=lambda x: self._validate_foreign_keys(x),
                error_message="Foreign key constraint violation",
                interface=InterfaceType.DATABASE,
                level=ValidationLevel.STRICT
            )
        ]
    
    def _get_ai_validation_rules(self) -> List[ValidationRule]:
        """Validation rules for AI interface"""
        return [
            ValidationRule(
                name="story_age_appropriate",
                validator=lambda x: self._validate_age_appropriateness(x),
                error_message="Story content not age-appropriate",
                interface=InterfaceType.AI,
                weight=2.0
            ),
            ValidationRule(
                name="content_safety",
                validator=lambda x: self._validate_content_safety(x.get('story_content', '')),
                error_message="Content safety violation detected",
                interface=InterfaceType.AI,
                weight=3.0
            ),
            ValidationRule(
                name="personalization_accuracy",
                validator=lambda x: self._validate_personalization(x),
                error_message="Personalization accuracy below threshold",
                interface=InterfaceType.AI
            ),
            ValidationRule(
                name="response_time_acceptable",
                validator=lambda x: x.get('generation_time_seconds', 0) <= 10,
                error_message="AI response time exceeds acceptable limit",
                interface=InterfaceType.AI
            )
        ]
    
    def _get_analytics_validation_rules(self) -> List[ValidationRule]:
        """Validation rules for analytics interface"""
        return [
            ValidationRule(
                name="metric_value_range",
                validator=lambda x: 0.0 <= x.get('metric_value', 0) <= 1.0,
                error_message="Metric value outside valid range",
                interface=InterfaceType.ANALYTICS
            ),
            ValidationRule(
                name="event_sequence_logical",
                validator=lambda x: self._validate_event_sequence(x),
                error_message="Illogical event sequence detected",
                interface=InterfaceType.ANALYTICS
            ),
            ValidationRule(
                name="completion_rate_realistic",
                validator=lambda x: 0.0 <= x.get('completion_rate', 0) <= 1.0,
                error_message="Completion rate outside realistic range",
                interface=InterfaceType.ANALYTICS
            )
        ]
    
    def _get_business_validation_rules(self) -> List[ValidationRule]:
        """Validation rules for business logic"""
        return [
            ValidationRule(
                name="freemium_usage_limit",
                validator=lambda x: x.get('monthly_usage', 0) <= config.business.free_tier_stories_per_month,
                error_message="Freemium usage limit exceeded",
                interface=InterfaceType.BUSINESS
            ),
            ValidationRule(
                name="conversion_rate_realistic",
                validator=lambda x: 0.0 <= x.get('conversion_probability', 0) <= 1.0,
                error_message="Conversion probability outside realistic range",
                interface=InterfaceType.BUSINESS
            ),
            ValidationRule(
                name="revenue_calculation_accurate",
                validator=lambda x: self._validate_revenue_calculation(x),
                error_message="Revenue calculation inconsistency",
                interface=InterfaceType.BUSINESS,
                level=ValidationLevel.STRICT
            )
        ]
    
    def validate_interface_data(self, interface: str, data: Dict[str, Any]) -> ValidationReport:
        """Validate data for specific interface"""
        if interface not in self._validation_rules:
            raise ValueError(f"Unknown interface: {interface}")
        
        rules = self._validation_rules[interface]
        applicable_rules = [r for r in rules if r.level.value <= self.validation_level.value or r.level == ValidationLevel.BASIC]
        
        passed_checks = 0
        failed_checks = 0
        errors = []
        warnings = []
        total_weight = 0
        weighted_score = 0
        
        for rule in applicable_rules:
            try:
                is_valid = rule.validator(data)
                total_weight += rule.weight
                
                if is_valid:
                    passed_checks += 1
                    weighted_score += rule.weight
                else:
                    failed_checks += 1
                    errors.append(f"{rule.name}: {rule.error_message}")
                    
            except Exception as e:
                failed_checks += 1
                errors.append(f"{rule.name}: Validation error - {str(e)}")
                logger.error(f"Validation rule {rule.name} failed: {e}")
        
        confidence_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        report = ValidationReport(
            interface_type=interface,
            data_type=data.get('data_type', 'unknown'),
            total_checks=len(applicable_rules),
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            confidence_score=confidence_score,
            errors=errors,
            warnings=warnings
        )
        
        # Track validation results
        self.analytics.track_system_health(f'{interface}_validation_rate', report.success_rate, interface)
        self.analytics.track_system_health(f'{interface}_confidence_score', confidence_score, interface)
        
        return report
    
    def validate_cross_interface_consistency(self, data_sets: Dict[str, Dict[str, Any]]) -> ValidationReport:
        """Validate consistency across multiple interfaces"""
        errors = []
        warnings = []
        passed_checks = 0
        total_checks = 0
        
        # Check for data consistency between interfaces
        if 'database' in data_sets and 'analytics' in data_sets:
            db_data = data_sets['database']
            analytics_data = data_sets['analytics']
            
            # Verify child_id consistency
            total_checks += 1
            if db_data.get('child_id') == analytics_data.get('child_id'):
                passed_checks += 1
            else:
                errors.append("Child ID mismatch between database and analytics")
            
            # Verify story count consistency
            total_checks += 1
            db_story_count = db_data.get('story_count', 0)
            analytics_story_count = analytics_data.get('story_count', 0)
            if abs(db_story_count - analytics_story_count) <= 1:  # Allow minor discrepancy
                passed_checks += 1
            else:
                errors.append(f"Story count mismatch: DB={db_story_count}, Analytics={analytics_story_count}")
        
        # Check phone and database consistency
        if 'phone' in data_sets and 'database' in data_sets:
            phone_data = data_sets['phone']
            db_data = data_sets['database']
            
            total_checks += 1
            if phone_data.get('session_id') and db_data.get('session_id'):
                if phone_data['session_id'] == db_data['session_id']:
                    passed_checks += 1
                else:
                    errors.append("Session ID mismatch between phone and database")
            else:
                warnings.append("Missing session ID in cross-interface validation")
        
        confidence_score = passed_checks / total_checks if total_checks > 0 else 1.0
        
        return ValidationReport(
            interface_type="cross_interface",
            data_type="consistency_check",
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            confidence_score=confidence_score,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        # Remove common formatting
        clean_phone = re.sub(r'[^\d+]', '', phone)
        # Check for valid US/international format
        return re.match(r'^\+?1?\d{10,15}$', clean_phone) is not None
    
    def _validate_session_id(self, session_id: str) -> bool:
        """Validate session ID format"""
        return len(session_id) >= 10 and session_id.isalnum()
    
    def _validate_uuid(self, uuid_str: str) -> bool:
        """Validate UUID format"""
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return re.match(uuid_pattern, uuid_str, re.IGNORECASE) is not None
    
    def _validate_timestamp(self, timestamp: str) -> bool:
        """Validate ISO timestamp format"""
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False
    
    def _validate_age_appropriateness(self, data: Dict[str, Any]) -> bool:
        """Validate story content is age-appropriate"""
        story_content = data.get('story_content', '')
        child_age = data.get('child_age', 5)
        
        # Basic age-appropriateness checks
        inappropriate_words = ['violence', 'scary', 'frightening', 'death', 'kill']
        
        if child_age <= 5:
            # Very strict for young children
            return not any(word in story_content.lower() for word in inappropriate_words)
        elif child_age <= 8:
            # Moderate restrictions
            severe_words = ['violence', 'death', 'kill']
            return not any(word in story_content.lower() for word in severe_words)
        else:
            # More lenient for older children
            return len(story_content) > 0
    
    def _validate_content_safety(self, content: str) -> bool:
        """Validate content safety"""
        if not content:
            return False
        
        # Check for potentially harmful content
        harmful_patterns = [
            r'personal\s+information',
            r'contact\s+details',
            r'address',
            r'phone\s+number',
            r'violent',
            r'inappropriate'
        ]
        
        for pattern in harmful_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False
        
        return True
    
    def _validate_personalization(self, data: Dict[str, Any]) -> bool:
        """Validate personalization accuracy"""
        interests = data.get('child_interests', [])
        story_content = data.get('story_content', '')
        
        if not interests or not story_content:
            return True  # Can't validate without data
        
        # Check if story content matches at least one interest
        for interest in interests:
            if interest.lower() in story_content.lower():
                return True
        
        return False
    
    def _validate_event_sequence(self, data: Dict[str, Any]) -> bool:
        """Validate logical event sequence"""
        events = data.get('event_sequence', [])
        
        if not events:
            return True
        
        # Check for logical sequence (e.g., call_start before story_begin)
        valid_transitions = {
            'call_start': ['registration', 'story_begin', 'call_end'],
            'registration': ['story_begin', 'call_end'],
            'story_begin': ['pause', 'skip', 'completion', 'call_end'],
            'pause': ['story_begin', 'skip', 'completion', 'call_end'],
            'skip': ['story_begin', 'call_end'],
            'completion': ['story_begin', 'call_end'],
            'replay': ['story_begin', 'completion', 'call_end']
        }
        
        for i in range(len(events) - 1):
            current_event = events[i]
            next_event = events[i + 1]
            
            if current_event not in valid_transitions:
                continue
            
            if next_event not in valid_transitions[current_event]:
                return False
        
        return True
    
    def _validate_foreign_keys(self, data: Dict[str, Any]) -> bool:
        """Validate foreign key constraints"""
        # This would typically check against actual database
        # For now, just validate format
        child_id = data.get('child_id')
        parent_phone = data.get('parent_phone')
        
        return (child_id and self._validate_uuid(child_id) and
                parent_phone and self._validate_phone_number(parent_phone))
    
    def _validate_revenue_calculation(self, data: Dict[str, Any]) -> bool:
        """Validate revenue calculation accuracy"""
        monthly_revenue = data.get('monthly_revenue', 0)
        subscriber_count = data.get('subscriber_count', 0)
        avg_price = data.get('average_subscription_price', 0)
        
        if subscriber_count == 0 or avg_price == 0:
            return monthly_revenue == 0
        
        expected_revenue = subscriber_count * avg_price
        return abs(monthly_revenue - expected_revenue) / expected_revenue <= 0.05  # 5% tolerance
    
    def generate_comprehensive_report(self, data_sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive validation report across all interfaces"""
        reports = {}
        overall_confidence = 0.0
        total_checks = 0
        passed_checks = 0
        
        # Validate each interface
        for interface, data in data_sources.items():
            if interface in self._validation_rules:
                report = self.validate_interface_data(interface, data)
                reports[interface] = {
                    'success_rate': report.success_rate,
                    'confidence_score': report.confidence_score,
                    'is_valid': report.is_valid,
                    'errors': report.errors,
                    'warnings': report.warnings
                }
                
                overall_confidence += report.confidence_score
                total_checks += report.total_checks
                passed_checks += report.passed_checks
        
        # Cross-interface validation
        cross_interface_report = self.validate_cross_interface_consistency(data_sources)
        reports['cross_interface'] = {
            'success_rate': cross_interface_report.success_rate,
            'confidence_score': cross_interface_report.confidence_score,
            'is_valid': cross_interface_report.is_valid,
            'errors': cross_interface_report.errors,
            'warnings': cross_interface_report.warnings
        }
        
        # Calculate overall metrics
        interface_count = len([r for r in reports if r != 'cross_interface'])
        overall_confidence = overall_confidence / interface_count if interface_count > 0 else 0.0
        overall_success_rate = passed_checks / total_checks if total_checks > 0 else 0.0
        
        return {
            'overall_health': {
                'success_rate': overall_success_rate,
                'confidence_score': overall_confidence,
                'is_system_healthy': overall_success_rate >= 0.95 and overall_confidence >= 0.8,
                'validation_level': self.validation_level.value
            },
            'interface_reports': reports,
            'generated_at': datetime.now().isoformat()
        }

# Global validation instance
validation_layer = DataValidationLayer()

def get_validation_layer() -> DataValidationLayer:
    """Get global validation layer instance"""
    return validation_layer