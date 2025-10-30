// Raw data from sources
export type RawHourlyData = {
  hora_utc?: string;
  hora_local?: string;
  sustentado: { valor: number; unidade: 'knots' | 'm/s' | 'km/h' };
  rajada: { valor: number; unidade: 'knots' | 'm/s' | 'km/h' };
  direcao: { graus?: number; cardinal?: string };
  fonte: string;
};

// Data after normalization (common units)
export type NormalizedHourlyData = {
  timestamp: Date;
  sustentado_kmh: number;
  rajada_kmh: number;
  direcao_graus: number;
  fonte: string;
};

// Data after fusing sources for a single hour
export type FusedHourlyData = {
  hora: string;
  vento_sustentado_kmh: number;
  rajada_kmh: number;
  direcao_graus: number;
  direcao_cardinal_leigo: string;
  flags: string[];
};

// Status of each data source
export type SourceStatus = {
  url: string;
  name: string;
  location: string;
  status: 'ok' | 'falha';
};

// Data for the main summary panel
export type PanelData = {
  media_24h_kmh: number | 'NA';
  status: 'OK' | 'DADOS_INSUFICIENTES';
  observacoes: string;
};

// Data for a single highlight (e.g., peak wind)
export type Highlight = {
  hora: string;
  vento_sustentado_kmh: number;
};

// Data for the highlights card
export type HighlightsData = {
  pico_vento: Highlight | null;
  calmaria: Highlight | null;
};

// The final output structure for the UI
export type ForecastOutput = {
  header: {
    titulo: string;
    atualizado_em: string;
    timezone: string;
  };
  painel: PanelData;
  highlights: HighlightsData;
  tabela_completa: FusedHourlyData[];
  fontes_utilizadas: SourceStatus[];
};