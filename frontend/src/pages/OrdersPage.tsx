import { useState } from "react";
import { Link } from "react-router-dom";
import StatusBadge from "../components/ui/StatusBadge";
import { useOrders } from "../hooks/useOrders";
import { formatDate, formatPrice } from "../utils/formatters";

const PAGE_SIZE = 20;

export default function OrdersPage() {
  const [page, setPage] = useState(0);
  const { orders, isLoading, error } = useOrders(page * PAGE_SIZE, PAGE_SIZE);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Orders</h1>
          <p className="text-sm text-slate-500 mt-1">
            Placed via SERIALIZABLE PostgreSQL transactions
          </p>
        </div>
        <Link
          to="/orders/new"
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded px-4 py-2 text-sm transition-colors"
        >
          + Place Order
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {isLoading && (
          <div className="p-8 text-center text-slate-400 text-sm">Loading orders...</div>
        )}
        {error && (
          <div className="p-4 text-sm text-red-600">
            Failed to load orders: {error.message}
          </div>
        )}
        {!isLoading && !error && (
          <>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Order ID</th>
                    <th>Customer</th>
                    <th>DC ID</th>
                    <th>Items</th>
                    <th>Total</th>
                    <th>Status</th>
                    <th>Placed At</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center text-slate-400 py-8">
                        No orders yet.{" "}
                        <Link to="/orders/new" className="text-blue-600 hover:underline">
                          Place the first one
                        </Link>
                      </td>
                    </tr>
                  ) : (
                    orders.map((order) => (
                      <tr key={order.id}>
                        <td>
                          <code className="text-xs bg-slate-100 px-1 rounded">
                            {order.id.slice(0, 8)}…
                          </code>
                        </td>
                        <td className="font-medium">{order.customer_id}</td>
                        <td>{order.dc_id}</td>
                        <td>{order.order_items.length}</td>
                        <td className="font-semibold">
                          {formatPrice(order.total_price_cents)}
                        </td>
                        <td>
                          <StatusBadge status={order.status} />
                        </td>
                        <td className="text-slate-500 text-xs">
                          {formatDate(order.placed_at)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="px-5 py-3 border-t border-slate-100 flex items-center gap-3">
              <button
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                className="px-3 py-1 text-sm border border-slate-200 rounded disabled:opacity-40 hover:bg-slate-50"
              >
                ← Prev
              </button>
              <span className="text-sm text-slate-500">Page {page + 1}</span>
              <button
                disabled={orders.length < PAGE_SIZE}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 text-sm border border-slate-200 rounded disabled:opacity-40 hover:bg-slate-50"
              >
                Next →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
