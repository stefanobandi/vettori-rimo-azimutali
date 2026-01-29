import numpy as np

# --- CONFIGURAZIONE FISICA NAVALE (V7.1 - Auto Pivot Logic) ---

# Dimensioni nave (ASD Tug)
SHIP_WIDTH = 12.0
SHIP_LENGTH = 32.0

# Massa e Inerzia
SHIP_MASS = 800000.0     # 800 Tonnellate
MOMENT_OF_INERTIA = 100000000.0  # Alta inerzia (Stable Tuning)

# Posizioni Geometriche Chiave
POS_SKEG_Y = 5.0    
POS_STERN_Y = -12.0 

# Posizione Propulsori (Offset dal centro 0,0)
THRUSTER_X_OFFSET = 3.5
THRUSTER_Y_OFFSET = -12.0 

# Motori
MAX_THRUST = 750000.0    # 75 ton per motore

# Damping (Resistenze Idrodinamiche)
LINEAR_DAMPING_SURGE = 50000.0
LINEAR_DAMPING_SWAY = 350000.0   
ANGULAR_DAMPING = 30000000.0     

# Visualizzazione
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
PIXELS_PER_METER = 10
COLOR_SEA = (20, 30, 40)
