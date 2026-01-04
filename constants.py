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

# --- FISICA "BRICK ON ICE" (Experimental V6.60 - Agile Rotation) ---
MASS = 800000.0          # kg (Manteniamo pesantezza per evitare effetto polistirolo)

# PRIMA: 100.000.000 -> ORA: 60.000.000
# Meno inerzia = Inizia a girare più facilmente
INERTIA = 60000000.0     

# --- DAMPING (Freno Idrodinamico) ---
DAMP_LINEAR_X = 30000.0  # Freno laterale (Scarroccio)
DAMP_LINEAR_Y = 8000.0   # Freno longitudinale (Avanzamento)

# PRIMA: 50.000.000 -> ORA: 25.000.000
# Meno freno rotazionale = La rotazione continua e si accumula meglio
DAMP_ANGULAR = 25000000.0
