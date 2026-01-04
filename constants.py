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

# --- FISICA "BRICK ON ICE" (Experimental V6.60 - Balanced) ---
MASS = 800000.0          # kg (Massa invariata)

# RIPRISTINATA: 60.000.000
# Un po' più di resistenza all'avvio per dare "corposità" alla manovra
INERTIA = 60000000.0     

# --- DAMPING (Freno Idrodinamico) ---
DAMP_LINEAR_X = 30000.0  # Freno laterale (Scarroccio)
DAMP_LINEAR_Y = 8000.0   # Freno longitudinale (Avanzamento)

# MANTENUTO BASSO: 12.000.000
# Una volta partita, la nave gira libera e veloce
DAMP_ANGULAR = 12000000.0
