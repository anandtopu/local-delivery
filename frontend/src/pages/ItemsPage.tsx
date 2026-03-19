import { useState } from "react";
import useSWR from "swr";
import { ItemResponse, listItems } from "../services/itemsService";
import { formatPrice } from "../utils/formatters";

const CATEGORIES = ["", "snacks", "beverages", "household", "personal_care", "frozen"];

export default function ItemsPage() {
  const [category, setCategory] = useState("");

  const { data: items = [], isLoading, error } = useSWR<ItemResponse[]>(
    ["items", category],
    () => listItems(category || undefined)
  );

  return (
    <div>
      <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Items</h1>
          <p className="text-sm text-slate-500 mt-1">
            Product catalogue — 100 items across 5 categories
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-500">Category:</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="border border-slate-200 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c === "" ? "All categories" : c.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {isLoading && (
          <div className="p-8 text-center text-slate-400 text-sm">Loading items...</div>
        )}
        {error && (
          <div className="p-4 text-sm text-red-600">
            Failed to load items: {error.message}
          </div>
        )}
        {!isLoading && !error && (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>SKU</th>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Price</th>
                  <th>Weight</th>
                  <th>Active</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center text-slate-400 py-8">
                      No items found.
                    </td>
                  </tr>
                ) : (
                  items.map((item) => (
                    <tr key={item.id}>
                      <td className="text-slate-400">{item.id}</td>
                      <td>
                        <code className="text-xs bg-slate-100 px-1 rounded">
                          {item.sku}
                        </code>
                      </td>
                      <td className="font-medium">{item.name}</td>
                      <td>
                        <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full capitalize">
                          {item.category.replace("_", " ")}
                        </span>
                      </td>
                      <td className="font-semibold">
                        {formatPrice(item.unit_price_cents)}
                      </td>
                      <td className="text-slate-500 text-sm">
                        {item.weight_grams ? `${item.weight_grams}g` : "—"}
                      </td>
                      <td>
                        {item.is_active ? (
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
