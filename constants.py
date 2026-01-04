import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665

# Posizione Propulsori (Rispetto al centro nave geometrico 0,0)
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 

# Dati Nave Reali
SHIP_LENGTH = 32.50
SHIP_WIDTH = 11.70

# --- FISICA "BRICK ON ICE" (Experimental V6.60 - Heavy Inertia) ---
MASS = 800000.0          # kg 

# AUMENTATA: 80.000.000 (Prima era 60M)
# Più resistenza iniziale alla rotazione = sensazione di maggiore stazza
INERTIA = 80000000.0     

# --- DAMPING (Freno Idrodinamico) ---
# Parametri calibrati sulla manovra "Side Step" e "Avanti"
DAMP_LINEAR_X = 85000.0  # Freno laterale (Side Step ~2.5 kn)
DAMP_LINEAR_Y = 50000.0  # Freno longitudinale
DAMP_ANGULAR = 12000000.0 # Freno rotazionale (mantenuto basso per agilità in velocità)
