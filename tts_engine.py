#!/usr/bin/env python3
"""
StoryLine AI - Cost-Optimized Text-to-Speech Engine
Implements smart TTS selection based on budget and quality needs
"""

import os
import subprocess
import tempfile
import json
from enum import Enum
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TTSProvider(Enum):
    """Available TTS providers with cost implications"""
    LOCAL_SAY = "local_say"           # macOS built-in (FREE)
    GOOGLE_FREE = "google_free"       # Google Cloud free tier
    AMAZON_FREE = "amazon_free"       # Amazon Polly free tier
    OPENAI = "openai"                 # OpenAI TTS ($15/1M chars)
    ELEVENLABS = "elevenlabs"         # ElevenLabs ($5-99/month)
    AZURE = "azure"                   # Azure Speech ($4/1M chars)

@dataclass
class TTSUsage:
    """Track TTS usage for cost management"""
    characters_used: int = 0
    api_calls_made: int = 0
    current_spend: float = 0.0
    last_reset: str = ""

@dataclass
class VoiceProfile:
    """Voice configuration for different story types"""
    name: str
    provider: TTSProvider
    voice_id: str
    rate: int = 150  # Words per minute
    pitch: int = 50  # Pitch adjustment
    suitable_for: list = None

class CostOptimizedTTS:
    """Smart TTS engine that minimizes costs while maintaining quality"""
    
    def __init__(self):
        self.monthly_budget = float(os.getenv('MONTHLY_TTS_BUDGET', '0'))
        self.testing_mode = os.getenv('TESTING_MODE', 'local_tts')
        self.quality_preference = os.getenv('TTS_QUALITY', 'basic')
        
        # Load usage tracking
        self.usage_file = "tts_usage.json"
        self.usage = self._load_usage()
        
        # Voice profiles for different scenarios
        self.voice_profiles = self._setup_voice_profiles()
        
        # Provider cost per 1M characters
        self.provider_costs = {
            TTSProvider.LOCAL_SAY: 0.0,
            TTSProvider.GOOGLE_FREE: 4.0,  # After free tier
            TTSProvider.AMAZON_FREE: 4.0,   # After free tier
            TTSProvider.OPENAI: 15.0,
            TTSProvider.ELEVENLABS: 22.0,   # Monthly minimum
            TTSProvider.AZURE: 4.0
        }
        
        # Free tier limits (characters per month)
        self.free_tier_limits = {
            TTSProvider.GOOGLE_FREE: 1_000_000,
            TTSProvider.AMAZON_FREE: 5_000_000,
            TTSProvider.AZURE: 500_000
        }
    
    def _load_usage(self) -> TTSUsage:
        """Load usage tracking from file"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    return TTSUsage(**data)
        except Exception as e:
            logger.warning(f"Could not load usage data: {e}")
        
        return TTSUsage(last_reset=datetime.now().strftime("%Y-%m"))
    
    def _save_usage(self):
        """Save usage tracking to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump({
                    'characters_used': self.usage.characters_used,
                    'api_calls_made': self.usage.api_calls_made,
                    'current_spend': self.usage.current_spend,
                    'last_reset': self.usage.last_reset
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save usage data: {e}")
    
    def _setup_voice_profiles(self) -> Dict[str, VoiceProfile]:
        """Setup voice profiles for different story types"""
        return {
            "narrator_female": VoiceProfile(
                name="Female Narrator",
                provider=TTSProvider.LOCAL_SAY,
                voice_id="Alice",
                rate=140,
                suitable_for=["general", "fantasy", "adventure"]
            ),
            "narrator_male": VoiceProfile(
                name="Male Narrator", 
                provider=TTSProvider.LOCAL_SAY,
                voice_id="Daniel",
                rate=135,
                suitable_for=["general", "space", "superhero"]
            ),
            "child_friendly": VoiceProfile(
                name="Child Friendly",
                provider=TTSProvider.LOCAL_SAY,
                voice_id="Princess",
                rate=130,
                suitable_for=["young_children", "fairy_tale"]
            ),
            "premium_female": VoiceProfile(
                name="Premium Female",
                provider=TTSProvider.GOOGLE_FREE,
                voice_id="en-US-Wavenet-C",
                rate=145,
                suitable_for=["premium", "emotional"]
            )
        }
    
    def select_optimal_provider(self, text: str, quality_needed: str = "basic", 
                              voice_type: str = "narrator_female") -> Tuple[TTSProvider, VoiceProfile]:
        """Smart provider selection based on cost, quality, and budget"""
        text_length = len(text)
        
        # Always use free local for basic testing
        if self.testing_mode == 'local_tts' or quality_needed == "test":
            profile = self.voice_profiles.get(voice_type, self.voice_profiles["narrator_female"])
            if profile.provider == TTSProvider.LOCAL_SAY:
                return TTSProvider.LOCAL_SAY, profile
        
        # Check monthly budget constraints
        if self.usage.current_spend >= self.monthly_budget:
            logger.info("Monthly budget exceeded, falling back to local TTS")
            return TTSProvider.LOCAL_SAY, self.voice_profiles["narrator_female"]
        
        # Check free tier availability
        for provider, limit in self.free_tier_limits.items():
            if self.usage.characters_used < limit:
                # Use free tier
                if provider == TTSProvider.GOOGLE_FREE and quality_needed in ["good", "premium"]:
                    return provider, self.voice_profiles["premium_female"]
        
        # Calculate cost for paid services
        cost_per_char = self.provider_costs.get(TTSProvider.OPENAI, 0) / 1_000_000
        estimated_cost = text_length * cost_per_char
        
        if quality_needed == "premium" and self.usage.current_spend + estimated_cost <= self.monthly_budget:
            return TTSProvider.OPENAI, self.voice_profiles["premium_female"]
        
        # Fallback to local
        return TTSProvider.LOCAL_SAY, self.voice_profiles[voice_type]
    
    def synthesize_speech(self, text: str, voice_type: str = "narrator_female", 
                         quality: str = "basic") -> Optional[bytes]:
        """Generate speech audio with cost optimization"""
        provider, voice_profile = self.select_optimal_provider(text, quality, voice_type)
        
        logger.info(f"Using {provider.value} for TTS ({len(text)} characters)")
        
        try:
            if provider == TTSProvider.LOCAL_SAY:
                audio_data = self._local_macos_tts(text, voice_profile)
            elif provider == TTSProvider.GOOGLE_FREE:
                audio_data = self._google_tts(text, voice_profile)
            elif provider == TTSProvider.AMAZON_FREE:
                audio_data = self._amazon_tts(text, voice_profile)
            elif provider == TTSProvider.OPENAI:
                audio_data = self._openai_tts(text, voice_profile)
            else:
                # Fallback to local
                audio_data = self._local_macos_tts(text, voice_profile)
            
            # Update usage tracking
            self._update_usage(len(text), provider)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"TTS failed with {provider.value}: {e}")
            # Fallback to local TTS
            if provider != TTSProvider.LOCAL_SAY:
                return self._local_macos_tts(text, self.voice_profiles["narrator_female"])
            return None
    
    def _local_macos_tts(self, text: str, voice_profile: VoiceProfile) -> bytes:
        """Generate speech using macOS built-in TTS (completely free)"""
        with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Use macOS say command with voice customization
            cmd = [
                "say",
                "-v", voice_profile.voice_id,
                "-r", str(voice_profile.rate),
                "-o", temp_path,
                text
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"say command failed: {result.stderr}")
                return b""
            
            # Read the generated audio file
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            return audio_data
            
        except subprocess.TimeoutExpired:
            logger.error("TTS generation timed out")
            return b""
        except Exception as e:
            logger.error(f"Local TTS error: {e}")
            return b""
        finally:
            # Cleanup temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def _google_tts(self, text: str, voice_profile: VoiceProfile) -> bytes:
        """Google Cloud Text-to-Speech (has free tier)"""
        try:
            logger.info(f"Using Google TTS with voice {voice_profile.voice_id}")
            
            # In production, would use google-cloud-texttospeech
            # For now, fallback to local
            return self._local_macos_tts(text, voice_profile)
            
        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return self._local_macos_tts(text, voice_profile)
    
    def _amazon_tts(self, text: str, voice_profile: VoiceProfile) -> bytes:
        """Amazon Polly TTS (has generous free tier)"""
        try:
            logger.info(f"Using Amazon Polly with voice {voice_profile.voice_id}")
            
            # In production, would use boto3
            # For now, fallback to local
            return self._local_macos_tts(text, voice_profile)
            
        except Exception as e:
            logger.error(f"Amazon TTS error: {e}")
            return self._local_macos_tts(text, voice_profile)
    
    def _openai_tts(self, text: str, voice_profile: VoiceProfile) -> bytes:
        """OpenAI TTS (premium quality, costs money)"""
        try:
            logger.info(f"Using OpenAI TTS with voice {voice_profile.voice_id}")
            
            # In production, would use openai library
            # For now, fallback to local
            return self._local_macos_tts(text, voice_profile)
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            return self._local_macos_tts(text, voice_profile)
    
    def _update_usage(self, character_count: int, provider: TTSProvider):
        """Update usage tracking and costs"""
        self.usage.characters_used += character_count
        self.usage.api_calls_made += 1
        
        # Calculate cost
        if provider != TTSProvider.LOCAL_SAY:
            # Check if within free tier
            free_limit = self.free_tier_limits.get(provider, 0)
            if self.usage.characters_used > free_limit:
                # Calculate cost for characters over free limit
                paid_chars = min(character_count, self.usage.characters_used - free_limit)
                cost_per_char = self.provider_costs[provider] / 1_000_000
                additional_cost = paid_chars * cost_per_char
                self.usage.current_spend += additional_cost
        
        self._save_usage()
    
    def get_cost_report(self) -> Dict[str, Any]:
        """Generate detailed cost and usage report"""
        report = {
            "current_month": datetime.now().strftime("%Y-%m"),
            "characters_used": self.usage.characters_used,
            "api_calls_made": self.usage.api_calls_made,
            "current_spend": round(self.usage.current_spend, 2),
            "monthly_budget": self.monthly_budget,
            "budget_remaining": round(self.monthly_budget - self.usage.current_spend, 2),
            "free_tier_status": {}
        }
        
        # Check free tier status for each provider
        for provider, limit in self.free_tier_limits.items():
            remaining = max(0, limit - self.usage.characters_used)
            report["free_tier_status"][provider.value] = {
                "limit": limit,
                "used": min(self.usage.characters_used, limit),
                "remaining": remaining,
                "percentage_used": round((min(self.usage.characters_used, limit) / limit) * 100, 1)
            }
        
        return report
    
    def reset_monthly_usage(self):
        """Reset usage counters for new month"""
        self.usage = TTSUsage(last_reset=datetime.now().strftime("%Y-%m"))
        self._save_usage()
        logger.info("Monthly usage reset")

def get_available_voices() -> Dict[str, list]:
    """Get list of available voices for each provider"""
    voices = {
        "local_macos": ["Alice", "Daniel", "Victoria", "Princess", "Fred", "Vicki"],
        "google_free": ["en-US-Wavenet-C", "en-US-Wavenet-D", "en-US-Standard-C"],
        "amazon_free": ["Joanna", "Matthew", "Ivy", "Justin"],
        "openai": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    }
    return voices