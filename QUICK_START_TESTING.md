# 🚀 StoryLine AI - Quick Start Testing Guide

> **Start testing immediately with $0 cost using macOS built-in TTS**

## ⚡ 30-Second Setup

```bash
# 1. Clone and setup
git clone https://github.com/localecho/storyline-ai.git
cd storyline-ai
pip install -r requirements.txt

# 2. Configure for free testing  
cp .env.testing .env

# 3. Test TTS locally (100% free)
python -c "
from tts_engine import CostOptimizedTTS
tts = CostOptimizedTTS()
audio = tts.synthesize_speech('Hello Emma! Ready for your bedtime story?')
print(f'✅ Generated {len(audio) if audio else 0} bytes of audio')
"

# 4. Test phone integration with ngrok
ngrok http 5000 &
python main.py
```

## 🎯 What You Get for $0

### Free Local TTS Testing
- **macOS Built-in Voices**: Alice, Daniel, Victoria, Princess
- **Unlimited Usage**: No API limits or costs
- **Instant Testing**: No signup or API keys needed
- **Voice Variety**: 6+ different voice personalities

### Phone Testing with Twilio Trial
- **$15 Free Credits**: Enough for extensive testing
- **Real Phone Calls**: Test complete user journey
- **Webhook Testing**: Full integration validation

## 💰 Cost Breakdown

| Testing Phase | Monthly Cost | What You Get |
|---------------|--------------|--------------|
| **Local Development** | **$0** | Unlimited TTS, story generation |
| **Phone Integration** | **$0** | Twilio trial credits ($15 free) |
| **Realistic Testing** | **$0-5** | Mix local + Google free tier |
| **Production Testing** | **$10-20** | High-quality TTS for demos |

## 🧪 Quick Tests

### Test 1: Basic TTS
```bash
# Verify TTS engine works
python -c "
import os
os.environ['TESTING_MODE'] = 'local_tts'
from tts_engine import CostOptimizedTTS
tts = CostOptimizedTTS()
audio = tts.synthesize_speech('Testing StoryLine AI')
print('✅ Success' if audio else '❌ Failed')
"
```

### Test 2: Story Generation
```bash
# Test complete story pipeline
python -c "
from main import StoryGenerator
gen = StoryGenerator()
story = gen.select_story({'name': 'Emma', 'age': 6, 'interests': ['unicorns']})
print(f'Story: {story[\"title\"]}')
print(f'Length: {len(story[\"content\"])} characters')
"
```

### Test 3: Phone Webhook (with ngrok)
```bash
# Start server and test webhook
python main.py &
curl -X POST http://localhost:5000/webhook/voice \
  -d "From=%2B15551234567" \
  -d "CallSid=test123"
```

## 🔧 Common Issues & Solutions

### Issue: "say command not found"
**Solution**: Only works on macOS. For other platforms:
```bash
# Linux: Install espeak
sudo apt-get install espeak
# Windows: Use Windows Speech API
```

### Issue: Twilio webhook not receiving calls
**Solution**: 
1. Ensure ngrok is running: `ngrok http 5000`
2. Copy the HTTPS URL (not HTTP)
3. Configure in Twilio Console: `https://abc123.ngrok.io/webhook/voice`

### Issue: Stories sound robotic
**Solution**: Upgrade TTS quality:
```bash
# Edit .env
TESTING_MODE=hybrid
TTS_QUALITY=premium
MONTHLY_TTS_BUDGET=10
```

## 📈 Scaling Strategy

### Phase 1: Free Development (Current)
- Use local TTS for all testing
- Perfect for logic and flow testing
- Zero ongoing costs

### Phase 2: Quality Testing ($0-5/month)
- Add Google Cloud free tier (1M chars/month free)
- Mix local + cloud TTS based on quality needs
- Still mostly free

### Phase 3: Production Testing ($10-20/month)  
- Enable OpenAI TTS for premium quality
- Use for user demos and feedback
- Budget-controlled spending

## 🎯 Next Steps

1. **Test locally** with the quick setup above
2. **Get Twilio trial** account for phone testing
3. **Deploy with ngrok** for webhook testing
4. **Gather feedback** from family/friends
5. **Scale TTS quality** based on user response

## 💡 Pro Tips

### Maximize Free Usage
```bash
# Always start with free tier
export TESTING_MODE=local_tts
export MONTHLY_TTS_BUDGET=0

# Only upgrade when needed
export TTS_QUALITY=premium  # When demo quality matters
export MONTHLY_TTS_BUDGET=20  # Set spending limits
```

### Test Different Scenarios
```python
# Test various story types
scenarios = [
    {"name": "Emma", "age": 4, "interests": ["animals"]},
    {"name": "Max", "age": 8, "interests": ["space", "robots"]},
    {"name": "Sofia", "age": 6, "interests": ["magic", "princesses"]}
]

for scenario in scenarios:
    # Test story generation for each
    story = generator.select_story(scenario)
    audio = tts.synthesize_speech(story["content"])
```

### Monitor Costs
```python
# Check spending regularly
tts = CostOptimizedTTS()
report = tts.get_cost_report()
print(f"Budget remaining: ${report['budget_remaining']}")
```

---

**Ready to start?** Run the 30-second setup above and start testing! 🚀

**Questions?** Check the full [TESTING_COST_OPTIMIZATION.md](TESTING_COST_OPTIMIZATION.md) guide.