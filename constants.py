import numpy as np

# --- CONFIGURAZIONE FISICA NAVALE (V7.1 - Auto Pivot Logic) ---

G_ACCEL = 9.80665

# Dimensioni nave (ASD Tug)
SHIP_WIDTH = 12.0
SHIP_LENGTH = 32.0

# Massa e Inerzia
SHIP_MASS = 800000.0     # 800 Tonnellate
MOMENT_OF_INERTIA = 100000000.0  # Alta inerzia (Stable Tuning)

# Posizioni Geometriche Chiave
# SKEG (Prua): Punto di resistenza laterale massima
POS_SKEG_Y = 5.0    
# STERN (Poppa): Punto di applicazione spinta motori e pivot per rotazione pura
POS_STERN_Y = -12.0 

# Posizione Propulsori (Offset dal centro geometrico 0,0)
# Usati per il calcolo del momento
THRUSTER_X_OFFSET = 3.5
THRUSTER_Y_OFFSET = -12.0 

# Motori
BOLLARD_PULL_PER_ENGINE = 35.0 # Tonnellate
MAX_THRUST = 750000.0          # Newton (approx 75 ton)

# Damping (Resistenze Idrodinamiche)
LINEAR_DAMPING_SURGE = 50000.0
LINEAR_DAMPING_SWAY = 350000.0   # Alto per simulare la carena profonda
ANGULAR_DAMPING = 30000000.0     # Alto per stabilità

# Posizioni per calcoli vettoriali V6.62
POS_THRUSTERS_X = THRUSTER_X_OFFSET
POS_THRUSTERS_Y = THRUSTER_Y_OFFSET

# Visualizzazione
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
COLOR_SEA = (20, 30, 40)
