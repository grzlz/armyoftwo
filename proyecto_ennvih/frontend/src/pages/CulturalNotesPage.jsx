import React, { useEffect, useState } from 'react';
import { getCulturalNotes } from '../services/api';

const CulturalNotesPage = () => {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLanguage, setSelectedLanguage] = useState('all');

  useEffect(() => {
    const fetchNotes = async () => {
      try {
        const response = await getCulturalNotes();
        setNotes(response.data);
      } catch (err) {
        console.error('Error fetching cultural notes:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchNotes();
  }, []);

  const filteredNotes = selectedLanguage === 'all'
    ? notes
    : notes.filter(note => note.language_name.toLowerCase().includes(selectedLanguage));

  if (loading) {
    return <div className="text-center py-12">Cargando notas culturales...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Notas Culturales</h1>
        <p className="text-lg text-gray-600">
          Descubre la historia, tradiciones y cultura de las lenguas indígenas
        </p>
      </div>

      {/* Language Filter */}
      <div className="flex justify-center gap-3 mb-8">
        <button
          onClick={() => setSelectedLanguage('all')}
          className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
            selectedLanguage === 'all'
              ? 'bg-orange-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Todas
        </button>
        <button
          onClick={() => setSelectedLanguage('maya')}
          className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
            selectedLanguage === 'maya'
              ? 'bg-green-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          🌿 Maya
        </button>
        <button
          onClick={() => setSelectedLanguage('tzotzil')}
          className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
            selectedLanguage === 'tzotzil'
              ? 'bg-teal-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          🏔️ Tzotzil
        </button>
        <button
          onClick={() => setSelectedLanguage('nahuatl')}
          className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
            selectedLanguage === 'nahuatl'
              ? 'bg-amber-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          🦅 Nahuatl
        </button>
      </div>

      {/* Cultural Notes Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        {filteredNotes.map((note) => (
          <div key={note.id} className="card hover:shadow-xl transition-shadow">
            <div className="flex items-center gap-2 mb-3">
              <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-semibold">
                {note.language_name}
              </span>
            </div>
            <h3 className="text-xl font-bold mb-3">{note.title}</h3>
            <p className="text-gray-700 leading-relaxed whitespace-pre-line">
              {note.content}
            </p>
            {note.image_url && (
              <div className="mt-4">
                <img
                  src={note.image_url}
                  alt={note.title}
                  className="w-full rounded-lg"
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredNotes.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No hay notas culturales disponibles para este filtro.
        </div>
      )}

      {/* Additional Info Section */}
      <div className="mt-16 card bg-gradient-to-r from-orange-50 to-red-50">
        <h2 className="text-2xl font-bold mb-4">¿Por qué es importante preservar estas lenguas?</h2>
        <div className="space-y-3 text-gray-700">
          <p>
            Las lenguas indígenas son portadoras de conocimientos ancestrales, cosmovisiones únicas
            y formas de entender el mundo que enriquecen la diversidad cultural de la humanidad.
          </p>
          <p>
            México es uno de los países con mayor diversidad lingüística del mundo, con 68 lenguas
            indígenas y 364 variantes. Sin embargo, muchas de ellas están en peligro de desaparecer.
          </p>
          <p>
            Al aprender estas lenguas, contribuyes a su preservación y demuestras respeto por las
            culturas que las han mantenido vivas durante siglos.
          </p>
        </div>
      </div>
    </div>
  );
};

export default CulturalNotesPage;
