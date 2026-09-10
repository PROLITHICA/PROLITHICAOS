export const deployment = (window as Window & {
  PROLITHICA_CONFIG?: { pages: boolean; apiOrigin: string };
}).PROLITHICA_CONFIG ?? { pages: false, apiOrigin: '' };
