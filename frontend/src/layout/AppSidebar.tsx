import React from "react";
import { Bus, BarChart2, Navigation, ChevronLeft, ChevronRight } from "lucide-react";
import { useSidebar } from "../context/SidebarContext";

interface AppSidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
} 

export const AppSidebar: React.FC<AppSidebarProps> = ({
  activeTab,
  setActiveTab,
}) => {
  const { isExpanded, isMobileOpen, isHovered, setIsHovered, toggleSidebar } = useSidebar();

  const navItems = [
    {
      id: "map",
      name: "Carte en Direct",
      icon: <Bus className="size-5" />,
    },
    {
      id: "analytics",
      name: "Analytics & Flux",
      icon: <BarChart2 className="size-5" />,
    },
    {
      id: "reco",
      name: "Recommandation",
      icon: <Navigation className="size-5" />,
    },
  ];

  const showText = isExpanded || isHovered || isMobileOpen;

  return (
    <aside
      className={`fixed top-0 left-0 z-50 flex flex-col h-screen bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-300 ease-in-out ${
        showText ? "w-64" : "w-20"
      } ${isMobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      onMouseEnter={() => !isExpanded && setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center size-10 rounded-xl">
            <Bus className="size-6" />
          </div>
          {showText && (
            <div>
              <h1 className="text-base font-bold text-gray-900 dark:text-white leading-tight">
                eTransport
              </h1>
            </div>
          )}
        </div>

        {/* Collapse Button for Desktop */}
        <button
          onClick={toggleSidebar}
          className="hidden lg:flex items-center justify-center size-8 text-gray-500 rounded-lg hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors"
          title="Toggle Sidebar"
        >
          {isExpanded ? <ChevronLeft className="size-5" /> : <ChevronRight className="size-5" />}
        </button>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 custom-scrollbar">
        {showText && (
          <h2 className="mb-3 px-3 text-[11px] font-bold tracking-wider uppercase text-gray-400 dark:text-gray-500">
            Supervision Flotte
          </h2>
        )}
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`menu-item group ${
                  isActive ? "menu-item-active" : "menu-item-inactive"
                } ${!showText ? "justify-center" : "justify-between"}`}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`${
                      isActive
                        ? "text-brand-600 dark:text-brand-400"
                        : "text-gray-500 group-hover:text-gray-700 dark:text-gray-400 dark:group-hover:text-gray-200"
                    }`}
                  >
                    {item.icon}
                  </span>
                  {showText && <span>{item.name}</span>}
                </div>
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
};
