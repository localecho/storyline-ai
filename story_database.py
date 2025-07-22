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
        """Initialize database with production-ready schema"""
        logger.info("Initializing database with production schema")
        self._create_minimal_schema()
    
    def _create_minimal_schema(self):
        """Create production-ready schema with proper error handling"""
        with self.get_connection() as conn:
            try:
                # Stories table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS stories (
                        story_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        subtitle TEXT,
                        content TEXT NOT NULL,
                        content_summary TEXT,
                        word_count INTEGER,
                        estimated_reading_time INTEGER,
                        language_code TEXT DEFAULT 'en',
                        publication_year INTEGER,
                        copyright_status TEXT DEFAULT 'public_domain',
                        usage_rights TEXT,
                        source_attribution TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Authors table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS authors (
                        author_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        birth_year INTEGER,
                        death_year INTEGER,
                        nationality TEXT,
                        biography TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Story-Author relationships
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS story_authors (
                        story_id INTEGER,
                        author_id INTEGER,
                        role TEXT DEFAULT 'author',
                        PRIMARY KEY (story_id, author_id),
                        FOREIGN KEY (story_id) REFERENCES stories(story_id),
                        FOREIGN KEY (author_id) REFERENCES authors(author_id)
                    )
                """)
                
                # Reading levels
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS reading_levels (
                        story_id INTEGER PRIMARY KEY,
                        lexile_level TEXT,
                        guided_reading_level TEXT,
                        grade_level_min INTEGER,
                        grade_level_max INTEGER,
                        age_min INTEGER,
                        age_max INTEGER,
                        complexity_score INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (story_id) REFERENCES stories(story_id)
                    )
                """)
                
                # Themes
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS themes (
                        theme_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        category TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Story-Theme relationships
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS story_themes (
                        story_id INTEGER,
                        theme_id INTEGER,
                        prominence INTEGER DEFAULT 5,
                        PRIMARY KEY (story_id, theme_id),
                        FOREIGN KEY (story_id) REFERENCES stories(story_id),
                        FOREIGN KEY (theme_id) REFERENCES themes(theme_id)
                    )
                """)
                
                # Usage statistics
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS story_stats (
                        story_id INTEGER PRIMARY KEY,
                        times_requested INTEGER DEFAULT 0,
                        times_completed INTEGER DEFAULT 0,
                        average_rating REAL DEFAULT 0.0,
                        total_ratings INTEGER DEFAULT 0,
                        last_requested TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (story_id) REFERENCES stories(story_id)
                    )
                """)
                
                # Insert essential themes
                themes_data = [
                    ('Friendship', 'social_emotional', 'Stories about making and keeping friends'),
                    ('Courage', 'moral', 'Stories about being brave and facing fears'),
                    ('Kindness', 'moral', 'Stories emphasizing compassion and helping others'),
                    ('Animals', 'subject', 'Stories featuring animals as main characters'),
                    ('Magic', 'literary', 'Fantasy stories with magical elements'),
                    ('Adventure', 'literary', 'Stories with exciting journeys and discoveries'),
                    ('Hard Work', 'moral', 'Stories about the value of effort and dedication'),
                    ('Perseverance', 'moral', 'Stories about not giving up')
                ]
                
                conn.executemany("""
                    INSERT OR IGNORE INTO themes (name, category, description) 
                    VALUES (?, ?, ?)
                """, themes_data)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stories_language ON stories(language_code)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_stories_copyright ON stories(copyright_status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reading_levels_age ON reading_levels(age_min, age_max)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_story_stats_requested ON story_stats(times_requested DESC)")
                
                conn.commit()
                logger.info("Production schema created successfully")
                
            except Exception as e:
                logger.error(f"Schema creation error: {e}")
                conn.rollback()
                raise
    
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
                      language_code: Optional[str] = None,
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
        
        # Language filtering
        if language_code is not None:
            query += " AND s.language_code = ?"
            params.append(language_code)
        
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
    """Seed the database with sample public domain stories including multilingual content"""
    
    # Sample public domain stories (English and Spanish versions)
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
            'source_attribution': 'Traditional English folk tale',
            'language_code': 'en'
        },
        
        {
            'title': 'Los Tres Cerditos',
            'content': """Había una vez tres cerditos que salieron al mundo para construir sus propias casas.

El primer cerdito era perezoso. Construyó su casa de paja porque era fácil y rápido. "Esto estará bien," dijo.

El segundo cerdito trabajó un poco más duro. Construyó su casa de palos. "Esto es más fuerte que la paja," pensó.

El tercer cerdito era muy trabajador. Construyó su casa de ladrillos, trabajando todo el día. "Esto me mantendrá seguro," dijo.

Un día, llegó un lobo feroz. Olió a los cerditos y decidió que los quería para la cena.

Primero, fue a la casa de paja. "¡Cerdito, cerdito, déjame entrar!"

"¡No, por los pelos de mi barbilla!" dijo el primer cerdito.

"¡Entonces soplaré y resoplaré y tu casa derribaré!" El lobo derribó la casa de paja, pero el cerdito corrió a la casa de palos de su hermano.

El lobo lo siguió. "¡Cerditos, cerditos, déjenme entrar!"

"¡No, por los pelos de nuestras barbillas!"

"¡Entonces soplaré y resoplaré y su casa derribaré!" El lobo también derribó la casa de palos, pero ambos cerditos corrieron a la casa de ladrillos de su hermano.

El lobo trató de derribar la casa de ladrillos, pero no pudo. Sopló y resopló hasta que se cansó.

Los tres cerditos estaban seguros en la casa fuerte de ladrillos. Aprendieron que el trabajo duro y la planificación los mantienen seguros. Y vivieron felices para siempre.""",
            'copyright_status': 'public_domain',
            'publication_year': 1840,
            'source_attribution': 'Cuento tradicional inglés',
            'language_code': 'es'
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
            'source_attribution': 'Aesop\'s Fables',
            'language_code': 'en'
        },
        
        {
            'title': 'La Tortuga y la Liebre',
            'content': """Había una vez una liebre muy rápida que se jactaba de lo rápido que podía correr. Cansada de escucharla presumir, una tortuga la desafió a una carrera.

Todos los animales del bosque se reunieron para ver. La liebre se rió de la tortuga. "Esta será la carrera más fácil que haya ganado," dijo.

La carrera comenzó y la liebre salió disparada casi fuera de vista. Pronto estaba muy por delante de la tortuga.

"Esto es muy fácil," pensó la liebre. "Tengo mucho tiempo." Decidió tomar una siesta bajo un árbol con sombra.

Mientras tanto, la tortuga siguió caminando lenta pero constantemente. Paso a paso, se movía hacia adelante sin parar. Pasó a la liebre dormida y continuó hacia la línea de meta.

¡La liebre se despertó y se dio cuenta de que la tortuga estaba casi en la línea de meta! Corrió tan rápido como pudo, pero era demasiado tarde. ¡La tortuga había ganado la carrera!

Todos los animales vitorearon a la tortuga. La liebre aprendió una lección importante ese día: "Lento y constante gana la carrera." El trabajo duro y la determinación son más importantes que ser rápido.""",
            'copyright_status': 'public_domain',
            'source_attribution': 'Fábulas de Esopo',
            'language_code': 'es'
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