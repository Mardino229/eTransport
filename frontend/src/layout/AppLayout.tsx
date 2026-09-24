import React from "react";
import { SidebarProvider, useSidebar } from "../context/SidebarContext";
import { ThemeProvider } from "../context/ThemeContext";
import { AppSidebar } from "./AppSidebar";
import { AppHeader } from "./AppHeader";
import { Backdrop } from "./Backdrop";

interface AppLayoutProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  wsConnected: boolean;
  lastUpdate: string;
  children: React.ReactNode;
}

const LayoutContent: React.FC<AppLayoutProps> = ({
  activeTab,
  setActiveTab,
  wsConnected,
  lastUpdate,
  children,
}) => {
  const { isExpanded, isHovered } = useSidebar();

  const marginClass = isExpanded || isHovered ? "lg:ml-64" : "lg:ml-20";

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors duration-200">
      <AppSidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />
      <Backdrop />

      <div className={`flex flex-col flex-1 transition-all duration-300 ease-in-out ${marginClass}`}>
        <AppHeader
          wsConnected={wsConnected}
          lastUpdate={lastUpdate}
          activeTab={activeTab}
        />

        <main className="flex-1 p-4 md:p-6 space-y-6 max-w-[1600px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

export const AppLayout: React.FC<AppLayoutProps> = (props) => {
  return (
    <ThemeProvider>
      <SidebarProvider>
        <LayoutContent {...props} />
      </SidebarProvider>
    </ThemeProvider>
  );
};
