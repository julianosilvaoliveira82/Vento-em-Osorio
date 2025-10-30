import React, { useMemo, useState } from 'react';
import type { SourceStatus } from '../types';

interface SourcesStatusProps {
  sources: SourceStatus[];
}

interface GroupedSources {
  [location: string]: SourceStatus[];
}

const StatusIndicator: React.FC<{ status: 'ok' | 'falha' }> = ({ status }) => {
  const baseClasses = "w-2 h-2 rounded-full";
  const statusClasses = status === 'ok' 
    ? "bg-green-500" 
    : "bg-red-500";
  return <div className={`${baseClasses} ${statusClasses}`} />;
};

const ChevronDown: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <polyline points="6 9 12 15 18 9" />
  </svg>
);

const SourcesStatus: React.FC<SourcesStatusProps> = ({ sources }) => {
  const [isOpen, setIsOpen] = useState(false);

  const groupedSources = useMemo(() => {
    return sources.reduce((acc, source) => {
      const { location } = source;
      if (!acc[location]) {
        acc[location] = [];
      }
      acc[location].push(source);
      return acc;
    }, {} as GroupedSources);
  }, [sources]);

  const locations = Object.keys(groupedSources).sort();

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
       <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex justify-between items-center text-left"
        aria-expanded={isOpen}
        aria-controls="sources-content"
      >
        <h3 className="text-lg font-semibold text-slate-800">Status das Fontes de Dados</h3>
        <ChevronDown className={`w-5 h-5 text-slate-500 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div id="sources-content" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-4 mt-4 border-t border-slate-100">
          {locations.map(location => (
            <div key={location} className="bg-slate-50 rounded-lg p-4">
              <h4 className="font-bold text-slate-700 text-md mb-3">{location}</h4>
              <div className="space-y-2">
                {groupedSources[location].map(source => (
                  <div 
                    key={source.url} 
                    className="flex items-center justify-between text-sm"
                  >
                    <div className="flex items-center space-x-2">
                      <StatusIndicator status={source.status} />
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-slate-600 hover:text-blue-600 hover:underline transition-colors duration-150"
                        title={`Visitar ${source.name}`}
                      >
                        {source.name}
                      </a>
                      {source.generated && (
                        <span className="text-xs text-slate-500 italic">(gerado por IA)</span>
                      )}
                    </div>
                    <span className={`font-medium text-xs ${source.status === 'ok' ? 'text-green-600' : 'text-red-600'}`}>
                      {source.status === 'ok' ? 'Online' : 'Falha'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SourcesStatus;
