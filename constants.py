import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 

# Dati Nave (Visualizzazione & UI)
SHIP_LENGTH = 28.0
SHIP_WIDTH = 11.0

# --- FISICA "BRICK ON ICE" (Experimental V6.60) ---
# Calibrazione per ASD
MASS = 800000.0          # kg (Dislocamento + Massa aggiunta)
INERTIA = 120000000.0    # kg*m^2 (Inerzia aumentata per movimenti più maestosi)

# --- DAMPING (Freno Idrodinamico) ---
# Resistenza proporzionale alla velocità (Viscosità)
# Impedisce alla nave di accelerare all'infinito
DAMP_LINEAR_X = 25000.0  # Freno laterale (Scarroccio) - Più alto perché lo scafo fa muro
DAMP_LINEAR_Y = 8000.0   # Freno longitudinale (Avanzamento) - Più basso, scafo idrodinamico
DAMP_ANGULAR = 40000000.0 # Freno rotazionale - Fondamentale per fermare la trottola
