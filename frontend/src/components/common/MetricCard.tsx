import React from "react";

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  subtext?: string;
  badge?: {
    text: string;
    variant: "success" | "warning" | "error" | "brand" | "info";
  };
}

export const MetricCard: React.FC<MetricCardProps> = ({
  icon,
  label,
  value,
  subtext,
  badge,
}) => {
  const badgeStyles = {
    success: "bg-success-50 text-success-700 dark:bg-success-500/15 dark:text-success-400",
    warning: "bg-warning-50 text-warning-700 dark:bg-warning-500/15 dark:text-warning-400",
    error: "bg-error-50 text-error-700 dark:bg-error-500/15 dark:text-error-400",
    brand: "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-400",
    info: "bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400",
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900 shadow-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center justify-center size-12 rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
          {icon}
        </div>
        {badge && (
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${badgeStyles[badge.variant]}`}
          >
            {badge.text}
          </span>
        )}
      </div>
      <div className="mt-4">
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
          {label}
        </span>
        <h4 className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">
          {value}
        </h4>
        {subtext && (
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {subtext}
          </p>
        )}
      </div>
    </div>
  );
};
