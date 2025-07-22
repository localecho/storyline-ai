#!/usr/bin/env python3
"""
StoryLine AI - Real-Time Verification Systems
Trust But Verify: Instant validation, alerting, and response
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from contextlib import contextmanager
import threading
import time
import uuid
import queue
import websocket
from collections import defaultdict, deque

from config import get_config
from analytics_engine import get_analytics_engine
from validation_layer import get_validation_layer
from quality_assurance import get_automated_qa

logger = logging.getLogger(__name__)
config = get_config()

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class VerificationStatus(Enum):
    """Real-time verification status"""
    VERIFIED = "verified"
    PENDING = "pending"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class RealTimeAlert:
    """Real-time alert structure"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    interface: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False

@dataclass
class VerificationEvent:
    """Real-time verification event"""
    event_id: str
    data_type: str
    data_payload: Dict[str, Any]
    verification_status: VerificationStatus
    confidence_score: float
    processing_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    alerts_triggered: List[str] = field(default_factory=list)

class RealTimeVerificationEngine:
    """Real-time verification and alerting system"""
    
    def __init__(self):
        self.analytics = get_analytics_engine()
        self.validator = get_validation_layer()
        self.qa_system = get_automated_qa()
        self.config = get_config()
        
        # Real-time processing queues
        self._verification_queue = queue.Queue(maxsize=1000)
        self._alert_queue = queue.Queue(maxsize=500)
        
        # Active alerts and verification history
        self._active_alerts = {}
        self._verification_history = deque(maxlen=10000)
        
        # Performance metrics
        self._metrics = defaultdict(float)
        self._metric_history = defaultdict(lambda: deque(maxlen=100))
        
        # Processing threads
        self._processing_threads = []
        self._is_running = False
        
        # Alert thresholds and rules
        self._alert_rules = self._initialize_alert_rules()
        
        self.init_realtime_database()
        
    def init_realtime_database(self):
        """Initialize real-time verification database"""
        logger.info("Initializing real-time verification database")
        
        with self.analytics.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS realtime_alerts (
                    alert_id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    interface TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TEXT NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS verification_events (
                    event_id TEXT PRIMARY KEY,
                    data_type TEXT NOT NULL,
                    data_payload TEXT NOT NULL,
                    verification_status TEXT NOT NULL,
                    confidence_score REAL,
                    processing_time_ms REAL,
                    timestamp TEXT NOT NULL,
                    alerts_triggered TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS realtime_metrics (
                    metric_name TEXT,
                    metric_value REAL,
                    timestamp TEXT,
                    PRIMARY KEY (metric_name, timestamp)
                )
            """)
            
            # Performance indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_level ON realtime_alerts(level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON realtime_alerts(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON verification_events(verification_status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON realtime_metrics(metric_name)")
            
            conn.commit()
            logger.info("Real-time verification database initialized")
    
    def _initialize_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize alert rules and thresholds"""
        return {
            'response_time_threshold': {
                'threshold': 5000,  # 5 seconds in milliseconds
                'level': AlertLevel.WARNING,
                'message_template': 'Response time exceeded {threshold}ms: {actual_time}ms'
            },
            'verification_failure_rate': {
                'threshold': 0.05,  # 5% failure rate
                'level': AlertLevel.ERROR,
                'message_template': 'Verification failure rate too high: {failure_rate}%'
            },
            'confidence_score_low': {
                'threshold': 0.7,
                'level': AlertLevel.WARNING,
                'message_template': 'Low confidence score detected: {confidence_score}'
            },
            'queue_overflow': {
                'threshold': 900,  # 90% of queue capacity
                'level': AlertLevel.CRITICAL,
                'message_template': 'Processing queue near capacity: {queue_size}/{max_size}'
            },
            'database_connection_failure': {
                'threshold': 1,
                'level': AlertLevel.CRITICAL,
                'message_template': 'Database connection failure detected'
            },
            'ai_generation_timeout': {
                'threshold': 30000,  # 30 seconds
                'level': AlertLevel.ERROR,
                'message_template': 'AI generation timeout: {duration}ms'
            }
        }
    
    def start_realtime_processing(self):
        """Start real-time verification processing"""
        if self._is_running:
            logger.warning("Real-time processing already running")
            return
        
        self._is_running = True
        
        # Start verification processing thread
        verification_thread = threading.Thread(
            target=self._verification_processing_loop,
            name="VerificationProcessor",
            daemon=True
        )
        verification_thread.start()
        self._processing_threads.append(verification_thread)
        
        # Start alert processing thread
        alert_thread = threading.Thread(
            target=self._alert_processing_loop,
            name="AlertProcessor",
            daemon=True
        )
        alert_thread.start()
        self._processing_threads.append(alert_thread)
        
        # Start metrics collection thread
        metrics_thread = threading.Thread(
            target=self._metrics_collection_loop,
            name="MetricsCollector",
            daemon=True
        )
        metrics_thread.start()
        self._processing_threads.append(metrics_thread)
        
        logger.info("Started real-time verification processing")
    
    def stop_realtime_processing(self):
        """Stop real-time verification processing"""
        self._is_running = False
        logger.info("Stopped real-time verification processing")
    
    def verify_realtime(self, data_type: str, data_payload: Dict[str, Any]) -> VerificationEvent:
        """Perform real-time verification of incoming data"""
        start_time = time.time()
        event_id = str(uuid.uuid4())
        
        try:
            # Add to processing queue
            if not self._verification_queue.full():
                verification_task = {
                    'event_id': event_id,
                    'data_type': data_type,
                    'data_payload': data_payload,
                    'start_time': start_time
                }
                self._verification_queue.put(verification_task, timeout=1)
                
                # For immediate response, perform quick validation
                quick_result = self._perform_quick_validation(data_type, data_payload)
                
                processing_time = (time.time() - start_time) * 1000
                
                event = VerificationEvent(
                    event_id=event_id,
                    data_type=data_type,
                    data_payload=data_payload,
                    verification_status=quick_result['status'],
                    confidence_score=quick_result['confidence'],
                    processing_time_ms=processing_time,
                    alerts_triggered=quick_result.get('alerts', [])
                )
                
                self._verification_history.append(event)
                
                # Trigger alerts if necessary
                if quick_result.get('alerts'):
                    for alert_type in quick_result['alerts']:
                        self._trigger_alert(alert_type, data_type, quick_result)
                
                return event
            else:
                # Queue full - trigger overflow alert
                self._trigger_alert('queue_overflow', 'system', {
                    'queue_size': self._verification_queue.qsize(),
                    'max_size': self._verification_queue.maxsize
                })
                
                processing_time = (time.time() - start_time) * 1000
                
                return VerificationEvent(
                    event_id=event_id,
                    data_type=data_type,
                    data_payload=data_payload,
                    verification_status=VerificationStatus.TIMEOUT,
                    confidence_score=0.0,
                    processing_time_ms=processing_time,
                    alerts_triggered=['queue_overflow']
                )
                
        except Exception as e:
            logger.error(f"Real-time verification error: {e}")
            processing_time = (time.time() - start_time) * 1000
            
            return VerificationEvent(
                event_id=event_id,
                data_type=data_type,
                data_payload=data_payload,
                verification_status=VerificationStatus.FAILED,
                confidence_score=0.0,
                processing_time_ms=processing_time,
                alerts_triggered=['verification_error']
            )
    
    def _perform_quick_validation(self, data_type: str, data_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform quick validation for immediate response"""
        result = {
            'status': VerificationStatus.VERIFIED,
            'confidence': 1.0,
            'alerts': []
        }
        
        try:
            # Interface-specific quick validation
            if data_type == 'phone_call':
                if not data_payload.get('session_id'):
                    result['status'] = VerificationStatus.FAILED
                    result['confidence'] = 0.0
                    result['alerts'].append('missing_session_id')
                
                if data_payload.get('duration_seconds', 0) > 1800:  # 30 minutes
                    result['alerts'].append('call_duration_excessive')
                    result['confidence'] *= 0.8
            
            elif data_type == 'story_generation':
                content = data_payload.get('story_content', '')
                if len(content) < 50:
                    result['status'] = VerificationStatus.FAILED
                    result['confidence'] = 0.3
                    result['alerts'].append('story_too_short')
                
                # Quick safety check
                unsafe_words = ['violence', 'scary', 'death']
                if any(word in content.lower() for word in unsafe_words):
                    result['alerts'].append('potential_unsafe_content')
                    result['confidence'] *= 0.5
            
            elif data_type == 'user_registration':
                required_fields = ['child_name', 'child_age', 'parent_phone']
                missing_fields = [f for f in required_fields if not data_payload.get(f)]
                
                if missing_fields:
                    result['status'] = VerificationStatus.FAILED
                    result['confidence'] = 0.0
                    result['alerts'].append('missing_required_fields')
                
                age = data_payload.get('child_age', 0)
                if age < 2 or age > 12:
                    result['alerts'].append('age_out_of_range')
                    result['confidence'] *= 0.7
            
            # Check response time threshold
            if hasattr(self, '_last_verification_time'):
                time_since_last = (time.time() - self._last_verification_time) * 1000
                if time_since_last > self._alert_rules['response_time_threshold']['threshold']:
                    result['alerts'].append('response_time_threshold')
            
            self._last_verification_time = time.time()
            
        except Exception as e:
            logger.error(f"Quick validation error: {e}")
            result['status'] = VerificationStatus.FAILED
            result['confidence'] = 0.0
            result['alerts'].append('validation_error')
        
        return result
    
    def _verification_processing_loop(self):
        """Main verification processing loop"""
        while self._is_running:
            try:
                # Get task from queue with timeout
                task = self._verification_queue.get(timeout=1)
                
                # Perform comprehensive validation
                self._perform_comprehensive_validation(task)
                
                self._verification_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Verification processing error: {e}")
                time.sleep(1)
    
    def _perform_comprehensive_validation(self, task: Dict[str, Any]):
        """Perform comprehensive validation in background"""
        try:
            data_type = task['data_type']
            data_payload = task['data_payload']
            
            # Determine interface type for validation
            interface_map = {
                'phone_call': 'phone',
                'story_generation': 'ai', 
                'user_registration': 'database',
                'analytics_event': 'analytics',
                'business_transaction': 'business'
            }
            
            interface = interface_map.get(data_type, 'database')
            
            # Perform full validation
            validation_report = self.validator.validate_interface_data(interface, data_payload)
            
            # Store comprehensive results
            processing_time = (time.time() - task['start_time']) * 1000
            
            verification_event = VerificationEvent(
                event_id=task['event_id'],
                data_type=data_type,
                data_payload=data_payload,
                verification_status=VerificationStatus.VERIFIED if validation_report.is_valid else VerificationStatus.FAILED,
                confidence_score=validation_report.confidence_score,
                processing_time_ms=processing_time
            )
            
            # Store in database
            self._store_verification_event(verification_event)
            
            # Update metrics
            self._update_verification_metrics(verification_event)
            
            # Trigger alerts for failures
            if not validation_report.is_valid:
                self._trigger_alert('verification_failure', interface, {
                    'event_id': task['event_id'],
                    'errors': validation_report.errors,
                    'confidence': validation_report.confidence_score
                })
            
        except Exception as e:
            logger.error(f"Comprehensive validation error: {e}")
    
    def _alert_processing_loop(self):
        """Process alerts and notifications"""
        while self._is_running:
            try:
                alert = self._alert_queue.get(timeout=1)
                
                # Process alert
                self._process_alert(alert)
                
                self._alert_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
                time.sleep(1)
    
    def _metrics_collection_loop(self):
        """Collect and update real-time metrics"""
        while self._is_running:
            try:
                # Collect current metrics
                self._collect_current_metrics()
                
                # Sleep for metric collection interval
                time.sleep(10)  # Collect every 10 seconds
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                time.sleep(30)
    
    def _trigger_alert(self, alert_type: str, interface: str, context: Dict[str, Any]):
        """Trigger real-time alert"""
        try:
            alert_rule = self._alert_rules.get(alert_type)
            if not alert_rule:
                logger.warning(f"Unknown alert type: {alert_type}")
                return
            
            # Create alert
            alert = RealTimeAlert(
                alert_id=str(uuid.uuid4()),
                level=alert_rule['level'],
                title=f"{alert_type.replace('_', ' ').title()}",
                message=alert_rule['message_template'].format(**context),
                interface=interface,
                metadata=context
            )
            
            # Add to active alerts
            self._active_alerts[alert.alert_id] = alert
            
            # Queue for processing
            if not self._alert_queue.full():
                self._alert_queue.put(alert)
            
            logger.warning(f"Alert triggered: {alert.title} - {alert.message}")
            
        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")
    
    def _process_alert(self, alert: RealTimeAlert):
        """Process individual alert"""
        try:
            # Store alert in database
            self._store_alert(alert)
            
            # Send notifications based on alert level
            if alert.level == AlertLevel.CRITICAL:
                self._send_critical_notification(alert)
            elif alert.level == AlertLevel.ERROR:
                self._send_error_notification(alert)
            
            # Update alert metrics
            self._metrics[f'alerts_{alert.level.value}'] += 1
            
        except Exception as e:
            logger.error(f"Failed to process alert: {e}")
    
    def _send_critical_notification(self, alert: RealTimeAlert):
        """Send critical alert notification"""
        # In production, this would integrate with PagerDuty, Slack, email, etc.
        logger.critical(f"CRITICAL ALERT: {alert.title} - {alert.message}")
        
        # Track critical alert
        self.analytics.track_system_health('critical_alert_triggered', 1.0, 'realtime_verification')
    
    def _send_error_notification(self, alert: RealTimeAlert):
        """Send error alert notification"""
        logger.error(f"ERROR ALERT: {alert.title} - {alert.message}")
        
        # Track error alert
        self.analytics.track_system_health('error_alert_triggered', 1.0, 'realtime_verification')
    
    def _collect_current_metrics(self):
        """Collect current system metrics"""
        try:
            # Queue metrics
            verification_queue_size = self._verification_queue.qsize()
            alert_queue_size = self._alert_queue.qsize()
            
            self._metrics['verification_queue_size'] = verification_queue_size
            self._metrics['alert_queue_size'] = alert_queue_size
            
            # Active alerts count
            self._metrics['active_alerts'] = len(self._active_alerts)
            
            # Recent verification statistics
            recent_verifications = [v for v in self._verification_history 
                                  if (datetime.now() - v.timestamp).total_seconds() < 300]  # Last 5 minutes
            
            if recent_verifications:
                success_rate = len([v for v in recent_verifications 
                                 if v.verification_status == VerificationStatus.VERIFIED]) / len(recent_verifications)
                avg_processing_time = sum(v.processing_time_ms for v in recent_verifications) / len(recent_verifications)
                avg_confidence = sum(v.confidence_score for v in recent_verifications) / len(recent_verifications)
                
                self._metrics['verification_success_rate'] = success_rate
                self._metrics['avg_processing_time_ms'] = avg_processing_time
                self._metrics['avg_confidence_score'] = avg_confidence
            
            # Store metrics in database
            self._store_realtime_metrics()
            
            # Track with analytics system
            for metric_name, metric_value in self._metrics.items():
                self.analytics.track_system_health(metric_name, metric_value, 'realtime_verification')
                
                # Update metric history
                self._metric_history[metric_name].append({
                    'value': metric_value,
                    'timestamp': datetime.now()
                })
            
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
    
    def _store_verification_event(self, event: VerificationEvent):
        """Store verification event in database"""
        with self.analytics.get_connection() as conn:
            conn.execute("""
                INSERT INTO verification_events 
                (event_id, data_type, data_payload, verification_status, 
                 confidence_score, processing_time_ms, timestamp, alerts_triggered)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id, event.data_type, json.dumps(event.data_payload),
                event.verification_status.value, event.confidence_score,
                event.processing_time_ms, event.timestamp.isoformat(),
                json.dumps(event.alerts_triggered)
            ))
            conn.commit()
    
    def _store_alert(self, alert: RealTimeAlert):
        """Store alert in database"""
        with self.analytics.get_connection() as conn:
            conn.execute("""
                INSERT INTO realtime_alerts 
                (alert_id, level, title, message, interface, metadata, timestamp, acknowledged)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id, alert.level.value, alert.title, alert.message,
                alert.interface, json.dumps(alert.metadata), 
                alert.timestamp.isoformat(), alert.acknowledged
            ))
            conn.commit()
    
    def _store_realtime_metrics(self):
        """Store real-time metrics in database"""
        timestamp = datetime.now().isoformat()
        
        with self.analytics.get_connection() as conn:
            for metric_name, metric_value in self._metrics.items():
                conn.execute("""
                    INSERT OR REPLACE INTO realtime_metrics 
                    (metric_name, metric_value, timestamp)
                    VALUES (?, ?, ?)
                """, (metric_name, metric_value, timestamp))
            conn.commit()
    
    def _update_verification_metrics(self, event: VerificationEvent):
        """Update verification-specific metrics"""
        # Update success/failure rates
        if event.verification_status == VerificationStatus.VERIFIED:
            self._metrics['total_successful_verifications'] += 1
        else:
            self._metrics['total_failed_verifications'] += 1
        
        # Update processing time metrics
        self._metrics['total_processing_time_ms'] += event.processing_time_ms
        self._metrics['total_verifications'] += 1
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an active alert"""
        if alert_id in self._active_alerts:
            self._active_alerts[alert_id].acknowledged = True
            
            # Update in database
            with self.analytics.get_connection() as conn:
                conn.execute("""
                    UPDATE realtime_alerts 
                    SET acknowledged = TRUE 
                    WHERE alert_id = ?
                """, (alert_id,))
                conn.commit()
            
            logger.info(f"Alert acknowledged: {alert_id}")
            return True
        
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        if alert_id in self._active_alerts:
            # Remove from active alerts
            del self._active_alerts[alert_id]
            
            # Update in database
            with self.analytics.get_connection() as conn:
                conn.execute("""
                    UPDATE realtime_alerts 
                    SET resolved_at = ? 
                    WHERE alert_id = ?
                """, (datetime.now().isoformat(), alert_id))
                conn.commit()
            
            logger.info(f"Alert resolved: {alert_id}")
            return True
        
        return False
    
    def get_realtime_status(self) -> Dict[str, Any]:
        """Get comprehensive real-time status"""
        return {
            'system_status': 'operational' if self._is_running else 'stopped',
            'processing_threads': len(self._processing_threads),
            'verification_queue_size': self._verification_queue.qsize(),
            'alert_queue_size': self._alert_queue.qsize(),
            'active_alerts': len(self._active_alerts),
            'recent_verifications': len(self._verification_history),
            'current_metrics': dict(self._metrics),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [
            {
                'alert_id': alert.alert_id,
                'level': alert.level.value,
                'title': alert.title,
                'message': alert.message,
                'interface': alert.interface,
                'timestamp': alert.timestamp.isoformat(),
                'acknowledged': alert.acknowledged,
                'metadata': alert.metadata
            }
            for alert in self._active_alerts.values()
        ]
    
    def get_verification_metrics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get verification metrics for specified time window"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        recent_events = [v for v in self._verification_history if v.timestamp > cutoff_time]
        
        if not recent_events:
            return {
                'time_window_minutes': time_window_minutes,
                'total_verifications': 0,
                'success_rate': 0.0,
                'avg_processing_time_ms': 0.0,
                'avg_confidence_score': 0.0
            }
        
        successful = len([e for e in recent_events if e.verification_status == VerificationStatus.VERIFIED])
        
        return {
            'time_window_minutes': time_window_minutes,
            'total_verifications': len(recent_events),
            'successful_verifications': successful,
            'failed_verifications': len(recent_events) - successful,
            'success_rate': successful / len(recent_events),
            'avg_processing_time_ms': sum(e.processing_time_ms for e in recent_events) / len(recent_events),
            'avg_confidence_score': sum(e.confidence_score for e in recent_events) / len(recent_events),
            'alerts_triggered': sum(len(e.alerts_triggered) for e in recent_events),
            'last_updated': datetime.now().isoformat()
        }

# Global real-time verification instance
realtime_verification = RealTimeVerificationEngine()

def get_realtime_verification() -> RealTimeVerificationEngine:
    """Get global real-time verification instance"""
    return realtime_verification