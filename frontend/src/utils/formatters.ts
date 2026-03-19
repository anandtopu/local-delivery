/**
 * Format a price in cents to a currency string.
 * e.g. 299 → "$2.99"
 */
export function formatPrice(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

/**
 * Format a distance in kilometres.
 * e.g. 1.23 → "1.23 km"
 */
export function formatDistance(km: number): string {
  return `${km.toFixed(1)} km`;
}

/**
 * Format travel time in minutes.
 * e.g. 7.5 → "7 min"   |  90 → "1h 30min"
 */
export function formatTravelTime(minutes: number): string {
  if (minutes < 60) {
    return `${Math.round(minutes)} min`;
  }
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return m > 0 ? `${h}h ${m}min` : `${h}h`;
}

/**
 * Format an ISO date string to a human-readable format.
 */
export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

/**
 * Map order status codes to display labels.
 */
export function formatOrderStatus(status: string): string {
  const map: Record<string, string> = {
    CONFIRMED: "Confirmed",
    IN_TRANSIT: "In Transit",
    DELIVERED: "Delivered",
    CANCELLED: "Cancelled",
  };
  return map[status] ?? status;
}
