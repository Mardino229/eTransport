/**
 * Service utilitaire pour interroger l'API OSRM (Open Source Routing Machine)
 * et obtenir les géométries de routes exactes (chaussées goudronnées, carrefours, virages réels).
 */

const osrmCache = new Map<string, [number, number][]>();

export async function fetchOSRMRoute(
  points: [number, number][],
  profile: "driving" | "foot" = "driving"
): Promise<[number, number][]> {
  if (!points || points.length < 2) return points;

  // Clé de cache unique pour éviter des requêtes réseau répétitives
  const cacheKey = `${profile}:${points.map((p) => `${p[0].toFixed(4)},${p[1].toFixed(4)}`).join(";")}`;
  if (osrmCache.has(cacheKey)) {
    return osrmCache.get(cacheKey)!;
  }

  try {
    // OSRM attend les coordonnées au format "longitude,latitude" séparées par des points-virgules
    const formattedCoords = points.map((p) => `${p[1]},${p[0]}`).join(";");
    const url = `https://router.project-osrm.org/route/v1/${profile}/${formattedCoords}?overview=full&geometries=geojson`;

    const response = await fetch(url);
    if (!response.ok) {
      console.warn(`[OSRM] Erreur HTTP ${response.status}, utilisation des points de secours`);
      return points;
    }

    const data = await response.json();
    if (data.code === "Ok" && data.routes && data.routes.length > 0) {
      const geojsonCoords: [number, number][] = data.routes[0].geometry.coordinates;
      // Convertir de [lng, lat] vers Leaflet [lat, lng]
      const leafletCoords: [number, number][] = geojsonCoords.map(([lng, lat]) => [lat, lng]);

      // Forcer le premier et dernier point à correspondre exactement aux coordonnées
      // d'origine pour éviter le "road snapping" d'OSRM qui déplace les extrémités
      // vers des carrefours proches (ex: Carrefour Kpota au lieu du Campus UAC)
      if (leafletCoords.length > 0) {
        leafletCoords[0] = points[0];
        leafletCoords[leafletCoords.length - 1] = points[points.length - 1];
      }

      osrmCache.set(cacheKey, leafletCoords);
      return leafletCoords;
    }
  } catch (err) {
    console.warn("[OSRM] Erreur réseau lors de la récupération du tracé routier:", err);
  }

  return points;
}
