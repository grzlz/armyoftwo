import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getCourses } from '../services/api';

const CoursesPage = () => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const response = await getCourses();
        setCourses(response.data);
      } catch (err) {
        setError('Error al cargar los cursos');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-xl">Cargando cursos...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 py-12">
        <p>{error}</p>
      </div>
    );
  }

  const getLanguageColor = (code) => {
    const colors = {
      yua: 'from-green-600 to-green-700',
      tzo: 'from-teal-600 to-teal-700',
      nah: 'from-amber-600 to-amber-700',
    };
    return colors[code] || 'from-gray-600 to-gray-700';
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Cursos Disponibles</h1>
        <p className="text-lg text-gray-600">
          Elige el curso que quieres comenzar
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {courses.map((course) => (
          <Link
            key={course.id}
            to={`/courses/${course.id}`}
            className="card hover:shadow-xl transition-all transform hover:scale-105"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-3xl">{course.learning_flag}</span>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold text-white bg-gradient-to-r ${getLanguageColor(course.learning_code)}`}>
                {course.level}
              </span>
            </div>

            <h3 className="text-xl font-bold mb-2">{course.learning_language}</h3>
            <p className="text-sm text-gray-500 mb-3">
              Desde {course.from_language}
            </p>
            <p className="text-gray-700 text-sm">{course.description}</p>

            <div className="mt-6 flex items-center justify-between">
              <span className="text-sm text-gray-500">
                Nivel: {course.level}
              </span>
              <span className="text-orange-600 font-semibold">
                Comenzar →
              </span>
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-12 text-center">
        <div className="card inline-block">
          <h3 className="font-semibold mb-2">¿No encuentras tu idioma base?</h3>
          <p className="text-sm text-gray-600">
            Actualmente ofrecemos cursos desde Español e Inglés. Más idiomas próximamente.
          </p>
        </div>
      </div>
    </div>
  );
};

export default CoursesPage;
