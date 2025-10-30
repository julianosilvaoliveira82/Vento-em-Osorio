import { GoogleGenAI } from '@google/genai';
import type { RawHourlyData, NormalizedHourlyData, ForecastOutput, FusedHourlyData, Highlight, HighlightsData, SourceStatus, PanelData } from '../types';
import { TIMEZONE, CONVERSION_FACTORS, FUSION_WEIGHTS, DIVERGENCE_THRESHOLD_KMH, MIN_VALID_POINTS_FOR_AVERAGE, SOURCES_CONFIG, WINDY_API_CONFIG } from '../constants';

// --- Helper Functions ---

const convertToKmh = (value: number, unit: 'knots' | 'm/s' | 'km/h'): number => {
  switch (unit) {
    case 'knots':
      return value * CONVERSION_FACTORS.knots_to_kmh;
    case 'm/s':
      return value * CONVERSION_FACTORS.ms_to_kmh;
    case 'km/h':
    default:
      return value;
  }
};

const cardinalToDegrees = (cardinal: string): number => {
    const directions: { [key: string]: number } = {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
    };
    return directions[cardinal.toUpperCase()] ?? -1;
};

const degreesToCardinalLeigo = (degrees: number | 'NA'): string => {
  if (degrees === 'NA' || typeof degrees !== 'number' || degrees < 0 || degrees > 360) return 'NA';
  
  const directions = [
    { dir: 'Norte', desc: 'vento da terra/continente' },
    { dir: 'Nordeste', desc: 'vento da terra/continente' },
    { dir: 'Leste', desc: 'vento do mar para o continente' },
    { dir: 'Sudeste', desc: 'vento do mar para o continente' },
    { dir: 'Sul', desc: 'vento da lagoa para a cidade' },
    { dir: 'Sudoeste', desc: 'vento da terra/continente' },
    { dir: 'Oeste', desc: 'vento da terra/continente' },
    { dir: 'Noroeste', desc: 'vento da terra/continente' },
  ];
  const index = Math.round(degrees / 45) % 8;
  const { dir, desc } = directions[index];
  return `${dir} – ${desc}`;
};

const getFormattedDateTime = (date: Date, format: 'full' | 'hourly'): string => {
    if (format === 'full') {
        return new Intl.DateTimeFormat('pt-BR', {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', timeZone: TIMEZONE
        }).format(date);
    }
    // hourly
    return new Intl.DateTimeFormat('pt-BR', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', hour12: false, timeZone: TIMEZONE
    }).format(date).replace(/,/, '').replace(/(\d{2})\/(\d{2})\/(\d{4}) (\d{2}:\d{2})/, '$3-$2-$1 $4').slice(0, 16);
};


// --- Core Logic ---

async function fetchWindyApiData(sourceId: string): Promise<RawHourlyData[]> {
    try {
        const payload = {
            lat: WINDY_API_CONFIG.lat,
            lon: WINDY_API_CONFIG.lon,
            model: WINDY_API_CONFIG.model,
            parameters: WINDY_API_CONFIG.parameters,
            levels: WINDY_API_CONFIG.levels,
            key: WINDY_API_CONFIG.apiKey,
        };

        const response = await fetch(WINDY_API_CONFIG.endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Windy API request failed with status ${response.status}`);
        }

        const data = await response.json();
        const { ts, ['wind_u-surface']: u, ['wind_v-surface']: v, ['gust-surface']: gust } = data;

        if (!ts || !u || !v) {
            throw new Error('Invalid data structure from Windy API');
        }
        
        const mpsToKnots = 1.943844;

        const formattedData: RawHourlyData[] = ts.map((t: number, i: number) => {
            const uu = u[i];
            const vv = v[i];

            const speed_mps = Math.hypot(uu, vv);
            // Meteorological direction (from where the wind blows)
            const direction_deg = (Math.atan2(-uu, -vv) * 180 / Math.PI + 360) % 360;

            const gust_mps = gust && gust[i] ? gust[i] : speed_mps;

            return {
                hora_utc: new Date(t * 1000).toISOString(),
                sustentado: { valor: speed_mps * mpsToKnots, unidade: 'knots' },
                rajada: { valor: gust_mps * mpsToKnots, unidade: 'knots' },
                direcao: { graus: Math.round(direction_deg) },
                fonte: sourceId,
            };
        });

        return formattedData;

    } catch (error) {
        console.error('Error fetching data from Windy API:', error);
        return []; // Return empty array on failure to trigger fallback
    }
}


async function fetchDataSources(): Promise<{ data: { [key: string]: RawHourlyData[] }, statuses: SourceStatus[] }> {
    const ai = new GoogleGenAI({ apiKey: import.meta.env.VITE_GOOGLE_API_KEY });

    const data: { [key: string]: RawHourlyData[] } = {};
    const statuses: SourceStatus[] = [];

    const promises = SOURCES_CONFIG.map(async (source) => {
        let isGenerated = true; // Default to true, assume generation unless API succeeds
        // If it's the Windy source, try the API first
        if (source.id === 'windyapp_osorio') {
            const apiData = await fetchWindyApiData(source.id);
            if (apiData.length > 0) {
                 isGenerated = false;
                return { id: source.id, data: apiData, status: 'ok' as const, sourceConfig: source, generated: isGenerated };
            }
            console.log('Windy API failed, falling back to Gemini generation.');
        }

        // Gemini generation for other sources or as fallback for Windy
        try {
            const prompt = `Gere uma previsão de vento realista de 72 horas para ${source.location}, RS, Brasil, com base no modelo de previsão ${source.name}. Use informações atuais da web para basear sua previsão. Forneça os dados como um array JSON de objetos. Cada objeto deve ter esta estrutura: { "hora_utc": "string (ISO 8601)", "sustentado": { "valor": number, "unidade": "knots" }, "rajada": { "valor": number, "unidade": "knots" }, "direcao": { "graus": number } }.`;

            const response = await ai.models.generateContent({
                model: 'gemini-2.5-flash',
                contents: prompt,
                config: {
                    tools: [{ googleSearch: {} }],
                },
            });

            let jsonText = response.text.trim();
            const jsonMatch = jsonText.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
            if (jsonMatch && jsonMatch[1]) {
                jsonText = jsonMatch[1];
            }

            const parsedData = JSON.parse(jsonText) as Omit<RawHourlyData, 'fonte'>[];
            const finalData = parsedData.map(d => ({ ...d, fonte: source.id }));

            return { id: source.id, data: finalData, status: 'ok' as const, sourceConfig: source, generated: isGenerated };
        } catch (error) {
            console.error(`Error fetching real-time data for source ${source.name} (${source.location}):`, error);
            return { id: source.id, data: [], status: 'falha' as const, sourceConfig: source, generated: isGenerated };
        }
    });

    const results = await Promise.all(promises);

    results.forEach(result => {
        data[result.id] = result.data;
        statuses.push({
            url: result.sourceConfig.url,
            name: result.sourceConfig.name,
            location: result.sourceConfig.location,
            status: result.status,
            generated: result.generated,
        });
    });

    return { data, statuses };
}

function normalizeAllData(rawData: { [key: string]: RawHourlyData[] }): NormalizedHourlyData[] {
    const normalized: NormalizedHourlyData[] = [];
    Object.values(rawData).flat().forEach(item => {
        if (!item) return;

        let timestamp: Date | null = null;
        if (item.hora_utc) {
            timestamp = new Date(item.hora_utc);
        } else if (item.hora_local) {
            // Assuming local time is already in the target timezone for simplicity
            timestamp = new Date(item.hora_local.replace(' ', 'T') + 'Z');
        }

        if (!timestamp || isNaN(timestamp.getTime())) return;
        
        let direcao_graus = -1;
        if (item.direcao.graus !== undefined) {
             direcao_graus = item.direcao.graus;
        } else if (item.direcao.cardinal) {
             direcao_graus = cardinalToDegrees(item.direcao.cardinal);
        }

        if (direcao_graus < 0) return;

        normalized.push({
            timestamp,
            sustentado_kmh: convertToKmh(item.sustentado.valor, item.sustentado.unidade),
            rajada_kmh: convertToKmh(item.rajada.valor, item.rajada.unidade),
            direcao_graus: direcao_graus,
            fonte: item.fonte,
        });
    });
    return normalized;
}

function fuseDataByHour(normalizedData: NormalizedHourlyData[]): FusedHourlyData[] {
    const dataByHour: { [key: string]: NormalizedHourlyData[] } = {};
    normalizedData.forEach(item => {
        const hourKey = new Date(item.timestamp);
        hourKey.setMinutes(0, 0, 0);
        const keyString = hourKey.toISOString();
        if (!dataByHour[keyString]) {
            dataByHour[keyString] = [];
        }
        dataByHour[keyString].push(item);
    });

    const fused: FusedHourlyData[] = [];
    const sortedHours = Object.keys(dataByHour).sort();

    for (const hourKey of sortedHours) {
        const hourlyEntries = dataByHour[hourKey];
        if (hourlyEntries.length === 0) continue;

        let totalSustentado = 0, totalRajada = 0, totalWeight = 0;
        // For direction, we use vector averaging
        let sumSin = 0, sumCos = 0;

        for (const entry of hourlyEntries) {
            const sourceInfo = SOURCES_CONFIG.find(s => s.id === entry.fonte);
            if (!sourceInfo) continue;
            
            const weight = FUSION_WEIGHTS[sourceInfo.weightKey];
            totalSustentado += entry.sustentado_kmh * weight;
            totalRajada += entry.rajada_kmh * weight;
            
            const angleRad = entry.direcao_graus * (Math.PI / 180);
            sumSin += Math.sin(angleRad) * weight;
            sumCos += Math.cos(angleRad) * weight;

            totalWeight += weight;
        }

        if (totalWeight > 0) {
            const avgSustentado = totalSustentado / totalWeight;
            const avgRajada = totalRajada / totalWeight;
            
            const avgAngleRad = Math.atan2(sumSin, sumCos);
            let avgDegrees = avgAngleRad * (180 / Math.PI);
            if (avgDegrees < 0) avgDegrees += 360;

            const minSustentado = Math.min(...hourlyEntries.map(e => e.sustentado_kmh));
            const maxSustentado = Math.max(...hourlyEntries.map(e => e.sustentado_kmh));
            const divergence = maxSustentado - minSustentado > DIVERGENCE_THRESHOLD_KMH;

            fused.push({
                hora: getFormattedDateTime(new Date(hourKey), 'hourly'),
                vento_sustentado_kmh: Math.round(avgSustentado),
                rajada_kmh: Math.round(avgRajada),
                direcao_graus: Math.round(avgDegrees),
                direcao_cardinal_leigo: degreesToCardinalLeigo(avgDegrees),
                flags: divergence ? ['ALTA_DIVERGÊNCIA'] : [],
            });
        }
    }
    return fused.filter(item => new Date(item.hora) >= new Date());
}

// --- Main Exported Function ---

export async function getWindForecast(): Promise<ForecastOutput> {
    const { data: rawData, statuses: fontes_utilizadas } = await fetchDataSources();
    const normalizedData = normalizeAllData(rawData);
    const fusedData = fuseDataByHour(normalizedData);
    
    const now = new Date();
    const future24h = new Date(now.getTime() + 24 * 3600 * 1000);
    
    const dataFor24h = fusedData
        .filter(d => new Date(d.hora) <= future24h);

    const dataFor24hAvg = dataFor24h.map(d => d.vento_sustentado_kmh);
        
    let media_24h_kmh: number | 'NA' = 'NA';
    let status: 'OK' | 'DADOS_INSUFICIENTES' = 'DADOS_INSUFICIENTES';

    if (dataFor24hAvg.length >= MIN_VALID_POINTS_FOR_AVERAGE) {
        const sum = dataFor24hAvg.reduce((acc, val) => acc + val, 0);
        media_24h_kmh = Math.round(sum / dataFor24hAvg.length);
        status = 'OK';
    }
    
    let pico_vento: Highlight | null = null;
    let calmaria: Highlight | null = null;
    
    if (dataFor24h.length > 0) {
        // Fix: With stricter types, filtering for 'number' is no longer needed.
        const validWindData = dataFor24h;

        if (validWindData.length > 0) {
            const maxWindEntry = validWindData.reduce((max, current) => 
                current.vento_sustentado_kmh > max.vento_sustentado_kmh ? current : max
            );
            pico_vento = { hora: maxWindEntry.hora, vento_sustentado_kmh: maxWindEntry.vento_sustentado_kmh };

            const minWindEntry = validWindData.reduce((min, current) => 
                current.vento_sustentado_kmh < min.vento_sustentado_kmh ? current : min
            );
            
            if (minWindEntry.vento_sustentado_kmh < 5) { // Threshold for calm conditions
                calmaria = { hora: minWindEntry.hora, vento_sustentado_kmh: minWindEntry.vento_sustentado_kmh };
            }
        }
    }

    const panel: PanelData = {
        media_24h_kmh,
        status,
        observacoes: status === 'DADOS_INSUFICIENTES' ? 'Pontos de dados insuficientes para uma média confiável.' : '',
    };

    const highlights: HighlightsData = {
        pico_vento,
        calmaria,
    };

    return {
        header: {
            titulo: 'Vento em Osório',
            atualizado_em: getFormattedDateTime(now, 'full'),
            timezone: TIMEZONE,
        },
        painel: panel,
        highlights,
        tabela_completa: fusedData,
        fontes_utilizadas,
    };
}