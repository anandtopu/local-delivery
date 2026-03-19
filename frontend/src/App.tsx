import { Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import AvailabilityPage from "./pages/AvailabilityPage";
import DashboardPage from "./pages/DashboardPage";
import DCsPage from "./pages/DCsPage";
import ItemsPage from "./pages/ItemsPage";
import OrdersPage from "./pages/OrdersPage";
import PlaceOrderPage from "./pages/PlaceOrderPage";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/availability" element={<AvailabilityPage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/orders/new" element={<PlaceOrderPage />} />
        <Route path="/dcs" element={<DCsPage />} />
        <Route path="/items" element={<ItemsPage />} />
      </Routes>
    </AppLayout>
  );
}
