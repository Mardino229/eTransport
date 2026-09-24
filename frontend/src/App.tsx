import { useState, useEffect } from "react";
import { AppLayout } from "./layout/AppLayout";
import MapView from "./components/MapView";
import AnalyticsPanel from "./components/AnalyticsPanel";
import RecommendationForm from "./components/RecommendationForm";
import "./index.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

function getWsUrl() {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.hostname || "localhost";
  return `${protocol}//${host}:8000/ws/buses`;
}

export type BusData = {
  bus_id: string;
  route_id: string | null;
  lat: number;
  lng: number;
  speed: number;
  capacity: number;
  passengers_count: number;
  available_seats: number;
  occupancy_rate: number;
  next_stop_id: string | null;
  timestamp: string;
};

export default function App() {
  const [activeTab, setActiveTab] = useState("map");
  const [buses, setBuses] = useState<BusData[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>("--");

  // WebSocket pour le suivi GPS temps réel
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      const wsUrl = getWsUrl();
      console.log(`[WS] Connexion à ${wsUrl}...`);
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
        console.log("[WS] Connecté au canal bus_updates");
      };

      ws.onmessage = (event) => {
        try {
          const raw = JSON.parse(event.data);
          if (raw.type === "snapshot" && Array.isArray(raw.buses)) {
            const data: BusData[] = raw.buses
              .filter((b: any) => b && b.bus_id)
              .map((b: any) => ({
                ...b,
                lat: Number(b.lat || 0),
                lng: Number(b.lng || 0),
                speed: Number(b.speed || 0),
                capacity: Number(b.capacity || 0),
                passengers_count: Number(b.passengers_count || 0),
                available_seats: Number(b.available_seats || 0),
                occupancy_rate: Number(b.occupancy_rate || 0),
              }));
            setBuses(data);
            setLastUpdate(new Date().toLocaleTimeString("fr-FR"));
          } else if (raw && raw.bus_id) {
            const data: BusData = {
              ...raw,
              lat: Number(raw.lat || 0),
              lng: Number(raw.lng || 0),
              speed: Number(raw.speed || 0),
              capacity: Number(raw.capacity || 0),
              passengers_count: Number(raw.passengers_count || 0),
              available_seats: Number(raw.available_seats || 0),
              occupancy_rate: Number(raw.occupancy_rate || 0),
            };
            setBuses((prev) => {
              const idx = prev.findIndex((b) => b?.bus_id === data.bus_id);
              if (idx >= 0) {
                const next = [...prev];
                next[idx] = data;
                return next;
              }
              return [...prev, data];
            });
            setLastUpdate(new Date().toLocaleTimeString("fr-FR"));
          }
        } catch {
          /* ignore */
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        console.log("[WS] Déconnecté. Nouvelle tentative dans 3s...");
        reconnectTimer = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws?.close();
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, []);

  // Polling de secours UNIQUEMENT si WebSocket non connecté
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (!wsConnected) {
      const poll = async () => {
        try {
          const res = await fetch(`${API_BASE}/buses/live`);
          if (res.ok) {
            const rawList: any[] = await res.json();
            const data: BusData[] = rawList.map((raw) => ({
              ...raw,
              lat: Number(raw.lat || 0),
              lng: Number(raw.lng || 0),
              speed: Number(raw.speed || 0),
              capacity: Number(raw.capacity || 0),
              passengers_count: Number(raw.passengers_count || 0),
              available_seats: Number(raw.available_seats || 0),
              occupancy_rate: Number(raw.occupancy_rate || 0),
            }));
            setBuses(data);
            setLastUpdate(new Date().toLocaleTimeString("fr-FR"));
          }
        } catch {
          /* ignore */
        }
      };
      poll();
      interval = setInterval(poll, 5000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [wsConnected]);

  const activeBusesCount = buses.filter((b) => b.passengers_count > 0).length;

  return (
    <AppLayout
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      busesCount={buses.length}
      activeBusesCount={activeBusesCount}
      wsConnected={wsConnected}
      lastUpdate={lastUpdate}
    >
      {activeTab === "map" && <MapView apiBase={API_BASE} buses={buses} />}
      {activeTab === "analytics" && <AnalyticsPanel apiBase={API_BASE} />}
      {activeTab === "reco" && <RecommendationForm apiBase={API_BASE} buses={buses} />}
    </AppLayout>
  );
}
