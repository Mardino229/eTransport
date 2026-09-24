import React, { useState, useEffect } from "react";
import { Navigation, Loader2, CheckCircle2, AlertCircle, Bus, Clock, Footprints, Users, RefreshCw } from "lucide-react";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { BusData } from "../App";
import { ComponentCard } from "./common/ComponentCard";
import { Badge } from "./ui/badge/Badge";
import { fetchOSRMRoute } from "../services/osrmService";

const studentIcon = L.divIcon({
  className: "",
  html: `<div style="
    width:30px; height:30px;
    background:#0284c7;
    border-radius:50%;
    border:2.5px solid white;
    box-shadow:0 4px 10px rgba(2,132,199,0.5);
    display:flex; align-items:center; justify-content:center;
    font-size:14px; color:white;
  ">🎓</div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15],
});

const destIcon = L.divIcon({
  className: "",
  html: `<div style="
    width:30px; height:30px;
    background:#10b981;
    border-radius:50%;
    border:2.5px solid white;
    box-shadow:0 4px 10px rgba(16,185,129,0.5);
    display:flex; align-items:center; justify-content:center;
    font-size:14px; color:white;
  ">🏁</div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15],
});

const busMarkerIcon = L.divIcon({
  className: "",
  html: `<div style="
    width:30px; height:30px;
    background:#465fff;
    border-radius:50%;
    border:2.5px solid white;
    box-shadow:0 4px 10px rgba(70,95,255,0.5);
    display:flex; align-items:center; justify-content:center;
    font-size:14px; color:white;
  ">🚌</div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15],
});

interface RecommendationRequest {
  student_id: string;
  student_lat: number;
  student_lng: number;
  destination_stop_id: string;
}

interface ScoreBreakdown {
  arrival_time_score: number;
  walking_distance_score: number;
  trip_time_score: number;
  occupancy_score: number;
  uturn_penalty_score?: number;
  final_score: number;
}

interface BusCandidate {
  bus_id: string;
  route_id: string | null;
  lat: number;
  lng: number;
  available_seats: number;
  capacity: number;
  occupancy_rate: number;
  eta_min: number;
  walking_distance_km: number;
  trip_duration_min: number;
  score: number;
  score_breakdown: ScoreBreakdown;
  is_direct: boolean;
  uturn_delay_min: number;
}

interface RecommendationResponse {
  student_id: string;
  destination_stop_id: string;
  recommended_bus: BusCandidate;
  alternatives: BusCandidate[];
  reserved: boolean;
  timestamp: string;
}

export interface Stop {
  id: string;
  name: string;
  lat: number;
  lng: number;
  shortName?: string;
  label?: string;
}

interface Props {
  apiBase: string;
  buses: BusData[];
}

export default function RecommendationForm({ apiBase, buses }: Props) {
  const [form, setForm] = useState<RecommendationRequest>({
    student_id: `STU_${Math.floor(Math.random() * 9000 + 1000)}`,
    student_lat: 6.368,
    student_lng: 2.412,
    destination_stop_id: "STOP_UAC",
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [walkPath, setWalkPath] = useState<[number, number][]>([]);
  const [busPath, setBusPath] = useState<[number, number][]>([]);

  const [stopsList, setStopsList] = useState<Stop[]>([]);
  const [stopsLoading, setStopsLoading] = useState(true);
  const [stopsError, setStopsError] = useState<string | null>(null);

  const fetchStops = async () => {
    setStopsLoading(true);
    setStopsError(null);
    try {
      const res = await fetch(`${apiBase}/network/stops`);
      if (!res.ok) {
        throw new Error(`Serveur HTTP ${res.status}`);
      }
      const contentType = res.headers.get("content-type") || "";
      if (!contentType.includes("application/json")) {
        throw new Error("Réponse non-JSON reçue (le serveur backend est indisponible ou en cours de démarrage).");
      }
      const data = await res.json();
      if (!Array.isArray(data) || data.length === 0) {
        throw new Error("Aucun arrêt de bus valide n'a été retourné par le backend");
      }
      setStopsList(data);
      if (data.length > 0 && (!form.destination_stop_id || !data.some((s) => s.id === form.destination_stop_id))) {
        setForm((p) => ({ ...p, destination_stop_id: data[0].id }));
      }
    } catch (err: any) {
      console.warn("Avertissement arrêts RecommendationForm:", err);
      const friendlyMsg = err instanceof SyntaxError
        ? "Le serveur API n'est pas prêt (réponse non-JSON)."
        : err.message || "Impossible de charger les arrêts.";
      setStopsError(friendlyMsg);
    } finally {
      setStopsLoading(false);
    }
  };

  useEffect(() => {
    fetchStops();
  }, [apiBase]);

  useEffect(() => {
    if (!result) return;
    const sLat = form.student_lat;
    const sLng = form.student_lng;
    const bus = result.recommended_bus;

    const destStopObj = stopsList.find((s) => s.id === form.destination_stop_id);
    const destLat = destStopObj ? destStopObj.lat : 6.41609;
    const destLng = destStopObj ? destStopObj.lng : 2.34199;

    // 1. Trajet piéton OSRM (Walk path) de l'étudiant vers le bus
    fetchOSRMRoute([[sLat, sLng], [bus.lat, bus.lng]], "foot").then((res) => setWalkPath(res));

    // 2. Trajet routier OSRM (Bus driving path) du bus vers l'arrêt destination
    fetchOSRMRoute([[bus.lat, bus.lng], [destLat, destLng]], "driving").then((res) => setBusPath(res));
  }, [result, stopsList]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${apiBase}/recommendation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Erreur de recommandation");
      }
      setResult(await res.json());
    } catch (err: any) {
      setError(err.message || "Erreur réseau");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      {/* Left Form Column */}
      <div className="lg:col-span-5">
        <ComponentCard
          title="Simulateur de Demande Étudiant"
          desc="Testez l'algorithme d'affectation automatique avec scoring pondéré"
        >
          {stopsError && (
            <div className="p-3 mb-4 rounded-xl border border-red-200 bg-red-50 dark:border-red-900/40 dark:bg-red-950/20 text-red-700 dark:text-red-400 text-xs flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <AlertCircle className="size-4 shrink-0 text-red-500" />
                <span>{stopsError}</span>
              </div>
              <button
                type="button"
                onClick={fetchStops}
                className="px-2 py-1 bg-red-600 text-white font-medium rounded hover:bg-red-700 text-[11px] shrink-0 flex items-center gap-1"
              >
                <RefreshCw className="size-3" /> Réessayer
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-1.5">
                ID Étudiant
              </label>
              <input
                type="text"
                value={form.student_id}
                onChange={(e) => setForm((p) => ({ ...p, student_id: e.target.value }))}
                placeholder="STU_1234"
                className="w-full h-10 px-3.5 text-sm rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10 transition-all"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-1.5">
                  Latitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={form.student_lat}
                  onChange={(e) => setForm((p) => ({ ...p, student_lat: parseFloat(e.target.value) }))}
                  className="w-full h-10 px-3.5 text-sm rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10 transition-all"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-1.5">
                  Longitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={form.student_lng}
                  onChange={(e) => setForm((p) => ({ ...p, student_lng: parseFloat(e.target.value) }))}
                  className="w-full h-10 px-3.5 text-sm rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-1.5">
                Arrêt Destination
              </label>
              {stopsLoading ? (
                <div className="flex items-center gap-2 text-xs text-brand-600 dark:text-brand-400 py-2.5 px-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                  <Loader2 className="size-4 animate-spin text-brand-500" />
                  <span>Chargement des arrêts du réseau...</span>
                </div>
              ) : (
                <select
                  value={form.destination_stop_id}
                  onChange={(e) => setForm((p) => ({ ...p, destination_stop_id: e.target.value }))}
                  disabled={stopsList.length === 0}
                  className="w-full h-10 px-3.5 text-sm rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/10 transition-all"
                >
                  {stopsList.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name || s.label}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Quick Position Selectors */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
                Positions Rapides
              </label>
              {stopsLoading ? (
                <div className="flex items-center gap-2 text-xs text-gray-400 py-1">
                  <Loader2 className="size-3.5 animate-spin" />
                  <span>Chargement des positions...</span>
                </div>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {stopsList.map((s) => (
                    <button
                      type="button"
                      key={s.id}
                      onClick={() => setForm((p) => ({ ...p, student_lat: s.lat, student_lng: s.lng }))}
                      className="px-2.5 py-1 text-xs font-medium rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors"
                    >
                      {s.shortName || s.name || s.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || stopsLoading || stopsList.length === 0}
              className="w-full h-11 mt-2 flex items-center justify-center gap-2 rounded-xl bg-brand-500 text-white font-semibold text-sm hover:bg-brand-600 disabled:opacity-50 transition-all shadow-md shadow-brand-500/20"
            >
              {loading ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Calcul de la Recommandation...
                </>
              ) : (
                <>
                  <Navigation className="size-4" />
                  Trouver le Meilleur Bus
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>Flotte active:</span>
            <span className="font-semibold text-gray-900 dark:text-white">
              {buses.filter((b) => b.available_seats > 0).length} / {buses.length} bus disponibles
            </span>
          </div>
        </ComponentCard>
      </div>

      {/* Right Results Column */}
      <div className="lg:col-span-7">
        {error && (
          <div className="p-4 rounded-2xl border border-error-200 bg-error-50 dark:border-error-500/30 dark:bg-error-500/10 flex items-center gap-3 text-error-700 dark:text-error-400">
            <AlertCircle className="size-5" />
            <span className="font-semibold text-sm">{error}</span>
          </div>
        )}

        {result && (
          <div className="space-y-6">
            {/* Recommended Bus Card */}
            <ComponentCard
              title="Bus Recommandé par l'IA"
              desc="Sélectionné d'après la fonction de score pondérée et réservation atomique Redis"
              action={
                result.reserved ? (
                  <Badge variant="success">✓</Badge>
                ) : (
                  <Badge variant="warning">Non réservé</Badge>
                )
              }
            >
              <div className="flex items-center justify-between p-4 rounded-2xl bg-brand-50/50 dark:bg-brand-500/10 border border-brand-100 dark:border-brand-500/20 mb-6">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center size-12 rounded-xl bg-emerald-500 text-white shadow-md shadow-emerald-500/20">
                    <CheckCircle2 className="size-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                        {result.recommended_bus.bus_id}
                      </h3>
                      {result.recommended_bus.is_direct ? (
                        <Badge variant="success">⚡ Direct (En amont)</Badge>
                      ) : (
                        <Badge variant="warning">
                          🔄 Demi-tour (+{result.recommended_bus.uturn_delay_min} min)
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs font-medium text-brand-600 dark:text-brand-400 mt-0.5">
                      Ligne : {result.recommended_bus.route_id || "Direct"}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-brand-600 dark:text-brand-400">
                    Score {(Number(result.recommended_bus.score || 0) * 100).toFixed(0)}
                  </div>
                  <div className="text-[11px] text-gray-500 dark:text-gray-400">
                    Score pondéré (le plus bas est le meilleur)
                  </div>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                <div className="p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 text-center">
                  <Clock className="size-4 text-brand-500 mx-auto mb-1" />
                  <div className="text-lg font-bold text-gray-900 dark:text-white">
                    {Number(result.recommended_bus.eta_min || 0).toFixed(0)} min
                  </div>
                  <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase">ETA Bus</div>
                </div>

                <div className="p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 text-center">
                  <Footprints className="size-4 text-cyan-500 mx-auto mb-1" />
                  <div className="text-lg font-bold text-gray-900 dark:text-white">
                    {(Number(result.recommended_bus.walking_distance_km || 0) * 1000).toFixed(0)} m
                  </div>
                  <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase">Distance Marche</div>
                </div>

                <div className="p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 text-center">
                  <Users className="size-4 text-emerald-500 mx-auto mb-1" />
                  <div className="text-lg font-bold text-gray-900 dark:text-white">
                    {result.recommended_bus.available_seats}
                  </div>
                  <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase">Places Libres</div>
                </div>

                <div className="p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 text-center">
                  <Bus className="size-4 text-amber-500 mx-auto mb-1" />
                  <div className="text-lg font-bold text-gray-900 dark:text-white">
                    {result.recommended_bus.occupancy_rate}%
                  </div>
                  <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase">Remplissage</div>
                </div>
              </div>

              {/* Score breakdown detail */}
              <div className="p-4 rounded-xl bg-gray-50/80 dark:bg-gray-800/40 border border-gray-200/60 dark:border-gray-800 space-y-2">
                <div className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
                  Détail de la Fonction de Score
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between text-gray-600 dark:text-gray-300">
                    <span>Temps d'arrivée ETA (× 0.35)</span>
                    <span className="font-mono">{result.recommended_bus.score_breakdown.arrival_time_score}</span>
                  </div>
                  <div className="flex justify-between text-gray-600 dark:text-gray-300">
                    <span>Distance de marche (× 0.25)</span>
                    <span className="font-mono">{result.recommended_bus.score_breakdown.walking_distance_score}</span>
                  </div>
                  <div className="flex justify-between text-gray-600 dark:text-gray-300">
                    <span>Durée trajet (× 0.25)</span>
                    <span className="font-mono">{result.recommended_bus.score_breakdown.trip_time_score}</span>
                  </div>
                  <div className="flex justify-between text-gray-600 dark:text-gray-300">
                    <span>Taux d'occupation (× 0.15)</span>
                    <span className="font-mono">{result.recommended_bus.score_breakdown.occupancy_score}</span>
                  </div>
                  {Boolean(result.recommended_bus.score_breakdown.uturn_penalty_score) && (
                    <div className="flex justify-between text-amber-600 dark:text-amber-400 font-medium">
                      <span>Pénalité Demi-tour (Terminus)</span>
                      <span className="font-mono">+{result.recommended_bus.score_breakdown.uturn_penalty_score}</span>
                    </div>
                  )}
                  <div className="flex justify-between pt-2 border-t border-gray-200 dark:border-gray-700 font-bold text-gray-900 dark:text-white">
                    <span>Score Final Total</span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-mono">
                      {Number(result.recommended_bus.score_breakdown.final_score || 0).toFixed(4)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Carte d'Itinéraire OSRM Voies Pratiquables */}
              <div className="mt-4 p-4 rounded-xl bg-gray-50/80 dark:bg-gray-800/40 border border-gray-200/60 dark:border-gray-800 space-y-2">
                <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                  <span>Itinéraire Routier OSRM (Voies Pratiquables)</span>
                  <Badge variant="brand">OpenStreetMap</Badge>
                </div>
                <div className="relative w-full h-[220px] rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
                  <MapContainer
                    center={[form.student_lat, form.student_lng]}
                    zoom={12}
                    style={{ height: "100%", width: "100%" }}
                  >
                    <TileLayer
                      attribution='&copy; OpenStreetMap'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    <Marker position={[form.student_lat, form.student_lng]} icon={studentIcon}>
                      <Popup>🎓 Position Étudiant ({form.student_id})</Popup>
                    </Marker>

                    <Marker position={[result.recommended_bus.lat, result.recommended_bus.lng]} icon={busMarkerIcon}>
                      <Popup>🚌 Bus Recommandé: {result.recommended_bus.bus_id}</Popup>
                    </Marker>

                    {(() => {
                      const destObj = stopsList.find((s) => s.id === form.destination_stop_id);
                      const dLat = destObj ? destObj.lat : 6.41609;
                      const dLng = destObj ? destObj.lng : 2.34199;
                      return (
                        <Marker position={[dLat, dLng]} icon={destIcon}>
                          <Popup>🏁 Arrêt Destination ({destObj?.name || destObj?.label || form.destination_stop_id})</Popup>
                        </Marker>
                      );
                    })()}

                    {walkPath.length > 0 && (
                      <Polyline positions={walkPath} color="#0284c7" weight={4} dashArray="6,6" />
                    )}

                    {busPath.length > 0 && (
                      <Polyline positions={busPath} color="#10b981" weight={5} />
                    )}
                  </MapContainer>
                </div>
                <div className="flex items-center gap-4 text-[11px] text-gray-500 pt-1">
                  <span className="flex items-center gap-1"><span className="w-3 h-1 bg-cyan-600 rounded"></span> 🚶 Trajet Piéton OSRM</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-1 bg-emerald-500 rounded"></span> 🚌 Trajet Bus Voies Pratiquables</span>
                </div>
              </div>
            </ComponentCard>

            {/* Alternatives Card */}
            {result.alternatives.length > 0 && (
              <ComponentCard title="Alternatives Disponibles" desc="Bus de secours classés par score de pertinence">
                <div className="space-y-2">
                  {result.alternatives.map((alt, i) => (
                    <div
                      key={alt.bus_id}
                      className="p-3.5 rounded-xl border border-gray-100 bg-gray-50/50 dark:border-gray-800 dark:bg-gray-800/40 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-3">
                        <span className="font-bold text-gray-400">#{i + 2}</span>
                        <span className="font-bold text-gray-900 dark:text-white">{alt.bus_id}</span>
                        <Badge variant="neutral" size="sm">
                          {alt.route_id || "Ligne"}
                        </Badge>
                        {alt.is_direct ? (
                          <Badge variant="success" size="sm">⚡ Direct</Badge>
                        ) : (
                          <Badge variant="warning" size="sm">🔄 Demi-tour (+{alt.uturn_delay_min}m)</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-gray-600 dark:text-gray-300">
                        <span>⏱ ETA {Number(alt.eta_min || 0).toFixed(0)} min</span>
                        <span>💺 {alt.available_seats} seats</span>
                        <span className="font-semibold text-brand-600 dark:text-brand-400">
                          Score {(Number(alt.score || 0) * 100).toFixed(0)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </ComponentCard>
            )}
          </div>
        )}

        {!result && !error && !loading && (
          <ComponentCard title="Résultat de la Recommandation">
            <div className="flex flex-col items-center justify-center p-12 text-center text-gray-400">
              <Navigation className="size-12 mb-3 opacity-20" />
              <h4 className="text-base font-bold text-gray-700 dark:text-gray-300">
                Simulez une demande de transport
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-sm">
                Remplissez les informations de position de l'étudiant à gauche pour déclencher l'algorithme d'optimisation.
              </p>
            </div>
          </ComponentCard>
        )}
      </div>
    </div>
  );
}
