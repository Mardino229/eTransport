import React from "react";
import { Menu, Sun, Moon, Wifi, WifiOff } from "lucide-react";
import { useSidebar } from "../context/SidebarContext";
import { useTheme } from "../context/ThemeContext";

interface AppHeaderProps {
  wsConnected: boolean;
  lastUpdate: string;
  activeTab: string;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  wsConnected,
  lastUpdate,
  activeTab,
}) => {
  const { toggleMobileSidebar, toggleSidebar } = useSidebar();
  const { theme, toggleTheme } = useTheme();

  const tabTitles: Record<string, string> = {
    map: "Carte des Bus en Temps Réel",
    analytics: "Analytics & Flux de Passagers",
    reco: "Algorithme de Recommandation Étudiant",
  };

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between h-16 px-4 md:px-6 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 transition-colors">
      {/* Left side: Hamburger & Page Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => {
            if (window.innerWidth < 1024) {
              toggleMobileSidebar();
            } else {
              toggleSidebar();
            }
          }}
          className="flex items-center justify-center size-10 text-gray-500 rounded-xl hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors"
          aria-label="Toggle Menu"
        >
          <Menu className="size-5" />
        </button>

        <div>
          <h2 className="text-base font-bold text-gray-900 dark:text-white">
            {tabTitles[activeTab] || "Tableau de Bord"}
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 hidden sm:block">
            Réseau de transport universitaire Bénin • Cotonou & Abomey-Calavi
          </p>
        </div>
      </div>

      {/* Right side: Search, Live Status, Theme Toggle, Profile */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Connection Status Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800 text-xs font-medium">
          {wsConnected ? (
            <>
              <Wifi className="size-4 text-emerald-500" />
              <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                WebSocket Live
              </span>
            </>
          ) : (
            <>
              <WifiOff className="size-4 text-amber-500" />
              <span className="text-amber-600 dark:text-amber-400 font-semibold">
                Polling (5s)
              </span>
            </>
          )}
          <span className="text-gray-400 dark:text-gray-500 text-[10px] hidden md:inline">
            • MàJ {lastUpdate}
          </span>
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="flex items-center justify-center size-10 rounded-xl border border-gray-200 dark:border-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          title={`Basculer en mode ${theme === "light" ? "sombre" : "clair"}`}
        >
          {theme === "light" ? <Moon className="size-5" /> : <Sun className="size-5" />}
        </button>

        {/* Profile Avatar */}
        <div className="flex items-center gap-3 pl-2 border-l border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-center size-9 rounded-full bg-brand-500 text-white font-bold text-xs shadow-xs">
            MTD
          </div>
        </div>
      </div>
    </header>
  );
};
