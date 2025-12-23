import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getCourseSkills, getSkillLessons } from '../services/api';

const CourseDetailPage = () => {
  const { courseId } = useParams();
  const [skills, setSkills] = useState([]);
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSkills = async () => {
      try {
        const response = await getCourseSkills(courseId);
        setSkills(response.data);
        if (response.data.length > 0) {
          setSelectedSkill(response.data[0]);
        }
      } catch (err) {
        console.error('Error fetching skills:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSkills();
  }, [courseId]);

  useEffect(() => {
    if (selectedSkill) {
      const fetchLessons = async () => {
        try {
          const response = await getSkillLessons(selectedSkill.id);
          setLessons(response.data);
        } catch (err) {
          console.error('Error fetching lessons:', err);
        }
      };

      fetchLessons();
    }
  }, [selectedSkill]);

  if (loading) {
    return <div className="text-center py-12">Cargando...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <Link to="/courses" className="text-orange-600 hover:text-orange-700 mb-4 inline-block">
          ← Volver a Cursos
        </Link>
        <h1 className="text-4xl font-bold mb-2">Unidades del Curso</h1>
        <p className="text-gray-600">Selecciona una unidad para ver las lecciones</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Skills Sidebar */}
        <div className="lg:col-span-1">
          <div className="card sticky top-4">
            <h2 className="text-xl font-bold mb-4">Unidades</h2>
            <div className="space-y-2">
              {skills.map((skill, index) => (
                <button
                  key={skill.id}
                  onClick={() => setSelectedSkill(skill)}
                  className={`w-full text-left p-4 rounded-lg transition-all ${
                    selectedSkill?.id === skill.id
                      ? 'bg-orange-600 text-white shadow-md'
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{skill.icon}</span>
                    <div className="flex-1">
                      <div className="font-semibold">{skill.title}</div>
                      <div className={`text-sm ${selectedSkill?.id === skill.id ? 'text-orange-100' : 'text-gray-500'}`}>
                        {skill.xp_reward} XP
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Lessons Content */}
        <div className="lg:col-span-2">
          {selectedSkill && (
            <div className="card">
              <div className="flex items-center gap-3 mb-6">
                <span className="text-5xl">{selectedSkill.icon}</span>
                <div>
                  <h2 className="text-3xl font-bold">{selectedSkill.title}</h2>
                  <p className="text-gray-600">{selectedSkill.description}</p>
                </div>
              </div>

              <div className="border-t pt-6">
                <h3 className="text-xl font-semibold mb-4">Lecciones</h3>
                {lessons.length > 0 ? (
                  <div className="space-y-3">
                    {lessons.map((lesson, index) => (
                      <Link
                        key={lesson.id}
                        to={`/lessons/${lesson.id}`}
                        className="block p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className="w-10 h-10 bg-orange-600 text-white rounded-full flex items-center justify-center font-bold">
                              {index + 1}
                            </div>
                            <div>
                              <div className="font-semibold">{lesson.title}</div>
                              {lesson.grammar_tips && (
                                <div className="text-sm text-gray-500 mt-1">
                                  💡 {lesson.grammar_tips}
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-sm text-gray-500">
                              {lesson.xp_reward} XP
                            </span>
                            <span className="text-orange-600">→</span>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No hay lecciones disponibles aún.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CourseDetailPage;
