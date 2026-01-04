import numpy as np

# --- DIMENSIONI & GEOMETRIA ---
G_ACCEL = 9.80665
POS_THRUSTERS_Y = -12.0
POS_THRUSTERS_X = 2.7
BOLLARD_PULL_PER_ENGINE = 35.0 

# --- FISICA "BRICK ON ICE" (Experimental) ---
# Calibrazione per ASD 2810 (circa)
# Massa aumentata (Added Mass) per simulare l'acqua spostata
MASS = 850000.0          # kg (Dislocamento + Massa aggiunta)
INERTIA = 100000000.0    # kg*m^2 (Inerzia rotazionale molto alta per evitare trottole)

# --- DAMPING (Freno Idrodinamico Semplificato) ---
# Questi valori frenano il "ghiaccio". 
# Più alti sono, più la nave è "immersa nella melassa".
DAMP_LINEAR_X = 15000.0  # Resistenza allo scarroccio laterale
DAMP_LINEAR_Y = 5000.0   # Resistenza all'avanzamento (minore dello scarroccio)
DAMP_ANGULAR = 25000000.0 # Resistenza alla rotazione (molto alta per stabilità)
