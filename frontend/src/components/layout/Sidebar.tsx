import { NavLink } from "react-router-dom";

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard", icon: "📊" },
  { to: "/availability", label: "Availability", icon: "📍" },
  { to: "/orders", label: "Orders", icon: "📦" },
  { to: "/orders/new", label: "Place Order", icon: "➕" },
  { to: "/dcs", label: "Distribution Centers", icon: "🏭" },
  { to: "/items", label: "Items", icon: "🛒" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="px-4 py-5 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🚀</span>
          <div>
            <p className="text-white font-bold text-sm leading-tight">Local Delivery</p>
            <p className="text-slate-400 text-xs">System Design Demo</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `sidebar-nav-item${isActive ? " active" : ""}`
            }
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-slate-700">
        <p className="text-slate-500 text-xs">
          Haversine + SERIALIZABLE + Cache-aside
        </p>
      </div>
    </aside>
  );
}
