
import React from 'react';
import type { PanelData } from '../types';
import { TrendingUp } from './icons/TrendingUp';
import { AlertTriangle } from './icons/AlertTriangle';

interface SummaryCardProps {
  panel: PanelData;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ panel }) => {
  const isDataAvailable = panel.status === 'OK' && panel.media_24h_kmh !== 'NA';

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center space-x-4">
        {isDataAvailable ? (
          <div className="p-3 bg-blue-100 rounded-full">
            <TrendingUp className="w-6 h-6 text-blue-600" />
          </div>
        ) : (
          <div className="p-3 bg-yellow-100 rounded-full">
            <AlertTriangle className="w-6 h-6 text-yellow-600" />
          </div>
        )}
        <div>
          <p className="text-sm text-slate-500 font-medium">Velocidade média (próx. 24h)</p>
          {isDataAvailable ? (
            <p className="text-3xl font-bold text-slate-800">
              {panel.media_24h_kmh} <span className="text-xl font-medium text-slate-500">km/h</span>
            </p>
          ) : (
            <p className="text-xl font-semibold text-slate-600">
              Dados Insuficientes
            </p>
          )}
        </div>
      </div>
      {panel.observacoes && (
        <p className="mt-4 text-xs text-center text-slate-500 bg-slate-50 p-2 rounded-md">
          {panel.observacoes}
        </p>
      )}
    </div>
  );
};

export default SummaryCard;