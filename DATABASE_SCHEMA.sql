-- StoryLine AI - Library-Standard Database Schema
-- Professional children's literature cataloging system

-- =====================================================
-- CORE ENTITIES
-- =====================================================

-- Authors and Creators
CREATE TABLE authors (
    author_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    birth_year INTEGER,
    death_year INTEGER,
    nationality VARCHAR(100),
    biography TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stories - Main content table
CREATE TABLE stories (
    story_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(500) NOT NULL,
    subtitle VARCHAR(500),
    content TEXT NOT NULL,
    content_summary TEXT,
    word_count INTEGER,
    estimated_reading_time INTEGER, -- minutes
    language_code VARCHAR(10) DEFAULT 'en',
    publication_year INTEGER,
    copyright_status VARCHAR(50) NOT NULL, -- 'public_domain', 'copyrighted', 'creative_commons'
    usage_rights TEXT,
    source_attribution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Story-Author relationships (many-to-many)
CREATE TABLE story_authors (
    story_id INTEGER REFERENCES stories(story_id),
    author_id INTEGER REFERENCES authors(author_id),
    role VARCHAR(50) DEFAULT 'author', -- 'author', 'illustrator', 'translator', 'editor'
    PRIMARY KEY (story_id, author_id, role)
);

-- =====================================================
-- LIBRARY CATALOGING METADATA
-- =====================================================

-- Reading Levels and Age Appropriateness
CREATE TABLE reading_levels (
    story_id INTEGER PRIMARY KEY REFERENCES stories(story_id),
    lexile_level VARCHAR(20), -- '200L', '500L', etc.
    guided_reading_level VARCHAR(5), -- 'A', 'B', 'C'...'Z'
    grade_level_min INTEGER, -- PreK=0, K=1, 1st=2, etc.
    grade_level_max INTEGER,
    age_min INTEGER, -- minimum age in years
    age_max INTEGER, -- maximum age in years
    complexity_score INTEGER, -- 1-10 scale
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Library Classification
CREATE TABLE classifications (
    classification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER REFERENCES stories(story_id),
    system VARCHAR(50) NOT NULL, -- 'dewey', 'loc', 'custom'
    code VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subject Headings (Library of Congress style)
CREATE TABLE subject_headings (
    heading_id INTEGER PRIMARY KEY AUTOINCREMENT,
    heading VARCHAR(200) NOT NULL UNIQUE,
    parent_heading_id INTEGER REFERENCES subject_headings(heading_id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Story-Subject relationships
CREATE TABLE story_subjects (
    story_id INTEGER REFERENCES stories(story_id),
    heading_id INTEGER REFERENCES subject_headings(heading_id),
    relevance_score INTEGER DEFAULT 5, -- 1-10 scale
    PRIMARY KEY (story_id, heading_id)
);

-- =====================================================
-- EDUCATIONAL & THEMATIC METADATA
-- =====================================================

-- Themes and Values
CREATE TABLE themes (
    theme_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50), -- 'social_emotional', 'moral', 'educational', 'literary'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE story_themes (
    story_id INTEGER REFERENCES stories(story_id),
    theme_id INTEGER REFERENCES themes(theme_id),
    prominence INTEGER DEFAULT 5, -- 1-10 scale, how prominent is this theme
    PRIMARY KEY (story_id, theme_id)
);

-- Character Types and Archetypes
CREATE TABLE characters (
    character_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER REFERENCES stories(story_id),
    name VARCHAR(200),
    character_type VARCHAR(100), -- 'protagonist', 'antagonist', 'supporting'
    archetype VARCHAR(100), -- 'hero', 'mentor', 'trickster', etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cultural and Diversity Metadata
CREATE TABLE cultural_metadata (
    story_id INTEGER PRIMARY KEY REFERENCES stories(story_id),
    cultural_background VARCHAR(100),
    representation_notes TEXT,
    diversity_aspects TEXT, -- JSON array of diversity elements
    cultural_sensitivity_reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- QUALITY & AWARDS
-- =====================================================

-- Literary Awards and Recognition
CREATE TABLE awards (
    award_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    organization VARCHAR(200),
    category VARCHAR(100),
    prestige_level INTEGER, -- 1-10 scale
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE story_awards (
    story_id INTEGER REFERENCES stories(story_id),
    award_id INTEGER REFERENCES awards(award_id),
    year_received INTEGER,
    status VARCHAR(50), -- 'winner', 'finalist', 'nominee', 'honorable_mention'
    PRIMARY KEY (story_id, award_id, year_received)
);

-- Reviews and Ratings
CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER REFERENCES stories(story_id),
    reviewer_type VARCHAR(50), -- 'professional', 'educator', 'parent', 'child'
    rating INTEGER, -- 1-5 stars
    review_text TEXT,
    reviewer_name VARCHAR(200),
    reviewer_credentials VARCHAR(500),
    review_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Educational Endorsements
CREATE TABLE endorsements (
    endorsement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER REFERENCES stories(story_id),
    organization VARCHAR(200),
    endorsement_type VARCHAR(100), -- 'curriculum', 'reading_list', 'award'
    grade_levels VARCHAR(50),
    subject_areas VARCHAR(200),
    endorsement_text TEXT,
    date_endorsed DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- USAGE AND ANALYTICS
-- =====================================================

-- Story Usage Statistics
CREATE TABLE story_stats (
    story_id INTEGER PRIMARY KEY REFERENCES stories(story_id),
    times_requested INTEGER DEFAULT 0,
    times_completed INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),
    total_ratings INTEGER DEFAULT 0,
    last_requested TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Preferences and Matching
CREATE TABLE story_preferences (
    preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_age INTEGER,
    child_interests VARCHAR(500), -- JSON array
    preferred_themes VARCHAR(500), -- JSON array
    preferred_reading_level VARCHAR(20),
    avoid_themes VARCHAR(500), -- JSON array of themes to avoid
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- CONTENT MANAGEMENT
-- =====================================================

-- Content Status and Workflow
CREATE TABLE content_status (
    story_id INTEGER PRIMARY KEY REFERENCES stories(story_id),
    status VARCHAR(50) NOT NULL, -- 'draft', 'review', 'approved', 'published', 'archived'
    reviewed_by VARCHAR(100),
    review_date TIMESTAMP,
    review_notes TEXT,
    published_date TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content Tags (flexible tagging system)
CREATE TABLE tags (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name VARCHAR(100) NOT NULL UNIQUE,
    tag_category VARCHAR(50), -- 'genre', 'mood', 'season', 'holiday', etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE story_tags (
    story_id INTEGER REFERENCES stories(story_id),
    tag_id INTEGER REFERENCES tags(tag_id),
    PRIMARY KEY (story_id, tag_id)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Search and filtering indexes
CREATE INDEX idx_stories_title ON stories(title);
CREATE INDEX idx_stories_word_count ON stories(word_count);
CREATE INDEX idx_stories_copyright ON stories(copyright_status);
CREATE INDEX idx_stories_publication_year ON stories(publication_year);

CREATE INDEX idx_reading_levels_age ON reading_levels(age_min, age_max);
CREATE INDEX idx_reading_levels_grade ON reading_levels(grade_level_min, grade_level_max);
CREATE INDEX idx_reading_levels_lexile ON reading_levels(lexile_level);

CREATE INDEX idx_story_themes_theme ON story_themes(theme_id);
CREATE INDEX idx_story_themes_prominence ON story_themes(prominence);

CREATE INDEX idx_story_stats_requested ON story_stats(times_requested DESC);
CREATE INDEX idx_story_stats_rating ON story_stats(average_rating DESC);

-- =====================================================
-- SAMPLE DATA INSERTS
-- =====================================================

-- Sample Authors
INSERT INTO authors (name, birth_year, death_year, nationality, biography) VALUES
('Hans Christian Andersen', 1805, 1875, 'Danish', 'Danish author famous for fairy tales including The Little Mermaid and The Ugly Duckling'),
('Brothers Grimm', 1785, 1863, 'German', 'German academics and authors who collected and published folklore'),
('Aesop', -620, -564, 'Greek', 'Ancient Greek fabulist and storyteller credited with Aesops Fables'),
('Unknown', NULL, NULL, 'Various', 'Traditional folk tales with unknown original authors');

-- Sample Themes
INSERT INTO themes (name, category, description) VALUES
('Friendship', 'social_emotional', 'Stories about making and keeping friends'),
('Courage', 'moral', 'Stories about being brave and facing fears'),
('Kindness', 'moral', 'Stories emphasizing compassion and helping others'),
('Problem Solving', 'educational', 'Stories where characters solve problems creatively'),
('Family', 'social_emotional', 'Stories about family relationships and love'),
('Animals', 'subject', 'Stories featuring animals as main characters'),
('Magic', 'literary', 'Fantasy stories with magical elements'),
('Adventure', 'literary', 'Stories with exciting journeys and discoveries');

-- Sample Subject Headings
INSERT INTO subject_headings (heading, description) VALUES
('Children -- Fiction', 'Stories with child protagonists'),
('Animals -- Fiction', 'Stories featuring animals'),
('Fairy tales', 'Traditional magical stories'),
('Fables', 'Short stories with moral lessons'),
('Bedtime stories', 'Stories appropriate for bedtime reading'),
('Moral education', 'Stories that teach values and ethics'),
('Social skills', 'Stories that help develop interpersonal skills');

-- Sample Awards
INSERT INTO awards (name, organization, category, prestige_level, description) VALUES
('Caldecott Medal', 'American Library Association', 'Picture Book', 10, 'Most distinguished American picture book'),
('Newbery Medal', 'American Library Association', 'Children Literature', 10, 'Most distinguished contribution to American literature for children'),
('Hans Christian Andersen Award', 'IBBY', 'International', 9, 'Highest international recognition for creators of children books');

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- View: Complete Story Information
CREATE VIEW story_details AS
SELECT 
    s.story_id,
    s.title,
    s.content,
    s.word_count,
    s.estimated_reading_time,
    s.copyright_status,
    GROUP_CONCAT(a.name, '; ') as authors,
    rl.age_min,
    rl.age_max,
    rl.grade_level_min,
    rl.grade_level_max,
    rl.lexile_level,
    ss.times_requested,
    ss.average_rating
FROM stories s
LEFT JOIN story_authors sa ON s.story_id = sa.story_id
LEFT JOIN authors a ON sa.author_id = a.author_id
LEFT JOIN reading_levels rl ON s.story_id = rl.story_id
LEFT JOIN story_stats ss ON s.story_id = ss.story_id
GROUP BY s.story_id;

-- View: Stories by Age Group
CREATE VIEW stories_by_age AS
SELECT 
    s.story_id,
    s.title,
    rl.age_min,
    rl.age_max,
    GROUP_CONCAT(t.name, ', ') as themes
FROM stories s
JOIN reading_levels rl ON s.story_id = rl.story_id
LEFT JOIN story_themes st ON s.story_id = st.story_id
LEFT JOIN themes t ON st.theme_id = t.theme_id
WHERE s.copyright_status = 'public_domain'
GROUP BY s.story_id, s.title, rl.age_min, rl.age_max;

-- =====================================================
-- TRIGGERS FOR MAINTAINING DATA INTEGRITY
-- =====================================================

-- Update story stats timestamp when story is requested
CREATE TRIGGER update_story_stats_timestamp
AFTER UPDATE ON story_stats
BEGIN
    UPDATE story_stats 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE story_id = NEW.story_id;
END;

-- Automatically update story updated_at timestamp
CREATE TRIGGER update_story_timestamp
AFTER UPDATE ON stories
BEGIN
    UPDATE stories 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE story_id = NEW.story_id;
END;