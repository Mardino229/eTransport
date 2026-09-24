import { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Bus, Users, Search, Gauge, ArrowRight, Loader2, AlertCircle, RefreshCw } from "lucide-react";
import type { BusData } from "../App";
import { ComponentCard } from "./common/ComponentCard";
import { Badge } from "./ui/badge/Badge";
import { fetchOSRMRoute } from "../services/osrmService";

// Fix Leaflet default icon issue with Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

interface MapViewProps {
  apiBase?: string;
  buses: BusData[];
}

export interface Stop {
  id: string;
  name: string;
  lat: number;
  lng: number;
  shortName?: string;
  label?: string;
}

export interface RouteInfo {
  name: string;
  color: string;
  positions?: [number, number][];
  waypoints?: [number, number][];
}

function getBusColor(occupancy: number) {
  if (occupancy < 70) return "#12b76a"; // success green
  if (occupancy < 90) return "#f79009"; // warning orange
  return "#f04438"; // error red
}

function createBusIcon(occupancy: number) {
  const color = getBusColor(occupancy);
  return L.divIcon({
    className: "",
    html: `<div style="
      width:34px; height:34px;
      background:${color};
      border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);
      border:3px solid white;
      box-shadow:0 4px 12px rgba(0,0,0,0.3);
      display:flex; align-items:center; justify-content:center;
    ">
      <div style="transform:rotate(45deg); font-size:14px; color:white;">🚌</div>
    </div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 34],
    popupAnchor: [0, -38],
  });
}

const stopIcon = L.divIcon({
  className: "",
  html: `<div style="
    width:18px; height:18px;
    background:#465fff;
    border-radius:50%;
    border:3px solid white;
    box-shadow:0 0 10px rgba(70,95,255,0.6);
  "></div>`,
  iconSize: [18, 18],
  iconAnchor: [9, 9],
  popupAnchor: [0, -14],
});

export default function MapView({ apiBase, buses }: MapViewProps) {
  const center: [number, number] = [6.4, 2.39];
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedRoute, setSelectedRoute] = useState<string>("ALL");
  const [osrmRoutes, setOsrmRoutes] = useState<Record<string, [number, number][]>>({});
  
  const [stopsList, setStopsList] = useState<Stop[]>([]);
  const [routesData, setRoutesData] = useState<Record<string, RouteInfo>>({});
  const [loadingNetwork, setLoadingNetwork] = useState<boolean>(true);
  const [networkError, setNetworkError] = useState<string | null>(null);

  const base = apiBase || (import.meta.env.VITE_API_URL as string) || "http://localhost:8000/api/v1";

  const fetchNetworkData = async () => {
    setLoadingNetwork(true);
    setNetworkError(null);
    try {
      const [stopsRes, routesRes] = await Promise.all([
        fetch(`${base}/network/stops`),
        fetch(`${base}/network/routes`),
      ]);

      const parseJsonSafely = async (res: Response, endpointLabel: string) => {
        if (!res.ok) {
          throw new Error(`Serveur HTTP ${res.status} (${endpointLabel})`);
        }
        const contentType = res.headers.get("content-type") || "";
        if (!contentType.includes("application/json")) {
          throw new Error(`Réponse non-JSON retournée pour ${endpointLabel} (Le backend FastAPI n'est pas encore prêt)`);
        }
        return res.json();
      };

      const stopsData = await parseJsonSafely(stopsRes, "arrêts");
      const routesDataObj = await parseJsonSafely(routesRes, "lignes");

      if (!Array.isArray(stopsData) || stopsData.length === 0) {
        throw new Error("Aucun arrêt de bus valide n'a été retourné par le backend");
      }
      if (!routesDataObj || Object.keys(routesDataObj).length === 0) {
        throw new Error("Aucune ligne de bus valide n'a été retournée par le backend");
      }

      setStopsList(stopsData);
      setRoutesData(routesDataObj);
    } catch (err: any) {
      console.warn("Avertissement réseau:", err);
      const friendlyMsg = err instanceof SyntaxError
        ? "Le serveur API backend n'est pas accessible (réponse HTML non-JSON reçue)."
        : err.message || "Impossible de charger le réseau.";
      setNetworkError(friendlyMsg);
    } finally {
      setLoadingNetwork(false);
    }
  };

  useEffect(() => {
    fetchNetworkData();
  }, [base]);

  const getStopName = (stopId?: string | null) => {
    if (!stopId) return "—";
    const found = stopsList.find((s) => s.id === stopId);
    return found ? (found.name || found.label || stopId) : stopId;
  };

  useEffect(() => {
    let isMounted = true;
    async function loadOSRMGeometries() {
      if (Object.keys(routesData).length === 0) return;

      const routesToFetch =
        selectedRoute === "ALL"
          ? Object.entries(routesData)
          : Object.entries(routesData).filter(([key]) => key === selectedRoute);

      for (const [key, r] of routesToFetch) {
        if (osrmRoutes[key]) continue; // déjà en mémoire
        const waypoints = r.positions || r.waypoints;
        if (!waypoints) continue;

        const realRoadCoords = await fetchOSRMRoute(waypoints, "driving");
        if (isMounted && realRoadCoords && realRoadCoords.length > 0) {
          setOsrmRoutes((prev) => ({ ...prev, [key]: realRoadCoords }));
        }
      }
    }
    loadOSRMGeometries();
    return () => {
      isMounted = false;
    };
  }, [selectedRoute, routesData]);

  if (loadingNetwork) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] p-8 text-center bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-xs">
        <Loader2 className="size-12 text-brand-500 animate-spin mb-4" />
        <h3 className="text-lg font-bold text-gray-900 dark:text-white">
          Chargement du Réseau COUS-AC...
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Récupération dynamique des 15 arrêts et des 14 lignes depuis le serveur backend
        </p>
      </div>
    );
  }

  if (networkError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] p-8 text-center bg-red-50/50 dark:bg-red-950/20 rounded-2xl border border-red-200 dark:border-red-900/40 shadow-xs">
        <AlertCircle className="size-12 text-red-500 mb-4" />
        <h3 className="text-lg font-bold text-red-700 dark:text-red-400">
          Erreur de Chargement des Lignes et Arrêts
        </h3>
        <p className="text-sm text-red-600 dark:text-red-300 mt-1 max-w-md">
          {networkError}
        </p>
        <button
          onClick={fetchNetworkData}
          className="mt-6 px-4 py-2.5 rounded-xl bg-red-600 text-white font-semibold text-sm hover:bg-red-700 transition-all flex items-center gap-2 shadow-md shadow-red-500/20"
        >
          <RefreshCw className="size-4" /> Réessayer le chargement
        </button>
      </div>
    );
  }

  const filteredBuses = (buses || []).filter((b) => {
    if (!b || !b.bus_id) return false;
    const busId = String(b.bus_id).toLowerCase();
    const routeId = String(b.route_id || "").toLowerCase();
    const search = (searchTerm || "").toLowerCase();

    const matchesSearch = busId.includes(search) || routeId.includes(search);
    const matchesRoute = selectedRoute === "ALL" || b.route_id === selectedRoute;
    return matchesSearch && matchesRoute;
  });

  const tileUrl = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

  const routesToDisplay =
    selectedRoute === "ALL"
      ? Object.entries(routesData)
      : Object.entries(routesData).filter(([key]) => key === selectedRoute);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[650px]">
      {/* Main Map Column */}
      <div className="lg:col-span-8 flex flex-col h-full">
        <ComponentCard
          title="Carte GPS en Direct"
          desc={`Géolocalisation continue des véhicules et tracés des ${Object.keys(routesData).length} lignes COUS-AC UAC`}
          action={
            <div className="flex items-center gap-2">
              <select
                value={selectedRoute}
                onChange={(e) => setSelectedRoute(e.target.value)}
                className="text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 font-medium text-gray-700 dark:text-gray-300"
              >
                <option value="ALL">Afficher les {Object.keys(routesData).length} Lignes</option>
                {Object.entries(routesData).map(([key, r]) => (
                  <option key={key} value={key}>
                    {r.name}
                  </option>
                ))}
              </select>
            </div>
          }
          className="flex-1 flex flex-col p-4 overflow-hidden"
        >
          <div className="relative w-full h-[580px] rounded-xl overflow-hidden border border-gray-200 dark:border-gray-800">
            <MapContainer
              center={center}
              zoom={12}
              maxZoom={18}
              style={{ height: "100%", width: "100%" }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url={tileUrl}
                maxZoom={18}
              />

              {/* Tracés des 14 lignes (OSRM Voies Pratiquables OpenStreetMap) */}
              {routesToDisplay.map(([key, route]) => {
                const positions = osrmRoutes[key] || route.positions || route.waypoints;
                if (!positions || !Array.isArray(positions) || positions.length === 0) return null;

                const isOSRM = Boolean(osrmRoutes[key]);
                return (
                  <Polyline
                    key={key}
                    positions={positions}
                    color={route.color || "#465fff"}
                    weight={selectedRoute === "ALL" ? 4 : 6}
                    opacity={isOSRM ? 0.9 : 0.6}
                    dashArray={isOSRM ? undefined : "6,6"}
                  />
                );
              })}


              {/* Marqueurs arrêts */}
              {stopsList.map((stop) => (
                <Marker key={stop.id} position={[stop.lat, stop.lng]} icon={stopIcon}>
                  <Popup>
                    <div className="p-1 min-w-[160px]">
                      <div className="font-bold text-sm text-gray-900">{stop.name}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        GPS: {stop.lat.toFixed(4)}, {stop.lng.toFixed(4)}
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}

              {/* Marqueurs bus temps réel */}
              {filteredBuses.map((bus) => (
                <Marker
                  key={bus.bus_id}
                  position={[Number(bus.lat), Number(bus.lng)]}
                  icon={createBusIcon(Number(bus.occupancy_rate))}
                >
                  <Popup>
                    <div className="p-2 min-w-[210px] space-y-2">
                      <div className="flex items-center justify-between font-bold text-base text-gray-900">
                        <span>{bus.bus_id}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-600 font-semibold">
                          {bus.route_id || "Ligne non assignée"}
                        </span>
                      </div>
                      <div className="text-xs text-gray-600 flex justify-between">
                        <span>Passagers:</span>
                        <span className="font-semibold">{bus.passengers_count} / {bus.capacity}</span>
                      </div>
                      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-300"
                          style={{
                            width: `${bus.occupancy_rate}%`,
                            backgroundColor: getBusColor(bus.occupancy_rate),
                          }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-xs pt-1 border-t border-gray-100">
                        <span className="text-gray-500 font-medium">Vitesse:</span>
                        <span className="font-bold text-gray-800">{Number(bus.speed || 0).toFixed(0)} km/h</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500 font-medium">Prochain arrêt:</span>
                        <span className="font-semibold text-brand-600">{getStopName(bus.next_stop_id)}</span>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </ComponentCard>
      </div>

      {/* Bus List Column */}
      <div className="lg:col-span-4 flex flex-col h-full">
        <ComponentCard
          title="Bus en Circulation"
          desc={`${buses.length} bus actifs suivis en temps réel`}
          className="flex-1 flex flex-col"
        >
          {/* Search Input */}
          <div className="relative mb-4">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher par Bus ID ou Ligne..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full h-10 pl-10 pr-4 text-sm rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10 transition-all"
            />
          </div>

          {/* Bus Cards List */}
          <div className="flex-1 overflow-y-auto space-y-3 pr-1 custom-scrollbar max-h-[500px]">
            {filteredBuses.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-8 text-center text-gray-400">
                <Bus className="size-10 mb-2 opacity-30" />
                <p className="text-sm font-medium">Aucun bus trouvé</p>
              </div>
            ) : (
              filteredBuses.map((bus) => {
                const color = getBusColor(bus.occupancy_rate);
                const badgeVariant =
                  bus.occupancy_rate >= 90
                    ? "error"
                    : bus.occupancy_rate >= 70
                    ? "warning"
                    : "success";

                return (
                  <div
                    key={bus.bus_id}
                    className="p-4 rounded-xl border border-gray-100 bg-gray-50/50 dark:border-gray-800 dark:bg-gray-800/40 hover:border-brand-300 dark:hover:border-brand-700 transition-all"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-gray-900 dark:text-white">
                          {bus.bus_id}
                        </span>
                        <Badge variant="brand" size="sm">
                          {bus.route_id || "En Transit"}
                        </Badge>
                      </div>
                      <Badge variant={badgeVariant} size="sm">
                        {bus.occupancy_rate}% chargé
                      </Badge>
                    </div>

                    {/* Progress bar */}
                    <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden my-2">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{ width: `${bus.occupancy_rate}%`, backgroundColor: color }}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs pt-2 text-gray-500 dark:text-gray-400">
                      <div className="flex items-center gap-1.5">
                        <Users className="size-3.5 text-gray-400" />
                        <span>{bus.passengers_count} / {bus.capacity} passagers</span>
                      </div>
                      <div className="flex items-center gap-1.5 justify-end">
                        <Gauge className="size-3.5 text-gray-400" />
                        <span>{Number(bus.speed || 0).toFixed(0)} km/h</span>
                      </div>
                    </div>

                    {bus.next_stop_id && (
                      <div className="mt-2 pt-2 border-t border-gray-200/60 dark:border-gray-700/60 flex items-center gap-1 text-[11px] text-brand-600 dark:text-brand-400 font-medium">
                        <span>Suivant: {getStopName(bus.next_stop_id)}</span>
                        <ArrowRight className="size-3" />
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </ComponentCard>
      </div>
    </div>
  );
}
