import React, { useState, useEffect, useCallback } from 'react';
import { getWindForecast } from './services/windService';
import type { ForecastOutput } from './types';
import Header from './components/Header';
import SummaryCard from './components/SummaryCard';
import ForecastTable from './components/ForecastTable';
import SourcesStatus from './components/SourcesStatus';
import { RefreshCw } from './components/icons/RefreshCw';
import HighlightsCard from './components/HighlightsCard';

const App: React.FC = () => {
  const [forecast, setForecast] = useState<ForecastOutput | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [displayedHours, setDisplayedHours] = useState<number>(8);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // In a real app, you might pass real data here if not using proxies.
      // For this example, the service uses mock data if proxies are empty.
      const data = await getWindForecast();
      setForecast(data);
      setDisplayedHours(8); // Reset view to initial 8 hours on refresh
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred.');
      }
      setForecast(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  const handleLoadMore = () => {
    setDisplayedHours(prev => prev + 8);
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex flex-col items-center justify-center text-center p-8 text-slate-500">
          <RefreshCw className="w-12 h-12 animate-spin mb-4" />
          <p className="text-lg font-medium">Analisando os ventos...</p>
          <p className="text-sm">Consolidando previsões para Osório.</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-center p-8 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          <h2 className="font-bold text-lg mb-2">Erro ao carregar dados</h2>
          <p>{error}</p>
        </div>
      );
    }

    if (!forecast) {
      return (
        <div className="text-center p-8 text-slate-500">
          <p>Nenhum dado de previsão disponível.</p>
        </div>
      );
    }

    const canLoadMore = displayedHours < forecast.tabela_completa.length;

    return (
      <>
        <SummaryCard panel={forecast.painel} />
        <HighlightsCard highlights={forecast.highlights} />
        <ForecastTable 
          tableData={forecast.tabela_completa.slice(0, displayedHours)}
          onLoadMore={handleLoadMore}
          canLoadMore={canLoadMore}
        />
        <SourcesStatus sources={forecast.fontes_utilizadas} />
      </>
    );
  };

  return (
    <div className="min-h-screen bg-slate-100 font-sans text-slate-800">
      <Header
        lastUpdated={forecast?.header.atualizado_em}
        onRefresh={fetchData}
        isLoading={loading}
      />
      <main className="p-4 sm:p-6 md:p-8 max-w-7xl mx-auto">
        <div className="space-y-6">
          {renderContent()}
        </div>
      </main>
    </div>
  );
};

export default App;