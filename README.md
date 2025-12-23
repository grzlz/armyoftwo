# Lenguas Vivas - Indigenous Language Learning Platform

A Duolingo-style language learning platform for indigenous Mexican languages: Yucatec Maya, Tzotzil, and Nahuatl.

## 🌟 Features

- **Interactive Lessons**: Learn through translation exercises, multiple choice questions, and more
- **Three Indigenous Languages**: Yucatec Maya, Tzotzil, and Nahuatl
- **Cultural Notes**: Learn about the history and culture behind each language
- **Progress Tracking**: Track your learning with XP points and achievements
- **Beautiful UI**: Modern, responsive design built with React and Tailwind CSS
- **RESTful API**: Full-featured backend API with PostgreSQL database

## 🚀 Tech Stack

### Frontend
- React 18
- React Router
- Axios
- Tailwind CSS
- Vite

### Backend
- Node.js
- Express
- PostgreSQL
- JWT Authentication (planned)

## 📋 Prerequisites

- Node.js (v16 or higher)
- PostgreSQL (v12 or higher)
- npm or yarn

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd armyoftwo
```

### 2. Set up the database

Install PostgreSQL if you haven't already, then create a database:

```bash
# Using psql
createdb indigenous_languages
```

### 3. Set up the backend

```bash
cd proyecto_ennvih/backend

# Install dependencies
npm install

# Create .env file from example
cp .env.example .env

# Edit .env with your database credentials
nano .env
```

Update your `.env` file with your PostgreSQL credentials:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=indigenous_languages
DB_USER=your_username
DB_PASSWORD=your_password
PORT=3000
```

### 4. Initialize the database

```bash
# Run schema creation
npm run init-db

# Seed with initial data
npm run seed
```

### 5. Set up the frontend

```bash
cd ../frontend

# Install dependencies
npm install
```

## 🏃 Running the Application

### Start the backend server

```bash
cd proyecto_ennvih/backend
npm run dev
```

The API will be available at `http://localhost:3000`

### Start the frontend development server

In a new terminal:

```bash
cd proyecto_ennvih/frontend
npm run dev
```

The app will be available at `http://localhost:5173`

## 📚 API Endpoints

### Languages
- `GET /api/languages` - Get all languages
- `GET /api/cultural-notes` - Get cultural notes

### Courses
- `GET /api/courses` - Get all courses
- `GET /api/courses/:courseId/skills` - Get skills for a course

### Skills & Lessons
- `GET /api/skills/:skillId/lessons` - Get lessons for a skill
- `GET /api/lessons/:lessonId/exercises` - Get exercises for a lesson
- `GET /api/lessons/:lessonId/vocabulary` - Get vocabulary for a lesson

### Exercises
- `POST /api/exercises/:exerciseId/submit` - Submit an exercise answer

## 🗄️ Database Schema

The database includes the following main tables:

- `languages` - Supported languages
- `courses` - Available courses
- `skills` - Skill units within courses
- `lessons` - Individual lessons
- `exercises` - Practice exercises
- `vocabulary` - Word dictionary
- `cultural_notes` - Cultural information
- User progress tracking tables (for future user authentication)

## 🎯 Current Status

**Completed:**
- ✅ Database schema design
- ✅ Backend API with all core endpoints
- ✅ Frontend UI with React
- ✅ Course browsing and selection
- ✅ Interactive lesson exercises
- ✅ Cultural notes section
- ✅ Seed data for all three languages

**Planned:**
- 🔜 User authentication and authorization
- 🔜 User progress persistence
- 🔜 Streak tracking and gamification
- 🔜 Audio pronunciation
- 🔜 Speaking exercises
- 🔜 Leaderboards
- 🔜 More lessons and vocabulary
- 🔜 Mobile app

## 🌍 Supported Languages

1. **Yucatec Maya** (Maaya t'aan)
   - ~800,000 speakers
   - Yucatán Peninsula region

2. **Tzotzil** (Bats'i k'op)
   - ~500,000 speakers
   - Chiapas highlands

3. **Nahuatl** (Nāhuatl)
   - ~1,700,000 speakers
   - Central Mexico
   - Language of the Aztec Empire

## 🤝 Contributing

Contributions are welcome! This project aims to preserve and promote indigenous languages.

Areas where you can help:
- Adding more lessons and vocabulary
- Recording native speaker audio
- Translating the interface to more languages
- Adding new exercise types
- Improving the UI/UX

## 📄 License

MIT License

## 🙏 Acknowledgments

This project is dedicated to the preservation of indigenous languages and cultures of Mexico. We acknowledge and respect the indigenous communities who have kept these languages alive for generations.

---

Made with ❤️ for language preservation