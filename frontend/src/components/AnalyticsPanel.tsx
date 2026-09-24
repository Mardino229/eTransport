import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import {
  Users,
  AlertTriangle,
  PlusCircle,
  Clock,
  GitMerge,
  MapPin,
  CheckCircle2,
  Activity,
} from "lucide-react";
import { ComponentCard } from "./common/ComponentCard";
import { MetricCard } from "./common/MetricCard";
import { Badge } from "./ui/badge/Badge";

interface StopAnalytics {
  stop_id: string;
  stop_name: string;
  total_boarded: number;
  total_alighted: number;
  current_waiting: number;
  avg_wait_time_min: number;
}

interface TopRoute {
  route_id: string;
  route_name: string;
  daily_passengers: number;
  saturation_rate: number;
}

interface OptimizationSuggestion {
  action_type: string;
  line_id: string | null;
  description: string;
  metric_value: number;
  metric_label: string;
}

interface OptimizationData {
  generated_at: string;
  suggestions: OptimizationSuggestion[];
  hotspots: { stop_id: string; stop_name: string; total_waiting_24h: number; total_boarded_24h: number }[];
  peak_hours: Record<string, { start: string; end: string; multiplier: number; direction: string }>;
}

interface Props {
  apiBase: string;
}

const ACTION_ICONS: Record<string, React.ReactNode> = {
  add_bus: <PlusCircle className="size-5 text-emerald-500" />,
  reschedule: <Clock className="size-5 text-amber-500" />,
  merge_lines: <GitMerge className="size-5 text-purple-500" />,
  new_stop: <MapPin className="size-5 text-cyan-500" />,
};

export default function AnalyticsPanel({ apiBase }: Props) {
  const [top5, setTop5] = useState<TopRoute[]>([]);
  const [stopData, setStopData] = useState<StopAnalytics[]>([]);
  const [networkStops, setNetworkStops] = useState<{ id: string; name: string }[]>([]);
  const [optimizations, setOptimizations] = useState<OptimizationData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        // Fetch network stops dynamically first
        const stopsRes = await fetch(`${apiBase}/network/stops`);
        const stopsData = stopsRes.ok ? await stopsRes.json() : [];
        const stops = Array.isArray(stopsData) ? stopsData : [];
        setNetworkStops(stops);

        const stopIds = stops.map((s) => s.id);

        const [top5Res, optRes, ...stopAnalyticsRes] = await Promise.all([
          fetch(`${apiBase}/routes/top5`).then((r) => (r.ok ? r.json() : [])),
          fetch(`${apiBase}/optimizations/suggestions`).then((r) => (r.ok ? r.json() : null)),
          ...stopIds.map((id) =>
            fetch(`${apiBase}/stops/${id}/analytics`).then((r) => (r.ok ? r.json() : null))
          ),
        ]);
        setTop5(top5Res);
        setOptimizations(optRes);
        setStopData(stopAnalyticsRes.filter(Boolean));
      } catch (e) {
        console.error("Error loading analytics:", e);
      } finally {
        setLoading(false);
      }
    };

    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [apiBase]);

  if (loading && !top5.length) {
    return (
      <div className="flex items-center justify-center h-80 rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <div className="flex items-center gap-3 text-gray-500 dark:text-gray-400">
          <Activity className="size-6 text-brand-500 animate-spin" />
          <span className="font-semibold text-sm">Chargement des données analytics...</span>
        </div>
      </div>
    );
  }

  const chartColors = ["#465fff", "#06b6d4", "#12b76a", "#f79009", "#7a5af8"];

  const totalPassengers = top5.reduce((sum, r) => sum + r.daily_passengers, 0);

  return (
    <div className="space-y-6">
      {/* Top Summary Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        <MetricCard
          icon={<Users className="size-6" />}
          label="Passagers 24h (Top 5)"
          value={totalPassengers.toLocaleString("fr-FR")}
          subtext="Volume total quotidien"
          badge={{ text: "Direct", variant: "brand" }}
        />
        <MetricCard
          icon={<AlertTriangle className="size-6" />}
          label="Suggestions"
          value={optimizations?.suggestions?.length || 0}
          subtext="Actions de rééquilibrage"
          badge={{ text: "Optimisation", variant: "brand" }}
        />
      </div>

      {/* Top 5 Itinéraires */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <ComponentCard
            title="Top 5 Itinéraires les plus fréquentés"
            desc="Volume de passagers quotidien par ligne de bus universitaire"
          >
            {top5.length === 0 ? (
              <div className="flex items-center justify-center p-12 text-gray-400">
                Pas encore de données enregistrées (le simulateur doit être en marche).
              </div>
            ) : (
              <div className="h-72 w-full pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={top5} layout="vertical" margin={{ left: 10, right: 20 }}>
                    <XAxis type="number" tick={{ fill: "#98a2b3", fontSize: 12 }} />
                    <YAxis
                      type="category"
                      dataKey="route_name"
                      tick={{ fill: "#667085", fontSize: 12 }}
                      width={120}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#101828",
                        borderColor: "#1d2939",
                        borderRadius: "12px",
                        color: "#fff",
                        boxShadow: "0 10px 25px -5px rgba(0,0,0,0.3)",
                      }}
                      itemStyle={{ color: "#9cb9ff" }}
                      formatter={(v: number) => [`${v} passagers`, "Volume"]}
                    />
                    <Bar dataKey="daily_passengers" radius={[0, 6, 6, 0]}>
                      {top5.map((_, i) => (
                        <Cell key={i} fill={chartColors[i % chartColors.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </ComponentCard>
        </div>

        <div className="lg:col-span-5 flex flex-col justify-between space-y-3">
          {top5.map((route, i) => (
            <div
              key={route.route_id}
              className="p-4 rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900 shadow-xs flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div
                  className="flex items-center justify-center size-8 rounded-xl font-bold text-sm text-white"
                  style={{ backgroundColor: chartColors[i % chartColors.length] }}
                >
                  #{i + 1}
                </div>
                <div>
                  <h4 className="font-bold text-sm text-gray-900 dark:text-white">
                    {route.route_name}
                  </h4>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {route.daily_passengers.toLocaleString("fr-FR")} passagers / jour
                  </p>
                </div>
              </div>
              <Badge
                variant={
                  route.saturation_rate > 85
                    ? "error"
                    : route.saturation_rate > 65
                    ? "warning"
                    : "success"
                }
              >
                Saturation {route.saturation_rate}%
              </Badge>
            </div>
          ))}
        </div>
      </div>

      {/* Analyse des Arrêts */}
      <ComponentCard
        title="Analyse des Arrêts Principaux (Dernières 24h)"
        desc="Suivi des flux de personnes montées, descendues et du temps moyen d'attente à quai"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {networkStops.map((stop) => {
            const data = stopData.find((s) => s.stop_id === stop.id);
            return (
              <div
                key={stop.id}
                className="p-4 rounded-xl border border-gray-200 bg-gray-50/50 dark:border-gray-800 dark:bg-gray-800/40 space-y-3"
              >
                <div className="flex items-center gap-2">
                  <MapPin className="size-4 text-brand-500" />
                  <span className="font-bold text-xs text-gray-900 dark:text-white truncate">
                    {data?.stop_name || stop.name || stop.id}
                  </span>
                </div>

                {data ? (
                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Montées:</span>
                      <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                        {data.total_boarded}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Descentes:</span>
                      <span className="font-semibold text-brand-600 dark:text-brand-400">
                        {data.total_alighted}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">En attente:</span>
                      <span className="font-semibold text-amber-600 dark:text-amber-400">
                        {data.current_waiting}
                      </span>
                    </div>
                    <div className="flex justify-between pt-1 border-t border-gray-200 dark:border-gray-700">
                      <span className="text-gray-500">Attente moy.:</span>
                      <span className="font-bold text-gray-800 dark:text-gray-200">
                        {data.avg_wait_time_min} min
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-gray-400">Chargement des données...</div>
                )}
              </div>
            );
          })}
        </div>
      </ComponentCard>

      {/* Recommandations d'Optimisation */}
      <ComponentCard
        title="Recommandations d'Optimisation du Réseau "
        desc="Actions correctives automatiques calculées à partir des points de congestion et des heures de pointe"
      >
        {!optimizations?.suggestions?.length ? (
          <div className="flex items-center justify-center p-8 text-gray-400 text-sm">
            <CheckCircle2 className="size-5 text-emerald-500 mr-2" />
            Aucune réallocation requise. Le réseau est équilibré.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {optimizations.suggestions.map((s, i) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-800/40 flex items-start gap-4"
              >
                <div className="p-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 flex-shrink-0">
                  {ACTION_ICONS[s.action_type] || <AlertTriangle className="size-5 text-amber-500" />}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <Badge variant="warning" size="sm">
                      {s.action_type}
                    </Badge>
                  </div>
                  <p className="text-sm font-semibold text-gray-900 dark:text-white leading-snug">
                    {s.description}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    📊 {s.metric_label}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </ComponentCard>
    </div>
  );
}
