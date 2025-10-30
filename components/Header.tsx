
import React from 'react';
import { RefreshCw } from './icons/RefreshCw';
import { Wind } from './icons/Wind';

interface HeaderProps {
  lastUpdated?: string;
  onRefresh: () => void;
  isLoading: boolean;
}

const Header: React.FC<HeaderProps> = ({ lastUpdated, onRefresh, isLoading }) => {
  return (
    <header className="sticky top-0 bg-white/80 backdrop-blur-md shadow-md z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-3">
            <Wind className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-xl font-bold text-slate-800">Vento em Osório, RS</h1>
              {lastUpdated && !isLoading && (
                 <p className="text-xs text-slate-500">
                  Atualizado em: {lastUpdated}
                </p>
              )}
               {isLoading && (
                 <p className="text-xs text-slate-500 animate-pulse">
                  Atualizando...
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center justify-center p-2 rounded-full text-slate-600 hover:bg-slate-200 hover:text-blue-600 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Atualizar dados"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
