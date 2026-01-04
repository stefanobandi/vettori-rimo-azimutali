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

# --- FISICA "BRICK ON ICE" (Experimental V6.60 - Precision Tuned) ---
MASS = 800000.0          # kg 

# INERTIA: 60.000.000 (Come richiesto: solido, non scatta a vuoto)
INERTIA = 60000000.0     

# --- DAMPING (Freno Idrodinamico) ---

# CALIBRATO SU SIDE STEP: 11t spinta -> 2.5 nodi velocità
# 108.000 N / 1.28 m/s = ~85.000
DAMP_LINEAR_X = 85000.0  

# CALIBRATO SU AVANTI:
# Impedisce al rimorchiatore di diventare un motoscafo da corsa
DAMP_LINEAR_Y = 50000.0   

# CALIBRATO SU ROTAZIONE:
# Basso (12M) per permettere rotazioni agili come piace a te
DAMP_ANGULAR = 12000000.0
