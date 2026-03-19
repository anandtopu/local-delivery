import { FormEvent, useState } from "react";
import StatusBadge from "../components/ui/StatusBadge";
import {
  AvailabilityResponse,
  checkAvailability,
} from "../services/availabilityService";
import { formatDistance, formatTravelTime } from "../utils/formatters";

const DEFAULT_ITEMS = "1,2,3";

export default function AvailabilityPage() {
  const [lat, setLat] = useState("34.0522");
  const [lng, setLng] = useState("-118.2437");
  const [itemIds, setItemIds] = useState(DEFAULT_ITEMS);
  const [radiusKm, setRadiusKm] = useState("15");
  const [result, setResult] = useState<AvailabilityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const ids = itemIds
        .split(",")
        .map((s) => parseInt(s.trim(), 10))
        .filter((n) => !isNaN(n));
      const res = await checkAvailability(
        parseFloat(lat),
        parseFloat(lng),
        ids,
        parseFloat(radiusKm)
      );
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Availability Check</h1>
        <p className="text-sm text-slate-500 mt-1">
          Find items in stock at DCs within radius — Haversine + Redis cache-aside
        </p>
      </div>

      {/* Query form */}
      <div className="bg-white rounded-lg shadow-sm p-5 mb-6">
        <form onSubmit={handleSubmit} className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">
              Latitude
            </label>
            <input
              type="number"
              step="any"
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              className="w-full border border-slate-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">
              Longitude
            </label>
            <input
              type="number"
              step="any"
              value={lng}
              onChange={(e) => setLng(e.target.value)}
              className="w-full border border-slate-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">
              Item IDs (comma-separated)
            </label>
            <input
              type="text"
              value={itemIds}
              onChange={(e) => setItemIds(e.target.value)}
              placeholder="e.g. 1,2,3"
              className="w-full border border-slate-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">
              Radius (km)
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={radiusKm}
              onChange={(e) => setRadiusKm(e.target.value)}
              className="w-full border border-slate-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold rounded px-4 py-2 text-sm transition-colors"
            >
              {loading ? "Checking..." : "Check Availability"}
            </button>
          </div>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4 mb-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-4 flex-wrap">
            <h2 className="text-sm font-semibold text-slate-700">
              {result.results.length} result{result.results.length !== 1 ? "s" : ""}
            </h2>
            <StatusBadge status={result.cache_status} />
            <span className="text-xs text-slate-400 ml-auto">
              {result.response_ms} ms
            </span>
          </div>

          {result.results.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-sm">
              No items found within {radiusKm} km of this location.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>DC Name</th>
                    <th>Region</th>
                    <th>Item</th>
                    <th>Qty</th>
                    <th>Distance</th>
                    <th>Travel Time</th>
                    <th>1h Delivery</th>
                  </tr>
                </thead>
                <tbody>
                  {result.results.map((r, i) => (
                    <tr key={i}>
                      <td className="font-medium">{r.dc_name}</td>
                      <td>
                        <code className="text-xs bg-slate-100 px-1 rounded">
                          {r.region_id}
                        </code>
                      </td>
                      <td>{r.item_name}</td>
                      <td>
                        <span className="font-semibold text-green-700">
                          {r.quantity}
                        </span>
                      </td>
                      <td>{formatDistance(r.distance_km)}</td>
                      <td>{formatTravelTime(r.travel_minutes)}</td>
                      <td>
                        {r.can_deliver_in_1h ? (
                          <span className="text-green-600 font-semibold">Yes</span>
                        ) : (
                          <span className="text-slate-400">No</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
