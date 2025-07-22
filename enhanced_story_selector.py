#!/usr/bin/env python3
"""
StoryLine AI - Enhanced Story Selection Engine
Combines templates, AI generation, and curated database for optimal story matching
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)

@dataclass
class Child:
    """Child profile for story selection"""
    name: str
    age: int
    interests: List[str]
    phone_number: str = ""

@dataclass
class StoryResult:
    """Standardized story result format"""
    title: str
    content: str
    duration: int  # estimated minutes
    source: str    # 'template', 'ai', 'database'
    metadata: Dict = None

class EnhancedStorySelector:
    """Multi-source story selection with quality scoring"""
    
    def __init__(self):
        self.template_generator = None
        self.ai_generator = None
        self.story_database = None
        
        # Initialize available story sources
        self._init_template_generator()
        self._init_ai_generator()
        self._init_story_database()
        
        # Selection preferences
        self.source_preferences = {
            'database': 10,    # Highest quality - curated stories
            'ai': 8,          # High quality - personalized
            'template': 5     # Baseline quality - fallback
        }
    
    def _init_template_generator(self):
        """Initialize template-based story generator"""
        try:
            # Import the existing template system from main.py
            from main import StoryGenerator
            self.template_generator = StoryGenerator()
            logger.info("Template story generator initialized")
        except ImportError as e:
            logger.warning(f"Template generator unavailable: {e}")
    
    def _init_ai_generator(self):
        """Initialize AI story generator (Ollama)"""
        try:
            if os.getenv('USE_OLLAMA_AI', 'false').lower() == 'true':
                from ollama_story_engine import OllamaStoryEngine
                self.ai_generator = OllamaStoryEngine()
                if self.ai_generator.check_ollama_status():
                    logger.info("AI story generator initialized")
                else:
                    logger.warning("Ollama service not running")
                    self.ai_generator = None
        except ImportError as e:
            logger.warning(f"AI generator unavailable: {e}")
    
    def _init_story_database(self):
        """Initialize curated story database"""
        try:
            from story_database import StoryDatabase
            self.story_database = StoryDatabase()
            
            # Check if database has stories
            stats = self.story_database.get_database_stats()
            if stats.get('total_stories', 0) > 0:
                logger.info(f"Story database initialized with {stats['total_stories']} stories")
            else:
                logger.info("Story database initialized but empty")
                # Seed with sample stories
                from story_database import seed_sample_stories
                seed_sample_stories(self.story_database)
                logger.info("Database seeded with sample stories")
        except ImportError as e:
            logger.warning(f"Story database unavailable: {e}")
    
    def select_best_story(self, child: Child, 
                         max_duration: Optional[int] = None,
                         preferred_sources: List[str] = None) -> Optional[StoryResult]:
        """Select the best story from all available sources"""
        
        if preferred_sources is None:
            preferred_sources = ['database', 'ai', 'template']
        
        story_candidates = []
        
        # Try each source in preference order
        for source in preferred_sources:
            try:
                if source == 'database' and self.story_database:
                    stories = self._get_database_stories(child, max_duration)
                    for story in stories:
                        story_candidates.append((
                            self._score_story(story, child, source),
                            story,
                            source
                        ))
                
                elif source == 'ai' and self.ai_generator:
                    story = self._get_ai_story(child, max_duration)
                    if story:
                        story_candidates.append((
                            self._score_story(story, child, source),
                            story,
                            source
                        ))
                
                elif source == 'template' and self.template_generator:
                    story = self._get_template_story(child)
                    if story:
                        story_candidates.append((
                            self._score_story(story, child, source),
                            story,
                            source
                        ))
            
            except Exception as e:
                logger.warning(f"Error getting story from {source}: {e}")
                continue
        
        if not story_candidates:
            logger.error("No stories available from any source")
            return None
        
        # Sort by score and return best story
        story_candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_story, best_source = story_candidates[0]
        
        logger.info(f"Selected story from {best_source} with score {best_score}")
        return StoryResult(
            title=best_story['title'],
            content=best_story['content'],
            duration=best_story.get('duration', 8),
            source=best_source,
            metadata=best_story
        )
    
    def _get_database_stories(self, child: Child, max_duration: Optional[int]) -> List[Dict]:
        """Get stories from curated database"""
        if not self.story_database:
            return []
        
        # Search database with child criteria
        stories = self.story_database.search_stories(
            age=child.age,
            interests=child.interests,
            max_reading_time=max_duration,
            copyright_status='public_domain',  # Free stories only for now
            limit=5
        )
        
        # Update story stats for database stories
        for story in stories:
            self.story_database.update_story_stats(story['story_id'], requested=True)
        
        # Convert to standard format
        formatted_stories = []
        for story in stories:
            formatted_stories.append({
                'title': story['title'],
                'content': story['content'],
                'duration': story['estimated_reading_time'],
                'authors': story.get('authors', []),
                'themes': story.get('themes', []),
                'age_range': f"{story.get('age_min', 0)}-{story.get('age_max', 12)}",
                'copyright_status': story.get('copyright_status', 'unknown')
            })
        
        return formatted_stories
    
    def _get_ai_story(self, child: Child, max_duration: Optional[int]) -> Optional[Dict]:
        """Get AI-generated story"""
        if not self.ai_generator:
            return None
        
        # Convert to AI generator format
        from ollama_story_engine import Child as AIChild
        ai_child = AIChild(
            name=child.name,
            age=child.age,
            interests=child.interests
        )
        
        # Map interests to themes
        theme_mapping = {
            'animals': 'animal friends',
            'magic': 'magical forest',
            'space': 'space exploration',
            'ocean': 'underwater adventure',
            'princess': 'fairy tale',
            'superhero': 'superhero adventure',
            'dragons': 'dragon adventure'
        }
        
        theme = "adventure"  # default
        for interest in child.interests:
            if interest.lower() in theme_mapping:
                theme = theme_mapping[interest.lower()]
                break
        
        # Generate story
        ai_story = self.ai_generator.generate_story(ai_child, theme, "fast")
        if not ai_story:
            return None
        
        return {
            'title': ai_story['title'],
            'content': ai_story['content'],
            'duration': ai_story['word_count'] // 150,  # words to minutes
            'word_count': ai_story['word_count'],
            'model_used': ai_story.get('model_used', 'unknown'),
            'theme': theme
        }
    
    def _get_template_story(self, child: Child) -> Optional[Dict]:
        """Get template-based story"""
        if not self.template_generator:
            return None
        
        # Convert to template generator format  
        from main import Child as TemplateChild
        template_child = TemplateChild(
            child_id="temp",
            name=child.name,
            age=child.age,
            interests=child.interests,
            parent_phone=child.phone_number,
            created_at=""
        )
        
        story = self.template_generator.select_story(template_child)
        if not story:
            return None
        
        return {
            'title': story['title'],
            'content': story['content'],
            'duration': story.get('duration', 8)
        }
    
    def _score_story(self, story: Dict, child: Child, source: str) -> float:
        """Score a story based on quality and relevance"""
        score = 0.0
        
        # Base score from source quality
        score += self.source_preferences.get(source, 1)
        
        # Age appropriateness (if available)
        if 'age_range' in story:
            try:
                age_min, age_max = map(int, story['age_range'].split('-'))
                if age_min <= child.age <= age_max:
                    score += 5  # Perfect age match
                elif abs(child.age - age_min) <= 1 or abs(child.age - age_max) <= 1:
                    score += 3  # Close age match
            except (ValueError, AttributeError):
                pass
        
        # Interest matching
        story_themes = story.get('themes', [])
        story_content = story.get('content', '').lower()
        story_title = story.get('title', '').lower()
        
        for interest in child.interests:
            interest_lower = interest.lower()
            
            # Theme matching
            if any(interest_lower in theme.lower() for theme in story_themes):
                score += 3
            
            # Content matching
            if interest_lower in story_content:
                score += 2
            
            # Title matching
            if interest_lower in story_title:
                score += 2
        
        # Length appropriateness (bedtime stories should be 5-12 minutes)
        duration = story.get('duration', 8)
        if 5 <= duration <= 12:
            score += 2
        elif duration > 15:
            score -= 2  # Too long for bedtime
        
        # Quality indicators for database stories
        if source == 'database':
            if story.get('copyright_status') == 'public_domain':
                score += 1  # Free to use
            if story.get('authors'):
                score += 1  # Has attribution
        
        # Quality indicators for AI stories  
        if source == 'ai':
            word_count = story.get('word_count', 0)
            if 300 <= word_count <= 800:  # Good length for bedtime
                score += 2
        
        return score
    
    def get_multiple_options(self, child: Child, count: int = 3) -> List[StoryResult]:
        """Get multiple story options for choice"""
        options = []
        
        # Try to get different types of stories
        source_combinations = [
            ['database', 'ai', 'template'],
            ['ai', 'database', 'template'],
            ['database', 'template', 'ai'],
        ]
        
        for i in range(count):
            preferred_sources = source_combinations[i % len(source_combinations)]
            story = self.select_best_story(child, preferred_sources=preferred_sources)
            if story and story not in options:
                options.append(story)
        
        return options
    
    def get_story_recommendations(self, child: Child) -> Dict[str, List[str]]:
        """Get story recommendations and metadata"""
        recommendations = {
            'themes_for_age': [],
            'popular_stories': [],
            'educational_value': [],
            'available_sources': []
        }
        
        # Age-appropriate themes
        if child.age <= 4:
            recommendations['themes_for_age'] = ['Animals', 'Family', 'Colors', 'Simple Adventures']
        elif child.age <= 6:
            recommendations['themes_for_age'] = ['Friendship', 'Kindness', 'Problem Solving', 'Magic']
        elif child.age <= 8:
            recommendations['themes_for_age'] = ['Courage', 'Teamwork', 'Discovery', 'Fantasy Adventures']
        else:
            recommendations['themes_for_age'] = ['Leadership', 'Complex Problem Solving', 'Science', 'History']
        
        # Check available sources
        if self.story_database:
            recommendations['available_sources'].append('Curated Library Stories')
        if self.ai_generator:
            recommendations['available_sources'].append('AI-Generated Personalized Stories')
        if self.template_generator:
            recommendations['available_sources'].append('Template-Based Stories')
        
        # Get popular stories if database available
        if self.story_database:
            try:
                popular = self.story_database.get_popular_stories(age=child.age, limit=5)
                recommendations['popular_stories'] = [story['title'] for story in popular]
            except Exception:
                pass
        
        return recommendations
    
    def get_selector_stats(self) -> Dict[str, any]:
        """Get statistics about the story selector"""
        stats = {
            'available_sources': [],
            'source_preferences': self.source_preferences,
            'database_stats': None,
            'ai_status': None
        }
        
        # Check source availability
        if self.story_database:
            stats['available_sources'].append('database')
            try:
                stats['database_stats'] = self.story_database.get_database_stats()
            except Exception:
                pass
        
        if self.ai_generator:
            stats['available_sources'].append('ai')
            stats['ai_status'] = 'available'
        
        if self.template_generator:
            stats['available_sources'].append('template')
        
        return stats