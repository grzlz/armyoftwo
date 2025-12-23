const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { Pool } = require('pg');

// Load environment variables
dotenv.config();

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Database connection pool
const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
});

// Test database connection
pool.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('❌ Database connection error:', err);
  } else {
    console.log('✅ Database connected successfully at:', res.rows[0].now);
  }
});

// Middleware
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:5173',
  credentials: true,
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Routes
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    message: 'Indigenous Language Learning API is running',
    timestamp: new Date().toISOString()
  });
});

// Language routes
app.get('/api/languages', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT id, name, code, native_name, description, total_speakers, flag_emoji FROM languages ORDER BY id'
    );
    res.json({ success: true, data: result.rows });
  } catch (error) {
    console.error('Error fetching languages:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch languages' });
  }
});

// Course routes
app.get('/api/courses', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT c.id, c.title, c.description, c.level,
             l1.name as learning_language, l1.code as learning_code, l1.flag_emoji as learning_flag,
             l2.name as from_language, l2.code as from_code
      FROM courses c
      JOIN languages l1 ON c.learning_language_id = l1.id
      JOIN languages l2 ON c.from_language_id = l2.id
      WHERE c.is_active = true
      ORDER BY c.id
    `);
    res.json({ success: true, data: result.rows });
  } catch (error) {
    console.error('Error fetching courses:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch courses' });
  }
});

// Get skills for a course
app.get('/api/courses/:courseId/skills', async (req, res) => {
  try {
    const { courseId } = req.params;
    const result = await pool.query(
      'SELECT * FROM skills WHERE course_id = $1 ORDER BY order_index',
      [courseId]
    );
    res.json({ success: true, data: result.rows });
  } catch (error) {
    console.error('Error fetching skills:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch skills' });
  }
});

// Get lessons for a skill
app.get('/api/skills/:skillId/lessons', async (req, res) => {
  try {
    const { skillId } = req.params;
    const result = await pool.query(
      'SELECT * FROM lessons WHERE skill_id = $1 ORDER BY order_index',
      [skillId]
    );
    res.json({ success: true, data: result.rows });
  } catch (error) {
    console.error('Error fetching lessons:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch lessons' });
  }
});

// Get exercises for a lesson
app.get('/api/lessons/:lessonId/exercises', async (req, res) => {
  try {
    const { lessonId } = req.params;

    // Get exercises
    const exercisesResult = await pool.query(
      'SELECT * FROM exercises WHERE lesson_id = $1 ORDER BY order_index',
      [lessonId]
    );

    // Get options for multiple choice exercises
    const exercises = await Promise.all(exercisesResult.rows.map(async (exercise) => {
      if (exercise.type === 'multiple_choice') {
        const optionsResult = await pool.query(
          'SELECT id, option_text, order_index FROM exercise_options WHERE exercise_id = $1 ORDER BY order_index',
          [exercise.id]
        );
        return { ...exercise, options: optionsResult.rows };
      }
      return exercise;
    }));

    res.json({ success: true, data: exercises });
  } catch (error) {
    console.error('Error fetching exercises:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch exercises' });
  }
});

// Get vocabulary for a lesson
app.get('/api/lessons/:lessonId/vocabulary', async (req, res) => {
  try {
    const { lessonId } = req.params;
    const result = await pool.query(`
      SELECT v.* FROM vocabulary v
      JOIN lesson_vocabulary lv ON v.id = lv.vocabulary_id
      WHERE lv.lesson_id = $1
    `, [lessonId]);
    res.json({ success: true, data: result.rows });
  } catch (error) {
    console.error('Error fetching vocabulary:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch vocabulary' });
  }
});

// Get cultural notes
app.get('/api/cultural-notes', async (req, res) => {
  try {
    const { languageId, skillId } = req.query;
    let query = 'SELECT cn.*, l.name as language_name FROM cultural_notes cn JOIN languages l ON cn.language_id = l.id WHERE 1=1';
    const params = [];

    if (languageId) {
      params.push(languageId);
      query += ` AND cn.language_id = $${params.length}`;
    }

    if (skillId) {
      params.push(skillId);
      query += ` AND cn.skill_id = $${params.length}`;
    }

    const result = await pool.query(query, params);
    res.json({ success: true, data: result.rows });
  } catch (error) {
    console.error('Error fetching cultural notes:', error);
    res.status(500).json({ success: false, error: 'Failed to fetch cultural notes' });
  }
});

// Submit exercise answer
app.post('/api/exercises/:exerciseId/submit', async (req, res) => {
  try {
    const { exerciseId } = req.params;
    const { userAnswer, userId } = req.body;

    // Get correct answer
    const exerciseResult = await pool.query(
      'SELECT correct_answer, xp_reward FROM exercises WHERE id = $1',
      [exerciseId]
    );

    if (exerciseResult.rows.length === 0) {
      return res.status(404).json({ success: false, error: 'Exercise not found' });
    }

    const exercise = exerciseResult.rows[0];
    const isCorrect = userAnswer.toLowerCase().trim() === exercise.correct_answer.toLowerCase().trim();

    // Record attempt (if userId provided)
    if (userId) {
      await pool.query(
        'INSERT INTO user_exercise_attempts (user_id, exercise_id, user_answer, is_correct) VALUES ($1, $2, $3, $4)',
        [userId, exerciseId, userAnswer, isCorrect]
      );
    }

    res.json({
      success: true,
      data: {
        isCorrect,
        correctAnswer: exercise.correct_answer,
        xpEarned: isCorrect ? exercise.xp_reward : 0
      }
    });
  } catch (error) {
    console.error('Error submitting exercise:', error);
    res.status(500).json({ success: false, error: 'Failed to submit exercise' });
  }
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Route not found'
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({
    success: false,
    error: 'Internal server error'
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
  console.log(`📚 API endpoints available at http://localhost:${PORT}/api`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, closing server...');
  pool.end();
  process.exit(0);
});

module.exports = { app, pool };
