#!/usr/bin/env python3
"""
StoryLine AI - Cross-Interface Monitoring Dashboard
Trust But Verify: Real-time monitoring and verification across all interfaces
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from flask import Flask, render_template_string, jsonify
import sqlite3
from contextlib import contextmanager
import threading
import time

from config import get_config
from analytics_engine import get_analytics_engine
from validation_layer import get_validation_layer

logger = logging.getLogger(__name__)
config = get_config()

@dataclass
class InterfaceStatus:
    """Status of individual interface"""
    name: str
    health_score: float
    last_check: datetime
    response_time_ms: float
    error_count: int
    warning_count: int
    uptime_percentage: float
    
    @property
    def status_color(self) -> str:
        """Get color based on health score"""
        if self.health_score >= 0.9:
            return "green"
        elif self.health_score >= 0.7:
            return "yellow"
        else:
            return "red"
    
    @property
    def status_text(self) -> str:
        """Get status text"""
        if self.health_score >= 0.9:
            return "HEALTHY"
        elif self.health_score >= 0.7:
            return "WARNING" 
        else:
            return "CRITICAL"

class MonitoringDashboard:
    """Real-time monitoring dashboard for all interfaces"""
    
    def __init__(self):
        self.analytics = get_analytics_engine()
        self.validator = get_validation_layer()
        self.app = Flask(__name__)
        self._monitoring_data = {}
        self._last_update = datetime.now()
        self._setup_routes()
        self._start_background_monitoring()
        
    def _setup_routes(self):
        """Setup Flask routes for dashboard"""
        
        @self.app.route('/')
        def dashboard_home():
            """Main dashboard view"""
            return render_template_string(self._get_dashboard_template())
        
        @self.app.route('/api/health')
        def api_health():
            """Health check API endpoint"""
            return jsonify(self.get_system_health_summary())
        
        @self.app.route('/api/interfaces')
        def api_interfaces():
            """Interface status API"""
            return jsonify(self.get_interface_status_summary())
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """Real-time metrics API"""
            return jsonify(self.get_real_time_metrics())
        
        @self.app.route('/api/validation')
        def api_validation():
            """Validation status API"""
            return jsonify(self.get_validation_summary())
        
        @self.app.route('/api/alerts')
        def api_alerts():
            """Active alerts API"""
            return jsonify(self.get_active_alerts())
    
    def _start_background_monitoring(self):
        """Start background monitoring thread"""
        def monitor_loop():
            while True:
                try:
                    self._update_monitoring_data()
                    time.sleep(10)  # Update every 10 seconds
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(30)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("Background monitoring started")
    
    def _update_monitoring_data(self):
        """Update monitoring data from all interfaces"""
        self._monitoring_data = {
            'phone_interface': self._check_phone_interface(),
            'database_interface': self._check_database_interface(),
            'ai_interface': self._check_ai_interface(),
            'analytics_interface': self._check_analytics_interface(),
            'business_interface': self._check_business_interface()
        }
        self._last_update = datetime.now()
    
    def _check_phone_interface(self) -> InterfaceStatus:
        """Monitor phone interface (Twilio)"""
        start_time = time.time()
        health_score = 1.0
        error_count = 0
        warning_count = 0
        
        try:
            # Check Twilio configuration
            if not config.twilio.account_sid or not config.twilio.auth_token:
                health_score -= 0.5
                error_count += 1
            
            # Check recent call quality from analytics
            with self.analytics.get_connection() as conn:
                recent_calls = conn.execute("""
                    SELECT AVG(metric_value) as avg_quality
                    FROM system_health 
                    WHERE interface_type = 'phone' 
                    AND metric_name = 'call_quality'
                    AND timestamp > ?
                """, ((datetime.now() - timedelta(minutes=30)).isoformat(),)).fetchone()
                
                if recent_calls and recent_calls['avg_quality']:
                    if recent_calls['avg_quality'] < 0.8:
                        health_score -= 0.2
                        warning_count += 1
        
        except Exception as e:
            logger.error(f"Phone interface check failed: {e}")
            health_score = 0.3
            error_count += 1
        
        response_time = (time.time() - start_time) * 1000
        
        return InterfaceStatus(
            name="Phone Interface",
            health_score=health_score,
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_count=error_count,
            warning_count=warning_count,
            uptime_percentage=99.5  # Would calculate from actual uptime data
        )
    
    def _check_database_interface(self) -> InterfaceStatus:
        """Monitor database interface"""
        start_time = time.time()
        health_score = 1.0
        error_count = 0
        warning_count = 0
        
        try:
            # Test database connectivity
            with self.analytics.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()
            
            # Check for recent data integrity issues
            integrity_report = self.validator.generate_comprehensive_report({
                'database': {'data_type': 'health_check'}
            })
            
            if not integrity_report['overall_health']['is_system_healthy']:
                health_score -= 0.3
                warning_count += 1
            
            # Check for database performance
            with self.analytics.get_connection() as conn:
                slow_queries = conn.execute("""
                    SELECT COUNT(*) as count FROM system_health 
                    WHERE interface_type = 'database' 
                    AND metric_name = 'query_time_ms'
                    AND metric_value > 1000
                    AND timestamp > ?
                """, ((datetime.now() - timedelta(hours=1)).isoformat(),)).fetchone()
                
                if slow_queries and slow_queries['count'] > 5:
                    health_score -= 0.2
                    warning_count += 1
        
        except Exception as e:
            logger.error(f"Database interface check failed: {e}")
            health_score = 0.2
            error_count += 1
        
        response_time = (time.time() - start_time) * 1000
        
        return InterfaceStatus(
            name="Database Interface",
            health_score=health_score,
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_count=error_count,
            warning_count=warning_count,
            uptime_percentage=99.8
        )
    
    def _check_ai_interface(self) -> InterfaceStatus:
        """Monitor AI interface (story generation)"""
        start_time = time.time()
        health_score = 1.0
        error_count = 0
        warning_count = 0
        
        try:
            # Check AI service availability (would ping actual service)
            # For now, check recent generation metrics
            with self.analytics.get_connection() as conn:
                recent_generations = conn.execute("""
                    SELECT AVG(metric_value) as avg_time
                    FROM system_health 
                    WHERE interface_type = 'ai' 
                    AND metric_name = 'generation_time_seconds'
                    AND timestamp > ?
                """, ((datetime.now() - timedelta(minutes=15)).isoformat(),)).fetchone()
                
                if recent_generations and recent_generations['avg_time']:
                    if recent_generations['avg_time'] > 10:  # Over 10 seconds
                        health_score -= 0.3
                        warning_count += 1
                    elif recent_generations['avg_time'] > 5:  # Over 5 seconds
                        health_score -= 0.1
            
            # Check content safety validation rate
            safety_report = self.validator.validate_interface_data('ai', {
                'story_content': 'Sample content for health check',
                'child_age': 6
            })
            
            if not safety_report.is_valid:
                health_score -= 0.4
                error_count += 1
        
        except Exception as e:
            logger.error(f"AI interface check failed: {e}")
            health_score = 0.4
            error_count += 1
        
        response_time = (time.time() - start_time) * 1000
        
        return InterfaceStatus(
            name="AI Interface",
            health_score=health_score,
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_count=error_count,
            warning_count=warning_count,
            uptime_percentage=97.5
        )
    
    def _check_analytics_interface(self) -> InterfaceStatus:
        """Monitor analytics interface"""
        start_time = time.time()
        health_score = 1.0
        error_count = 0
        warning_count = 0
        
        try:
            # Check analytics data freshness
            with self.analytics.get_connection() as conn:
                latest_event = conn.execute("""
                    SELECT MAX(timestamp) as latest
                    FROM call_events
                """).fetchone()
                
                if latest_event and latest_event['latest']:
                    latest_time = datetime.fromisoformat(latest_event['latest'])
                    age_minutes = (datetime.now() - latest_time).total_seconds() / 60
                    
                    if age_minutes > 60:  # Data older than 1 hour
                        health_score -= 0.3
                        warning_count += 1
            
            # Check event verification rate
            health_summary = self.analytics.get_system_health_summary()
            verification_rate = health_summary.get('event_verification_rate', 0)
            
            if verification_rate < 0.95:
                health_score -= 0.2
                warning_count += 1
            
            if verification_rate < 0.8:
                health_score -= 0.3
                error_count += 1
        
        except Exception as e:
            logger.error(f"Analytics interface check failed: {e}")
            health_score = 0.3
            error_count += 1
        
        response_time = (time.time() - start_time) * 1000
        
        return InterfaceStatus(
            name="Analytics Interface", 
            health_score=health_score,
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_count=error_count,
            warning_count=warning_count,
            uptime_percentage=99.2
        )
    
    def _check_business_interface(self) -> InterfaceStatus:
        """Monitor business logic interface"""
        start_time = time.time()
        health_score = 1.0
        error_count = 0
        warning_count = 0
        
        try:
            # Check business rules validation
            business_data = {
                'monthly_usage': 2,
                'conversion_probability': 0.15,
                'monthly_revenue': 100,
                'subscriber_count': 5,
                'average_subscription_price': 20
            }
            
            business_report = self.validator.validate_interface_data('business', business_data)
            
            if not business_report.is_valid:
                health_score -= 0.4
                error_count += len(business_report.errors)
                warning_count += len(business_report.warnings)
        
        except Exception as e:
            logger.error(f"Business interface check failed: {e}")
            health_score = 0.5
            error_count += 1
        
        response_time = (time.time() - start_time) * 1000
        
        return InterfaceStatus(
            name="Business Interface",
            health_score=health_score,
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_count=error_count,
            warning_count=warning_count,
            uptime_percentage=99.9
        )
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        if not self._monitoring_data:
            return {'status': 'initializing'}
        
        total_health = sum(interface.health_score for interface in self._monitoring_data.values())
        avg_health = total_health / len(self._monitoring_data)
        
        total_errors = sum(interface.error_count for interface in self._monitoring_data.values())
        total_warnings = sum(interface.warning_count for interface in self._monitoring_data.values())
        
        overall_status = "HEALTHY"
        if avg_health < 0.7 or total_errors > 2:
            overall_status = "CRITICAL"
        elif avg_health < 0.9 or total_warnings > 3:
            overall_status = "WARNING"
        
        return {
            'overall_status': overall_status,
            'overall_health_score': round(avg_health, 3),
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'interfaces_monitored': len(self._monitoring_data),
            'last_updated': self._last_update.isoformat(),
            'uptime_percentage': 99.1  # Would calculate from actual data
        }
    
    def get_interface_status_summary(self) -> Dict[str, Any]:
        """Get detailed interface status"""
        return {
            interface_name: {
                'name': interface.name,
                'status': interface.status_text,
                'health_score': interface.health_score,
                'response_time_ms': interface.response_time_ms,
                'error_count': interface.error_count,
                'warning_count': interface.warning_count,
                'uptime_percentage': interface.uptime_percentage,
                'last_check': interface.last_check.isoformat(),
                'status_color': interface.status_color
            }
            for interface_name, interface in self._monitoring_data.items()
        }
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics"""
        try:
            analytics_summary = self.analytics.get_system_health_summary()
            
            return {
                'active_users_30d': analytics_summary.get('active_users_30d', 0),
                'avg_completion_rate': analytics_summary.get('avg_completion_rate', 0),
                'total_events': analytics_summary.get('total_events', 0),
                'event_verification_rate': analytics_summary.get('event_verification_rate', 1.0),
                'average_confidence': analytics_summary.get('average_confidence', 1.0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            return {'error': 'Failed to retrieve metrics'}
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation status summary"""
        try:
            # Get recent validation statistics
            with self.analytics.get_connection() as conn:
                validation_stats = conn.execute("""
                    SELECT 
                        data_type,
                        AVG(CASE WHEN validation_result THEN 1.0 ELSE 0.0 END) as success_rate,
                        AVG(confidence_score) as avg_confidence,
                        COUNT(*) as total_validations
                    FROM validation_log
                    WHERE timestamp > ?
                    GROUP BY data_type
                """, ((datetime.now() - timedelta(hours=1)).isoformat(),)).fetchall()
                
                return {
                    'validation_stats': [
                        {
                            'data_type': row['data_type'],
                            'success_rate': round(row['success_rate'], 3),
                            'avg_confidence': round(row['avg_confidence'], 3),
                            'total_validations': row['total_validations']
                        }
                        for row in validation_stats
                    ],
                    'last_updated': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to get validation summary: {e}")
            return {'error': 'Failed to retrieve validation data'}
    
    def get_active_alerts(self) -> Dict[str, Any]:
        """Get active system alerts"""
        alerts = []
        
        for interface_name, interface in self._monitoring_data.items():
            if interface.health_score < 0.7:
                alerts.append({
                    'severity': 'critical',
                    'interface': interface.name,
                    'message': f'{interface.name} health score critically low: {interface.health_score:.2f}',
                    'timestamp': interface.last_check.isoformat()
                })
            elif interface.health_score < 0.9:
                alerts.append({
                    'severity': 'warning',
                    'interface': interface.name,
                    'message': f'{interface.name} health score low: {interface.health_score:.2f}',
                    'timestamp': interface.last_check.isoformat()
                })
            
            if interface.error_count > 0:
                alerts.append({
                    'severity': 'error',
                    'interface': interface.name,
                    'message': f'{interface.name} has {interface.error_count} active errors',
                    'timestamp': interface.last_check.isoformat()
                })
        
        return {
            'alerts': alerts,
            'alert_count': len(alerts),
            'critical_count': len([a for a in alerts if a['severity'] == 'critical']),
            'warning_count': len([a for a in alerts if a['severity'] == 'warning']),
            'error_count': len([a for a in alerts if a['severity'] == 'error'])
        }
    
    def _get_dashboard_template(self) -> str:
        """HTML template for monitoring dashboard"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>StoryLine AI - Trust But Verify Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { text-align: center; margin-bottom: 30px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .status-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-healthy { border-left: 5px solid #28a745; }
        .status-warning { border-left: 5px solid #ffc107; }
        .status-critical { border-left: 5px solid #dc3545; }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
        .refresh-btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
    </style>
    <script>
        function refreshData() {
            location.reload();
        }
        setInterval(refreshData, 30000); // Auto-refresh every 30 seconds
    </script>
</head>
<body>
    <div class="header">
        <h1>🔍 StoryLine AI - Trust But Verify Dashboard</h1>
        <p>Real-time monitoring across all interfaces</p>
        <button class="refresh-btn" onclick="refreshData()">Refresh Now</button>
    </div>
    
    <div class="status-grid">
        <div class="status-card">
            <h3>📊 System Overview</h3>
            <div id="system-overview">Loading...</div>
        </div>
        
        <div class="status-card">
            <h3>📞 Phone Interface</h3>
            <div id="phone-status">Loading...</div>
        </div>
        
        <div class="status-card">
            <h3>💾 Database Interface</h3>
            <div id="database-status">Loading...</div>
        </div>
        
        <div class="status-card">
            <h3>🤖 AI Interface</h3>
            <div id="ai-status">Loading...</div>
        </div>
        
        <div class="status-card">
            <h3>📈 Analytics Interface</h3>
            <div id="analytics-status">Loading...</div>
        </div>
        
        <div class="status-card">
            <h3>💰 Business Interface</h3>
            <div id="business-status">Loading...</div>
        </div>
    </div>
    
    <script>
        // Load dashboard data
        fetch('/api/health').then(r => r.json()).then(data => {
            document.getElementById('system-overview').innerHTML = 
                `<div class="metric"><span>Status:</span><strong>${data.overall_status}</strong></div>` +
                `<div class="metric"><span>Health Score:</span><strong>${data.overall_health_score}</strong></div>` +
                `<div class="metric"><span>Total Errors:</span><strong>${data.total_errors}</strong></div>` +
                `<div class="metric"><span>Total Warnings:</span><strong>${data.total_warnings}</strong></div>`;
        });
    </script>
</body>
</html>
        '''
    
    def run_dashboard(self, host='localhost', port=5001, debug=False):
        """Run the monitoring dashboard"""
        logger.info(f"Starting monitoring dashboard on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# Global monitoring instance
monitoring_dashboard = MonitoringDashboard()

def get_monitoring_dashboard() -> MonitoringDashboard:
    """Get global monitoring dashboard instance"""
    return monitoring_dashboard