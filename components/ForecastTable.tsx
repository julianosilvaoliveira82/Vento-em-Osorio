import React from 'react';
import type { FusedHourlyData } from '../types';
import { Navigation } from './icons/Navigation';
import { AlertTriangle } from './icons/AlertTriangle';

interface ForecastTableProps {
  tableData: FusedHourlyData[];
  onLoadMore: () => void;
  canLoadMore: boolean;
}

const ForecastTable: React.FC<ForecastTableProps> = ({ tableData, onLoadMore, canLoadMore }) => {
  if (!tableData || tableData.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 text-center text-slate-500">
        <p>Não há dados de previsão detalhada para as próximas horas.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      <div className="p-6">
        <h2 className="text-lg font-semibold text-slate-800">Previsão Detalhada por Hora</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-slate-600">
          <thead className="text-xs text-slate-700 uppercase bg-slate-50">
            <tr>
              <th scope="col" className="px-6 py-3">Hora</th>
              <th scope="col" className="px-6 py-3 text-center">Vento (km/h)</th>
              <th scope="col" className="px-6 py-3">Direção</th>
            </tr>
          </thead>
          <tbody>
            {tableData.map((row, index) => {
              const hasDivergence = row.flags.includes('ALTA_DIVERGÊNCIA');
              const rowClass = hasDivergence ? 'bg-amber-50' : 'bg-white';
              
              const hour = new Date(row.hora).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo' });

              return (
                <tr key={index} className={`${rowClass} border-b last:border-b-0`}>
                  <td className="px-6 py-4 font-medium text-slate-900 whitespace-nowrap">
                    {hour}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="text-xl font-bold text-slate-800">{row.vento_sustentado_kmh}</div>
                    <div className="text-xs text-slate-500">Raj: {row.rajada_kmh}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      {/* Fix: Simplified check as `direcao_graus` is now strictly a number */}
                      {typeof row.direcao_graus === 'number' ? (
                        <Navigation
                          className="w-4 h-4 text-blue-500 shrink-0"
                          style={{ transform: `rotate(${row.direcao_graus}deg)` }}
                        />
                      ) : <div className="w-4 h-4 shrink-0" /> }
                      <span className="flex-1 text-xs">{row.direcao_cardinal_leigo}</span>
                       {hasDivergence && (
                        <div title="Alta divergência entre as fontes de dados para este horário.">
                          <AlertTriangle className="w-4 h-4 text-amber-500" />
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {canLoadMore && (
        <div className="p-4 text-center border-t border-slate-100">
            <button
              onClick={onLoadMore}
              className="px-5 py-2 text-sm font-semibold text-blue-600 bg-blue-50 rounded-full hover:bg-blue-100 transition-colors duration-200"
            >
              Carregar mais
            </button>
        </div>
      )}
    </div>
  );
};

export default ForecastTable;