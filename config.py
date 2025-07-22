#!/usr/bin/env python3
"""
StoryLine AI - Production Configuration System
Handles all environment-specific settings and runtime configuration
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"

@dataclass
class TwilioConfig:
    """Twilio API configuration"""
    account_sid: str
    auth_token: str
    phone_number: str
    webhook_base_url: str
    voice_model: str = "experimental_conversations"
    enhanced_speech: bool = True
    timeout_seconds: int = 30

@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_connections: int = 10

@dataclass
class VoiceConfig:
    """Voice processing configuration"""
    default_language: str = "en"
    supported_languages: list = field(default_factory=lambda: ["en", "es"])
    speech_timeout: int = 5
    dtmf_timeout: int = 10
    max_story_length_minutes: int = 15

@dataclass
class SecurityConfig:
    """Security and privacy configuration"""
    coppa_compliance: bool = True
    data_retention_days: int = 90
    voice_data_encrypted: bool = True
    session_timeout_minutes: int = 60

@dataclass
class BusinessConfig:
    """Business logic configuration"""
    free_tier_stories_per_month: int = 3
    max_children_per_account: int = 5
    story_personalization_enabled: bool = True
    voice_cloning_enabled: bool = False

@dataclass
class MonitoringConfig:
    """Monitoring and analytics configuration"""
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"
    metrics_enabled: bool = True
    call_recording_enabled: bool = False

class Config:
    """Main configuration manager"""
    
    def __init__(self, env: Optional[str] = None):
        self.env = Environment(env or os.getenv("ENVIRONMENT", "development"))
        self._load_config()
    
    def _load_config(self):
        """Load configuration based on environment"""
        logger.info(f"Loading configuration for {self.env.value} environment")
        
        self.twilio = self._load_twilio_config()
        self.database = self._load_database_config()
        self.voice = self._load_voice_config()
        self.security = self._load_security_config()
        self.business = self._load_business_config()
        self.monitoring = self._load_monitoring_config()
        
        self._validate_config()
    
    def _load_twilio_config(self) -> TwilioConfig:
        """Load Twilio configuration"""
        return TwilioConfig(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            phone_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
            webhook_base_url=os.getenv("BASE_URL", "http://localhost:5000"),
            voice_model="experimental_conversations" if self.env != Environment.PRODUCTION else "default",
            enhanced_speech=True,
            timeout_seconds=30 if self.env == Environment.PRODUCTION else 10
        )
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        if self.env == Environment.PRODUCTION:
            db_path = "/var/lib/storyline/production.db"
        elif self.env == Environment.STAGING:
            db_path = "staging_storyline.db"
        else:
            db_path = "storyline_ai.db"
        
        return DatabaseConfig(
            path=os.getenv("DATABASE_PATH", db_path),
            backup_enabled=self.env == Environment.PRODUCTION,
            backup_interval_hours=24 if self.env == Environment.PRODUCTION else 168,
            max_connections=20 if self.env == Environment.PRODUCTION else 5
        )
    
    def _load_voice_config(self) -> VoiceConfig:
        """Load voice processing configuration"""
        return VoiceConfig(
            default_language=os.getenv("DEFAULT_LANGUAGE", "en"),
            supported_languages=json.loads(os.getenv("SUPPORTED_LANGUAGES", '["en", "es"]')),
            speech_timeout=int(os.getenv("SPEECH_TIMEOUT", "5")),
            dtmf_timeout=int(os.getenv("DTMF_TIMEOUT", "10")),
            max_story_length_minutes=int(os.getenv("MAX_STORY_LENGTH", "15"))
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration"""
        return SecurityConfig(
            coppa_compliance=True,
            data_retention_days=int(os.getenv("DATA_RETENTION_DAYS", "90")),
            voice_data_encrypted=True,
            session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT", "60"))
        )
    
    def _load_business_config(self) -> BusinessConfig:
        """Load business logic configuration"""
        return BusinessConfig(
            free_tier_stories_per_month=int(os.getenv("FREE_TIER_STORIES", "3")),
            max_children_per_account=int(os.getenv("MAX_CHILDREN", "5")),
            story_personalization_enabled=os.getenv("PERSONALIZATION_ENABLED", "true").lower() == "true",
            voice_cloning_enabled=os.getenv("VOICE_CLONING_ENABLED", "false").lower() == "true"
        )
    
    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration"""
        log_level = "ERROR" if self.env == Environment.PRODUCTION else "INFO"
        
        return MonitoringConfig(
            sentry_dsn=os.getenv("SENTRY_DSN"),
            log_level=os.getenv("LOG_LEVEL", log_level),
            metrics_enabled=self.env != Environment.DEVELOPMENT,
            call_recording_enabled=os.getenv("CALL_RECORDING", "false").lower() == "true"
        )
    
    def _validate_config(self):
        """Validate required configuration"""
        errors = []
        
        if not self.twilio.account_sid:
            errors.append("TWILIO_ACCOUNT_SID is required")
        if not self.twilio.auth_token:
            errors.append("TWILIO_AUTH_TOKEN is required")
        if not self.twilio.phone_number:
            errors.append("TWILIO_PHONE_NUMBER is required")
        
        if self.env == Environment.PRODUCTION:
            if not self.monitoring.sentry_dsn:
                logger.warning("SENTRY_DSN not configured for production")
            if not self.database.backup_enabled:
                errors.append("Database backup must be enabled in production")
        
        if errors:
            error_msg = "Configuration validation failed: " + ", ".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask-specific configuration"""
        return {
            "TESTING": False,
            "SECRET_KEY": os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
            "JSON_SORT_KEYS": False,
            "JSONIFY_PRETTYPRINT_REGULAR": False
        }
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.env == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.env == Environment.PRODUCTION
    
    def get_log_level(self) -> int:
        """Get numeric log level"""
        levels = {
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return levels.get(self.monitoring.log_level, logging.INFO)

config = Config()

def get_config() -> Config:
    """Get global configuration instance"""
    return config

def reload_config():
    """Reload configuration (useful for testing)"""
    global config
    config = Config()