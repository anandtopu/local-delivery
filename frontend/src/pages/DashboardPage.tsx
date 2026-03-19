import { useEffect, useState } from "react";
import MetricCard from "../components/ui/MetricCard";
import { useStats } from "../hooks/useStats";
import api from "../services/api";

interface HealthResponse {
  status: string;
  postgres: string;
  redis: string;
}

function ServiceIndicator({ name, status }: { name: string; status: string }) {
  const ok = status === "ok";
  return (
    <div className="flex items-center gap-2 py-2">
      <span
        className={`h-2.5 w-2.5 rounded-full ${ok ? "bg-green-500" : "bg-red-500"}`}
      />
      <span className="text-sm text-slate-700">{name}</span>
      <span
        className={`ml-auto text-xs font-semibold uppercase ${
          ok ? "text-green-600" : "text-red-600"
        }`}
      >
        {ok ? "Healthy" : "Error"}
      </span>
    </div>
  );
}

export default function DashboardPage() {
  const { stats, isLoading: statsLoading } = useStats();
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    api
      .get<HealthResponse>("/health")
      .then((r) => setHealth(r.data))
      .catch(() => setHealth({ status: "error", postgres: "error", redis: "error" }));
  }, []);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          GoPuff-inspired local delivery — system design practice application
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
        <MetricCard
          title="Distribution Centers"
          value={statsLoading ? "—" : stats?.total_dcs ?? 0}
          icon="🏭"
          color="blue"
          subtitle="Active DCs"
        />
        <MetricCard
          title="Catalogue Items"
          value={statsLoading ? "—" : stats?.total_items ?? 0}
          icon="🛒"
          color="purple"
          subtitle="Active items"
        />
        <MetricCard
          title="Total Orders"
          value={statsLoading ? "—" : stats?.total_orders ?? 0}
          icon="📦"
          color="green"
          subtitle="All time"
        />
        <MetricCard
          title="Orders Today"
          value={statsLoading ? "—" : stats?.orders_today ?? 0}
          icon="📅"
          color="orange"
          subtitle="Since midnight UTC"
        />
        <MetricCard
          title="Active Regions"
          value={statsLoading ? "—" : stats?.active_regions ?? 0}
          icon="📍"
          color="blue"
          subtitle="ZIP prefix regions"
        />
      </div>

      {/* System Health */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">
            System Health
          </h2>
          <div className="divide-y divide-slate-100">
            <ServiceIndicator name="PostgreSQL" status={health?.postgres ?? "loading"} />
            <ServiceIndicator name="Redis" status={health?.redis ?? "loading"} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-3">
            Key Design Patterns
          </h2>
          <ul className="space-y-2 text-sm text-slate-600">
            <li className="flex items-start gap-2">
              <span className="text-blue-500 font-bold mt-0.5">●</span>
              <span>
                <strong>Haversine + Bounding Box</strong> — two-pass DC geo-filter
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-500 font-bold mt-0.5">●</span>
              <span>
                <strong>Redis Cache-aside</strong> — availability TTL 60s, invalidated on order
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-500 font-bold mt-0.5">●</span>
              <span>
                <strong>SERIALIZABLE Transaction</strong> — SELECT FOR UPDATE prevents overselling
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-orange-500 font-bold mt-0.5">●</span>
              <span>
                <strong>Read/Write Split</strong> — separate DB pools for reads vs writes
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-slate-500 font-bold mt-0.5">●</span>
              <span>
                <strong>Region Partitioning</strong> — <code className="bg-slate-100 px-1 rounded">region_id = zipcode[:3]</code>
              </span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
