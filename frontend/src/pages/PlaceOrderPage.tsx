import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useDCs } from "../hooks/useDCs";
import useSWR from "swr";
import { listItems, ItemResponse } from "../services/itemsService";
import { placeOrder, OrderResponse } from "../services/ordersService";
import { formatPrice } from "../utils/formatters";

interface CartLine {
  item_id: number;
  quantity: number;
}

export default function PlaceOrderPage() {
  const { dcs } = useDCs();
  const { data: items = [] } = useSWR<ItemResponse[]>("all-items", () => listItems());

  const [customerId, setCustomerId] = useState("");
  const [dcId, setDcId] = useState<number | "">("");
  const [cart, setCart] = useState<CartLine[]>([{ item_id: 0, quantity: 1 }]);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<OrderResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  function addLine() {
    setCart((c) => [...c, { item_id: 0, quantity: 1 }]);
  }

  function removeLine(i: number) {
    setCart((c) => c.filter((_, idx) => idx !== i));
  }

  function updateLine(i: number, field: "item_id" | "quantity", value: number) {
    setCart((c) => c.map((line, idx) => (idx === i ? { ...line, [field]: value } : line)));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!dcId) return;

    const validLines = cart.filter((l) => l.item_id > 0 && l.quantity > 0);
    if (validLines.length === 0) {
      setError("Add at least one item.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const order = await placeOrder({
        customer_id: customerId,
        dc_id: Number(dcId),
        items: validLines,
      });
      setSuccess(order);
      setCart([{ item_id: 0, quantity: 1 }]);
      setCustomerId("");
      setDcId("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Order failed");
    } finally {
      setSubmitting(false);
    }
  }

  const totalCents = cart.reduce((sum, line) => {
    const item = items.find((i) => i.id === line.item_id);
    return sum + (item ? item.unit_price_cents * line.quantity : 0);
  }, 0);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Place Order</h1>
        <p className="text-sm text-slate-500 mt-1">
          SERIALIZABLE transaction — SELECT FOR UPDATE → check → decrement
        </p>
      </div>

      {success && (
        <div className="bg-green-50 border border-green-200 rounded p-4 mb-6">
          <p className="text-green-800 font-semibold text-sm">
            Order placed successfully!
          </p>
          <p className="text-green-700 text-xs mt-1">
            Order ID:{" "}
            <code className="bg-green-100 px-1 rounded">{success.id}</code> —{" "}
            Total: {formatPrice(success.total_price_cents)}
          </p>
          <Link
            to="/orders"
            className="text-green-700 underline text-xs mt-2 inline-block"
          >
            View all orders →
          </Link>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4 mb-6 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm p-6">
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Customer ID */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">
                Customer ID *
              </label>
              <input
                type="text"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                placeholder="e.g. cust-abc123"
                required
                className="w-full border border-slate-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">
                Distribution Centre *
              </label>
              <select
                value={dcId}
                onChange={(e) => setDcId(e.target.value === "" ? "" : Number(e.target.value))}
                required
                className="w-full border border-slate-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              >
                <option value="">Select a DC...</option>
                {dcs.map((dc) => (
                  <option key={dc.id} value={dc.id}>
                    [{dc.region_id}] {dc.name} — {dc.city}, {dc.state}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-500">Items *</label>
              <button
                type="button"
                onClick={addLine}
                className="text-blue-600 text-xs hover:underline"
              >
                + Add item
              </button>
            </div>
            <div className="space-y-2">
              {cart.map((line, i) => {
                const item = items.find((it) => it.id === line.item_id);
                return (
                  <div key={i} className="flex items-center gap-3">
                    <select
                      value={line.item_id || ""}
                      onChange={(e) =>
                        updateLine(i, "item_id", Number(e.target.value))
                      }
                      className="flex-1 border border-slate-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                    >
                      <option value="">Select item...</option>
                      {items.map((it) => (
                        <option key={it.id} value={it.id}>
                          {it.name} — {formatPrice(it.unit_price_cents)}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min={1}
                      value={line.quantity}
                      onChange={(e) =>
                        updateLine(i, "quantity", Number(e.target.value))
                      }
                      className="w-20 border border-slate-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                    />
                    {item && (
                      <span className="text-sm text-slate-500 w-20 text-right">
                        {formatPrice(item.unit_price_cents * line.quantity)}
                      </span>
                    )}
                    {cart.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeLine(i)}
                        className="text-red-400 hover:text-red-600 text-lg leading-none"
                      >
                        ×
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Total + Submit */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-100">
            <div className="text-sm text-slate-600">
              Estimated total:{" "}
              <span className="font-bold text-slate-800">
                {formatPrice(totalCents)}
              </span>
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold rounded px-6 py-2 text-sm transition-colors"
            >
              {submitting ? "Placing Order..." : "Place Order"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
