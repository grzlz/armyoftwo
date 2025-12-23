# API Documentation

Base URL: `http://localhost:3000/api`

## Response Format

All endpoints return JSON in the following format:

**Success Response:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message description"
}
```

## Endpoints

### Health Check

#### GET /api/health

Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "message": "Indigenous Language Learning API is running",
  "timestamp": "2025-12-23T12:00:00.000Z"
}
```

---

### Languages

#### GET /api/languages

Get all available languages.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 3,
      "name": "Yucatec Maya",
      "code": "yua",
      "native_name": "Maaya t'aan",
      "description": "Mayan language spoken in Yucatán Peninsula",
      "total_speakers": 800000,
      "flag_emoji": "🌿"
    }
  ]
}
```

---

### Courses

#### GET /api/courses

Get all available courses.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Spanish to Yucatec Maya",
      "description": "Learn Yucatec Maya from Spanish - Beginner Course",
      "level": "beginner",
      "learning_language": "Yucatec Maya",
      "learning_code": "yua",
      "learning_flag": "🌿",
      "from_language": "Spanish",
      "from_code": "es"
    }
  ]
}
```

#### GET /api/courses/:courseId/skills

Get all skills (units) for a specific course.

**Parameters:**
- `courseId` (path parameter) - Course ID

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "course_id": 1,
      "title": "Basics",
      "description": "Essential words and phrases",
      "icon": "👋",
      "order_index": 1,
      "required_level": 0,
      "xp_reward": 20,
      "created_at": "2025-12-23T12:00:00.000Z"
    }
  ]
}
```

---

### Skills & Lessons

#### GET /api/skills/:skillId/lessons

Get all lessons for a specific skill.

**Parameters:**
- `skillId` (path parameter) - Skill ID

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "skill_id": 1,
      "title": "Hello and Thank You",
      "order_index": 1,
      "grammar_tips": "Maya uses glottal stops (') which are important for pronunciation",
      "xp_reward": 15,
      "created_at": "2025-12-23T12:00:00.000Z"
    }
  ]
}
```

#### GET /api/lessons/:lessonId/exercises

Get all exercises for a specific lesson.

**Parameters:**
- `lessonId` (path parameter) - Lesson ID

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "lesson_id": 1,
      "type": "translation",
      "order_index": 1,
      "question": "Translate to Maya: Gracias",
      "correct_answer": "Dios bo'otik",
      "audio_url": null,
      "image_url": null,
      "xp_reward": 5
    },
    {
      "id": 2,
      "lesson_id": 1,
      "type": "multiple_choice",
      "order_index": 2,
      "question": "How do you say 'Good' in Maya?",
      "correct_answer": "Ma'alob",
      "xp_reward": 5,
      "options": [
        {
          "id": 1,
          "option_text": "Ma'alob",
          "order_index": 1
        },
        {
          "id": 2,
          "option_text": "Janal",
          "order_index": 2
        }
      ]
    }
  ]
}
```

**Exercise Types:**
- `translation` - User must type the correct translation
- `multiple_choice` - User selects from provided options

#### GET /api/lessons/:lessonId/vocabulary

Get vocabulary words for a specific lesson.

**Parameters:**
- `lessonId` (path parameter) - Lesson ID

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "language_id": 3,
      "word": "Ba'ax ka wa'alik?",
      "translation": "¿Cómo estás?",
      "translation_language_id": 1,
      "pronunciation": "báash ka waʼáalik",
      "audio_url": null,
      "image_url": null,
      "part_of_speech": "phrase",
      "difficulty_level": 1
    }
  ]
}
```

---

### Exercises

#### POST /api/exercises/:exerciseId/submit

Submit an answer for an exercise.

**Parameters:**
- `exerciseId` (path parameter) - Exercise ID

**Request Body:**
```json
{
  "userAnswer": "Dios bo'otik",
  "userId": 1  // Optional - for tracking if user is logged in
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "isCorrect": true,
    "correctAnswer": "Dios bo'otik",
    "xpEarned": 5
  }
}
```

**Note:** Answers are case-insensitive and trimmed of whitespace.

---

### Cultural Notes

#### GET /api/cultural-notes

Get cultural notes, optionally filtered by language or skill.

**Query Parameters:**
- `languageId` (optional) - Filter by language ID
- `skillId` (optional) - Filter by skill ID

**Example:**
```
GET /api/cultural-notes?languageId=3
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "language_id": 3,
      "language_name": "Yucatec Maya",
      "skill_id": 1,
      "title": "The Maya Writing System",
      "content": "The ancient Maya developed one of the most sophisticated writing systems...",
      "image_url": null,
      "created_at": "2025-12-23T12:00:00.000Z"
    }
  ]
}
```

---

## Error Codes

- `200` - Success
- `404` - Resource not found
- `500` - Internal server error

## Rate Limiting

Currently no rate limiting is implemented. Will be added in future versions.

## Authentication

User authentication endpoints will be added in a future version. Current endpoints are public.

## Future Endpoints

Coming soon:

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/me` - Get current user

### User Progress
- `GET /api/user/progress` - Get user progress
- `POST /api/user/progress/lesson` - Mark lesson complete
- `GET /api/user/streak` - Get user streak info
- `GET /api/user/achievements` - Get user achievements

### Leaderboard
- `GET /api/leaderboard/weekly` - Weekly leaderboard
- `GET /api/leaderboard/monthly` - Monthly leaderboard
- `GET /api/leaderboard/alltime` - All-time leaderboard
