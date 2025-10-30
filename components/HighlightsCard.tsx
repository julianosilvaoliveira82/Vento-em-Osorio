import React from 'react';
import type { HighlightsData } from '../types';
import { ChevronsUp } from './icons/ChevronsUp';
import { ChevronsDown } from './icons/ChevronsDown';

interface HighlightsCardProps {
  highlights: HighlightsData;
}

const HighlightItem: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string | number;
  unit: string;
  time: string;
}> = ({ icon, label, value, unit, time }) => (
  <div className="flex items-start space-x-4">
    <div className="shrink-0">{icon}</div>
    <div>
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="text-2xl font-bold text-slate-800">
        {value} <span className="text-base font-medium text-slate-500">{unit}</span>
      </p>
      <p className="text-xs text-slate-500">
        previsto para ~{time}
      </p>
    </div>
  </div>
);

const HighlightsCard: React.FC<HighlightsCardProps> = ({ highlights }) => {
  const { pico_vento, calmaria } = highlights;

  const formatHour = (horaStr: string) => {
    return new Date(horaStr).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'America/Sao_Paulo'
    });
  };

  if (!pico_vento && !calmaria) {
    return null; // Don't render the card if there's nothing to show
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">Destaques das Próximas 24h</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {pico_vento ? (
          <HighlightItem
            icon={<div className="p-3 bg-red-100 rounded-full"><ChevronsUp className="w-6 h-6 text-red-600" /></div>}
            label="Pico de Vento"
            value={pico_vento.vento_sustentado_kmh}
            unit="km/h"
            time={formatHour(pico_vento.hora)}
          />
        ) : (
          <div className="text-sm text-slate-500">Não há dados de pico de vento.</div>
        )}

        {calmaria ? (
          <HighlightItem
            icon={<div className="p-3 bg-green-100 rounded-full"><ChevronsDown className="w-6 h-6 text-green-600" /></div>}
            label="Período de Calmaria"
            value={calmaria.vento_sustentado_kmh}
            unit="km/h"
            time={formatHour(calmaria.hora)}
          />
        ) : (
          <div className="flex items-start space-x-4">
             <div className="p-3 bg-slate-100 rounded-full"><ChevronsDown className="w-6 h-6 text-slate-500" /></div>
             <div>
                <p className="text-sm font-medium text-slate-500">Período de Calmaria</p>
                <p className="text-base font-semibold text-slate-600 pt-1">Sem previsão de calmaria.</p>
             </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HighlightsCard;