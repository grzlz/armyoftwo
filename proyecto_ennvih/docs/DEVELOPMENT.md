# Development Guide

## Project Structure

```
proyecto_ennvih/
├── backend/
│   ├── server.js           # Main Express server
│   ├── package.json        # Backend dependencies
│   ├── .env.example        # Environment variables template
│   ├── scripts/
│   │   ├── initDatabase.js # Database initialization
│   │   └── seedDatabase.js # Seed data insertion
│   └── bd/
│       ├── schema.sql      # Database schema
│       └── seed_data.sql   # Initial data
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API service layer
│   │   └── styles/         # CSS and Tailwind config
│   ├── package.json        # Frontend dependencies
│   └── vite.config.js      # Vite configuration
└── docs/
    └── DEVELOPMENT.md      # This file
```

## Development Workflow

### Backend Development

1. **Making Database Changes**
   - Edit `bd/schema.sql` for schema changes
   - Edit `bd/seed_data.sql` for seed data changes
   - Run `npm run init-db` to recreate tables
   - Run `npm run seed` to populate data

2. **Adding API Endpoints**
   - Add routes in `server.js`
   - Follow RESTful conventions
   - Return consistent JSON responses:
     ```json
     {
       "success": true,
       "data": {...}
     }
     ```

3. **Database Queries**
   - Use parameterized queries to prevent SQL injection
   - Example:
     ```javascript
     await pool.query('SELECT * FROM lessons WHERE id = $1', [lessonId]);
     ```

### Frontend Development

1. **Creating New Pages**
   - Add page component in `src/pages/`
   - Add route in `src/App.jsx`
   - Use React Router's `<Link>` for navigation

2. **API Integration**
   - Add API functions in `src/services/api.js`
   - Use async/await for API calls
   - Handle loading and error states

3. **Styling**
   - Use Tailwind CSS utility classes
   - Custom components in `src/styles/index.css`
   - Follow existing color scheme

## Database Management

### Resetting the Database

```bash
# Drop all tables and recreate
cd proyecto_ennvih/backend
npm run init-db
npm run seed
```

### Adding New Languages

1. Add language to `languages` table in `seed_data.sql`
2. Create corresponding courses
3. Add skills, lessons, and exercises
4. Add vocabulary and cultural notes

### Exercise Types

Currently supported:
- `translation` - User types the translation
- `multiple_choice` - User selects from options

Future types:
- `listening` - Audio-based exercises
- `speaking` - Voice recognition
- `matching` - Match words to translations
- `fill_blank` - Fill in the blank

## API Response Format

All API endpoints return JSON in this format:

**Success:**
```json
{
  "success": true,
  "data": {
    // Response data here
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message"
}
```

## Testing

### Manual Testing Checklist

- [ ] Can browse all courses
- [ ] Can view skills for a course
- [ ] Can start a lesson
- [ ] Translation exercises work
- [ ] Multiple choice exercises work
- [ ] XP is calculated correctly
- [ ] Can complete a lesson
- [ ] Cultural notes load correctly
- [ ] Navigation works properly
- [ ] Responsive on mobile

### Future: Automated Testing

```bash
# Backend tests
cd backend
npm test

# Frontend tests
cd frontend
npm test
```

## Adding Content

### Adding Vocabulary

```sql
INSERT INTO vocabulary (language_id, word, translation, translation_language_id, pronunciation, part_of_speech, difficulty_level)
VALUES (3, 'K''aaba''', 'Nombre', 1, 'kʼáabaʼ', 'noun', 1);
```

### Adding Exercises

```sql
-- Add translation exercise
INSERT INTO exercises (lesson_id, type, order_index, question, correct_answer, xp_reward)
VALUES (1, 'translation', 1, 'Translate: Hello', 'Bix a beel?', 5);

-- Add multiple choice exercise
INSERT INTO exercises (lesson_id, type, order_index, question, correct_answer, xp_reward)
VALUES (1, 'multiple_choice', 2, 'What does "Dios bo''otik" mean?', 'Thank you', 5);

-- Add options for multiple choice
INSERT INTO exercise_options (exercise_id, option_text, is_correct, order_index) VALUES
(1, 'Thank you', true, 1),
(1, 'Hello', false, 2),
(1, 'Goodbye', false, 3),
(1, 'Please', false, 4);
```

### Adding Cultural Notes

```sql
INSERT INTO cultural_notes (language_id, skill_id, title, content)
VALUES (
  3,
  1,
  'Maya Calendar',
  'The ancient Maya developed a sophisticated calendar system that tracked time with remarkable precision...'
);
```

## Performance Optimization

### Database
- Indexes are already created on frequently queried columns
- Use `EXPLAIN ANALYZE` to optimize slow queries
- Consider materialized views for complex aggregations

### Frontend
- Use React.lazy() for code splitting
- Optimize images
- Implement caching with React Query (planned)

### Backend
- Enable compression middleware
- Implement response caching
- Use connection pooling (already configured)

## Environment Variables

### Backend (.env)

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=indigenous_languages
DB_USER=postgres
DB_PASSWORD=your_password

# Server
PORT=3000
NODE_ENV=development

# JWT (for future auth)
JWT_SECRET=your_secret_key
JWT_EXPIRES_IN=7d

# CORS
CORS_ORIGIN=http://localhost:5173
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:3000/api
```

## Common Issues

### Database Connection Error
- Check PostgreSQL is running
- Verify credentials in `.env`
- Ensure database exists

### CORS Error
- Check `CORS_ORIGIN` in backend `.env`
- Verify frontend is running on correct port

### Build Errors
- Delete `node_modules` and reinstall
- Clear npm/yarn cache
- Check Node.js version

## Next Steps for Development

1. **User Authentication**
   - Implement JWT-based auth
   - Add registration/login endpoints
   - Protect user-specific routes

2. **Progress Persistence**
   - Save user exercise attempts
   - Track lesson completion
   - Calculate streaks

3. **Audio Integration**
   - Record native speaker audio
   - Store audio files or use cloud storage
   - Add audio playback in exercises

4. **Enhanced Gamification**
   - Implement achievements system
   - Add leaderboards
   - Create daily challenges

5. **Content Expansion**
   - Add more lessons per skill
   - Expand vocabulary database
   - Add more cultural notes
   - Create advanced courses
