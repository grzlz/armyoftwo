import React from 'react';
import { Link } from 'react-router-dom';

const HomePage = () => {
  return (
    <div className="max-w-6xl mx-auto">
      {/* Hero Section */}
      <div className="text-center py-16">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Aprende Lenguas Indígenas de México
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Maya • Tzotzil • Nahuatl
        </p>
        <p className="text-lg text-gray-700 mb-12 max-w-3xl mx-auto">
          Preserva y celebra las lenguas originarias de México. Aprende con lecciones
          interactivas, ejercicios prácticos y sumérgete en la riqueza cultural de estos
          pueblos milenarios.
        </p>
        <Link
          to="/courses"
          className="inline-block bg-gradient-to-r from-orange-600 to-red-600 text-white text-lg font-semibold px-8 py-4 rounded-lg hover:from-orange-700 hover:to-red-700 transition-all transform hover:scale-105"
        >
          Comenzar a Aprender
        </Link>
      </div>

      {/* Language Cards */}
      <div className="grid md:grid-cols-3 gap-8 py-12">
        <div className="card hover:shadow-xl transition-shadow">
          <div className="text-center">
            <div className="text-6xl mb-4">🌿</div>
            <h3 className="text-2xl font-bold mb-2 text-indigenous-maya">
              Yucatec Maya
            </h3>
            <p className="text-gray-600 mb-4">Maaya t'aan</p>
            <p className="text-sm text-gray-700">
              Lengua maya hablada en la península de Yucatán. Con más de 800,000
              hablantes, es una de las lenguas mayas más vitales.
            </p>
            <div className="mt-4 text-sm text-gray-500">
              ~800,000 hablantes
            </div>
          </div>
        </div>

        <div className="card hover:shadow-xl transition-shadow">
          <div className="text-center">
            <div className="text-6xl mb-4">🏔️</div>
            <h3 className="text-2xl font-bold mb-2 text-indigenous-tzotzil">
              Tzotzil
            </h3>
            <p className="text-gray-600 mb-4">Bats'i k'op</p>
            <p className="text-sm text-gray-700">
              Lengua maya hablada en los Altos de Chiapas. Rica tradición oral y
              cultural de las comunidades indígenas chiapanecas.
            </p>
            <div className="mt-4 text-sm text-gray-500">
              ~500,000 hablantes
            </div>
          </div>
        </div>

        <div className="card hover:shadow-xl transition-shadow">
          <div className="text-center">
            <div className="text-6xl mb-4">🦅</div>
            <h3 className="text-2xl font-bold mb-2 text-indigenous-nahuatl">
              Nahuatl
            </h3>
            <p className="text-gray-600 mb-4">Nāhuatl</p>
            <p className="text-sm text-gray-700">
              Lengua del imperio azteca, todavía hablada por comunidades en el
              centro de México. Origen de muchas palabras del español.
            </p>
            <div className="mt-4 text-sm text-gray-500">
              ~1,700,000 hablantes
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 bg-white rounded-2xl shadow-md my-12">
        <h2 className="text-3xl font-bold text-center mb-12">
          ¿Por qué aprender lenguas indígenas?
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 px-8">
          <div className="text-center">
            <div className="text-4xl mb-3">📚</div>
            <h4 className="font-semibold mb-2">Lecciones Interactivas</h4>
            <p className="text-sm text-gray-600">
              Aprende con ejercicios dinámicos y prácticos
            </p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-3">🎯</div>
            <h4 className="font-semibold mb-2">Progreso Personalizado</h4>
            <p className="text-sm text-gray-600">
              Sigue tu avance y gana puntos XP
            </p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-3">🎨</div>
            <h4 className="font-semibold mb-2">Cultura Viva</h4>
            <p className="text-sm text-gray-600">
              Descubre la historia y tradiciones
            </p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-3">🔊</div>
            <h4 className="font-semibold mb-2">Audio Nativo</h4>
            <p className="text-sm text-gray-600">
              Pronunciación de hablantes nativos
            </p>
          </div>
        </div>
      </div>

      {/* Call to Action */}
      <div className="text-center py-12">
        <h2 className="text-3xl font-bold mb-4">
          Únete a la preservación de las lenguas originarias
        </h2>
        <p className="text-lg text-gray-600 mb-8">
          Cada aprendiz ayuda a mantener vivas estas lenguas milenarias
        </p>
        <Link
          to="/courses"
          className="inline-block btn-primary text-lg px-8 py-4"
        >
          Explorar Cursos
        </Link>
      </div>
    </div>
  );
};

export default HomePage;
