import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="bg-gradient-to-r from-orange-600 to-red-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-2xl">🌿</span>
            <span className="text-xl font-bold">Lenguas Vivas</span>
          </Link>

          <div className="flex items-center space-x-6">
            <Link to="/courses" className="hover:text-orange-200 transition-colors">
              Cursos
            </Link>
            <Link to="/cultural-notes" className="hover:text-orange-200 transition-colors">
              Cultura
            </Link>
            <button className="bg-white text-orange-600 px-4 py-2 rounded-lg font-semibold hover:bg-orange-50 transition-colors">
              Iniciar Sesión
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
