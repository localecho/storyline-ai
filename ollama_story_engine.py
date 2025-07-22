#!/usr/bin/env python3
"""
StoryLine AI - Ollama Integration for Local AI Story Generation
Completely free AI story generation using local Ollama models
"""

import requests
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Child:
    """Child profile for story personalization"""
    name: str
    age: int
    interests: List[str]

class OllamaStoryEngine:
    """Generate personalized bedtime stories using local Ollama models"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.default_model = "llama3.2:latest"  # Lightweight and fast
        self.story_models = {
            "fast": "llama3.2:latest",      # 2GB - Quick responses
            "balanced": "llama3:8b",        # 4.7GB - Good quality/speed
            "creative": "llama3.1:8b",      # 4.9GB - Most creative
            "coding": "deepseek-coder:latest" # 776MB - Very fast fallback
        }
        
    def check_ollama_status(self) -> bool:
        """Check if Ollama service is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/version", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def list_available_models(self) -> List[str]:
        """Get list of locally available models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
        except requests.exceptions.RequestException:
            pass
        return []
    
    def select_best_model(self, quality: str = "fast") -> str:
        """Select best available model based on quality preference"""
        available_models = self.list_available_models()
        
        # Try preferred model for quality level
        preferred_model = self.story_models.get(quality, self.default_model)
        if preferred_model in available_models:
            return preferred_model
        
        # Fallback to any available model in order of preference
        fallback_order = ["llama3.2:latest", "llama3:8b", "llama3:latest", "deepseek-coder:latest"]
        for model in fallback_order:
            if model in available_models:
                return model
                
        # Use first available model
        if available_models:
            return available_models[0]
            
        return self.default_model
    
    def create_story_prompt(self, child: Child, story_theme: str = "adventure") -> str:
        """Create a personalized story prompt for the child"""
        
        age_guidance = {
            (2, 4): "Use very simple words, short sentences, and repetitive phrases. Focus on basic concepts like colors, animals, and family.",
            (5, 7): "Use age-appropriate vocabulary, longer sentences, and include basic moral lessons. Add some adventure but keep it gentle.",
            (8, 10): "Use more complex vocabulary and longer story arcs. Include problem-solving and character development.",
            (11, 13): "Use advanced vocabulary and complex themes. Include deeper moral lessons and more sophisticated plots."
        }
        
        # Find appropriate age guidance
        guidance = "Use simple, child-friendly language"
        for (min_age, max_age), age_guide in age_guidance.items():
            if min_age <= child.age <= max_age:
                guidance = age_guide
                break
        
        # Build interests string
        interests_str = ", ".join(child.interests) if child.interests else "adventures"
        
        prompt = f"""You are a professional children's bedtime story writer. Create a magical, calming bedtime story for {child.name}, who is {child.age} years old and loves {interests_str}.

WRITING GUIDELINES:
- {guidance}
- Story should be 5-8 minutes when read aloud (approximately 300-500 words)
- Theme: {story_theme}
- Include {child.name} as the main character
- Incorporate their interests: {interests_str}
- End with a peaceful, sleepy conclusion
- Use a warm, soothing tone perfect for bedtime
- Include gentle life lessons about kindness, courage, or friendship

STORY STRUCTURE:
1. Gentle opening that introduces {child.name}
2. A magical discovery or adventure
3. A small challenge that {child.name} overcomes with kindness/cleverness
4. A happy resolution
5. A peaceful ending that encourages sleep

Please write the complete bedtime story now:"""

        return prompt
    
    def generate_story(self, child: Child, theme: str = "adventure", 
                      quality: str = "fast") -> Optional[Dict[str, str]]:
        """Generate a personalized bedtime story using Ollama"""
        
        if not self.check_ollama_status():
            logger.error("Ollama service not available")
            return None
        
        model = self.select_best_model(quality)
        prompt = self.create_story_prompt(child, theme)
        
        logger.info(f"Generating story for {child.name} using model {model}")
        
        try:
            # Ollama API request
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,  # Creative but not too random
                        "top_p": 0.9,       # Good variety
                        "max_tokens": 1000   # Reasonable story length
                    }
                },
                timeout=60  # Allow time for generation
            )
            
            if response.status_code == 200:
                result = response.json()
                story_text = result.get("response", "").strip()
                
                if story_text:
                    # Extract title if possible
                    lines = story_text.split('\n')
                    title = f"A Magical Adventure for {child.name}"
                    
                    # Look for a title in the first few lines
                    for line in lines[:3]:
                        if line.strip() and (
                            "title:" in line.lower() or 
                            len(line.strip()) < 50 and 
                            not line.strip().startswith("Once")
                        ):
                            title = line.replace("Title:", "").strip()
                            break
                    
                    return {
                        "title": title,
                        "content": story_text,
                        "word_count": len(story_text.split()),
                        "character_count": len(story_text),
                        "model_used": model,
                        "theme": theme,
                        "generated_at": datetime.now().isoformat()
                    }
            
            logger.error(f"Ollama API error: {response.status_code}")
            return None
            
        except requests.exceptions.Timeout:
            logger.error("Story generation timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            return None
    
    def generate_multiple_stories(self, child: Child, count: int = 3) -> List[Dict[str, str]]:
        """Generate multiple story options for the child"""
        themes = ["adventure", "magical forest", "space exploration", "underwater adventure", 
                 "fairy tale", "animal friends", "superhero", "mystery"]
        
        stories = []
        selected_themes = themes[:count] if count <= len(themes) else themes * ((count // len(themes)) + 1)
        
        for i, theme in enumerate(selected_themes[:count]):
            logger.info(f"Generating story {i+1}/{count}: {theme}")
            story = self.generate_story(child, theme)
            if story:
                stories.append(story)
        
        return stories
    
    def get_story_stats(self, story: Dict[str, str]) -> Dict[str, any]:
        """Get statistics about a generated story"""
        content = story.get("content", "")
        words = content.split()
        
        # Estimate reading time (average 150 words per minute for bedtime stories)
        reading_time_minutes = len(words) / 150
        
        return {
            "word_count": len(words),
            "character_count": len(content),
            "estimated_reading_time": f"{reading_time_minutes:.1f} minutes",
            "sentences": content.count('.') + content.count('!') + content.count('?'),
            "paragraphs": content.count('\n\n') + 1,
            "model_used": story.get("model_used", "unknown"),
            "theme": story.get("theme", "unknown")
        }