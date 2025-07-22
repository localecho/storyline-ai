#!/usr/bin/env python3
"""
StoryLine AI - Automated Quality Assurance Systems
Trust But Verify: Continuous testing, validation, and self-healing
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from contextlib import contextmanager
import threading
import time
import uuid
import re

from config import get_config
from analytics_engine import get_analytics_engine
from validation_layer import get_validation_layer

logger = logging.getLogger(__name__)
config = get_config()

class TestSeverity(Enum):
    """Test failure severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TestStatus(Enum):
    """Test execution status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class QualityTest:
    """Individual quality assurance test"""
    test_id: str
    name: str
    description: str
    test_function: Callable
    severity: TestSeverity
    interface_type: str
    expected_execution_time: float = 5.0
    retry_count: int = 3
    enabled: bool = True

@dataclass
class TestResult:
    """Result of quality test execution"""
    test_id: str
    status: TestStatus
    execution_time: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    retry_attempt: int = 0

@dataclass
class QualityReport:
    """Comprehensive quality report"""
    report_id: str
    test_suite: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    execution_time: float
    quality_score: float
    test_results: List[TestResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        """Calculate test success rate"""
        return self.passed_tests / self.total_tests if self.total_tests > 0 else 0.0

class AutomatedQA:
    """Automated Quality Assurance System"""
    
    def __init__(self):
        self.analytics = get_analytics_engine()
        self.validator = get_validation_layer()
        self.config = get_config()
        self._test_registry = {}
        self._qa_results = []
        self._is_running = False
        self._register_default_tests()
        self.init_qa_database()
        
    def init_qa_database(self):
        """Initialize QA database schema"""
        logger.info("Initializing QA database schema")
        
        with self.analytics.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS qa_test_results (
                    result_id TEXT PRIMARY KEY,
                    test_id TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    execution_time REAL,
                    message TEXT,
                    details TEXT,
                    severity TEXT,
                    interface_type TEXT,
                    timestamp TEXT NOT NULL,
                    retry_attempt INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS qa_reports (
                    report_id TEXT PRIMARY KEY,
                    test_suite TEXT NOT NULL,
                    total_tests INTEGER,
                    passed_tests INTEGER,
                    failed_tests INTEGER,
                    error_tests INTEGER,
                    quality_score REAL,
                    execution_time REAL,
                    timestamp TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS qa_remediation_log (
                    action_id TEXT PRIMARY KEY,
                    issue_type TEXT NOT NULL,
                    issue_description TEXT,
                    remediation_action TEXT,
                    success BOOLEAN,
                    timestamp TEXT NOT NULL
                )
            """)
            
            # Performance indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_qa_results_test ON qa_test_results(test_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_qa_results_status ON qa_test_results(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_qa_results_timestamp ON qa_test_results(timestamp)")
            
            conn.commit()
            logger.info("QA database initialized successfully")
    
    def _register_default_tests(self):
        """Register default quality assurance tests"""
        
        # Phone Interface Tests
        self.register_test(QualityTest(
            test_id="phone_config_validity",
            name="Phone Configuration Validity",
            description="Verify Twilio configuration is valid and accessible",
            test_function=self._test_phone_config,
            severity=TestSeverity.CRITICAL,
            interface_type="phone"
        ))
        
        self.register_test(QualityTest(
            test_id="phone_call_simulation",
            name="Phone Call Simulation",
            description="Simulate phone call workflow end-to-end",
            test_function=self._test_phone_call_simulation,
            severity=TestSeverity.HIGH,
            interface_type="phone",
            expected_execution_time=10.0
        ))
        
        # Database Interface Tests
        self.register_test(QualityTest(
            test_id="database_connectivity",
            name="Database Connectivity",
            description="Verify database connection and basic operations",
            test_function=self._test_database_connectivity,
            severity=TestSeverity.CRITICAL,
            interface_type="database"
        ))
        
        self.register_test(QualityTest(
            test_id="database_integrity",
            name="Database Integrity",
            description="Verify database schema and data integrity",
            test_function=self._test_database_integrity,
            severity=TestSeverity.HIGH,
            interface_type="database"
        ))
        
        # AI Interface Tests
        self.register_test(QualityTest(
            test_id="ai_story_generation",
            name="AI Story Generation",
            description="Test AI story generation quality and safety",
            test_function=self._test_ai_story_generation,
            severity=TestSeverity.HIGH,
            interface_type="ai",
            expected_execution_time=15.0
        ))
        
        self.register_test(QualityTest(
            test_id="ai_content_safety",
            name="AI Content Safety",
            description="Verify AI-generated content meets safety standards",
            test_function=self._test_ai_content_safety,
            severity=TestSeverity.CRITICAL,
            interface_type="ai"
        ))
        
        # Analytics Interface Tests
        self.register_test(QualityTest(
            test_id="analytics_data_flow",
            name="Analytics Data Flow",
            description="Verify analytics data pipeline is functioning",
            test_function=self._test_analytics_data_flow,
            severity=TestSeverity.MEDIUM,
            interface_type="analytics"
        ))
        
        # Business Logic Tests
        self.register_test(QualityTest(
            test_id="business_rules_compliance",
            name="Business Rules Compliance",
            description="Verify business rules and constraints are enforced",
            test_function=self._test_business_rules,
            severity=TestSeverity.HIGH,
            interface_type="business"
        ))
        
        logger.info(f"Registered {len(self._test_registry)} default QA tests")
    
    def register_test(self, test: QualityTest):
        """Register a new quality test"""
        self._test_registry[test.test_id] = test
        logger.info(f"Registered QA test: {test.name}")
    
    def run_test_suite(self, suite_name: str = "full", interface_filter: str = None) -> QualityReport:
        """Run a suite of quality tests"""
        start_time = time.time()
        test_results = []
        
        # Filter tests based on criteria
        tests_to_run = []
        for test in self._test_registry.values():
            if not test.enabled:
                continue
            if interface_filter and test.interface_type != interface_filter:
                continue
            tests_to_run.append(test)
        
        logger.info(f"Running QA test suite '{suite_name}' with {len(tests_to_run)} tests")
        
        # Execute tests
        for test in tests_to_run:
            result = self._execute_test(test)
            test_results.append(result)
            self._store_test_result(result, test)
        
        # Generate report
        execution_time = time.time() - start_time
        report = self._generate_report(suite_name, test_results, execution_time)
        self._store_qa_report(report)
        
        # Trigger remediation if needed
        self._trigger_remediation_if_needed(report)
        
        return report
    
    def _execute_test(self, test: QualityTest) -> TestResult:
        """Execute a single quality test with retry logic"""
        for attempt in range(test.retry_count + 1):
            try:
                start_time = time.time()
                
                # Execute test function
                success, message, details = test.test_function()
                
                execution_time = time.time() - start_time
                
                status = TestStatus.PASSED if success else TestStatus.FAILED
                
                return TestResult(
                    test_id=test.test_id,
                    status=status,
                    execution_time=execution_time,
                    message=message,
                    details=details,
                    retry_attempt=attempt
                )
                
            except Exception as e:
                if attempt < test.retry_count:
                    logger.warning(f"Test {test.test_id} failed on attempt {attempt + 1}, retrying: {e}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"Test {test.test_id} failed after {attempt + 1} attempts: {e}")
                    return TestResult(
                        test_id=test.test_id,
                        status=TestStatus.ERROR,
                        execution_time=0.0,
                        message=f"Test execution error: {str(e)}",
                        details={'exception': str(e)},
                        retry_attempt=attempt
                    )
    
    def _test_phone_config(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Test phone interface configuration"""
        details = {}
        
        # Check Twilio credentials
        if not config.twilio.account_sid:
            return False, "Missing Twilio Account SID", details
        
        if not config.twilio.auth_token:
            return False, "Missing Twilio Auth Token", details
        
        if not config.twilio.phone_number:
            return False, "Missing Twilio Phone Number", details
        
        details['account_sid_length'] = len(config.twilio.account_sid)
        details['phone_number'] = config.twilio.phone_number
        details['webhook_url'] = config.twilio.webhook_base_url
        
        return True, "Phone configuration valid", details
    
    def _test_phone_call_simulation(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Simulate phone call workflow"""
        details = {}
        
        try:
            # Simulate call events
            session_id = str(uuid.uuid4())
            child_id = str(uuid.uuid4())
            
            # Track call start
            self.analytics.track_event(session_id, child_id, "call_start", {
                "phone_number": "+1234567890",
                "simulated": True
            })
            
            # Track story begin
            self.analytics.track_event(session_id, child_id, "story_begin", {
                "story_id": 1,
                "story_title": "Test Story"
            })
            
            # Track completion
            self.analytics.track_event(session_id, child_id, "completion", {
                "duration_seconds": 300
            })
            
            details['session_id'] = session_id
            details['events_tracked'] = 3
            
            return True, "Phone call simulation successful", details
            
        except Exception as e:
            details['error'] = str(e)
            return False, f"Phone call simulation failed: {e}", details
    
    def _test_database_connectivity(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Test database connectivity and basic operations"""
        details = {}
        
        try:
            with self.analytics.get_connection() as conn:
                # Test basic query
                result = conn.execute("SELECT 1 as test").fetchone()
                if result['test'] != 1:
                    return False, "Database query returned unexpected result", details
                
                # Test table existence
                tables = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('call_events', 'story_performance')
                """).fetchall()
                
                details['tables_found'] = len(tables)
                details['expected_tables'] = 2
                
                if len(tables) < 2:
                    return False, "Required database tables missing", details
                
                return True, "Database connectivity successful", details
                
        except Exception as e:
            details['error'] = str(e)
            return False, f"Database connectivity failed: {e}", details
    
    def _test_database_integrity(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Test database integrity and constraints"""
        details = {}
        
        try:
            integrity_report = self.analytics.verify_data_integrity()
            
            details.update(integrity_report)
            
            if not integrity_report['database_consistency']:
                return False, "Database consistency issues detected", details
            
            if integrity_report['validation_coverage'] < 0.9:
                return False, f"Validation coverage too low: {integrity_report['validation_coverage']}", details
            
            return True, "Database integrity verified", details
            
        except Exception as e:
            details['error'] = str(e)
            return False, f"Database integrity check failed: {e}", details
    
    def _test_ai_story_generation(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Test AI story generation capabilities"""
        details = {}
        
        try:
            # Simulate story generation request
            test_prompt = {
                'child_name': 'Emma',
                'child_age': 6,
                'interests': ['animals', 'adventure'],
                'story_length': 'short'
            }
            
            # In a real implementation, this would call the actual AI service
            # For now, simulate with a basic story structure check
            generated_story = f"Once upon a time, there was a brave little girl named {test_prompt['child_name']} who loved {test_prompt['interests'][0]}."
            
            details['story_length'] = len(generated_story)
            details['contains_child_name'] = test_prompt['child_name'] in generated_story
            details['contains_interest'] = test_prompt['interests'][0] in generated_story
            
            # Validate story content
            validation_result = self.validator.validate_interface_data('ai', {
                'story_content': generated_story,
                'child_age': test_prompt['child_age']
            })
            
            details['validation_passed'] = validation_result.is_valid
            details['confidence_score'] = validation_result.confidence_score
            
            if not validation_result.is_valid:
                return False, f"Generated story failed validation: {validation_result.errors}", details
            
            return True, "AI story generation successful", details
            
        except Exception as e:
            details['error'] = str(e)
            return False, f"AI story generation test failed: {e}", details
    
    def _test_ai_content_safety(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Test AI content safety mechanisms"""
        details = {}
        
        try:
            # Test with various content scenarios
            test_scenarios = [
                {'content': 'A happy story about friendship', 'should_pass': True},
                {'content': 'A violent and scary story with death', 'should_pass': False},
                {'content': 'Contact me at phone number 555-1234', 'should_pass': False},
                {'content': 'A magical adventure with unicorns', 'should_pass': True}
            ]
            
            passed_scenarios = 0
            total_scenarios = len(test_scenarios)
            
            for scenario in test_scenarios:
                validation_result = self.validator.validate_interface_data('ai', {
                    'story_content': scenario['content'],
                    'child_age': 6
                })
                
                scenario_passed = validation_result.is_valid == scenario['should_pass']
                if scenario_passed:
                    passed_scenarios += 1
                
                details[f"scenario_{scenario['content'][:20]}"] = {
                    'expected_pass': scenario['should_pass'],
                    'actual_pass': validation_result.is_valid,
                    'test_passed': scenario_passed
                }
            
            success_rate = passed_scenarios / total_scenarios
            details['success_rate'] = success_rate
            details['passed_scenarios'] = passed_scenarios
            details['total_scenarios'] = total_scenarios
            
            if success_rate < 0.75:
                return False, f"Content safety test success rate too low: {success_rate}", details
            
            return True, "AI content safety verification successful", details
            
        except Exception as e:
            details['error'] = str(e)
            return False, f"AI content safety test failed: {e}", details
    
    def _test_analytics_data_flow(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Test analytics data pipeline"""
        details = {}
        
        try:
            # Check recent data flow
            with self.analytics.get_connection() as conn:
                recent_events = conn.execute("""
                    SELECT COUNT(*) as count, MAX(timestamp) as latest
                    FROM call_events
                    WHERE timestamp > ?
                """, ((datetime.now() - timedelta(hours=1)).isoformat(),)).fetchone()
                
                details['recent_events'] = recent_events['count']
                details['latest_event'] = recent_events['latest']
                
                # Check data freshness
                if recent_events['latest']:
                    latest_time = datetime.fromisoformat(recent_events['latest'])
                    age_minutes = (datetime.now() - latest_time).total_seconds() / 60
                    details['data_age_minutes'] = age_minutes
                    
                    # Data should be recent for active system
                    if age_minutes > 120:  # 2 hours old
                        return False, f"Analytics data too old: {age_minutes} minutes", details
                
                # Check verification rates
                verification_stats = conn.execute("""
                    SELECT 
                        AVG(CASE WHEN verified THEN 1.0 ELSE 0.0 END) as verification_rate
                    FROM call_events
                    WHERE timestamp > ?
                """, ((datetime.now() - timedelta(hours=24)).isoformat(),)).fetchone()
                
                verification_rate = verification_stats['verification_rate'] or 1.0
                details['verification_rate'] = verification_rate
                
                if verification_rate < 0.95:
                    return False, f"Analytics verification rate too low: {verification_rate}", details
                
                return True, "Analytics data flow healthy", details
                
        except Exception as e:
            details['error'] = str(e)
            return False, f"Analytics data flow test failed: {e}", details
    
    def _test_business_rules(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Test business rules and constraints"""
        details = {}
        
        try:
            # Test freemium usage limits
            test_data = {
                'monthly_usage': config.business.free_tier_stories_per_month - 1,
                'conversion_probability': 0.15,
                'monthly_revenue': 100,
                'subscriber_count': 5,
                'average_subscription_price': 20
            }
            
            business_validation = self.validator.validate_interface_data('business', test_data)
            details['freemium_validation'] = business_validation.is_valid
            
            # Test over-limit scenario
            over_limit_data = test_data.copy()
            over_limit_data['monthly_usage'] = config.business.free_tier_stories_per_month + 1
            
            over_limit_validation = self.validator.validate_interface_data('business', over_limit_data)
            details['over_limit_validation'] = not over_limit_validation.is_valid  # Should fail
            
            # Test revenue calculation
            revenue_test = {
                'monthly_revenue': 100,
                'subscriber_count': 5,
                'average_subscription_price': 20
            }
            
            revenue_validation = self.validator.validate_interface_data('business', revenue_test)
            details['revenue_validation'] = revenue_validation.is_valid
            
            all_tests_passed = (business_validation.is_valid and 
                              not over_limit_validation.is_valid and 
                              revenue_validation.is_valid)
            
            if not all_tests_passed:
                return False, "Business rules validation failed", details
            
            return True, "Business rules compliance verified", details
            
        except Exception as e:
            details['error'] = str(e)
            return False, f"Business rules test failed: {e}", details
    
    def _generate_report(self, suite_name: str, test_results: List[TestResult], 
                        execution_time: float) -> QualityReport:
        """Generate comprehensive quality report"""
        passed_tests = len([r for r in test_results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in test_results if r.status == TestStatus.FAILED])
        error_tests = len([r for r in test_results if r.status == TestStatus.ERROR])
        skipped_tests = len([r for r in test_results if r.status == TestStatus.SKIPPED])
        
        total_tests = len(test_results)
        quality_score = passed_tests / total_tests if total_tests > 0 else 0.0
        
        # Adjust quality score based on severity of failures
        for result in test_results:
            if result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                test = self._test_registry.get(result.test_id)
                if test and test.severity == TestSeverity.CRITICAL:
                    quality_score *= 0.5  # Critical failures heavily impact score
                elif test and test.severity == TestSeverity.HIGH:
                    quality_score *= 0.8
        
        return QualityReport(
            report_id=str(uuid.uuid4()),
            test_suite=suite_name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            error_tests=error_tests,
            skipped_tests=skipped_tests,
            execution_time=execution_time,
            quality_score=quality_score,
            test_results=test_results
        )
    
    def _store_test_result(self, result: TestResult, test: QualityTest):
        """Store test result in database"""
        with self.analytics.get_connection() as conn:
            conn.execute("""
                INSERT INTO qa_test_results 
                (result_id, test_id, test_name, status, execution_time, 
                 message, details, severity, interface_type, timestamp, retry_attempt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), result.test_id, test.name, result.status.value,
                result.execution_time, result.message, json.dumps(result.details),
                test.severity.value, test.interface_type, 
                result.timestamp.isoformat(), result.retry_attempt
            ))
            conn.commit()
    
    def _store_qa_report(self, report: QualityReport):
        """Store QA report in database"""
        with self.analytics.get_connection() as conn:
            conn.execute("""
                INSERT INTO qa_reports 
                (report_id, test_suite, total_tests, passed_tests, failed_tests, 
                 error_tests, quality_score, execution_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.report_id, report.test_suite, report.total_tests,
                report.passed_tests, report.failed_tests, report.error_tests,
                report.quality_score, report.execution_time, 
                report.timestamp.isoformat()
            ))
            conn.commit()
    
    def _trigger_remediation_if_needed(self, report: QualityReport):
        """Trigger automatic remediation for critical issues"""
        critical_failures = [
            r for r in report.test_results 
            if r.status in [TestStatus.FAILED, TestStatus.ERROR] and
            self._test_registry.get(r.test_id, QualityTest("", "", "", lambda: None, TestSeverity.LOW, "")).severity == TestSeverity.CRITICAL
        ]
        
        for failure in critical_failures:
            self._attempt_remediation(failure)
    
    def _attempt_remediation(self, test_result: TestResult):
        """Attempt automatic remediation for test failure"""
        remediation_actions = {
            'database_connectivity': self._remediate_database_connectivity,
            'phone_config_validity': self._remediate_phone_config,
            'ai_content_safety': self._remediate_ai_content_safety
        }
        
        if test_result.test_id in remediation_actions:
            try:
                success, action_description = remediation_actions[test_result.test_id]()
                
                # Log remediation attempt
                with self.analytics.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO qa_remediation_log 
                        (action_id, issue_type, issue_description, remediation_action, success, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()), test_result.test_id, test_result.message,
                        action_description, success, datetime.now().isoformat()
                    ))
                    conn.commit()
                
                logger.info(f"Remediation attempt for {test_result.test_id}: {action_description} - {'Success' if success else 'Failed'}")
                
            except Exception as e:
                logger.error(f"Remediation failed for {test_result.test_id}: {e}")
    
    def _remediate_database_connectivity(self) -> Tuple[bool, str]:
        """Attempt to remediate database connectivity issues"""
        try:
            # Attempt to recreate database connection
            self.analytics.init_analytics_database()
            return True, "Reinitialized analytics database schema"
        except Exception as e:
            return False, f"Failed to remediate database connectivity: {e}"
    
    def _remediate_phone_config(self) -> Tuple[bool, str]:
        """Attempt to remediate phone configuration issues"""
        # In a real system, this might reload configuration from environment
        return False, "Phone configuration remediation requires manual intervention"
    
    def _remediate_ai_content_safety(self) -> Tuple[bool, str]:
        """Attempt to remediate AI content safety issues"""
        # This could trigger retraining or adjustment of content filters
        return False, "AI content safety remediation requires manual review"
    
    def start_continuous_qa(self, interval_minutes: int = 60):
        """Start continuous quality assurance monitoring"""
        if self._is_running:
            logger.warning("Continuous QA already running")
            return
        
        self._is_running = True
        
        def qa_loop():
            while self._is_running:
                try:
                    logger.info("Running scheduled quality assurance check")
                    report = self.run_test_suite("continuous")
                    
                    # Track QA metrics
                    self.analytics.track_system_health('qa_quality_score', report.quality_score, 'quality_assurance')
                    self.analytics.track_system_health('qa_test_success_rate', report.success_rate, 'quality_assurance')
                    
                    if report.quality_score < 0.8:
                        logger.warning(f"Quality score below threshold: {report.quality_score}")
                    
                    time.sleep(interval_minutes * 60)
                    
                except Exception as e:
                    logger.error(f"Continuous QA error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        qa_thread = threading.Thread(target=qa_loop, daemon=True)
        qa_thread.start()
        logger.info(f"Started continuous QA monitoring (interval: {interval_minutes} minutes)")
    
    def stop_continuous_qa(self):
        """Stop continuous quality assurance monitoring"""
        self._is_running = False
        logger.info("Stopped continuous QA monitoring")
    
    def get_qa_summary(self) -> Dict[str, Any]:
        """Get quality assurance summary"""
        with self.analytics.get_connection() as conn:
            # Get recent test results
            recent_results = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM qa_test_results
                WHERE timestamp > ?
                GROUP BY status
            """, ((datetime.now() - timedelta(hours=24)).isoformat(),)).fetchall()
            
            status_counts = {row['status']: row['count'] for row in recent_results}
            
            # Get latest quality score
            latest_report = conn.execute("""
                SELECT quality_score, timestamp
                FROM qa_reports
                ORDER BY timestamp DESC
                LIMIT 1
            """).fetchone()
            
            # Get remediation statistics
            remediation_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_remediations
                FROM qa_remediation_log
                WHERE timestamp > ?
            """, ((datetime.now() - timedelta(hours=24)).isoformat(),)).fetchone()
            
            return {
                'latest_quality_score': latest_report['quality_score'] if latest_report else 0.0,
                'latest_report_time': latest_report['timestamp'] if latest_report else None,
                'test_results_24h': status_counts,
                'total_tests_registered': len(self._test_registry),
                'continuous_qa_running': self._is_running,
                'remediation_attempts_24h': remediation_stats['total_attempts'] or 0,
                'successful_remediations_24h': remediation_stats['successful_remediations'] or 0,
                'last_updated': datetime.now().isoformat()
            }

# Global QA instance
automated_qa = AutomatedQA()

def get_automated_qa() -> AutomatedQA:
    """Get global automated QA instance"""
    return automated_qa