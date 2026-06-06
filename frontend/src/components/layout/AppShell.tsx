"use client";
import { Sidebar } from "./Sidebar";
import { Bell, Search } from "lucide-react";
import { useAlerts } from "@/hooks/useAlerts";

interface Props { children: React.ReactNode; title?: string }

export function AppShell({ children, title }: Props) {
  const { data: alerts } = useAlerts();
  const unresolved = alerts?.length ?? 0;

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-14 items-center justify-between border-b bg-white px-6 dark:bg-gray-900">
          <h1 className="text-lg font-semibold">{title}</h1>
          <div className="flex items-center gap-3">
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input placeholder="Search..." className="h-9 w-64 rounded-lg border bg-gray-50 pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <button className="relative rounded-lg p-2 hover:bg-gray-100">
              <Bell className="h-5 w-5" />
              {unresolved > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
                  {unresolved > 9 ? "9+" : unresolved}
                </span>
              )}
            </button>
          </div>
        </header>
        {/* Page */}
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
