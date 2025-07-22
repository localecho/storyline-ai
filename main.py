#!/usr/bin/env python3
"""
StoryLine AI - Phone-Based Bedtime Story Service
Main application with Twilio integration for MVP functionality
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import sqlite3
import uuid
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
BASE_URL = os.environ.get('BASE_URL', 'https://your-domain.ngrok.io')

# Initialize Twilio client
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    twilio_client = None
    logger.warning("Twilio credentials not found. Running in demo mode.")

@dataclass
class Child:
    """Child profile data structure"""
    child_id: str
    name: str
    age: int
    interests: List[str]
    parent_phone: str
    created_at: str
    last_story_date: Optional[str] = None
    story_count: int = 0

@dataclass
class StorySession:
    """Story session tracking"""
    session_id: str
    child_id: str
    story_title: str
    story_content: str
    start_time: str
    duration_seconds: Optional[int] = None
    completed: bool = False

class DatabaseManager:
    """Handles SQLite database operations"""
    
    def __init__(self, db_path: str = "storyline_ai.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS children (
                    child_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    interests TEXT NOT NULL,
                    parent_phone TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_story_date TEXT,
                    story_count INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS story_sessions (
                    session_id TEXT PRIMARY KEY,
                    child_id TEXT NOT NULL,
                    story_title TEXT NOT NULL,
                    story_content TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    duration_seconds INTEGER,
                    completed BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (child_id) REFERENCES children (child_id)
                );
                
                CREATE TABLE IF NOT EXISTS usage_tracking (
                    phone_number TEXT,
                    month_year TEXT,
                    story_count INTEGER DEFAULT 0,
                    PRIMARY KEY (phone_number, month_year)
                );
            """)
            conn.commit()
    
    def get_child_by_phone(self, phone_number: str) -> Optional[Child]:
        """Get child profile by parent phone number"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM children WHERE parent_phone = ? ORDER BY created_at DESC LIMIT 1",
                (phone_number,)
            ).fetchone()
            
            if row:
                interests = json.loads(row['interests'])
                return Child(
                    child_id=row['child_id'],
                    name=row['name'],
                    age=row['age'],
                    interests=interests,
                    parent_phone=row['parent_phone'],
                    created_at=row['created_at'],
                    last_story_date=row['last_story_date'],
                    story_count=row['story_count']
                )
        return None
    
    def create_child(self, name: str, age: int, interests: List[str], phone_number: str) -> Child:
        """Create new child profile"""
        child = Child(
            child_id=str(uuid.uuid4()),
            name=name,
            age=age,
            interests=interests,
            parent_phone=phone_number,
            created_at=datetime.now().isoformat()
        )
        
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO children 
                   (child_id, name, age, interests, parent_phone, created_at, story_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (child.child_id, child.name, child.age, json.dumps(child.interests),
                 child.parent_phone, child.created_at, child.story_count)
            )
            conn.commit()
        
        return child
    
    def update_story_count(self, child_id: str):
        """Update story count for child"""
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE children 
                   SET story_count = story_count + 1, last_story_date = ?
                   WHERE child_id = ?""",
                (datetime.now().isoformat(), child_id)
            )
            conn.commit()
    
    def check_monthly_usage(self, phone_number: str) -> int:
        """Check monthly story usage for freemium limits"""
        current_month = datetime.now().strftime("%Y-%m")
        
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT story_count FROM usage_tracking WHERE phone_number = ? AND month_year = ?",
                (phone_number, current_month)
            ).fetchone()
            
            return row['story_count'] if row else 0
    
    def increment_monthly_usage(self, phone_number: str):
        """Increment monthly usage counter"""
        current_month = datetime.now().strftime("%Y-%m")
        
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO usage_tracking (phone_number, month_year, story_count)
                   VALUES (?, ?, COALESCE((SELECT story_count FROM usage_tracking 
                           WHERE phone_number = ? AND month_year = ?), 0) + 1)""",
                (phone_number, current_month, phone_number, current_month)
            )
            conn.commit()

class StoryGenerator:
    """Handles story generation and selection"""
    
    def __init__(self):
        self.story_templates = self._load_story_templates()
        self.use_ai = os.getenv('USE_OLLAMA_AI', 'false').lower() == 'true'
        
        # Initialize Ollama if available
        if self.use_ai:
            try:
                from ollama_story_engine import OllamaStoryEngine
                self.ollama_engine = OllamaStoryEngine()
                if self.ollama_engine.check_ollama_status():
                    logger.info("Ollama AI story generation enabled")
                else:
                    logger.warning("Ollama not available, falling back to templates")
                    self.use_ai = False
            except ImportError:
                logger.warning("Ollama engine not available, using templates")
    
    def _load_story_templates(self) -> Dict[str, Dict]:
        """Load pre-written story templates"""
        return {
            "magic_forest": {
                "title": "The Magic Forest Adventure",
                "template": "Once upon a time, {name} discovered a magical forest where {interest} lived...",
                "themes": ["magic", "adventure", "animals", "forest"],
                "age_range": [3, 8],
                "duration": 8
            },
            "brave_astronaut": {
                "title": "Space Adventure with {name}",
                "template": "{name} put on a special space suit and blasted off to explore {interest} among the stars...",
                "themes": ["space", "adventure", "exploration", "science"],
                "age_range": [4, 10],
                "duration": 10
            },
            "friendly_dragon": {
                "title": "The Friendly Dragon",
                "template": "{name} met a friendly dragon who loved {interest} just as much as {name} did...",
                "themes": ["dragons", "friendship", "magic", "adventure"],
                "age_range": [3, 9],
                "duration": 9
            },
            "underwater_adventure": {
                "title": "Under the Sea with {name}",
                "template": "{name} put on magical fins and dove deep underwater to discover {interest}...",
                "themes": ["ocean", "fish", "adventure", "exploration"],
                "age_range": [3, 8],
                "duration": 7
            },
            "superhero_day": {
                "title": "{name} the Superhero",
                "template": "One morning, {name} woke up with amazing superpowers and used them to help {interest}...",
                "themes": ["superhero", "helping", "adventure", "powers"],
                "age_range": [4, 10],
                "duration": 8
            }
        }
    
    def select_story(self, child: Child) -> Dict[str, str]:
        """Select appropriate story based on child's profile"""
        
        # Try AI generation first if enabled
        if self.use_ai and hasattr(self, 'ollama_engine'):
            try:
                from ollama_story_engine import Child as OllamaChild
                ollama_child = OllamaChild(
                    name=child.name,
                    age=child.age, 
                    interests=child.interests
                )
                
                # Select theme based on interests
                theme_mapping = {
                    'animals': 'animal friends',
                    'magic': 'magical forest', 
                    'space': 'space exploration',
                    'ocean': 'underwater adventure',
                    'princess': 'fairy tale',
                    'superhero': 'superhero',
                    'dragons': 'magical forest'
                }
                
                theme = "adventure"  # default
                for interest in child.interests:
                    if interest.lower() in theme_mapping:
                        theme = theme_mapping[interest.lower()]
                        break
                
                ai_story = self.ollama_engine.generate_story(ollama_child, theme, "fast")
                if ai_story:
                    logger.info(f"Generated AI story: {ai_story['title']}")
                    return {
                        "title": ai_story["title"],
                        "content": ai_story["content"],
                        "duration": int(ai_story["word_count"] / 25)  # Rough duration estimate
                    }
            except Exception as e:
                logger.warning(f"AI story generation failed: {e}, falling back to templates")
        
        # Fallback to template-based stories
        # Filter stories by age
        suitable_stories = {
            key: story for key, story in self.story_templates.items()
            if story["age_range"][0] <= child.age <= story["age_range"][1]
        }
        
        # Score stories based on interests
        scored_stories = []
        for key, story in suitable_stories.items():
            score = 0
            for interest in child.interests:
                if any(interest.lower() in theme for theme in story["themes"]):
                    score += 2
                if interest.lower() in story["template"].lower():
                    score += 3
            scored_stories.append((score, key, story))
        
        # Select highest scoring story
        if scored_stories:
            scored_stories.sort(reverse=True)
            _, story_key, story_data = scored_stories[0]
        else:
            # Fallback to first suitable story
            story_key = list(suitable_stories.keys())[0]
            story_data = suitable_stories[story_key]
        
        # Generate personalized content
        primary_interest = child.interests[0] if child.interests else "wonderful things"
        
        story_content = self._generate_full_story(
            story_data["template"], 
            child.name, 
            primary_interest,
            child.age
        )
        
        return {
            "title": story_data["title"].format(name=child.name),
            "content": story_content,
            "duration": story_data["duration"]
        }
    
    def _generate_full_story(self, template: str, name: str, interest: str, age: int) -> str:
        """Generate a complete story from template"""
        # This is a simplified version. In production, this would use GPT-4
        beginning = template.format(name=name, interest=interest)
        
        if age <= 5:
            middle = f"As {name} explored, they made new friends and learned about kindness. "
            ending = f"At the end of the day, {name} felt happy and sleepy, knowing tomorrow would bring new adventures. The End."
        else:
            middle = f"{name} faced challenges with courage and discovered the importance of friendship and helping others. "
            ending = f"When the adventure was over, {name} returned home with wonderful memories and valuable lessons. Sweet dreams, {name}!"
        
        return f"{beginning} {middle} {ending}"

# Initialize components
db = DatabaseManager()
story_gen = StoryGenerator()

# Simple session storage for language preferences
session_storage = {}

# Initialize enhanced story selector
try:
    from enhanced_story_selector import EnhancedStorySelector
    enhanced_selector = EnhancedStorySelector()
    USE_ENHANCED_SELECTOR = True
    logger.info("Enhanced story selector initialized")
except ImportError as e:
    logger.warning(f"Enhanced selector unavailable: {e}")
    enhanced_selector = None
    USE_ENHANCED_SELECTOR = False

@app.route("/webhook/voice", methods=['POST'])
def handle_voice_call():
    """Main webhook handler for incoming voice calls"""
    try:
        caller_number = request.values.get('From', '')
        logger.info(f"Incoming call from {caller_number}")
        
        # Check if this is a returning user
        child = db.get_child_by_phone(caller_number)
        
        response = VoiceResponse()
        
        if child:
            # Returning user flow
            response.say(f"Hi there! Is this {child.name}? Press 1 for yes, or say a different name.", 
                        voice='alice', rate='slow')
            response.gather(
                num_digits=1,
                action=f'{BASE_URL}/webhook/returning_user',
                method='POST',
                timeout=10
            )
        else:
            # New user flow
            # Detect language preference first
            response.say("Hello! ¡Hola! Welcome to StoryLine AI. "
                        "For English, press 1. Para Español, press 2. "
                        "First time calling? Press 1 for English, 2 for Español.", 
                        voice='alice', rate='slow')
            response.gather(
                num_digits=1,
                action=f'{BASE_URL}/webhook/new_user',
                method='POST',
                timeout=10
            )
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in handle_voice_call: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, we're having technical difficulties. Please try calling back in a few minutes.")
        return Response(str(response), mimetype='text/xml')

@app.route("/webhook/new_user", methods=['POST'])
def handle_new_user():
    """Handle new user registration flow with language support"""
    try:
        caller_number = request.values.get('From', '')
        digits = request.values.get('Digits', '')
        
        response = VoiceResponse()
        
        # Determine language and store in session
        if digits == '1':
            # English - Store preference and start simplified registration
            session_storage[caller_number] = {'language': 'en', 'timestamp': datetime.now().isoformat()}
            response.say("Welcome! Let's get started quickly. Just your child's name and age. "
                        "Child's name?", voice='alice', rate='slow')
            response.record(
                max_length=8,
                action=f'{BASE_URL}/webhook/get_name?lang=en',
                method='POST',
                transcribe=True,
                speech_model='experimental_conversations',  # Enhanced recognition
                enhanced='true'
            )
        elif digits == '2':
            # Spanish - Store preference and start simplified registration
            session_storage[caller_number] = {'language': 'es', 'timestamp': datetime.now().isoformat()}
            response.say("¡Bienvenido! Vamos a empezar rápido. Solo el nombre y edad de su niño. "
                        "¿Nombre del niño?", voice='alice', rate='slow', language='es-ES')
            response.record(
                max_length=8,
                action=f'{BASE_URL}/webhook/get_name?lang=es',
                method='POST',
                transcribe=True,
                speech_model='experimental_conversations',  # Enhanced recognition
                enhanced='true'
            )
        else:
            # Default to English with slower pace
            response.say("Welcome! Let's keep this simple. I just need your child's name. "
                        "Please say their name slowly after the beep.", voice='alice', rate='slow')
            response.record(
                max_length=10,
                action=f'{BASE_URL}/webhook/get_name?lang=en',
                method='POST',
                transcribe=True
            )
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in handle_new_user: {e}")
        response = VoiceResponse()
        response.say("Sorry, let me try again. Por favor, intente de nuevo.")
        response.redirect(f'{BASE_URL}/webhook/voice')
        return Response(str(response), mimetype='text/xml')

@app.route("/webhook/get_name", methods=['POST'])
def handle_get_name():
    """Handle name collection during registration with language support"""
    try:
        caller_number = request.values.get('From', '')
        transcription = request.values.get('TranscriptionText', '').strip()
        language = request.args.get('lang', 'en')
        
        response = VoiceResponse()
        
        if transcription and len(transcription) > 1:
            # Store name temporarily and ask for age
            name = transcription.title()
            
            if language == 'es':
                response.say(f"¡Mucho gusto, {name}! ¿Cuántos años tiene {name}? "
                            "Diga su edad, como 'cinco' o 'siete'. "
                            "O puede presionar números en el teléfono.", voice='alice', rate='slow', language='es-ES')
            else:
                response.say(f"Nice to meet you, {name}! How old is {name}? "
                            "Please say their age, like 'five' or 'seven'. "
                            "Or you can press numbers on your phone.", voice='alice', rate='slow')
            
            # Enhanced recording with DTMF fallback option
            response.record(
                max_length=5,
                action=f'{BASE_URL}/webhook/get_age?name={name}&lang={language}',
                method='POST',
                transcribe=True,
                speech_model='experimental_conversations',
                enhanced='true',
                play_beep=True
            )
            
            # Also allow DTMF input
            response.gather(
                num_digits=2,
                action=f'{BASE_URL}/webhook/get_age_dtmf?name={name}&lang={language}',
                method='POST',
                timeout=3,
                finish_on_key='#'
            )
        else:
            # Enhanced retry with DTMF fallback
            if language == 'es':
                response.say("No escuché bien. ¿Puede decir el nombre de su niño otra vez, despacio? "
                            "O presione 0 para ayuda.", voice='alice', rate='slow', language='es-ES')
            else:
                response.say("I didn't catch that. Could you say your child's name again, nice and clearly? "
                            "Or press 0 for help.", voice='alice', rate='slow')
            
            response.record(
                max_length=10,
                action=f'{BASE_URL}/webhook/get_name?lang={language}',
                method='POST',
                transcribe=True,
                speech_model='experimental_conversations',
                enhanced='true'
            )
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in handle_get_name: {e}")
        response = VoiceResponse()
        response.say("Sorry, let me try again. Lo siento, vamos a intentar otra vez.")
        response.redirect(f'{BASE_URL}/webhook/voice')
        return Response(str(response), mimetype='text/xml')

@app.route("/webhook/get_age", methods=['POST'])
def handle_get_age():
    """Handle age collection during registration with language support"""
    try:
        caller_number = request.values.get('From', '')
        name = request.args.get('name', '')
        language = request.args.get('lang', 'en')
        transcription = request.values.get('TranscriptionText', '').strip().lower()
        
        response = VoiceResponse()
        
        # Convert spoken numbers to digits (English and Spanish)
        number_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12,
            # Spanish numbers
            'uno': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
            'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
            'once': 11, 'doce': 12
        }
        
        age = None
        for word, num in number_words.items():
            if word in transcription:
                age = num
                break
        
        # Try parsing as digit
        if age is None:
            try:
                age = int(''.join(filter(str.isdigit, transcription)))
            except ValueError:
                pass
        
        if age and 2 <= age <= 12:
            # Valid age - SIMPLIFIED: Skip interests, use default and complete registration
            child = db.create_child(name, age, ['adventure', 'animals'], caller_number)
            monthly_usage = db.check_monthly_usage(caller_number)
            
            if language == 'es':
                if monthly_usage >= 3:
                    response.say(f"¡Perfecto! {name} tiene {age} años. "
                                "Ya usó sus 3 cuentos gratis este mes. "
                                "Para cuentos ilimitados, marque 1, o marque 2 para esperar.", 
                                voice='alice', rate='slow', language='es-ES')
                else:
                    stories_left = 3 - monthly_usage
                    response.say(f"¡Perfecto! {name} tiene {age} años. "
                                f"Tiene {stories_left} cuentos gratis este mes. "
                                "¿Listo para su primer cuento mágico? Marque 1.", 
                                voice='alice', rate='slow', language='es-ES')
            else:
                if monthly_usage >= 3:
                    response.say(f"Perfect! {name} is {age} years old. "
                                "You've used your 3 free stories this month. "
                                "Press 1 to upgrade, or 2 to try again next month.", 
                                voice='alice', rate='slow')
                else:
                    stories_left = 3 - monthly_usage
                    response.say(f"Perfect! {name} is {age} years old. "
                                f"You have {stories_left} free stories this month. "
                                "Ready for your first magical story? Press 1!", 
                                voice='alice', rate='slow')
            
            if monthly_usage >= 3:
                response.gather(
                    num_digits=1,
                    action=f'{BASE_URL}/webhook/upgrade_prompt',
                    method='POST',
                    timeout=10
                )
            else:
                response.gather(
                    num_digits=1,
                    action=f'{BASE_URL}/webhook/start_story',
                    method='POST',
                    timeout=10
                )
        else:
            # Retry age collection with language support
            if language == 'es':
                response.say("No entendí la edad. ¿Puede decir cuántos años tiene su niño? "
                            "Como 'cinco años' o solo 'siete'?", voice='alice', rate='slow', language='es-ES')
            else:
                response.say("I didn't understand the age. Could you say how old your child is? "
                            "Like 'five years old' or just 'seven'?", voice='alice', rate='slow')
            
            response.record(
                max_length=5,
                action=f'{BASE_URL}/webhook/get_age?name={name}&lang={language}',
                method='POST',
                transcribe=True
            )
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in handle_get_age: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, there was an error. Let me start over.")
        response.redirect(f'{BASE_URL}/webhook/voice')
        return Response(str(response), mimetype='text/xml')

@app.route("/webhook/get_age_dtmf", methods=['POST'])
def handle_get_age_dtmf():
    """Handle age collection via DTMF (phone keypad) input"""
    try:
        caller_number = request.values.get('From', '')
        name = request.args.get('name', '')
        language = request.args.get('lang', 'en')
        digits = request.values.get('Digits', '')
        
        response = VoiceResponse()
        
        if digits and digits.isdigit():
            age = int(digits)
            if 2 <= age <= 12:
                # Valid age - proceed with simplified registration
                child = db.create_child(name, age, ['adventure', 'animals'], caller_number)
                monthly_usage = db.check_monthly_usage(caller_number)
                
                if language == 'es':
                    if monthly_usage >= 3:
                        response.say(f"¡Perfecto! {name} tiene {age} años. "
                                    "Ya usó sus 3 cuentos gratis este mes. "
                                    "Para cuentos ilimitados, marque 1, o marque 2 para esperar.", 
                                    voice='alice', rate='slow', language='es-ES')
                    else:
                        stories_left = 3 - monthly_usage
                        response.say(f"¡Perfecto! {name} tiene {age} años. "
                                    f"Tiene {stories_left} cuentos gratis este mes. "
                                    "¿Listo para su primer cuento mágico? Marque 1.", 
                                    voice='alice', rate='slow', language='es-ES')
                else:
                    if monthly_usage >= 3:
                        response.say(f"Perfect! {name} is {age} years old. "
                                    "You've used your 3 free stories this month. "
                                    "Press 1 to upgrade, or 2 to try again next month.", 
                                    voice='alice', rate='slow')
                    else:
                        stories_left = 3 - monthly_usage
                        response.say(f"Perfect! {name} is {age} years old. "
                                    f"You have {stories_left} free stories this month. "
                                    "Ready for your first magical story? Press 1!", 
                                    voice='alice', rate='slow')
                
                if monthly_usage >= 3:
                    response.gather(
                        num_digits=1,
                        action=f'{BASE_URL}/webhook/upgrade_prompt',
                        method='POST',
                        timeout=10
                    )
                else:
                    response.gather(
                        num_digits=1,
                        action=f'{BASE_URL}/webhook/start_story',
                        method='POST',
                        timeout=10
                    )
            else:
                # Invalid age
                if language == 'es':
                    response.say("Esa edad no parece correcta. Por favor, marque la edad entre 2 y 12.", 
                                voice='alice', rate='slow', language='es-ES')
                else:
                    response.say("That age doesn't seem right. Please press the age between 2 and 12.", 
                                voice='alice', rate='slow')
                
                response.gather(
                    num_digits=2,
                    action=f'{BASE_URL}/webhook/get_age_dtmf?name={name}&lang={language}',
                    method='POST',
                    timeout=10,
                    finish_on_key='#'
                )
        else:
            # No digits or invalid input - redirect to voice
            response.redirect(f'{BASE_URL}/webhook/get_age?name={name}&lang={language}')
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in handle_get_age_dtmf: {e}")
        response = VoiceResponse()
        response.say("Sorry, let me try again. Lo siento, vamos a intentar otra vez.")
        response.redirect(f'{BASE_URL}/webhook/voice')
        return Response(str(response), mimetype='text/xml')

@app.route("/webhook/get_interests", methods=['POST'])
def handle_get_interests():
    """Handle interests collection and complete registration"""
    try:
        caller_number = request.values.get('From', '')
        name = request.args.get('name', '')
        age = int(request.args.get('age', 5))
        transcription = request.values.get('TranscriptionText', '').strip().lower()
        
        response = VoiceResponse()
        
        # Parse interests from transcription
        interest_keywords = ['animals', 'dogs', 'cats', 'horses', 'dinosaurs', 'dragons',
                           'magic', 'princesses', 'knights', 'adventure', 'space', 'rockets',
                           'cars', 'trucks', 'trains', 'ocean', 'fish', 'pirates',
                           'superheroes', 'music', 'dancing', 'sports', 'soccer', 'basketball']
        
        interests = []
        for keyword in interest_keywords:
            if keyword in transcription:
                interests.append(keyword)
        
        # If no specific interests found, use general categories
        if not interests:
            if any(word in transcription for word in ['animal', 'pet', 'dog', 'cat']):
                interests = ['animals']
            elif any(word in transcription for word in ['magic', 'fairy', 'princess']):
                interests = ['magic']
            elif any(word in transcription for word in ['adventure', 'explore']):
                interests = ['adventure']
            else:
                interests = ['adventure']  # Default
        
        # Create child profile
        child = db.create_child(name, age, interests, caller_number)
        
        # Check freemium usage
        monthly_usage = db.check_monthly_usage(caller_number)
        
        if monthly_usage >= 3:
            response.say(f"Thanks for setting up {name}'s profile! "
                        "You've used your 3 free stories this month. "
                        "To hear unlimited stories, press 1 to upgrade, or press 2 to try again next month.", 
                        voice='alice', rate='slow')
            response.gather(
                num_digits=1,
                action=f'{BASE_URL}/webhook/upgrade_prompt',
                method='POST',
                timeout=10
            )
        else:
            stories_left = 3 - monthly_usage
            response.say(f"Perfect! {name} loves {', '.join(interests)}. "
                        f"You have {stories_left} free stories this month. "
                        "Ready for your first magical story? Press 1 to begin!", 
                        voice='alice', rate='slow')
            response.gather(
                num_digits=1,
                action=f'{BASE_URL}/webhook/start_story',
                method='POST',
                timeout=10
            )
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in handle_get_interests: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, there was an error setting up the profile. Let me start over.")
        response.redirect(f'{BASE_URL}/webhook/voice')
        return Response(str(response), mimetype='text/xml')

@app.route("/webhook/returning_user", methods=['POST'])
def handle_returning_user():
    """Handle returning user flow"""
    try:
        caller_number = request.values.get('From', '')
        digits = request.values.get('Digits', '')
        
        child = db.get_child_by_phone(caller_number)
        response = VoiceResponse()
        
        if digits == '1' and child:
            # Check freemium usage
            monthly_usage = db.check_monthly_usage(caller_number)
            
            if monthly_usage >= 3:
                response.say(f"Hi {child.name}! You've used your 3 free stories this month. "
                           "Press 1 to upgrade for unlimited stories, or press 2 to wait until next month.", 
                           voice='alice', rate='slow')
                response.gather(
                    num_digits=1,
                    action=f'{BASE_URL}/webhook/upgrade_prompt',
                    method='POST',
                    timeout=10
                )
            else:
                stories_left = 3 - monthly_usage
                response.say(f"Welcome back, {child.name}! You have {stories_left} stories left this month. "
                           "Ready for tonight's magical story? Press 1 to begin!", 
                           voice='alice', rate='slow')
                response.gather(
                    num_digits=1,
                    action=f'{BASE_URL}/webhook/start_story',
                    method='POST',
                    timeout=10
                )
        else:
            # Handle different name or new registration
            response.say("Let me help you set up a new profile. What's your child's name?", 
                        voice='alice', rate='slow')
            response.record(
                max_length=10,
                action=f'{BASE_URL}/webhook/get_name',
                method='POST',
                transcribe=True
            )
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in handle_returning_user: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, there was an error. Let me start over.")
        response.redirect(f'{BASE_URL}/webhook/voice')
        return Response(str(response), mimetype='text/xml')

@app.route("/webhook/start_story", methods=['POST'])
def handle_start_story():
    """Start playing a story"""
    try:
        caller_number = request.values.get('From', '')
        digits = request.values.get('Digits', '')
        
        child = db.get_child_by_phone(caller_number)
        response = VoiceResponse()
        
        if digits == '1' and child:
            # Use enhanced selector if available, otherwise fallback to original
            if USE_ENHANCED_SELECTOR and enhanced_selector:
                # Convert to enhanced selector format
                from enhanced_story_selector import Child as SelectorChild
                selector_child = SelectorChild(
                    name=child.name,
                    age=child.age,
                    interests=child.interests,
                    phone_number=caller_number
                )
                
                # Detect language preference from session or use default
                # TODO: Extract language from session storage
                language_preference = 'en'  # Default for now
                
                # Get best story from all sources
                story_result = enhanced_selector.select_best_story(selector_child, max_duration=10)
                
                if story_result:
                    story = {
                        'title': story_result.title,
                        'content': story_result.content,
                        'duration': story_result.duration
                    }
                    logger.info(f"Using {story_result.source} story: {story_result.title}")
                else:
                    # Fallback to template generator
                    story = story_gen.select_story(child)
                    logger.info("Enhanced selector failed, using template fallback")
            else:
                # Use original story generator
                story = story_gen.select_story(child)
                logger.info("Using original story generator")
            
            # Update usage tracking
            db.increment_monthly_usage(caller_number)
            db.update_story_count(child.child_id)
            
            # Create story session
            session_id = str(uuid.uuid4())
            # In a real implementation, you'd save this session to the database
            
            response.say(f"Here's a special story just for {child.name}: {story['title']}", 
                        voice='alice', rate='slow')
            response.pause(length=1)
            response.say(story['content'], voice='alice', rate='slow')
            response.pause(length=2)
            response.say("The end! Sweet dreams, and call back anytime for another story. Goodbye!", 
                        voice='alice', rate='slow')
        else:
            response.say("No problem! Call back anytime when you're ready for a story. Goodbye!", 
                        voice='alice')
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in handle_start_story: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, there was an error with the story. Please try calling back.")
        return Response(str(response), mimetype='text/xml')

@app.route("/webhook/upgrade_prompt", methods=['POST'])
def handle_upgrade_prompt():
    """Handle upgrade prompts for users who hit freemium limits"""
    try:
        digits = request.values.get('Digits', '')
        response = VoiceResponse()
        
        if digits == '1':
            response.say("Great! Visit storyline-ai.com to upgrade your account for unlimited stories, "
                        "custom voice recording, and premium features. Thank you for calling!", 
                        voice='alice', rate='slow')
        else:
            response.say("No problem! Your free stories reset each month. "
                        "Call back anytime, and thanks for using StoryLine AI!", 
                        voice='alice', rate='slow')
        
        return Response(str(response), mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in handle_upgrade_prompt: {e}")
        response = VoiceResponse()
        response.say("Thank you for calling StoryLine AI. Goodbye!")
        return Response(str(response), mimetype='text/xml')

@app.route("/health", methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.route("/", methods=['GET'])
def home():
    """Simple home page"""
    return """
    <html>
        <head><title>StoryLine AI</title></head>
        <body>
            <h1>📞 StoryLine AI</h1>
            <p>Phone-based bedtime story service for families</p>
            <h2>Demo Mode</h2>
            <p>To test the system:</p>
            <ol>
                <li>Set up ngrok: <code>ngrok http 5000</code></li>
                <li>Configure Twilio webhook to your ngrok URL + /webhook/voice</li>
                <li>Call your Twilio phone number</li>
            </ol>
            <h2>Features</h2>
            <ul>
                <li>✅ Voice call handling with Twilio</li>
                <li>✅ Child profile creation and management</li>
                <li>✅ Personalized story selection</li>
                <li>✅ Freemium usage tracking (3 stories/month)</li>
                <li>✅ Story templates with personalization</li>
                <li>🚧 AI story generation (GPT-4 integration)</li>
                <li>🚧 Voice cloning capabilities</li>
                <li>🚧 Premium subscription features</li>
            </ul>
        </body>
    </html>
    """

if __name__ == '__main__':
    logger.info("Starting StoryLine AI server...")
    
    # In production, use a proper WSGI server like Gunicorn
    app.run(host='0.0.0.0', port=5000, debug=True)