import { ReactNode } from "react";
import Sidebar from "./Sidebar";

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="main-content flex-1">
        {children}
      </main>
    </div>
  );
}
