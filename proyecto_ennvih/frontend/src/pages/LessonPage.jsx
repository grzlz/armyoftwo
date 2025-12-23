import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getLessonExercises, getLessonVocabulary, submitExerciseAnswer } from '../services/api';

const LessonPage = () => {
  const { lessonId } = useParams();
  const navigate = useNavigate();
  const [exercises, setExercises] = useState([]);
  const [vocabulary, setVocabulary] = useState([]);
  const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [totalXP, setTotalXP] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLessonData = async () => {
      try {
        const [exercisesRes, vocabRes] = await Promise.all([
          getLessonExercises(lessonId),
          getLessonVocabulary(lessonId),
        ]);
        setExercises(exercisesRes.data);
        setVocabulary(vocabRes.data);
      } catch (err) {
        console.error('Error fetching lesson data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchLessonData();
  }, [lessonId]);

  const currentExercise = exercises[currentExerciseIndex];

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!userAnswer.trim()) return;

    try {
      const response = await submitExerciseAnswer(currentExercise.id, userAnswer);
      setFeedback(response.data);

      if (response.data.isCorrect) {
        setTotalXP(prev => prev + response.data.xpEarned);
      }
    } catch (err) {
      console.error('Error submitting answer:', err);
    }
  };

  const handleNext = () => {
    setUserAnswer('');
    setFeedback(null);

    if (currentExerciseIndex < exercises.length - 1) {
      setCurrentExerciseIndex(prev => prev + 1);
    } else {
      // Lesson complete!
      alert(`¡Lección completada! Has ganado ${totalXP} XP total`);
      navigate(-1);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Cargando lección...</div>;
  }

  if (exercises.length === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <p className="text-gray-600">No hay ejercicios disponibles para esta lección.</p>
        <button onClick={() => navigate(-1)} className="btn-primary mt-4">
          Volver
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold">
            Progreso: {currentExerciseIndex + 1} / {exercises.length}
          </span>
          <span className="text-sm font-semibold text-orange-600">
            {totalXP} XP
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-orange-500 to-orange-600 h-3 rounded-full transition-all duration-300"
            style={{ width: `${((currentExerciseIndex + 1) / exercises.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Vocabulary Preview (if available) */}
      {vocabulary.length > 0 && currentExerciseIndex === 0 && !feedback && (
        <div className="card mb-6 bg-blue-50 border-2 border-blue-200">
          <h3 className="font-bold text-lg mb-3">📚 Vocabulario de esta lección:</h3>
          <div className="grid grid-cols-2 gap-3">
            {vocabulary.slice(0, 4).map((word) => (
              <div key={word.id} className="bg-white p-3 rounded-lg">
                <div className="font-semibold text-sm">{word.word}</div>
                <div className="text-gray-600 text-xs">{word.translation}</div>
                {word.pronunciation && (
                  <div className="text-gray-500 text-xs italic mt-1">
                    [{word.pronunciation}]
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Exercise Card */}
      <div className="card">
        <div className="mb-6">
          <div className="inline-block px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-semibold mb-4">
            {currentExercise.type === 'translation' ? '📝 Traducción' : '✅ Opción Múltiple'}
          </div>
          <h2 className="text-2xl font-bold">{currentExercise.question}</h2>
        </div>

        {!feedback ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            {currentExercise.type === 'translation' ? (
              <div>
                <input
                  type="text"
                  value={userAnswer}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  placeholder="Escribe tu respuesta..."
                  className="input-field text-lg"
                  autoFocus
                />
              </div>
            ) : (
              <div className="space-y-3">
                {currentExercise.options?.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => setUserAnswer(option.option_text)}
                    className={`w-full p-4 text-left rounded-lg border-2 transition-all ${
                      userAnswer === option.option_text
                        ? 'border-orange-500 bg-orange-50'
                        : 'border-gray-300 hover:border-orange-300 hover:bg-gray-50'
                    }`}
                  >
                    {option.option_text}
                  </button>
                ))}
              </div>
            )}

            <button
              type="submit"
              disabled={!userAnswer.trim()}
              className="btn-primary w-full text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Verificar Respuesta
            </button>
          </form>
        ) : (
          <div>
            <div className={`p-6 rounded-lg mb-6 ${
              feedback.isCorrect ? 'bg-green-100 border-2 border-green-500' : 'bg-red-100 border-2 border-red-500'
            }`}>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-4xl">
                  {feedback.isCorrect ? '✅' : '❌'}
                </span>
                <div>
                  <div className="text-xl font-bold">
                    {feedback.isCorrect ? '¡Correcto!' : 'Incorrecto'}
                  </div>
                  {!feedback.isCorrect && (
                    <div className="text-sm mt-1">
                      Respuesta correcta: <strong>{feedback.correctAnswer}</strong>
                    </div>
                  )}
                </div>
              </div>
              {feedback.isCorrect && (
                <div className="text-green-700">
                  +{feedback.xpEarned} XP
                </div>
              )}
            </div>

            <button onClick={handleNext} className="btn-primary w-full text-lg">
              {currentExerciseIndex < exercises.length - 1 ? 'Siguiente →' : 'Completar Lección ✨'}
            </button>
          </div>
        )}
      </div>

      {/* Exit Button */}
      <div className="text-center mt-6">
        <button
          onClick={() => navigate(-1)}
          className="text-gray-500 hover:text-gray-700 text-sm"
        >
          ← Salir de la lección
        </button>
      </div>
    </div>
  );
};

export default LessonPage;
