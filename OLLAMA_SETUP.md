# 🤖 StoryLine AI - Ollama Setup Guide

> **Enable completely free, unlimited AI story generation with local Ollama models**

## 🎯 Why Ollama?

| Feature | OpenAI GPT-4 | Ollama (Local) |
|---------|--------------|----------------|
| **Cost** | $15/1M characters | **$0 forever** |
| **Privacy** | Data sent to OpenAI | **100% local** |
| **Internet** | Required | **Works offline** |
| **Speed** | API dependent | **Instant response** |
| **Customization** | Limited | **Full control** |

## 🚀 Quick Setup (5 minutes)

### 1. Install Ollama
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

### 2. Download a Story Model
```bash
# Lightweight model (2GB) - Fast generation
ollama pull llama3.2:latest

# Better quality model (4.7GB) - More creative
ollama pull llama3:8b

# Creative model (4.9GB) - Best stories
ollama pull llama3.1:8b
```

### 3. Start Ollama Service
```bash
# Start Ollama server
ollama serve

# Test it's working
ollama list
```

### 4. Enable AI in StoryLine AI
```bash
# Edit your .env file
echo "USE_OLLAMA_AI=true" >> .env

# Test the integration
python -c "
from main import StoryGenerator
gen = StoryGenerator()
print('✅ Ollama enabled' if gen.use_ai else '❌ Still using templates')
"
```

## 📊 Model Comparison

### Recommended Models for Bedtime Stories

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **llama3.2:latest** | 2GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Quick testing, fast stories |
| **llama3:8b** | 4.7GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **Recommended balance** |
| **llama3.1:8b** | 4.9GB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Creative, detailed stories |
| **deepseek-coder** | 776MB | ⭐⭐⭐⭐⭐ | ⭐⭐ | Fallback/testing only |

### Performance Benchmarks
```bash
# Test generation speed
time ollama run llama3.2:latest "Write a 200-word bedtime story about Emma and unicorns"

# Typical results:
# llama3.2:latest: ~15 seconds (2GB model)
# llama3:8b: ~25 seconds (4.7GB model)
# llama3.1:8b: ~35 seconds (4.9GB model)
```

## 🧪 Testing Your Setup

### Basic Test
```bash
cd storyline-ai

# Set environment for AI stories
export USE_OLLAMA_AI=true

# Test story generation
python -c "
from ollama_story_engine import OllamaStoryEngine, Child
engine = OllamaStoryEngine()
child = Child('Emma', 6, ['unicorns', 'magic'])
story = engine.generate_story(child)
print(f'Success: {story[\"title\"] if story else \"Failed\"}')
"
```

### Full Integration Test
```bash
# Test complete phone system with AI
python main.py &

# Test webhook with AI enabled
curl -X POST http://localhost:5000/webhook/voice \
  -d "From=%2B15551234567" \
  -d "CallSid=test123"
```

## ⚙️ Configuration Options

### Environment Variables
```bash
# Enable Ollama AI stories
USE_OLLAMA_AI=true

# Ollama server URL (if not default)
OLLAMA_URL=http://localhost:11434

# Story quality preference
OLLAMA_QUALITY=fast        # fast, balanced, creative
```

### Model Selection Strategy
```python
# In your code, you can specify quality levels:
story = engine.generate_story(child, theme="adventure", quality="creative")

# Quality levels automatically select best available model:
# "fast" → llama3.2:latest (2GB, ~15s generation)
# "balanced" → llama3:8b (4.7GB, ~25s generation) 
# "creative" → llama3.1:8b (4.9GB, ~35s generation)
```

## 🔧 Advanced Configuration

### Custom Model Setup
```bash
# Use a different model
ollama pull mistral:latest

# Create custom model with specific parameters
cat > Modelfile << 'EOF'
FROM llama3.2:latest
PARAMETER temperature 0.8
PARAMETER top_p 0.9
SYSTEM You are a gentle bedtime story writer for children.
EOF

ollama create bedtime-storyteller -f Modelfile
```

### Performance Tuning
```bash
# Increase context length for longer stories
ollama run llama3.2:latest --ctx-size 4096

# Adjust generation parameters
ollama run llama3.2:latest --temperature 0.7 --top-p 0.9
```

## 💰 Cost Analysis

### Hardware Requirements
- **Minimum**: 8GB RAM, 10GB disk space
- **Recommended**: 16GB RAM, 20GB disk space
- **Optimal**: 32GB RAM, 50GB disk space

### Ongoing Costs
- **Electricity**: ~$0.50/month (24/7 usage)
- **Internet**: $0 (works completely offline)
- **API calls**: $0 (unlimited local generation)
- **Storage**: One-time ~5-15GB per model

**Total monthly cost: ~$0.50** vs **$50+ for OpenAI GPT-4**

## 🚨 Troubleshooting

### Common Issues

#### "Ollama service not running"
```bash
# Start Ollama server
ollama serve

# Or run in background
nohup ollama serve > ollama.log 2>&1 &
```

#### "Model not found"
```bash
# List available models
ollama list

# Pull missing model
ollama pull llama3.2:latest
```

#### "Story generation slow"
```bash
# Check system resources
htop

# Use smaller model
export OLLAMA_QUALITY=fast

# Or reduce story length
# Edit ollama_story_engine.py max_tokens: 500
```

#### "Generated stories low quality"
```bash
# Use better model
ollama pull llama3.1:8b
export OLLAMA_QUALITY=creative

# Adjust temperature for more creativity
# Edit ollama_story_engine.py temperature: 0.9
```

## 🎭 Story Quality Examples

### Template-Based (Original)
```
"Once upon a time, Emma discovered a magical forest where unicorns lived. 
Emma explored and made new friends and learned about kindness. At the end 
of the day, Emma felt happy and sleepy, knowing tomorrow would bring new 
adventures. The End."
```

### Ollama-Generated (AI)
```
"Emma and the Whispering Rainbow Bridge"

Emma was playing in her grandmother's garden when she noticed something 
extraordinary - a shimmering rainbow bridge had appeared between two old 
oak trees. As she approached, she heard gentle whispers...

[Full 500-word personalized story with Emma meeting Luna the unicorn, 
learning about the magic of kindness, and discovering her own special 
power to help others through compassion...]
```

## 📈 Scaling Strategy

### Development Phase
1. **Start with llama3.2:latest** (2GB, fast)
2. **Test story quality** with users
3. **Upgrade to llama3:8b** if needed (4.7GB)

### Production Phase
1. **Deploy on dedicated server** (16GB+ RAM)
2. **Use llama3.1:8b** for best quality (4.9GB)
3. **Load balance** multiple models if needed
4. **Cache** popular stories for faster delivery

### Enterprise Phase
1. **Fine-tune models** on story datasets
2. **Custom voice personas** for different story types
3. **Multi-language support** with international models
4. **Real-time personalization** based on child feedback

## 🎯 Next Steps

1. **Install Ollama** following the quick setup
2. **Test story generation** with the basic test
3. **Compare quality** between template and AI stories
4. **Gather feedback** from children on story preferences
5. **Scale up models** based on usage and feedback

## 💡 Pro Tips

### Maximize Story Quality
```bash
# Use creative model for special occasions
export OLLAMA_QUALITY=creative

# Generate multiple story options
python -c "
from ollama_story_engine import OllamaStoryEngine, Child
engine = OllamaStoryEngine()
child = Child('Emma', 6, ['unicorns'])
stories = engine.generate_multiple_stories(child, 3)
print(f'Generated {len(stories)} story options')
"
```

### Optimize Performance
```bash
# Pre-warm models (first generation is slower)
ollama run llama3.2:latest "Hello" > /dev/null

# Use SSD storage for faster model loading
# Monitor GPU usage if available: nvidia-smi
```

### Content Safety
```python
# Built-in content filtering in ollama_story_engine.py
# All stories are designed for bedtime with gentle themes
# No violent, scary, or inappropriate content
```

---

**Ready to enable unlimited AI stories?** Follow the 5-minute quick setup above! 🚀

**Questions?** Check the troubleshooting section or the main [TESTING_COST_OPTIMIZATION.md](TESTING_COST_OPTIMIZATION.md) guide.