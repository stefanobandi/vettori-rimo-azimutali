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

# --- FISICA "BRICK ON ICE" (Tuning V6.62 - Stable & Heavy) ---
MASS = 800000.0          # kg 

# AUMENTATA: 100.000.000 (Era 80M)
# Rende la nave molto più restia a iniziare a ruotare per errore.
# Filtra le "sporcizie" vettoriali nei Side Step.
INERTIA = 100000000.0     

# --- DAMPING (Freno Idrodinamico) ---
DAMP_LINEAR_X = 85000.0  # Freno laterale (Invariato - ottimo per Side Step)
DAMP_LINEAR_Y = 50000.0  # Freno longitudinale (Invariato)

# AUMENTATO DRASTICAMENTE: 30.000.000 (Era 12M)
# Questo è il "segreto": un freno rotazionale alto impedisce che
# un piccolo disallineamento del vettore forza crei una rotazione continua.
# La nave tenderà a raddrizzarsi o a ruotare molto lentamente.
DAMP_ANGULAR = 20000000.0
