/**
 * City configuration. UCIP's pipeline is city-agnostic; this is the single
 * place the frontend learns which city it is showing, so city-specific widgets
 * (live weather, map centre, copy) never hardcode a location.
 */

export type CityConfig = {
  name: string;
  lat: number;
  lon: number;
  timezone: string;
};

export const MUMBAI: CityConfig = {
  name: "Mumbai",
  lat: 19.076,
  lon: 72.877,
  timezone: "Asia/Kolkata",
};
