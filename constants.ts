export const TIMEZONE = 'America/Sao_Paulo';

export const CONVERSION_FACTORS = {
  knots_to_kmh: 1.852,
  ms_to_kmh: 3.6,
};

export const FUSION_WEIGHTS: { [key: string]: number } = {
  windguru: 1.0,
  windfinder: 1.0,
  windyapp: 1.2, // Higher weight for real API data
};

export const DIVERGENCE_THRESHOLD_KMH = 8;
export const MIN_VALID_POINTS_FOR_AVERAGE = 8;

export const SOURCES_CONFIG = [
  { id: 'windyapp_osorio', name: 'Windy', location: 'Osório', url: 'https://windy.app/pt/forecast2/spot/4906371/Osorio', weightKey: 'windyapp' },
  { id: 'windguru_86525', name: 'Windguru', location: 'Osório', url: 'https://www.windguru.cz/86525', weightKey: 'windguru' },
  { id: 'windguru_119156', name: 'Windguru', location: 'Lagoa dos Barros', url: 'https://www.windguru.cz/119156', weightKey: 'windguru' },
  { id: 'windfinder_osorio', name: 'Windfinder', location: 'Osório', url: 'https://pt.windfinder.com/forecast/osorio_rio_grande_do_sul_brazil', weightKey: 'windfinder' },
];

export const WINDY_API_CONFIG = {
  apiKey: 'UCOjESHJtVKjmLQYKUi9mEwvbLgaud28',
  lat: -29.90035,
  lon: -50.27377,
  model: 'gfs',
  parameters: ['wind', 'windGust'],
  levels: ['surface'],
  endpoint: 'https://api.windy.com/api/point-forecast/v2'
};
