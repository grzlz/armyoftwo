import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Languages
export const getLanguages = async () => {
  const response = await api.get('/languages');
  return response.data;
};

// Courses
export const getCourses = async () => {
  const response = await api.get('/courses');
  return response.data;
};

export const getCourseSkills = async (courseId) => {
  const response = await api.get(`/courses/${courseId}/skills`);
  return response.data;
};

// Skills & Lessons
export const getSkillLessons = async (skillId) => {
  const response = await api.get(`/skills/${skillId}/lessons`);
  return response.data;
};

export const getLessonExercises = async (lessonId) => {
  const response = await api.get(`/lessons/${lessonId}/exercises`);
  return response.data;
};

export const getLessonVocabulary = async (lessonId) => {
  const response = await api.get(`/lessons/${lessonId}/vocabulary`);
  return response.data;
};

// Exercises
export const submitExerciseAnswer = async (exerciseId, userAnswer, userId = null) => {
  const response = await api.post(`/exercises/${exerciseId}/submit`, {
    userAnswer,
    userId,
  });
  return response.data;
};

// Cultural Notes
export const getCulturalNotes = async (languageId = null, skillId = null) => {
  const params = {};
  if (languageId) params.languageId = languageId;
  if (skillId) params.skillId = skillId;

  const response = await api.get('/cultural-notes', { params });
  return response.data;
};

export default api;
