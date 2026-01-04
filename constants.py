import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665

# Posizione Propulsori (Rispetto al centro nave geometrico 0,0)
# Confermati dai tuoi dati: Y=-12.00, X=2.70
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 

# Dati Nave Reali (Aggiornati)
SHIP_LENGTH = 32.50
SHIP_WIDTH = 11.70

# --- FISICA "BRICK ON ICE" (Experimental V6.60) ---
MASS = 800000.0          # kg (Dislocamento + Massa aggiunta)
INERTIA = 100000000.0    # kg*m^2 (Inerzia aumentata per evitare spin troppo rapidi)

# --- DAMPING (Freno Idrodinamico) ---
DAMP_LINEAR_X = 30000.0  # Freno laterale aumentato (Scafo fa muro)
DAMP_LINEAR_Y = 8000.0   # Freno longitudinale (Avanzamento idrodinamico)
DAMP_ANGULAR = 50000000.0 # Freno rotazionale elevato per stabilità
