"""

Toutes les informations sur les 15 arrêts, 14 lignes et 35 bus sont centralisées ici.
"""

# 1. Les 15 Arrêts Officiels COUS-AC 
STOPS = {
    "STOP_UAC": {
        "id": "STOP_UAC",
        "name": "Université d'Abomey-Calavi (Campus UAC)",
        "zone": "Abomey-Calavi",
        "lat": 6.41609,
        "lng": 2.34199,
        "label": "Université d'Abomey-Calavi (Campus UAC)",
        "shortName": "Campus UAC",
    },
    "STOP_GODOMEY": {
        "id": "STOP_GODOMEY",
        "name": "Échangeur Godomey",
        "zone": "Godomey",
        "lat": 6.3888,
        "lng": 2.3485,
        "label": "Échangeur Godomey",
        "shortName": "Godomey",
    },
    "STOP_ETOILE": {
        "id": "STOP_ETOILE",
        "name": "Étoile Rouge (Cotonou)",
        "zone": "Cotonou",
        "lat": 6.3762,
        "lng": 2.4180,
        "label": "Étoile Rouge (Cotonou)",
        "shortName": "Étoile Rouge",
    },
    "STOP_ENEAM": {
        "id": "STOP_ENEAM",
        "name": "ENEAM (Gbégamey)",
        "zone": "Cotonou",
        "lat": 6.3675,
        "lng": 2.4111,
        "label": "ENEAM (Gbégamey)",
        "shortName": "ENEAM",
    },
    "STOP_AKPAKPA": {
        "id": "STOP_AKPAKPA",
        "name": "Akpakpa (Place Lénine)",
        "zone": "Akpakpa",
        "lat": 6.3631,
        "lng": 2.4452,
        "label": "Akpakpa (Place Lénine)",
        "shortName": "Akpakpa",
    },
    "STOP_GANHI": {
        "id": "STOP_GANHI",
        "name": "Marché Ganhi (Cotonou)",
        "zone": "Cotonou",
        "lat": 6.3600,
        "lng": 2.4301,
        "label": "Marché Ganhi (Cotonou)",
        "shortName": "Ganhi",
    },
    "STOP_SURULERE": {
        "id": "STOP_SURULERE",
        "name": "Suru-Léré (Yénawa)",
        "zone": "Akpakpa",
        "lat": 6.3550,
        "lng": 2.4550,
        "label": "Suru-Léré (Yénawa)",
        "shortName": "Suru-Léré",
    },
    "STOP_AVOTROU": {
        "id": "STOP_AVOTROU",
        "name": "Avotrou (Agblangandan)",
        "zone": "Agblangandan",
        "lat": 6.3650,
        "lng": 2.4680,
        "label": "Avotrou (Agblangandan)",
        "shortName": "Avotrou",
    },
    "STOP_FIDJROSSE": {
        "id": "STOP_FIDJROSSE",
        "name": "Fidjrossè (Adjahà)",
        "zone": "Fidjrossè",
        "lat": 6.3620,
        "lng": 2.3780,
        "label": "Fidjrossè (Adjahà)",
        "shortName": "Fidjrossè",
    },
    "STOP_STADE": {
        "id": "STOP_STADE",
        "name": "Stade de l'Amitié Kérékou",
        "zone": "Houéyiho",
        "lat": 6.3820,
        "lng": 2.3720,
        "label": "Stade Kérékou",
        "shortName": "Stade Kérékou",
    },
    "STOP_AGLA": {
        "id": "STOP_AGLA",
        "name": "Agla (Club des Rois)",
        "zone": "Agla",
        "lat": 6.3780,
        "lng": 2.3850,
        "label": "Agla (Club des Rois)",
        "shortName": "Agla",
    },
    "STOP_COCOTOMEY": {
        "id": "STOP_COCOTOMEY",
        "name": "Cocotomey (Zico)",
        "zone": "Godomey",
        "lat": 6.3950,
        "lng": 2.3120,
        "label": "Cocotomey (Zico)",
        "shortName": "Cocotomey",
    },
    "STOP_ADJAGBO": {
        "id": "STOP_ADJAGBO",
        "name": "Akassato (Pylône Adjagbo)",
        "zone": "Akassato",
        "lat": 6.5100,
        "lng": 2.3600,
        "label": "Akassato (Pylône Adjagbo)",
        "shortName": "Adjagbo",
    },
    "STOP_TORI": {
        "id": "STOP_TORI",
        "name": "Togba / Hêvié / Tori",
        "zone": "Tori",
        "lat": 6.4800,
        "lng": 2.2500,
        "label": "Togba / Hêvié / Tori",
        "shortName": "Tori",
    },
    "STOP_PORTO_NOVO": {
        "id": "STOP_PORTO_NOVO",
        "name": "Porto-Novo (Ouando)",
        "zone": "Porto-Novo",
        "lat": 6.4960,
        "lng": 2.6280,
        "label": "Porto-Novo (Ouando)",
        "shortName": "Porto-Novo",
    },
}

# 2. Les 14 Lignes Officiel COUS-AC UAC
ROUTES = {
    "L1_SURULERE": {
        "id": "L1_SURULERE",
        "code": "L1",
        "name": "Ligne 1: Campus UAC ➔ Suru-Léré (Tokpa - Yénawa)",
        "color": "#465fff",
        "stops": ["STOP_UAC", "STOP_GODOMEY", "STOP_ETOILE", "STOP_AKPAKPA", "STOP_SURULERE"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485),
            (6.3820, 2.3720), (6.3780, 2.3850), (6.3750, 2.4000), (6.3762, 2.4180),
            (6.3680, 2.4280), (6.3620, 2.4330), (6.3630, 2.4390), (6.3631, 2.4452),
            (6.3550, 2.4550)
        ],
    },
    "L2_AVOTROU": {
        "id": "L2_AVOTROU",
        "code": "L2",
        "name": "Ligne 2: Campus UAC ➔ Avotrou (Agblangandan)",
        "color": "#7a5af8",
        "stops": ["STOP_UAC", "STOP_GODOMEY", "STOP_ETOILE", "STOP_AVOTROU"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485), (6.3820, 2.3720),
            (6.3762, 2.4180), (6.3680, 2.4280), (6.3630, 2.4390), (6.3631, 2.4452),
            (6.3650, 2.4680)
        ],
    },
    "L3_ADJAHA": {
        "id": "L3_ADJAHA",
        "code": "L3",
        "name": "Ligne 3: Campus UAC ➔ Fidjrossè (Adjahà)",
        "color": "#06aed4",
        "stops": ["STOP_UAC", "STOP_STADE", "STOP_FIDJROSSE"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485), (6.3820, 2.3650),
            (6.3820, 2.3720), (6.3675, 2.3750), (6.3620, 2.3780)
        ],
    },
    "L4_CLUB_ROIS": {
        "id": "L4_CLUB_ROIS",
        "code": "L4",
        "name": "Ligne 4: Campus UAC ➔ Agla (Club des Rois)",
        "color": "#12b76a",
        "stops": ["STOP_UAC", "STOP_GODOMEY", "STOP_AGLA"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485), (6.3820, 2.3720),
            (6.3780, 2.3850)
        ],
    },
    "L5_PECHES": {
        "id": "L5_PECHES",
        "code": "L5",
        "name": "Ligne 5: Campus UAC ➔ Route des Pêches",
        "color": "#f79009",
        "stops": ["STOP_UAC", "STOP_AGLA", "STOP_FIDJROSSE"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485), (6.3820, 2.3720),
            (6.3780, 2.3850), (6.3620, 2.3780)
        ],
    },
    "L6_GBEDJROMEDE": {
        "id": "L6_GBEDJROMEDE",
        "code": "L6",
        "name": "Ligne 6: Campus UAC ➔ Gbèdjromédé (Fifadji)",
        "color": "#ee46bc",
        "stops": ["STOP_UAC", "STOP_GODOMEY", "STOP_ETOILE", "STOP_ENEAM"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485), (6.3820, 2.3720),
            (6.3750, 2.4000), (6.3762, 2.4180), (6.3675, 2.4111)
        ],
    },
    "L7_COCOTOMEY": {
        "id": "L7_COCOTOMEY",
        "code": "L7",
        "name": "Ligne 7: Campus UAC ➔ Cocotomey (Zico)",
        "color": "#9b51e0",
        "stops": ["STOP_UAC", "STOP_GODOMEY", "STOP_COCOTOMEY"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485), (6.3910, 2.3300),
            (6.3950, 2.3120)
        ],
    },
    "L8_ADJAGBO": {
        "id": "L8_ADJAGBO",
        "code": "L8",
        "name": "Ligne 8: Campus UAC ➔ Akassato (Pylône Adjagbo)",
        "color": "#f04438",
        "stops": ["STOP_UAC", "STOP_ADJAGBO"],
        "waypoints": [
            (6.41609, 2.34199), (6.4650, 2.3540), (6.4800, 2.3560), (6.5100, 2.3600)
        ],
    },
    "L9_TORI": {
        "id": "L9_TORI",
        "code": "L9",
        "name": "Ligne 9: Campus UAC ➔ Togba - Hêvié - Tori",
        "color": "#10b981",
        "stops": ["STOP_UAC", "STOP_TORI"],
        "waypoints": [
            (6.41609, 2.34199), (6.4500, 2.3000), (6.4800, 2.2500)
        ],
    },
    "L10_PK10": {
        "id": "L10_PK10",
        "code": "L10",
        "name": "Ligne 10: Campus UAC ➔ PK10 (Sèmè-Kpodji)",
        "color": "#6366f1",
        "stops": ["STOP_UAC", "STOP_ETOILE", "STOP_AKPAKPA", "STOP_AVOTROU"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485), (6.3762, 2.4180),
            (6.3680, 2.4280), (6.3630, 2.4390), (6.3631, 2.4452), (6.3650, 2.4680),
            (6.3700, 2.5200)
        ],
    },
    "L11_PORTO_NOVO": {
        "id": "L11_PORTO_NOVO",
        "code": "L11",
        "name": "Ligne 11: Campus UAC ➔ Porto-Novo (Ouando)",
        "color": "#ec4899",
        "stops": ["STOP_UAC", "STOP_GODOMEY", "STOP_PORTO_NOVO"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485), (6.3762, 2.4180),
            (6.3630, 2.4390), (6.3700, 2.5200), (6.4750, 2.6180), (6.4960, 2.6280)
        ],
    },
    "L12_BON_PASTEUR": {
        "id": "L12_BON_PASTEUR",
        "code": "L12",
        "name": "Ligne 12: Campus UAC ➔ Cadjehoun (Bon Pasteur)",
        "color": "#8b5cf6",
        "stops": ["STOP_UAC", "STOP_GODOMEY", "STOP_STADE"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485), (6.3820, 2.3720),
            (6.3675, 2.3900)
        ],
    },
    "L13_ENEAM": {
        "id": "L13_ENEAM",
        "code": "L13",
        "name": "Ligne 13: Campus UAC ➔ ENEAM Gbégamey ➔ Ganhi",
        "color": "#0284c7",
        "stops": ["STOP_UAC", "STOP_GODOMEY", "STOP_ETOILE", "STOP_ENEAM", "STOP_GANHI"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485), (6.3820, 2.3720),
            (6.3762, 2.4180), (6.3675, 2.4111), (6.3650, 2.4200), (6.3600, 2.4301)
        ],
    },
    "L14_DANGBO": {
        "id": "L14_DANGBO",
        "code": "L14",
        "name": "Ligne 14: Campus UAC ➔ IMS Dangbo",
        "color": "#d97706",
        "stops": ["STOP_UAC", "STOP_PORTO_NOVO"],
        "waypoints": [
            (6.41609, 2.34199), (6.3888, 2.3485), (6.3762, 2.4180),
            (6.3630, 2.4390), (6.3700, 2.5200), (6.4750, 2.6180), (6.4960, 2.6280),
            (6.5800, 2.5500)
        ],
    },
}

# 3. La Flotte Officielle des 35 Bus COUS-AC UAC
BUSES = [
    {"id": "BUS-UAC-01", "registration_number": "RB-BUS-UAC-01", "route_id": "L1_SURULERE", "capacity": 60},
    {"id": "BUS-UAC-02", "registration_number": "RB-BUS-UAC-02", "route_id": "L1_SURULERE", "capacity": 60},
    {"id": "BUS-UAC-03", "registration_number": "RB-BUS-UAC-03", "route_id": "L1_SURULERE", "capacity": 60},
    {"id": "BUS-UAC-04", "registration_number": "RB-BUS-UAC-04", "route_id": "L1_SURULERE", "capacity": 60},
    {"id": "BUS-UAC-05", "registration_number": "RB-BUS-UAC-05", "route_id": "L2_AVOTROU", "capacity": 60},
    {"id": "BUS-UAC-06", "registration_number": "RB-BUS-UAC-06", "route_id": "L2_AVOTROU", "capacity": 60},
    {"id": "BUS-UAC-07", "registration_number": "RB-BUS-UAC-07", "route_id": "L2_AVOTROU", "capacity": 60},
    {"id": "BUS-UAC-08", "registration_number": "RB-BUS-UAC-08", "route_id": "L3_ADJAHA", "capacity": 60},
    {"id": "BUS-UAC-09", "registration_number": "RB-BUS-UAC-09", "route_id": "L3_ADJAHA", "capacity": 60},
    {"id": "BUS-UAC-10", "registration_number": "RB-BUS-UAC-10", "route_id": "L3_ADJAHA", "capacity": 45},
    {"id": "BUS-UAC-11", "registration_number": "RB-BUS-UAC-11", "route_id": "L4_CLUB_ROIS", "capacity": 60},
    {"id": "BUS-UAC-12", "registration_number": "RB-BUS-UAC-12", "route_id": "L4_CLUB_ROIS", "capacity": 60},
    {"id": "BUS-UAC-13", "registration_number": "RB-BUS-UAC-13", "route_id": "L5_PECHES", "capacity": 60},
    {"id": "BUS-UAC-14", "registration_number": "RB-BUS-UAC-14", "route_id": "L5_PECHES", "capacity": 45},
    {"id": "BUS-UAC-15", "registration_number": "RB-BUS-UAC-15", "route_id": "L6_GBEDJROMEDE", "capacity": 60},
    {"id": "BUS-UAC-16", "registration_number": "RB-BUS-UAC-16", "route_id": "L6_GBEDJROMEDE", "capacity": 60},
    {"id": "BUS-UAC-17", "registration_number": "RB-BUS-UAC-17", "route_id": "L7_COCOTOMEY", "capacity": 60},
    {"id": "BUS-UAC-18", "registration_number": "RB-BUS-UAC-18", "route_id": "L7_COCOTOMEY", "capacity": 60},
    {"id": "BUS-UAC-19", "registration_number": "RB-BUS-UAC-19", "route_id": "L8_ADJAGBO", "capacity": 60},
    {"id": "BUS-UAC-20", "registration_number": "RB-BUS-UAC-20", "route_id": "L8_ADJAGBO", "capacity": 60},
    {"id": "BUS-UAC-21", "registration_number": "RB-BUS-UAC-21", "route_id": "L9_TORI", "capacity": 60},
    {"id": "BUS-UAC-22", "registration_number": "RB-BUS-UAC-22", "route_id": "L9_TORI", "capacity": 60},
    {"id": "BUS-UAC-23", "registration_number": "RB-BUS-UAC-23", "route_id": "L10_PK10", "capacity": 60},
    {"id": "BUS-UAC-24", "registration_number": "RB-BUS-UAC-24", "route_id": "L10_PK10", "capacity": 60},
    {"id": "BUS-UAC-25", "registration_number": "RB-BUS-UAC-25", "route_id": "L11_PORTO_NOVO", "capacity": 60},
    {"id": "BUS-UAC-26", "registration_number": "RB-BUS-UAC-26", "route_id": "L11_PORTO_NOVO", "capacity": 60},
    {"id": "BUS-UAC-27", "registration_number": "RB-BUS-UAC-27", "route_id": "L11_PORTO_NOVO", "capacity": 60},
    {"id": "BUS-UAC-28", "registration_number": "RB-BUS-UAC-28", "route_id": "L12_BON_PASTEUR", "capacity": 60},
    {"id": "BUS-UAC-29", "registration_number": "RB-BUS-UAC-29", "route_id": "L12_BON_PASTEUR", "capacity": 60},
    {"id": "BUS-UAC-30", "registration_number": "RB-BUS-UAC-30", "route_id": "L13_ENEAM", "capacity": 60},
    {"id": "BUS-UAC-31", "registration_number": "RB-BUS-UAC-31", "route_id": "L13_ENEAM", "capacity": 60},
    {"id": "BUS-UAC-32", "registration_number": "RB-BUS-UAC-32", "route_id": "L13_ENEAM", "capacity": 60},
    {"id": "BUS-UAC-33", "registration_number": "RB-BUS-UAC-33", "route_id": "L14_DANGBO", "capacity": 60},
    {"id": "BUS-UAC-34", "registration_number": "RB-BUS-UAC-34", "route_id": "L14_DANGBO", "capacity": 60},
    {"id": "BUS-UAC-35", "registration_number": "RB-BUS-UAC-35", "route_id": "L14_DANGBO", "capacity": 60},
]
