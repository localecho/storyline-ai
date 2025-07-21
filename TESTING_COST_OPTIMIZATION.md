# 💰 StoryLine AI - Cost-Effective Testing Guide

> **Goal**: Minimize API costs during development while maintaining realistic testing

## 🎯 Text-to-Speech Cost Analysis (2025)

### 🆓 **FREE Options (Best for Testing)**

#### 1. **macOS Built-in `say` Command** ⭐ RECOMMENDED
```bash
# Completely free, no API calls
say "Hello Emma, ready for your magical story?"
say -v Alice "Once upon a time in a magical forest..."
say -v Victoria -r 150 "Sweet dreams, goodnight!"
```
- **Cost**: $0 (uses system TTS)
- **Voices**: 40+ built-in voices
- **Quality**: Good for testing
- **Rate Limits**: None

#### 2. **Google Cloud Text-to-Speech FREE Tier**
```python
# 1 million characters FREE per month
from google.cloud import texttospeech
client = texttospeech.TextToSpeechClient()
```
- **Free Tier**: 1M characters/month
- **Cost After**: $4.00 per 1M characters
- **Quality**: Excellent
- **Voices**: 220+ voices, 40+ languages

#### 3. **Amazon Polly FREE Tier**
```python
# 5 million characters FREE for 12 months
import boto3
polly = boto3.client('polly')
```
- **Free Tier**: 5M characters for 12 months
- **Cost After**: $4.00 per 1M characters
- **Quality**: Excellent
- **Voices**: 60+ voices, 29 languages

### 💸 **Low-Cost Premium Options**

#### 1. **OpenAI TTS** (Production Quality)
```python
# $15.00 per 1M characters
from openai import OpenAI
client = OpenAI()
response = client.audio.speech.create(
    model="tts-1",  # Cheaper than tts-1-hd
    voice="alloy",
    input="Your story text here"
)
```
- **Cost**: $15.00 per 1M characters
- **Quality**: Very high
- **Voices**: 6 voices (alloy, echo, fable, onyx, nova, shimmer)

#### 2. **ElevenLabs** (Best Voice Cloning)
```python
# $5-$99/month based on usage
import elevenlabs
client = elevenlabs.Client(api_key="your-api-key")
```
- **Free Tier**: 10,000 characters/month
- **Starter**: $5/month (30,000 chars)
- **Creator**: $22/month (100,000 chars)
- **Quality**: Exceptional (voice cloning)

#### 3. **Azure Speech Services**
```python
# $4.00 per 1M characters
import azure.cognitiveservices.speech as speechsdk
```
- **Free Tier**: 500,000 characters/month
- **Cost**: $4.00 per 1M characters
- **Quality**: Excellent
- **Voices**: 400+ voices, 140+ languages

## 🧪 **Testing Strategy by Development Phase**

### Phase 1: Initial Development (FREE)
```bash
# Use macOS say command for all testing
export TESTING_MODE="local_tts"
export TTS_COMMAND="say"
```

### Phase 2: Realistic Testing (LOW COST)
```bash
# Mix of local + Google Cloud free tier
export TESTING_MODE="hybrid"
export FALLBACK_TTS="say"
```

### Phase 3: Production Testing (BUDGET)
```bash
# Small budget for high-quality testing
export TESTING_MODE="production"
export MONTHLY_TTS_BUDGET="20"  # $20/month
```

## 🛠️ **Implementation: Cost-Optimized TTS Engine**

### Smart TTS Router
```python
import os
import subprocess
from enum import Enum
from typing import Optional

class TTSProvider(Enum):
    LOCAL_SAY = "local_say"
    GOOGLE_FREE = "google_free" 
    AMAZON_FREE = "amazon_free"
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"

class CostOptimizedTTS:
    def __init__(self):
        self.monthly_budget = float(os.getenv('MONTHLY_TTS_BUDGET', '0'))
        self.current_spend = 0.0
        self.character_count = 0
        
    def select_provider(self, text: str, quality_needed: str = "basic") -> TTSProvider:
        """Smart provider selection based on cost and quality needs"""
        text_length = len(text)
        
        # Always use free local for development
        if os.getenv('TESTING_MODE') == 'local_tts':
            return TTSProvider.LOCAL_SAY
            
        # Check budget constraints
        if self.current_spend >= self.monthly_budget:
            return TTSProvider.LOCAL_SAY
            
        # Quality-based selection
        if quality_needed == "basic":
            # Use free tiers first
            if self.character_count < 1_000_000:  # Google free tier
                return TTSProvider.GOOGLE_FREE
            elif self.character_count < 5_000_000:  # Amazon free tier
                return TTSProvider.AMAZON_FREE
            else:
                return TTSProvider.LOCAL_SAY
                
        elif quality_needed == "premium":
            # Use paid services within budget
            estimated_cost = (text_length / 1_000_000) * 15  # OpenAI pricing
            if self.current_spend + estimated_cost <= self.monthly_budget:
                return TTSProvider.OPENAI
            else:
                return TTSProvider.GOOGLE_FREE
                
        return TTSProvider.LOCAL_SAY
    
    def synthesize_speech(self, text: str, voice: str = "default", 
                         quality: str = "basic") -> bytes:
        """Generate speech with cost optimization"""
        provider = self.select_provider(text, quality)
        
        if provider == TTSProvider.LOCAL_SAY:
            return self._local_tts(text, voice)
        elif provider == TTSProvider.GOOGLE_FREE:
            return self._google_tts(text, voice)
        elif provider == TTSProvider.AMAZON_FREE:
            return self._amazon_tts(text, voice)
        elif provider == TTSProvider.OPENAI:
            return self._openai_tts(text, voice)
        elif provider == TTSProvider.ELEVENLABS:
            return self._elevenlabs_tts(text, voice)
    
    def _local_tts(self, text: str, voice: str) -> bytes:
        """Free macOS TTS"""
        voice_map = {
            "default": "Alice",
            "male": "Daniel", 
            "female": "Victoria",
            "child": "Princess"
        }
        
        selected_voice = voice_map.get(voice, "Alice")
        
        # Generate to temporary file
        temp_file = "/tmp/storyline_tts.aiff"
        subprocess.run([
            "say", "-v", selected_voice, 
            "-o", temp_file, text
        ])
        
        with open(temp_file, "rb") as f:
            return f.read()
    
    def _google_tts(self, text: str, voice: str) -> bytes:
        """Google Cloud TTS (free tier)"""
        # Implementation would go here
        # Track usage against free tier limits
        self.character_count += len(text)
        return b"audio_data"
    
    def get_cost_report(self) -> dict:
        """Track spending and usage"""
        return {
            "current_spend": self.current_spend,
            "monthly_budget": self.monthly_budget,
            "character_count": self.character_count,
            "budget_remaining": self.monthly_budget - self.current_spend,
            "free_tier_remaining": max(0, 1_000_000 - self.character_count)
        }
```

## 📊 **Cost Estimation Calculator**

### Typical Story Lengths
- **Short Story (2 min)**: ~300 words = ~1,800 characters
- **Medium Story (5 min)**: ~750 words = ~4,500 characters  
- **Long Story (8 min)**: ~1,200 words = ~7,200 characters

### Monthly Testing Costs
```python
def calculate_monthly_costs():
    stories_per_day = 10  # Testing volume
    avg_story_length = 4500  # characters
    days_per_month = 30
    
    total_chars = stories_per_day * avg_story_length * days_per_month
    # = 10 * 4,500 * 30 = 1,350,000 characters/month
    
    costs = {
        "Local (say)": 0,
        "Google (free)": 0 if total_chars <= 1_000_000 else (total_chars - 1_000_000) * 0.000004,
        "Amazon (free)": 0 if total_chars <= 5_000_000 else (total_chars - 5_000_000) * 0.000004,
        "OpenAI": total_chars * 0.000015,  # $15 per 1M chars
        "ElevenLabs": 22 if total_chars <= 100_000 else 99  # Monthly plans
    }
    
    return costs

# Result for 1.35M chars/month:
# Local: $0
# Google: $1.40 (350K chars over free tier)  
# Amazon: $0 (under free tier)
# OpenAI: $20.25
# ElevenLabs: $22-99
```

## 🔧 **Recommended Testing Setup**

### Development Environment (.env)
```bash
# Cost optimization settings
TESTING_MODE=local_tts
MONTHLY_TTS_BUDGET=0
TTS_FALLBACK=say
TTS_QUALITY=basic

# Twilio settings (for phone testing)
TWILIO_ACCOUNT_SID=your_test_sid
TWILIO_AUTH_TOKEN=your_test_token
TWILIO_PHONE_NUMBER=your_test_number

# Use ngrok for local testing (free)
BASE_URL=https://your-id.ngrok.io
```

### Production-Ready Testing (.env.production)
```bash
# Mixed approach for realistic testing
TESTING_MODE=hybrid
MONTHLY_TTS_BUDGET=20
TTS_PRIMARY=google_free
TTS_FALLBACK=local_say
TTS_QUALITY=premium

# Production APIs
GOOGLE_CLOUD_PROJECT_ID=your_project
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### Testing Scripts
```bash
#!/bin/bash
# test_tts_costs.sh - Monitor costs during testing

echo "🧪 Starting cost-optimized TTS testing..."

# Test with local TTS first
TESTING_MODE=local_tts python test_story_generation.py

# Check if we want to test premium
read -p "Test with premium TTS? (costs money) [y/N]: " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    TESTING_MODE=production MONTHLY_TTS_BUDGET=5 python test_story_generation.py
fi

echo "✅ Testing complete. Check cost_report.json for usage."
```

## 🎯 **Free Testing Strategy (Recommended)**

1. **Use macOS `say` for 90% of testing**
   - Perfect for logic testing
   - No API costs
   - Multiple voices available

2. **Google Cloud free tier for quality testing**
   - 1M characters/month free
   - Test a few stories with production quality

3. **Twilio trial credits for phone testing**
   - $15 in free credits
   - Enough for extensive phone integration testing

4. **ngrok free tier for webhooks**
   - Free local tunnel
   - Perfect for development testing

### Total Monthly Testing Cost: **$0**

## 📈 **Scaling Strategy**

### When to Upgrade TTS
1. **User Feedback**: "Voice sounds robotic"
2. **Engagement Metrics**: Low story completion rates
3. **Revenue**: When monthly revenue > $100
4. **Feature Needs**: Voice cloning requirements

### Cost-Effective Scaling
```python
def should_upgrade_tts(metrics: dict) -> bool:
    """Smart upgrade decision based on business metrics"""
    monthly_revenue = metrics.get('monthly_revenue', 0)
    completion_rate = metrics.get('story_completion_rate', 0)
    user_complaints = metrics.get('voice_quality_complaints', 0)
    
    # Upgrade if revenue supports it and quality is impacting metrics
    if monthly_revenue > 100 and (completion_rate < 0.7 or user_complaints > 10):
        return True
    
    # Always upgrade if revenue is strong
    if monthly_revenue > 500:
        return True
        
    return False
```

---

**Bottom Line**: Start with **$0/month** using local TTS, upgrade strategically based on user feedback and revenue growth. 🚀💰