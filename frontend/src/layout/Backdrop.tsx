import React from "react";
import { useSidebar } from "../context/SidebarContext";

export const Backdrop: React.FC = () => {
  const { isMobileOpen, toggleMobileSidebar } = useSidebar();

  if (!isMobileOpen) return null;

  return (
    <div
      className="fixed inset-0 z-40 bg-gray-900/50 backdrop-blur-xs lg:hidden"
      onClick={toggleMobileSidebar}
    />
  );
};
