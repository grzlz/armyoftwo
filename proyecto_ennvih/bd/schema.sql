-- Indigenous Language Learning Platform Database Schema
-- Duolingo-style app for Maya, Tzotzil, and Nahuatl

-- Languages supported
CREATE TABLE languages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    code VARCHAR(10) NOT NULL UNIQUE,
    native_name VARCHAR(100),
    description TEXT,
    total_speakers INTEGER,
    flag_emoji VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    native_language_id INTEGER REFERENCES languages(id),
    total_xp INTEGER DEFAULT 0,
    streak_days INTEGER DEFAULT 0,
    last_activity_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Courses (e.g., "Spanish to Maya", "English to Nahuatl")
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    learning_language_id INTEGER NOT NULL REFERENCES languages(id),
    from_language_id INTEGER NOT NULL REFERENCES languages(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    level VARCHAR(20) DEFAULT 'beginner',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(learning_language_id, from_language_id)
);

-- Skills/Units (e.g., "Greetings", "Food", "Family")
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    order_index INTEGER NOT NULL,
    required_level INTEGER DEFAULT 0,
    xp_reward INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lessons within each skill
CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    order_index INTEGER NOT NULL,
    grammar_tips TEXT,
    xp_reward INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exercise types: translation, multiple_choice, listening, speaking, matching
CREATE TABLE exercises (
    id SERIAL PRIMARY KEY,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    type VARCHAR(30) NOT NULL,
    order_index INTEGER NOT NULL,
    question TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    audio_url VARCHAR(255),
    image_url VARCHAR(255),
    xp_reward INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Multiple choice options
CREATE TABLE exercise_options (
    id SERIAL PRIMARY KEY,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT false,
    order_index INTEGER NOT NULL
);

-- Vocabulary words
CREATE TABLE vocabulary (
    id SERIAL PRIMARY KEY,
    language_id INTEGER NOT NULL REFERENCES languages(id),
    word TEXT NOT NULL,
    translation TEXT NOT NULL,
    translation_language_id INTEGER REFERENCES languages(id),
    pronunciation VARCHAR(255),
    audio_url VARCHAR(255),
    image_url VARCHAR(255),
    part_of_speech VARCHAR(50),
    difficulty_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Link vocabulary to lessons
CREATE TABLE lesson_vocabulary (
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    vocabulary_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
    PRIMARY KEY (lesson_id, vocabulary_id)
);

-- User course enrollment
CREATE TABLE user_courses (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_level INTEGER DEFAULT 1,
    total_xp INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, course_id)
);

-- User progress on skills
CREATE TABLE user_skill_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    level INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT false,
    last_practiced_at TIMESTAMP,
    strength DECIMAL(3,2) DEFAULT 1.00, -- Decay over time
    UNIQUE(user_id, skill_id)
);

-- User progress on lessons
CREATE TABLE user_lesson_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    is_completed BOOLEAN DEFAULT false,
    score INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    completed_at TIMESTAMP,
    last_attempted_at TIMESTAMP,
    UNIQUE(user_id, lesson_id)
);

-- User exercise attempts
CREATE TABLE user_exercise_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    user_answer TEXT,
    is_correct BOOLEAN,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily goals
CREATE TABLE user_daily_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_type VARCHAR(50) NOT NULL, -- 'xp_target', 'lessons_completed'
    target_value INTEGER NOT NULL,
    current_value INTEGER DEFAULT 0,
    goal_date DATE NOT NULL,
    is_achieved BOOLEAN DEFAULT false,
    UNIQUE(user_id, goal_type, goal_date)
);

-- Achievements/Badges
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50),
    requirement_type VARCHAR(50), -- 'streak', 'total_xp', 'lessons_completed'
    requirement_value INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User achievements
CREATE TABLE user_achievements (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id INTEGER NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, achievement_id)
);

-- Leaderboard (weekly/monthly/all-time)
CREATE TABLE leaderboard_entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_type VARCHAR(20) NOT NULL, -- 'weekly', 'monthly', 'all_time'
    period_start DATE NOT NULL,
    xp_earned INTEGER DEFAULT 0,
    rank INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, period_type, period_start)
);

-- Cultural notes and tips
CREATE TABLE cultural_notes (
    id SERIAL PRIMARY KEY,
    language_id INTEGER NOT NULL REFERENCES languages(id),
    skill_id INTEGER REFERENCES skills(id),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_courses_languages ON courses(learning_language_id, from_language_id);
CREATE INDEX idx_skills_course ON skills(course_id);
CREATE INDEX idx_lessons_skill ON lessons(skill_id);
CREATE INDEX idx_exercises_lesson ON exercises(lesson_id);
CREATE INDEX idx_user_courses ON user_courses(user_id, course_id);
CREATE INDEX idx_user_skill_progress ON user_skill_progress(user_id, skill_id);
CREATE INDEX idx_user_lesson_progress ON user_lesson_progress(user_id, lesson_id);
CREATE INDEX idx_vocabulary_language ON vocabulary(language_id);
CREATE INDEX idx_leaderboard ON leaderboard_entries(period_type, period_start, xp_earned DESC);
