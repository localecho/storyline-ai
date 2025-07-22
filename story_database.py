#!/usr/bin/env python3
"""
StoryLine AI - Library Database Models and ORM
Professional children's literature cataloging system with SQLAlchemy
"""

import os
import json
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import sqlite3
from contextlib import contextmanager

import logging
logger = logging.getLogger(__name__)

class StoryDatabase:
    """Professional story database with library cataloging standards"""
    
    def __init__(self, db_path: str = "storyline_library.db"):
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
        """Initialize database with schema from DATABASE_SCHEMA.sql"""
        schema_path = "DATABASE_SCHEMA.sql"
        if not os.path.exists(schema_path):
            logger.warning("DATABASE_SCHEMA.sql not found, creating minimal schema")
            self._create_minimal_schema()
            return
        
        try:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            with self.get_connection() as conn:
                # Execute schema in chunks to handle complex SQL
                statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                for statement in statements:
                    if statement and not statement.startswith('--'):
                        try:
                            conn.execute(statement)
                        except sqlite3.Error as e:
                            if "already exists" not in str(e):
                                logger.warning(f"Schema execution warning: {e}")
                conn.commit()
            
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            self._create_minimal_schema()
    
    def _create_minimal_schema(self):
        """Create minimal schema if full schema fails"""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS stories (
                    story_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    word_count INTEGER,
                    estimated_reading_time INTEGER,
                    copyright_status TEXT DEFAULT 'unknown',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS authors (
                    author_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    birth_year INTEGER,
                    death_year INTEGER
                );
                
                CREATE TABLE IF NOT EXISTS reading_levels (
                    story_id INTEGER PRIMARY KEY,
                    age_min INTEGER,
                    age_max INTEGER,
                    grade_level_min INTEGER,
                    grade_level_max INTEGER,
                    FOREIGN KEY (story_id) REFERENCES stories (story_id)
                );
            """)
            conn.commit()
    
    def add_story(self, story_data: Dict[str, Any]) -> int:
        """Add a new story to the database"""
        required_fields = ['title', 'content']
        for field in required_fields:
            if field not in story_data:
                raise ValueError(f"Required field '{field}' missing")
        
        # Calculate word count if not provided
        if 'word_count' not in story_data:
            story_data['word_count'] = len(story_data['content'].split())
        
        # Estimate reading time if not provided (150 words per minute)
        if 'estimated_reading_time' not in story_data:
            story_data['estimated_reading_time'] = max(1, story_data['word_count'] // 150)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO stories (title, subtitle, content, content_summary, 
                                   word_count, estimated_reading_time, language_code,
                                   publication_year, copyright_status, usage_rights, 
                                   source_attribution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                story_data['title'],
                story_data.get('subtitle'),
                story_data['content'],
                story_data.get('content_summary'),
                story_data['word_count'],
                story_data['estimated_reading_time'],
                story_data.get('language_code', 'en'),
                story_data.get('publication_year'),
                story_data.get('copyright_status', 'unknown'),
                story_data.get('usage_rights'),
                story_data.get('source_attribution')
            ))
            story_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Added story '{story_data['title']}' with ID {story_id}")
            return story_id
    
    def add_author(self, name: str, birth_year: Optional[int] = None, 
                   death_year: Optional[int] = None, nationality: Optional[str] = None,
                   biography: Optional[str] = None) -> int:
        """Add an author to the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO authors (name, birth_year, death_year, nationality, biography)
                VALUES (?, ?, ?, ?, ?)
            """, (name, birth_year, death_year, nationality, biography))
            author_id = cursor.lastrowid
            conn.commit()
            return author_id
    
    def link_story_author(self, story_id: int, author_id: int, role: str = 'author'):
        """Link a story to an author"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO story_authors (story_id, author_id, role)
                VALUES (?, ?, ?)
            """, (story_id, author_id, role))
            conn.commit()
    
    def set_reading_level(self, story_id: int, age_min: int, age_max: int,
                         grade_min: Optional[int] = None, grade_max: Optional[int] = None,
                         lexile_level: Optional[str] = None,
                         guided_reading_level: Optional[str] = None):
        """Set reading level metadata for a story"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO reading_levels 
                (story_id, age_min, age_max, grade_level_min, grade_level_max, 
                 lexile_level, guided_reading_level, complexity_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (story_id, age_min, age_max, grade_min, grade_max, 
                  lexile_level, guided_reading_level, 
                  self._calculate_complexity_score(age_min, age_max)))
            conn.commit()
    
    def _calculate_complexity_score(self, age_min: int, age_max: int) -> int:
        """Calculate complexity score based on age range"""
        avg_age = (age_min + age_max) / 2
        if avg_age <= 4:
            return 1  # Very simple
        elif avg_age <= 6:
            return 3  # Simple
        elif avg_age <= 8:
            return 5  # Medium
        elif avg_age <= 10:
            return 7  # Complex
        else:
            return 9  # Very complex
    
    def add_theme_to_story(self, story_id: int, theme_name: str, 
                          category: str = 'general', prominence: int = 5):
        """Add a theme to a story"""
        with self.get_connection() as conn:
            # Get or create theme
            cursor = conn.cursor()
            cursor.execute("SELECT theme_id FROM themes WHERE name = ?", (theme_name,))
            row = cursor.fetchone()
            
            if row:
                theme_id = row[0]
            else:
                cursor.execute("""
                    INSERT INTO themes (name, category)
                    VALUES (?, ?)
                """, (theme_name, category))
                theme_id = cursor.lastrowid
            
            # Link story to theme
            cursor.execute("""
                INSERT OR REPLACE INTO story_themes (story_id, theme_id, prominence)
                VALUES (?, ?, ?)
            """, (story_id, theme_id, prominence))
            
            conn.commit()
    
    def search_stories(self, age: Optional[int] = None, 
                      interests: List[str] = None,
                      max_reading_time: Optional[int] = None,
                      copyright_status: Optional[str] = None,
                      limit: int = 10) -> List[Dict[str, Any]]:
        """Search for stories based on criteria"""
        
        query = """
            SELECT DISTINCT s.story_id, s.title, s.content, s.word_count, 
                   s.estimated_reading_time, s.copyright_status,
                   GROUP_CONCAT(DISTINCT a.name) as authors,
                   rl.age_min, rl.age_max,
                   GROUP_CONCAT(DISTINCT t.name) as themes
            FROM stories s
            LEFT JOIN story_authors sa ON s.story_id = sa.story_id
            LEFT JOIN authors a ON sa.author_id = a.author_id  
            LEFT JOIN reading_levels rl ON s.story_id = rl.story_id
            LEFT JOIN story_themes st ON s.story_id = st.story_id
            LEFT JOIN themes t ON st.theme_id = t.theme_id
            WHERE 1=1
        """
        
        params = []
        
        # Age filtering
        if age is not None:
            query += " AND rl.age_min <= ? AND rl.age_max >= ?"
            params.extend([age, age])
        
        # Reading time filtering
        if max_reading_time is not None:
            query += " AND s.estimated_reading_time <= ?"
            params.append(max_reading_time)
        
        # Copyright status filtering
        if copyright_status is not None:
            query += " AND s.copyright_status = ?"
            params.append(copyright_status)
        
        # Interest-based theme filtering
        if interests:
            interest_conditions = []
            for interest in interests:
                interest_conditions.append("t.name LIKE ?")
                params.append(f"%{interest}%")
            if interest_conditions:
                query += f" AND ({' OR '.join(interest_conditions)})"
        
        query += " GROUP BY s.story_id ORDER BY s.story_id LIMIT ?"
        params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            stories = []
            for row in rows:
                story = {
                    'story_id': row['story_id'],
                    'title': row['title'],
                    'content': row['content'],
                    'word_count': row['word_count'],
                    'estimated_reading_time': row['estimated_reading_time'],
                    'copyright_status': row['copyright_status'],
                    'authors': row['authors'].split(',') if row['authors'] else [],
                    'age_min': row['age_min'],
                    'age_max': row['age_max'],
                    'themes': row['themes'].split(',') if row['themes'] else []
                }
                stories.append(story)
            
            return stories
    
    def get_story_by_id(self, story_id: int) -> Optional[Dict[str, Any]]:
        """Get a complete story by ID"""
        stories = self.search_stories()
        for story in stories:
            if story['story_id'] == story_id:
                return story
        return None
    
    def update_story_stats(self, story_id: int, requested: bool = True, 
                          completed: bool = False, rating: Optional[int] = None):
        """Update story usage statistics"""
        with self.get_connection() as conn:
            # Get current stats
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM story_stats WHERE story_id = ?", (story_id,))
            row = cursor.fetchone()
            
            if not row:
                # Create new stats record
                cursor.execute("""
                    INSERT INTO story_stats (story_id, times_requested, times_completed)
                    VALUES (?, ?, ?)
                """, (story_id, 1 if requested else 0, 1 if completed else 0))
            else:
                # Update existing stats
                updates = []
                params = []
                
                if requested:
                    updates.append("times_requested = times_requested + 1")
                    updates.append("last_requested = CURRENT_TIMESTAMP")
                
                if completed:
                    updates.append("times_completed = times_completed + 1")
                
                if rating is not None:
                    # Simplified rating update (would need more complex logic for proper averages)
                    updates.append("average_rating = ?")
                    updates.append("total_ratings = total_ratings + 1")
                    params.extend([rating])
                
                if updates:
                    params.append(story_id)
                    query = f"UPDATE story_stats SET {', '.join(updates)} WHERE story_id = ?"
                    cursor.execute(query, params)
            
            conn.commit()
    
    def get_popular_stories(self, age: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular stories by request count"""
        query = """
            SELECT s.story_id, s.title, ss.times_requested, ss.average_rating
            FROM stories s
            JOIN story_stats ss ON s.story_id = ss.story_id
            LEFT JOIN reading_levels rl ON s.story_id = rl.story_id
            WHERE ss.times_requested > 0
        """
        
        params = []
        if age is not None:
            query += " AND rl.age_min <= ? AND rl.age_max >= ?"
            params.extend([age, age])
        
        query += " ORDER BY ss.times_requested DESC, ss.average_rating DESC LIMIT ?"
        params.append(limit)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Story count
            cursor.execute("SELECT COUNT(*) FROM stories")
            stats['total_stories'] = cursor.fetchone()[0]
            
            # Author count
            cursor.execute("SELECT COUNT(*) FROM authors")
            stats['total_authors'] = cursor.fetchone()[0]
            
            # Stories by copyright status
            cursor.execute("""
                SELECT copyright_status, COUNT(*) 
                FROM stories 
                GROUP BY copyright_status
            """)
            stats['by_copyright'] = dict(cursor.fetchall())
            
            # Stories by age range
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN age_min <= 4 THEN 'Preschool (2-4)'
                        WHEN age_min <= 6 THEN 'Early Elementary (5-6)'
                        WHEN age_min <= 8 THEN 'Elementary (7-8)'
                        WHEN age_min <= 10 THEN 'Middle Elementary (9-10)'
                        ELSE 'Advanced (11+)'
                    END as age_group,
                    COUNT(*)
                FROM reading_levels 
                GROUP BY age_group
            """)
            stats['by_age_group'] = dict(cursor.fetchall())
            
            return stats

def seed_sample_stories(db: StoryDatabase):
    """Seed the database with sample public domain stories"""
    
    # Sample public domain stories
    sample_stories = [
        {
            'title': 'The Three Little Pigs',
            'content': """Once upon a time, there were three little pigs who went out into the world to build their own homes.

The first little pig was lazy. He built his house out of straw because it was easy and quick. "This will do just fine," he said.

The second little pig worked a bit harder. He built his house out of sticks. "This is stronger than straw," he thought.

The third little pig was very hardworking. He built his house out of bricks, working all day long. "This will keep me safe," he said.

One day, a big bad wolf came along. He smelled the pigs and decided he wanted them for dinner.

First, he went to the straw house. "Little pig, little pig, let me come in!"

"Not by the hair of my chinny-chin-chin!" said the first pig.

"Then I'll huff and I'll puff and I'll blow your house in!" The wolf blew the straw house down, but the pig ran to his brother's stick house.

The wolf followed. "Little pigs, little pigs, let me come in!"

"Not by the hair of our chinny-chin-chins!"

"Then I'll huff and I'll puff and I'll blow your house in!" The wolf blew the stick house down too, but both pigs ran to their brother's brick house.

The wolf tried to blow down the brick house, but he couldn't. He huffed and puffed until he was tired.

The three little pigs were safe in the strong brick house. They learned that hard work and planning ahead keep you safe. And they all lived happily ever after.""",
            'copyright_status': 'public_domain',
            'publication_year': 1840,
            'source_attribution': 'Traditional English folk tale'
        },
        
        {
            'title': 'The Tortoise and the Hare',
            'content': """Once upon a time, there was a speedy hare who bragged about how fast he could run. Tired of hearing him boast, a tortoise challenged him to a race.

All the animals in the forest gathered to watch. The hare laughed at the tortoise. "This will be the easiest race I've ever won," he said.

The race began and the hare darted almost out of sight at once. Soon he was far ahead of the tortoise.

"This is too easy," thought the hare. "I have plenty of time." He decided to take a nap under a shady tree.

Meanwhile, the tortoise kept walking slowly but steadily. Step by step, he moved forward without stopping. He passed the sleeping hare and continued toward the finish line.

The hare woke up and realized the tortoise was almost at the finish line! He ran as fast as he could, but it was too late. The tortoise had won the race!

All the animals cheered for the tortoise. The hare learned an important lesson that day: "Slow and steady wins the race." Hard work and determination are more important than just being fast.""",
            'copyright_status': 'public_domain',
            'source_attribution': 'Aesop\'s Fables'
        }
    ]
    
    # Add sample authors
    authors = [
        {'name': 'Traditional Folk Tales', 'nationality': 'Various'},
        {'name': 'Aesop', 'birth_year': -620, 'death_year': -564, 'nationality': 'Greek'}
    ]
    
    author_ids = {}
    for author_data in authors:
        author_id = db.add_author(**author_data)
        author_ids[author_data['name']] = author_id
    
    # Add stories with metadata
    for i, story_data in enumerate(sample_stories):
        story_id = db.add_story(story_data)
        
        # Link to author
        if i == 0:  # Three Little Pigs
            db.link_story_author(story_id, author_ids['Traditional Folk Tales'])
            db.set_reading_level(story_id, 3, 7, grade_min=1, grade_max=3)
            db.add_theme_to_story(story_id, 'Hard Work', 'moral', 8)
            db.add_theme_to_story(story_id, 'Animals', 'subject', 7)
            db.add_theme_to_story(story_id, 'Safety', 'moral', 6)
            
        else:  # Tortoise and Hare
            db.link_story_author(story_id, author_ids['Aesop'])
            db.set_reading_level(story_id, 4, 8, grade_min=2, grade_max=4)
            db.add_theme_to_story(story_id, 'Perseverance', 'moral', 9)
            db.add_theme_to_story(story_id, 'Animals', 'subject', 8)
            db.add_theme_to_story(story_id, 'Competition', 'social_emotional', 5)
    
    logger.info("Sample stories seeded successfully")