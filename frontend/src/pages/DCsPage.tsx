import { useState } from "react";
import { useDCs } from "../hooks/useDCs";

export default function DCsPage() {
  const [regionFilter, setRegionFilter] = useState("");
  const { dcs, isLoading, error } = useDCs(regionFilter || undefined);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Distribution Centers</h1>
          <p className="text-sm text-slate-500 mt-1">
            region_id = zipcode[:3] — enables future table partitioning
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-500">Filter by region:</label>
          <input
            type="text"
            maxLength={3}
            value={regionFilter}
            onChange={(e) => setRegionFilter(e.target.value.toUpperCase())}
            placeholder="e.g. 900"
            className="border border-slate-200 rounded px-3 py-1.5 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          {regionFilter && (
            <button
              onClick={() => setRegionFilter("")}
              className="text-slate-400 hover:text-slate-600 text-sm"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {isLoading && (
          <div className="p-8 text-center text-slate-400 text-sm">
            Loading distribution centres...
          </div>
        )}
        {error && (
          <div className="p-4 text-sm text-red-600">Failed to load DCs: {error.message}</div>
        )}
        {!isLoading && !error && (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Region</th>
                  <th>City</th>
                  <th>State</th>
                  <th>Lat / Lng</th>
                  <th>ZIP</th>
                  <th>Stock Lines</th>
                  <th>Active</th>
                </tr>
              </thead>
              <tbody>
                {dcs.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center text-slate-400 py-8">
                      No distribution centres found.
                    </td>
                  </tr>
                ) : (
                  dcs.map((dc) => (
                    <tr key={dc.id}>
                      <td className="text-slate-400">{dc.id}</td>
                      <td className="font-medium">{dc.name}</td>
                      <td>
                        <code className="text-xs bg-slate-100 px-1 rounded">
                          {dc.region_id}
                        </code>
                      </td>
                      <td>{dc.city ?? "—"}</td>
                      <td>{dc.state ?? "—"}</td>
                      <td className="text-xs text-slate-500 font-mono">
                        {dc.lat.toFixed(4)}, {dc.lng.toFixed(4)}
                      </td>
                      <td>{dc.zipcode}</td>
                      <td>
                        <span className="font-semibold text-green-700">
                          {dc.inventory_count}
                        </span>
                      </td>
                      <td>
                        {dc.is_active ? (
                          <span className="text-green-600 font-semibold text-xs">Active</span>
                        ) : (
                          <span className="text-red-500 text-xs">Inactive</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
