"""
Données et paramètres du simulateur IoT eTransport COUS-AC.

Les données du réseau (STOPS, ROUTES, BUSES) sont importées directement de la
source unique de vérité `backend/app/data/dataset.py`.
Ce fichier ne conserve que les constantes spécifiques à la physique de simulation.
"""

import sys
import os
import importlib.util

# Détection robuste du chemin d'accès au module backend/app/data/dataset.py (Local & Docker)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

for p in [ROOT_DIR, BACKEND_DIR, "/app", "/app/backend"]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.data.dataset import STOPS, ROUTES, BUSES
except (ModuleNotFoundError, ImportError):
    try:
        from backend.app.data.dataset import STOPS, ROUTES, BUSES
    except (ModuleNotFoundError, ImportError):
        # Fallback de secours si le conteneur s'exécute sans volume monté
        dataset_file = "/app/app/data/dataset.py"
        if not os.path.exists(dataset_file):
            dataset_file = os.path.join(BACKEND_DIR, "app", "data", "dataset.py")
        if os.path.exists(dataset_file):
            spec = importlib.util.spec_from_file_location("dataset_mod", dataset_file)
            if spec and spec.loader:
                dataset_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(dataset_mod)
                STOPS = dataset_mod.STOPS
                ROUTES = dataset_mod.ROUTES
                BUSES = dataset_mod.BUSES
        else:
            raise RuntimeError(f"Fichier dataset.py introuvable aux emplacements attendus.")

# Paramètres Physiques & Temporels du Simulateur IoT 
GPS_UPDATE_INTERVAL = 2  # Intervalle de rafraîchissement des télémétries GPS (secondes)
BUS_SPEED_KMH = 32.0     # Vitesse moyenne de circulation des bus (km/h)

# Horaires de départ officiels du réseau universitaire COUS-AC
DEPARTURE_SLOTS = ["06:30", "07:45", "09:10", "13:00", "16:00", "19:00"]

# Coefficients d'affluence réels des étudiants (Heures de pointe matin & soir)
PEAK_MORNING = {"start_h": 6, "start_m": 30, "end_h": 9, "end_m": 10, "factor": 3.0}
PEAK_EVENING = {"start_h": 16, "start_m": 0, "end_h": 19, "end_m": 30, "factor": 2.8}
