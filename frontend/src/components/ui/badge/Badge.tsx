import React from "react";

interface BadgeProps {
  variant?: "success" | "warning" | "error" | "brand" | "info" | "neutral";
  size?: "sm" | "md";
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "brand",
  size = "md",
  children,
  className = "",
}) => {
  const variantStyles = {
    success: "bg-success-50 text-success-700 dark:bg-success-500/15 dark:text-success-400 border-success-200 dark:border-success-500/30",
    warning: "bg-warning-50 text-warning-700 dark:bg-warning-500/15 dark:text-warning-400 border-warning-200 dark:border-warning-500/30",
    error: "bg-error-50 text-error-700 dark:bg-error-500/15 dark:text-error-400 border-error-200 dark:border-error-500/30",
    brand: "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-400 border-brand-200 dark:border-brand-500/30",
    info: "bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400 border-blue-200 dark:border-blue-500/30",
    neutral: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-xs font-medium",
    md: "px-2.5 py-1 text-xs font-semibold",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};
