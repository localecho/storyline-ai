-- StoryLine AI - Simplified SQLite Compatible Schema
-- Production-ready database structure for phone-based bedtime stories

-- Core story content
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
);

-- Authors and creators
CREATE TABLE IF NOT EXISTS authors (
    author_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    birth_year INTEGER,
    death_year INTEGER,
    nationality TEXT,
    biography TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Story-Author relationships
CREATE TABLE IF NOT EXISTS story_authors (
    story_id INTEGER,
    author_id INTEGER,
    role TEXT DEFAULT 'author',
    PRIMARY KEY (story_id, author_id),
    FOREIGN KEY (story_id) REFERENCES stories(story_id),
    FOREIGN KEY (author_id) REFERENCES authors(author_id)
);

-- Reading levels and age appropriateness
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
);

-- Themes and categories
CREATE TABLE IF NOT EXISTS themes (
    theme_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Story-Theme relationships
CREATE TABLE IF NOT EXISTS story_themes (
    story_id INTEGER,
    theme_id INTEGER,
    prominence INTEGER DEFAULT 5,
    PRIMARY KEY (story_id, theme_id),
    FOREIGN KEY (story_id) REFERENCES stories(story_id),
    FOREIGN KEY (theme_id) REFERENCES themes(theme_id)
);

-- Usage statistics
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
);

-- User profiles (children)
CREATE TABLE IF NOT EXISTS children (
    child_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    interests TEXT NOT NULL,
    parent_phone TEXT NOT NULL,
    language_preference TEXT DEFAULT 'en',
    created_at TEXT NOT NULL,
    last_story_date TEXT,
    story_count INTEGER DEFAULT 0
);

-- Story sessions (call tracking)
CREATE TABLE IF NOT EXISTS story_sessions (
    session_id TEXT PRIMARY KEY,
    child_id TEXT NOT NULL,
    story_id INTEGER,
    story_title TEXT NOT NULL,
    story_content TEXT NOT NULL,
    language_used TEXT DEFAULT 'en',
    start_time TEXT NOT NULL,
    duration_seconds INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (child_id) REFERENCES children(child_id),
    FOREIGN KEY (story_id) REFERENCES stories(story_id)
);

-- Usage tracking for freemium limits
CREATE TABLE IF NOT EXISTS usage_tracking (
    phone_number TEXT,
    month_year TEXT,
    story_count INTEGER DEFAULT 0,
    language_preference TEXT DEFAULT 'en',
    PRIMARY KEY (phone_number, month_year)
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_stories_language ON stories(language_code);
CREATE INDEX IF NOT EXISTS idx_stories_copyright ON stories(copyright_status);
CREATE INDEX IF NOT EXISTS idx_reading_levels_age ON reading_levels(age_min, age_max);
CREATE INDEX IF NOT EXISTS idx_children_phone ON children(parent_phone);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_month ON usage_tracking(month_year);
CREATE INDEX IF NOT EXISTS idx_story_stats_requested ON story_stats(times_requested DESC);

-- Insert sample themes
INSERT OR IGNORE INTO themes (name, category, description) VALUES
('Friendship', 'social_emotional', 'Stories about making and keeping friends'),
('Courage', 'moral', 'Stories about being brave and facing fears'),
('Kindness', 'moral', 'Stories emphasizing compassion and helping others'),
('Problem Solving', 'educational', 'Stories where characters solve problems creatively'),
('Family', 'social_emotional', 'Stories about family relationships and love'),
('Animals', 'subject', 'Stories featuring animals as main characters'),
('Magic', 'literary', 'Fantasy stories with magical elements'),
('Adventure', 'literary', 'Stories with exciting journeys and discoveries'),
('Perseverance', 'moral', 'Stories about not giving up'),
('Hard Work', 'moral', 'Stories about the value of effort and dedication');